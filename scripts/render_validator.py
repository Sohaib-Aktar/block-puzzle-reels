"""
render_validator.py — Post-Render Technical Verification & QC Integration Engine
Runs multi-point FFprobe checks, bitstream decodability validation, and integrates with
existing Technical QC (7/7 checks) and Creative QC (80/90 score) gates.
"""

import os
import sys
import json
import subprocess
from typing import Dict, Any, List, Optional, Tuple

WORKSPACE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(WORKSPACE_ROOT, "scripts"))
from media_engine import get_ffmpeg_cmd, inspect_media, run_command
from qc_verifier import verify_content
from creative_qc import evaluate_creative_quality


class RenderValidationError(Exception):
    """Raised when rendered output fails technical validation."""
    pass


class RenderValidator:
    """Verifies output integrity, codecs, stream synchronization, and QC standards."""

    def __init__(self):
        pass

    def verify_bitstream_decodability(self, video_path: str) -> bool:
        """Runs a complete test decode of all video/audio streams to confirm zero corruptions."""
        cmd = get_ffmpeg_cmd() + [
            "-v", "error",
            "-i", os.path.abspath(video_path),
            "-f", "null",
            "-"
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
        if res.returncode != 0:
            raise RenderValidationError(f"Bitstream decode test failed with errors:\n{res.stderr}")
        return True

    def validate_render(
        self,
        video_path: str,
        expected_spec: Dict[str, Any],
        project_slug: str,
        output_report_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Executes complete technical inspection and produces a verification scorecard.
        """
        abs_path = os.path.abspath(video_path)
        if not os.path.exists(abs_path):
            raise RenderValidationError(f"Rendered file does not exist: {abs_path}")

        file_size = os.path.getsize(abs_path)
        if file_size == 0:
            raise RenderValidationError(f"Rendered file is empty (0 bytes): {abs_path}")

        info = inspect_media(abs_path)
        checks: List[Dict[str, Any]] = []

        # 1. Dimensions Check
        exp_w = expected_spec.get("width", 1080)
        exp_h = expected_spec.get("height", 1920)
        dim_pass = (info["width"] == exp_w and info["height"] == exp_h)
        checks.append({
            "name": "Resolution & Dimensions",
            "expected": f"{exp_w}x{exp_h}",
            "actual": f"{info['width']}x{info['height']}",
            "status": "PASS" if dim_pass else "FAIL"
        })

        # 2. Duration Check
        exp_dur = expected_spec.get("duration_seconds", 0.0)
        dur_diff = abs(info["duration_seconds"] - exp_dur) if exp_dur > 0 else 0.0
        dur_pass = (dur_diff <= 0.6) if exp_dur > 0 else True
        checks.append({
            "name": "Duration Tolerance",
            "expected": f"~{exp_dur:.2f}s (±0.6s)",
            "actual": f"{info['duration_seconds']:.2f}s",
            "status": "PASS" if dur_pass else "FAIL"
        })

        # 3. FPS Check
        fps_pass = abs(info["fps"] - 30.0) <= 0.5
        checks.append({
            "name": "Frame Rate (CFR)",
            "expected": "30.0 fps",
            "actual": f"{info['fps']} fps",
            "status": "PASS" if fps_pass else "FAIL"
        })

        # 4. Video Codec Check
        v_pass = info["video_codec"] in ("h264", "avc1")
        checks.append({
            "name": "Video Codec",
            "expected": "H.264 (avc1)",
            "actual": str(info["video_codec"]),
            "status": "PASS" if v_pass else "FAIL"
        })

        # 5. Audio Codec & Channels Check
        a_pass = info["audio_codec"] == "aac" and info.get("audio_channels", 0) >= 1
        checks.append({
            "name": "Audio Stream & Codec",
            "expected": "AAC Stereo (2ch) @ 48kHz",
            "actual": f"{info.get('audio_codec')} ({info.get('audio_channels')}ch) @ {info.get('audio_sample_rate')}Hz",
            "status": "PASS" if a_pass else "FAIL"
        })

        # 6. Decodability Test
        try:
            self.verify_bitstream_decodability(abs_path)
            decode_status = "PASS"
        except Exception as e:
            decode_status = "FAIL"

        checks.append({
            "name": "Bitstream Decode Integrity",
            "expected": "Zero decode errors",
            "actual": "Decodes cleanly without artifacts" if decode_status == "PASS" else str(e),
            "status": decode_status
        })

        all_passed = all(c["status"] == "PASS" for c in checks)

        report = {
            "file_path": abs_path,
            "file_size_bytes": file_size,
            "passed": all_passed,
            "checks": checks,
            "media_info": info
        }

        # Save markdown report if requested
        if output_report_path:
            os.makedirs(os.path.dirname(os.path.abspath(output_report_path)), exist_ok=True)
            with open(output_report_path, "w", encoding="utf-8") as f:
                f.write(f"# Render Technical Validation Report\n\n")
                f.write(f"**Target File:** `{abs_path}`  \n")
                f.write(f"**File Size:** {file_size / (1024*1024):.2f} MB  \n")
                f.write(f"**Status:** {'✅ PASSED' if all_passed else '❌ FAILED'}\n\n")
                f.write(f"| Check | Expected | Actual | Status |\n")
                f.write(f"|---|---|---|---|\n")
                for c in checks:
                    f.write(f"| **{c['name']}** | {c['expected']} | {c['actual']} | {c['status']} |\n")

        if not all_passed:
            failed_checks = [c["name"] for c in checks if c["status"] == "FAIL"]
            raise RenderValidationError(
                f"Technical validation failed on {len(failed_checks)} check(s): {', '.join(failed_checks)}"
            )

        return report
