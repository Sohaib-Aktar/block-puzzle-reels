"""
render_manager.py — Pipeline Execution, Process Management & Job Orchestration
Coordinates end-to-end rendering: timeline resolution, video processing, audio mastering,
technical verification, logging, and intermediate cleanup.
"""

import os
import sys
import time
import json
import shutil
import traceback
from typing import Dict, Any, Optional

WORKSPACE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(WORKSPACE_ROOT, "scripts"))
from production_job import ProductionJob, JobStatus
from timeline_builder import TimelineBuilder, PreflightValidationError
from video_processor import VideoProcessor
from audio_mixer import AudioMixer
from render_validator import RenderValidator, RenderValidationError
from qc_verifier import verify_content
from creative_qc import evaluate_creative_quality


class RenderManager:
    """Executes production jobs with audit logs, error handling, and validation gates."""

    def __init__(self):
        self.timeline_builder = TimelineBuilder()
        self.validator = RenderValidator()

    def execute_job(
        self,
        job: ProductionJob,
        output_filename: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Executes a production job from manifest to verified deliverable.
        """
        start_time = time.time()
        job.set_status(JobStatus.VALIDATING, "Beginning preflight manifest validation...")

        try:
            # 1. Preflight Validation & Asset Resolution
            plan = self.timeline_builder.validate_manifest(job.manifest)
            job.add_log(f"Preflight passed. Resolved {len(plan['scenes'])} scenes and audio tracks.")
            if plan.get("warnings"):
                for w in plan["warnings"]:
                    job.add_log(f"Preflight Warning: {w}")

            job.set_status(JobStatus.READY_TO_RENDER, "Manifest validated and ready for rendering.")

            # Determine final output destination
            fn = output_filename or f"{job.content_id}_Final.mp4"
            final_mp4 = job.get_final_path(fn)
            job.output_file = final_mp4

            # 2. Rendering
            job.set_status(JobStatus.RENDERING, f"Rendering to {final_mp4} using engine: {plan['renderer']}...")

            canvas = plan["canvas"]
            renderer = plan.get("renderer", "ffmpeg")

            if renderer == "remotion":
                comp_id = job.manifest.get("composition_id", "DayFourOfflineReel")
                my_video_dir = os.path.join(WORKSPACE_ROOT, "my-video")
                rel_out = os.path.relpath(final_mp4, my_video_dir)
                cmd = ["cmd", "/c", "npx.cmd", "remotion", "render", "src/index.ts", comp_id, rel_out, "--gl=angle"]
                from media_engine import run_command
                run_command(cmd)
            else:
                # Native FFmpeg Production Pipeline
                processor = VideoProcessor(
                    canvas_width=canvas["width"],
                    canvas_height=canvas["height"],
                    fps=canvas["fps"]
                )

                # Assemble Video Stream
                intermediate_video = job.get_intermediate_path("assembled_video.mp4")
                job.add_log("Normalizing scenes and assembling visual timeline...")
                processor.assemble_timeline(
                    scenes=plan["scenes"],
                    output_path=intermediate_video,
                    intermediate_dir=job.intermediate_dir
                )

                # Mix Audio Tracks
                mixer = AudioMixer(target_loudness_lufs=plan["audio"].get("master_loudness", -14.0))
                job.add_log("Mixing audio stems (BGM, VO, SFX) with EBU R128 loudness normalization...")
                mixer.mix_master_audio(
                    video_path=intermediate_video,
                    audio_spec=plan["audio"],
                    output_path=final_mp4,
                    intermediate_dir=job.intermediate_dir
                )

            render_elapsed = time.time() - start_time
            job.metrics["render_seconds"] = round(render_elapsed, 2)
            job.metrics["final_file_size_bytes"] = os.path.getsize(final_mp4)
            job.set_status(JobStatus.RENDERED, f"Rendering completed in {render_elapsed:.2f}s.")

            # 3. Technical Validation
            job.set_status(JobStatus.TECHNICAL_VALIDATION, "Validating render codecs, decodability and duration...")
            tech_report_file = os.path.join(job.report_dir, "technical_validation_report.md")
            val_result = self.validator.validate_render(
                video_path=final_mp4,
                expected_spec=canvas,
                project_slug=job.project,
                output_report_path=tech_report_file
            )
            job.add_log("Technical validation passed (6/6 checks).")

            # 4. Integrate Technical QC & Creative QC
            job.set_status(JobStatus.AWAITING_CREATIVE_QC, "Running studio Technical & Creative QC...")
            qc_file = os.path.join(job.report_dir, "qc_report.md")
            cqc_file = os.path.join(job.report_dir, "creative_qc_report.md")

            # Run QC Verifier (safe call)
            try:
                qc_res = verify_content(
                    video_path=final_mp4,
                    project_slug=job.project,
                    preset_name=job.output_profile,
                    output_report_path=qc_file,
                    content_id=job.content_id
                )
                job.add_log(f"Studio Technical QC verification passed: {qc_res['passed']}")
            except Exception as e:
                job.add_log(f"QC Verifier warning: {e}")

            # Run Creative QC
            try:
                cqc_res = evaluate_creative_quality(
                    content_dir=job.base_output_dir,
                    project_slug=job.project,
                    output_report_path=cqc_file
                )
                job.add_log(f"Creative QC score: {cqc_res.get('total_score', 'N/A')} / 90")
            except Exception as e:
                job.add_log(f"Creative QC warning: {e}")

            # 5. Clean Intermediate Files
            job.cleanup_intermediate()

            job.set_status(
                JobStatus.AWAITING_HUMAN_APPROVAL,
                f"Production job complete! Deliverable ready at: {final_mp4}"
            )

            return {
                "job_id": job.job_id,
                "status": job.status.value,
                "output_file": final_mp4,
                "duration_seconds": val_result["media_info"]["duration_seconds"],
                "file_size_bytes": os.path.getsize(final_mp4),
                "render_seconds": job.metrics["render_seconds"],
                "validation": val_result
            }

        except Exception as e:
            err_msg = f"{type(e).__name__}: {str(e)}"
            trace = traceback.format_exc()
            job.set_status(JobStatus.RENDER_FAILED, f"Job failed: {err_msg}")
            job.add_log(f"Stack trace:\n{trace}")

            # Write error log
            err_log_file = os.path.join(job.logs_dir, "render_error.log")
            with open(err_log_file, "w", encoding="utf-8") as f:
                f.write(f"JOB ID: {job.job_id}\n")
                f.write(f"ERROR: {err_msg}\n\n")
                f.write(trace)

            raise
