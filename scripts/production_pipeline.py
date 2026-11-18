"""
production_pipeline.py — Master CLI & Orchestrator for Phase 3 Production Pipeline
Provides operational CLI commands for manifest validation, job execution, preview, and status tracking.
"""

import os
import sys
import json
import argparse
from typing import Dict, Any, Optional

WORKSPACE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(WORKSPACE_ROOT, "scripts"))
from production_job import ProductionJob, JobStatus
from timeline_builder import TimelineBuilder
from render_manager import RenderManager


def cmd_validate(manifest_path: str, allow_review_audio: bool = False) -> bool:
    """Validates an editing manifest and prints a structured preflight audit."""
    print(f"\n=======================================================")
    print(f"      PREFLIGHT MANIFEST VALIDATION AUDIT")
    print(f"=======================================================")
    abs_manifest = os.path.abspath(manifest_path)
    if not os.path.exists(abs_manifest):
        print(f"❌ Error: Manifest file not found: {abs_manifest}")
        return False

    with open(abs_manifest, "r", encoding="utf-8") as f:
        data = json.load(f)

    if allow_review_audio:
        data["allow_review_audio"] = True

    builder = TimelineBuilder()
    try:
        plan = builder.validate_manifest(data)
        print(f"✅ Preflight Validation: PASSED")
        print(f"   • Project         : {plan['project']}")
        print(f"   • Campaign        : {plan['campaign']}")
        print(f"   • Content ID      : {plan['content_id']}")
        print(f"   • Output Profile  : {plan['output_profile']}")
        print(f"   • Canvas Spec     : {plan['canvas']['width']}x{plan['canvas']['height']} @ {plan['canvas']['fps']}fps ({plan['canvas']['duration_seconds']:.2f}s)")
        print(f"   • Resolved Scenes : {len(plan['scenes'])} scenes")
        for sc in plan["scenes"]:
            print(f"     - [{sc['scene_id']}] {os.path.basename(sc['file_path'])} ({sc['source_in']:.1f}s -> {sc['source_out']:.1f}s, dur: {sc['duration']:.1f}s, overlays: {len(sc['overlays'])})")

        audio = plan["audio"]
        print(f"   • Audio Elements  :")
        if audio.get("music"):
            m = audio["music"]
            print(f"     - Music Track  : {m['filename']} (Licensing: {m['license_status']}, Vol: {m['volume']})")
        if audio.get("voiceover"):
            v = audio["voiceover"]
            vo_desc = f"Text: \"{v['text'][:35]}...\"" if v.get("text") else f"File: {v.get('asset_id')}"
            print(f"     - Voiceover    : {vo_desc} (Ducking: {v['ducking']}, Vol: {v['volume']})")
        if audio.get("sound_effects"):
            print(f"     - Sound Effects: {len(audio['sound_effects'])} cue(s)")

        if plan.get("warnings"):
            print(f"\n⚠️  Preflight Warnings ({len(plan['warnings'])}):")
            for w in plan["warnings"]:
                print(f"   • {w}")

        print(f"=======================================================\n")
        return True

    except Exception as e:
        print(f"❌ Preflight Validation FAILED:")
        print(f"   {str(e)}\n")
        return False


def cmd_render(
    manifest_path: str,
    output_filename: Optional[str] = None,
    keep_intermediate: bool = False,
    allow_review_audio: bool = False
) -> Optional[Dict[str, Any]]:
    """Executes a production render job from a manifest file."""
    abs_manifest = os.path.abspath(manifest_path)
    if not os.path.exists(abs_manifest):
        print(f"❌ Error: Manifest file not found: {abs_manifest}")
        return None

    with open(abs_manifest, "r", encoding="utf-8") as f:
        data = json.load(f)

    if allow_review_audio:
        data["allow_review_audio"] = True

    print(f"\n🚀 Initiating Production Job for: {data.get('content_id')} ({data.get('project')})...")
    job = ProductionJob(
        manifest_data=data,
        manifest_path=abs_manifest,
        keep_intermediate=keep_intermediate
    )
    print(f"   • Job ID: {job.job_id}")
    print(f"   • Work Dir: {job.base_output_dir}")

    manager = RenderManager()
    try:
        result = manager.execute_job(job, output_filename=output_filename)
        print(f"\n🎉 Production Job Succeeded!")
        print(f"   • Output Deliverable : {result['output_file']}")
        print(f"   • Duration           : {result['duration_seconds']:.2f}s")
        print(f"   • File Size          : {result['file_size_bytes'] / (1024*1024):.2f} MB")
        print(f"   • Processing Time    : {result['render_seconds']:.2f}s")
        print(f"   • Job Status         : {result['status']}")
        return result
    except Exception as e:
        print(f"\n❌ Production Job Failed: {e}")
        return None


def cmd_status(job_id: str):
    """Retrieves and prints current status of a production job."""
    try:
        job = ProductionJob.load(job_id)
        print(f"\n=======================================================")
        print(f"             PRODUCTION JOB STATUS: {job.job_id}")
        print(f"=======================================================")
        print(f"Status        : {job.status.value}")
        print(f"Project       : {job.project}")
        print(f"Content ID    : {job.content_id}")
        print(f"Created At    : {job.created_at}")
        print(f"Updated At    : {job.updated_at}")
        print(f"Output File   : {job.output_file or 'None'}")
        if job.error_message:
            print(f"Error Message : {job.error_message}")
        print(f"\nExecution Log ({len(job.execution_log)} events):")
        for log in job.execution_log[-6:]:
            print(f"  [{log['timestamp']}] ({log['status']}): {log['message']}")
        print(f"=======================================================\n")
    except Exception as e:
        print(f"❌ Could not retrieve job '{job_id}': {e}")


def cmd_list_jobs():
    """Lists recent production jobs in data/production_jobs."""
    jobs_dir = os.path.join(WORKSPACE_ROOT, "data", "production_jobs")
    if not os.path.exists(jobs_dir):
        print("No production jobs recorded yet.")
        return

    files = [f for f in os.listdir(jobs_dir) if f.endswith(".json")]
    if not files:
        print("No production jobs found.")
        return

    print(f"\n{'JOB ID':<45} | {'PROJECT':<18} | {'STATUS':<20} | {'UPDATED'}")
    print("-" * 105)
    for fn in sorted(files, reverse=True)[:15]:
        try:
            with open(os.path.join(jobs_dir, fn), "r", encoding="utf-8") as f:
                d = json.load(f)
            jid = d.get("job_id", fn[:-5])
            proj = d.get("project", "unknown")
            stat = d.get("status", "UNKNOWN")
            upd = d.get("updated_at", "")[:19]
            print(f"{jid:<45} | {proj:<18} | {stat:<20} | {upd}")
        except Exception:
            continue
    print("")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Pyapiras Games Video Production Pipeline")
    subparsers = parser.add_subparsers(dest="action")

    # Validate
    p_val = subparsers.add_parser("validate", help="Validate an editing manifest")
    p_val.add_argument("--manifest", required=True, help="Path to manifest JSON")
    p_val.add_argument("--allow-review-audio", action="store_true", help="Allow NEEDS_REVIEW audio for internal preview")

    # Render
    p_ren = subparsers.add_parser("render", help="Render video from an editing manifest")
    p_ren.add_argument("--manifest", required=True, help="Path to manifest JSON")
    p_ren.add_argument("--output-filename", default=None, help="Custom output filename")
    p_ren.add_argument("--keep-intermediate", action="store_true", help="Preserve intermediate scratch files")
    p_ren.add_argument("--allow-review-audio", action="store_true", help="Allow NEEDS_REVIEW audio for internal preview")

    # Status
    p_stat = subparsers.add_parser("status", help="Get status of a production job")
    p_stat.add_argument("--job-id", required=True, help="Job ID")

    # List
    p_list = subparsers.add_parser("list-jobs", help="List recent production jobs")

    args = parser.parse_args()

    if args.action == "validate":
        success = cmd_validate(args.manifest, args.allow_review_audio)
        sys.exit(0 if success else 1)
    elif args.action == "render":
        res = cmd_render(args.manifest, args.output_filename, args.keep_intermediate, args.allow_review_audio)
        sys.exit(0 if res else 1)
    elif args.action == "status":
        cmd_status(args.job_id)
    elif args.action == "list-jobs":
        cmd_list_jobs()
    else:
        parser.print_help()
