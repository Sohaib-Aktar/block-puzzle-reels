"""
qc_calibration.py — Phase 5 QC Calibration & Held-Out Validation Harness
Constructs a labeled dataset of clean and defective video/manifest fixtures PLUS real studio
production examples, split strictly into:
  - Calibration Set
  - Held-Out Validation Set

Measures TP, FP, TN, FN, Precision, Recall, Critical False-Pass Rate, and False-Failure Rate
separately for Deterministic checks and Local OCR checks.
"""

import os
import sys
import json
import time
import shutil
import tempfile
import datetime
import subprocess
from typing import Dict, Any, List, Optional
from PIL import Image, ImageDraw, ImageFont

WORKSPACE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(WORKSPACE_ROOT, "scripts"))

from media_engine import get_ffmpeg_cmd
from qc_orchestrator import QCOrchestrator


def _make_text_frame(
    out_png: str,
    width: int,
    height: int,
    text: str,
    x: int,
    y: int,
    font_size: int = 52,
    bg_color=(15, 25, 55, 235),
    text_color=(255, 255, 255, 255),
):
    """Creates a transparent RGBA overlay layer containing a high-contrast text badge."""
    img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    font = None
    for fp in (r"C:\Windows\Fonts\arialbd.ttf", r"C:\Windows\Fonts\arial.ttf"):
        if os.path.exists(fp):
            font = ImageFont.truetype(fp, font_size)
            break
    if font is None:
        font = ImageFont.load_default()
    bbox = draw.textbbox((x, y), text, font=font)
    pad = 16
    draw.rounded_rectangle(
        [max(0, bbox[0] - pad), max(0, bbox[1] - pad), min(width, bbox[2] + pad), min(height, bbox[3] + pad)],
        radius=18,
        fill=bg_color,
        outline=(255, 215, 0, 255),
        width=3,
    )
    draw.text((x, y), text, fill=text_color, font=font)
    img.save(out_png, "PNG")


def _build_moving_clean_video(
    out_mp4: str,
    width: int = 1080,
    height: int = 1920,
    duration: float = 3.5,
    audio_mode: str = "normal",  # normal | silent | clipped | none | short_sync
    video_mode: str = "moving",  # moving | black | frozen | overlay_png
    overlay_png: Optional[str] = None,
):
    """Generates deterministic synthetic video/audio test fixtures via FFmpeg."""
    ffmpeg = get_ffmpeg_cmd()
    cmd = list(ffmpeg) + ["-y", "-v", "error"]

    if video_mode == "black":
        cmd += ["-f", "lavfi", "-i", f"color=c=black:s={width}x{height}:r=30:d={duration}"]
    elif video_mode == "frozen":
        cmd += ["-f", "lavfi", "-i", f"testsrc2=size={width}x{height}:rate=30:duration=0.1"]
    elif video_mode == "overlay_png" and overlay_png:
        # Animated moving color background with crisp PNG text overlay (prevents freeze false positives)
        cmd += [
            "-f", "lavfi", "-i", f"testsrc2=size={width}x{height}:rate=30:duration={duration}",
            "-loop", "1", "-t", str(duration), "-i", overlay_png,
        ]
    else:
        cmd += ["-f", "lavfi", "-i", f"testsrc2=size={width}x{height}:rate=30:duration={duration}"]

    # Audio input
    audio_idx = 2 if (video_mode == "overlay_png" and overlay_png) else 1
    if audio_mode == "normal":
        cmd += ["-f", "lavfi", "-i", f"sine=frequency=440:sample_rate=48000:duration={duration}"]
    elif audio_mode == "silent":
        cmd += ["-f", "lavfi", "-i", f"anullsrc=channel_layout=stereo:sample_rate=48000", "-t", str(duration)]
    elif audio_mode == "clipped":
        cmd += ["-f", "lavfi", "-i", f"sine=frequency=440:sample_rate=48000:duration={duration}"]
    elif audio_mode == "short_sync":
        cmd += ["-f", "lavfi", "-i", f"sine=frequency=440:sample_rate=48000:duration=1.2"]

    if video_mode == "overlay_png" and overlay_png:
        # Composite crisp RGBA text badge over genuinely moving testsrc2 video
        cmd += [
            "-filter_complex",
            f"[0:v]scale={width}:{height},eq=brightness=-0.25[bg];[1:v]format=rgba[ov];[bg][ov]overlay=0:0,setsar=1,fps=30,format=yuv420p[vout]",
            "-map", "[vout]",
        ]
    elif video_mode == "frozen":
        cmd += ["-map", "0:v:0", "-vf", f"tpad=stop_mode=clone:stop_duration={duration},setsar=1,fps=30,format=yuv420p", "-t", str(duration)]
    else:
        cmd += ["-map", "0:v:0", "-vf", f"setsar=1,fps=30,format=yuv420p"]

    if audio_mode == "normal":
        cmd += ["-map", f"{audio_idx}:a:0", "-af", "volume=-11dB", "-c:a", "aac", "-b:a", "160k", "-ar", "48000", "-ac", "2"]
    elif audio_mode == "silent":
        cmd += ["-map", f"{audio_idx}:a:0", "-c:a", "aac", "-b:a", "160k", "-ar", "48000", "-ac", "2"]
    elif audio_mode == "clipped":
        cmd += ["-map", f"{audio_idx}:a:0", "-af", "volume=+24dB", "-c:a", "aac", "-b:a", "160k", "-ar", "48000", "-ac", "2"]
    elif audio_mode == "short_sync":
        cmd += ["-map", f"{audio_idx}:a:0", "-af", "volume=-12dB", "-c:a", "aac", "-b:a", "160k", "-ar", "48000", "-ac", "2"]
    else:  # none
        cmd += ["-an"]

    cmd += ["-c:v", "libx264", "-crf", "23", "-preset", "ultrafast", "-movflags", "+faststart", out_mp4]
    subprocess.run(cmd, check=True)


def _compute_metrics(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    tp = fp = tn = fn = 0
    for r in records:
        exp_defect = r["expected_defect"]
        det_defect = r["detected_defect"]
        if exp_defect and det_defect:
            tp += 1
        elif (not exp_defect) and det_defect:
            fp += 1
        elif (not exp_defect) and (not det_defect):
            tn += 1
        else:
            fn += 1

    precision = round(tp / (tp + fp), 4) if (tp + fp) > 0 else 1.0
    recall = round(tp / (tp + fn), 4) if (tp + fn) > 0 else 1.0
    false_pass_rate = round(fn / (tp + fn), 4) if (tp + fn) > 0 else 0.0
    false_fail_rate = round(fp / (tn + fp), 4) if (tn + fp) > 0 else 0.0
    return {
        "total": len(records),
        "tp": tp,
        "fp": fp,
        "tn": tn,
        "fn": fn,
        "precision": precision,
        "recall": recall,
        "critical_false_pass_rate": false_pass_rate,
        "false_failure_rate": false_fail_rate,
    }


def run_calibration_and_validation() -> Dict[str, Any]:
    """Builds calibration + held-out datasets, runs Phase 5 QC, and computes empirical metrics."""
    t0 = time.time()
    orch = QCOrchestrator()
    tmp_dir = tempfile.mkdtemp(prefix="p5_calib_")
    results: List[Dict[str, Any]] = []

    try:
        # Prepare base manifests
        def clean_manifest(project="block-puzzle-burst", title="No WiFi Play Free Today", audio_id="AUDIO_753DE70D", cta=True):
            return {
                "project": project,
                "campaign": "calibration",
                "content_id": "calib",
                "timeline": [{
                    "scene_id": "s1",
                    "asset_id": "VID_0DD488E3",
                    "source_in": 0.0,
                    "source_out": 3.5,
                    "duration": 3.5,
                    "overlays": [{"title": title, "start_time": 0.0, "end_time": 3.0}] if title else [],
                }],
                "audio": {
                    "music": {"asset_id": audio_id, "volume": 0.25},
                },
            }

        # ── Build Synthetic Fixtures ──
        # 1. Clean 9:16 with centered safe OCR text + CTA
        p_clean_9x16_png = os.path.join(tmp_dir, "clean_9x16.png")
        _make_text_frame(p_clean_9x16_png, 1080, 1920, "No WiFi Play Free Today", x=180, y=820, font_size=56)
        v_clean_9x16 = os.path.join(tmp_dir, "clean_9x16.mp4")
        _build_moving_clean_video(v_clean_9x16, 1080, 1920, 3.5, "normal", "overlay_png", p_clean_9x16_png)

        # 2. Clean 16:9 with centered safe OCR text + CTA (held-out)
        p_clean_16x9_png = os.path.join(tmp_dir, "clean_16x9.png")
        _make_text_frame(p_clean_16x9_png, 1920, 1080, "Block Puzzle Play Free Today", x=450, y=460, font_size=60)
        v_clean_16x9 = os.path.join(tmp_dir, "clean_16x9.mp4")
        _build_moving_clean_video(v_clean_16x9, 1920, 1080, 3.5, "normal", "overlay_png", p_clean_16x9_png)

        # 3. Black frames defect
        v_black = os.path.join(tmp_dir, "defect_black.mp4")
        _build_moving_clean_video(v_black, 1080, 1920, 3.5, "normal", "black")

        # 4. Frozen frames defect
        v_frozen = os.path.join(tmp_dir, "defect_frozen.mp4")
        _build_moving_clean_video(v_frozen, 1080, 1920, 3.5, "normal", "frozen")

        # 5. Audio clipping defect
        v_clipped = os.path.join(tmp_dir, "defect_clipped.mp4")
        _build_moving_clean_video(v_clipped, 1080, 1920, 3.5, "clipped", "overlay_png", p_clean_9x16_png)

        # 6. Missing audio defect
        v_no_audio = os.path.join(tmp_dir, "defect_no_audio.mp4")
        _build_moving_clean_video(v_no_audio, 1080, 1920, 3.5, "none", "overlay_png", p_clean_9x16_png)

        # 7. Excessive silence defect (held-out)
        v_silent = os.path.join(tmp_dir, "defect_silent.mp4")
        _build_moving_clean_video(v_silent, 1080, 1920, 3.5, "silent", "overlay_png", p_clean_9x16_png)

        # 8. A/V sync mismatch defect (held-out)
        v_av_desync = os.path.join(tmp_dir, "defect_av_desync.mp4")
        _build_moving_clean_video(v_av_desync, 1080, 1920, 3.5, "short_sync", "overlay_png", p_clean_9x16_png)

        # 9. OCR Clipped text touching canvas edge
        p_clip_txt = os.path.join(tmp_dir, "clipped_txt.png")
        _make_text_frame(p_clip_txt, 1080, 1920, "NO WIFI PLAY FREE TODAY NOW", x=2, y=820, font_size=68)
        v_clip_txt = os.path.join(tmp_dir, "defect_clipped_text.mp4")
        _build_moving_clean_video(v_clip_txt, 1080, 1920, 3.5, "normal", "overlay_png", p_clip_txt)

        # 10. OCR Unsafe text placement in top Reels header occlusion zone (y=30) (held-out)
        p_unsafe_txt = os.path.join(tmp_dir, "unsafe_txt.png")
        _make_text_frame(p_unsafe_txt, 1080, 1920, "No WiFi Play Free Today", x=180, y=30, font_size=52)
        v_unsafe_txt = os.path.join(tmp_dir, "defect_unsafe_text.mp4")
        _build_moving_clean_video(v_unsafe_txt, 1080, 1920, 3.5, "normal", "overlay_png", p_unsafe_txt)

        # 11. OCR Missing expected text (video says "Random Unrelated Banner", manifest expects "Offline Puzzle Challenge") (held-out)
        p_wrong_txt = os.path.join(tmp_dir, "wrong_txt.png")
        _make_text_frame(p_wrong_txt, 1080, 1920, "Random Unrelated Play Free", x=180, y=820, font_size=50)
        v_wrong_txt = os.path.join(tmp_dir, "defect_missing_text.mp4")
        _build_moving_clean_video(v_wrong_txt, 1080, 1920, 3.5, "normal", "overlay_png", p_wrong_txt)

        # Define complete labeled dataset (Calibration vs Held-Out Validation, Deterministic vs OCR)
        cases = [
            # === CALIBRATION SET (Deterministic) ===
            {"id": "CAL_DET_CLEAN_01", "split": "calibration", "track": "deterministic", "expected_defect": False, "video": v_clean_9x16, "project": "block-puzzle-burst", "profile": "instagram_reels", "manifest": clean_manifest(), "target_issue": None},
            {"id": "CAL_DET_BLACK_02", "split": "calibration", "track": "deterministic", "expected_defect": True, "video": v_black, "project": "block-puzzle-burst", "profile": "instagram_reels", "manifest": clean_manifest(title=None), "target_issue": "unexpected_black_frames"},
            {"id": "CAL_DET_FREEZE_03", "split": "calibration", "track": "deterministic", "expected_defect": True, "video": v_frozen, "project": "block-puzzle-burst", "profile": "instagram_reels", "manifest": clean_manifest(title=None), "target_issue": "frozen_frames_detected"},
            {"id": "CAL_DET_CLIP_04", "split": "calibration", "track": "deterministic", "expected_defect": True, "video": v_clipped, "project": "block-puzzle-burst", "profile": "instagram_reels", "manifest": clean_manifest(), "target_issue": "audio_clipping"},
            {"id": "CAL_DET_NOAUD_05", "split": "calibration", "track": "deterministic", "expected_defect": True, "video": v_no_audio, "project": "block-puzzle-burst", "profile": "instagram_reels", "manifest": clean_manifest(), "target_issue": "missing_audio"},
            {"id": "CAL_DET_BRAND_06", "split": "calibration", "track": "deterministic", "expected_defect": True, "video": v_clean_9x16, "project": "block-puzzle-burst", "profile": "instagram_reels", "manifest": clean_manifest(title="Expand eziSales Order Booking Play Free"), "target_issue": "incorrect_project_branding"},
            {"id": "CAL_DET_LIC_07", "split": "calibration", "track": "deterministic", "expected_defect": True, "video": v_clean_9x16, "project": "block-puzzle-burst", "profile": "instagram_reels", "manifest": clean_manifest(audio_id="AUDIO_UNKNOWN_UNLICENSED_999"), "target_issue": "restricted_or_unknown_audio_license"},

            # === CALIBRATION SET (OCR / Visual Text) ===
            {"id": "CAL_OCR_CLEAN_08", "split": "calibration", "track": "ocr", "expected_defect": False, "video": v_clean_9x16, "project": "block-puzzle-burst", "profile": "instagram_reels", "manifest": clean_manifest(), "target_issue": None},
            {"id": "CAL_OCR_CLIPTXT_09", "split": "calibration", "track": "ocr", "expected_defect": True, "video": v_clip_txt, "project": "block-puzzle-burst", "profile": "instagram_reels", "manifest": clean_manifest(title="NO WIFI PLAY FREE TODAY NOW"), "target_issue": "clipped_text"},

            # === HELD-OUT VALIDATION SET (Deterministic) ===
            {"id": "VAL_DET_CLEAN16X9_10", "split": "held_out", "track": "deterministic", "expected_defect": False, "video": v_clean_16x9, "project": "block-puzzle-burst", "profile": "youtube_standard", "manifest": clean_manifest(title="Block Puzzle Play Free Today"), "target_issue": None},
            {"id": "VAL_DET_SILENCE_11", "split": "held_out", "track": "deterministic", "expected_defect": True, "video": v_silent, "project": "block-puzzle-burst", "profile": "instagram_reels", "manifest": clean_manifest(), "target_issue": "excessive_silence"},
            {"id": "VAL_DET_AVSYNC_12", "split": "held_out", "track": "deterministic", "expected_defect": True, "video": v_av_desync, "project": "block-puzzle-burst", "profile": "instagram_reels", "manifest": clean_manifest(), "target_issue": "av_sync_mismatch"},
            {"id": "VAL_DET_WRONGPROF_13", "split": "held_out", "track": "deterministic", "expected_defect": True, "video": v_clean_16x9, "project": "block-puzzle-burst", "profile": "instagram_reels", "manifest": clean_manifest(title="Block Puzzle Play Free Today"), "target_issue": "resolution_match"},
            {"id": "VAL_DET_NOCTA_14", "split": "held_out", "track": "deterministic", "expected_defect": True, "video": v_clean_9x16, "project": "block-puzzle-burst", "profile": "instagram_reels", "manifest": clean_manifest(title="Simple Title Only"), "target_issue": "missing_cta", "strip_ocr_cta": True},
            {"id": "VAL_DET_CLAIM_15", "split": "held_out", "track": "deterministic", "expected_defect": True, "video": v_clean_9x16, "project": "block-puzzle-burst", "profile": "instagram_reels", "manifest": clean_manifest(title="500% growth guaranteed Play Free"), "target_issue": "unsupported_marketing_claim"},
            {"id": "VAL_DET_REVLIC_16", "split": "held_out", "track": "deterministic", "expected_defect": True, "video": v_clean_9x16, "project": "block-puzzle-burst", "profile": "instagram_reels", "manifest": clean_manifest(audio_id="AUDIO_C9B3EDFF"), "target_issue": "unverified_audio_licensing"},

            # === HELD-OUT VALIDATION SET (OCR / Visual Text) ===
            {"id": "VAL_OCR_CLEAN16X9_17", "split": "held_out", "track": "ocr", "expected_defect": False, "video": v_clean_16x9, "project": "block-puzzle-burst", "profile": "youtube_standard", "manifest": clean_manifest(title="Block Puzzle Play Free Today"), "target_issue": None},
            {"id": "VAL_OCR_UNSAFE_18", "split": "held_out", "track": "ocr", "expected_defect": True, "video": v_unsafe_txt, "project": "block-puzzle-burst", "profile": "instagram_reels", "manifest": clean_manifest(title="No WiFi Play Free Today"), "target_issue": "unsafe_text_placement"},
            {"id": "VAL_OCR_MISSTXT_19", "split": "held_out", "track": "ocr", "expected_defect": True, "video": v_wrong_txt, "project": "block-puzzle-burst", "profile": "instagram_reels", "manifest": clean_manifest(title="Offline Puzzle Challenge Play Free"), "target_issue": "expected_text_missing"},

            # === HELD-OUT REAL STUDIO EXAMPLES ===
            {
                "id": "VAL_REAL_DAY04_CLEAN_20",
                "split": "held_out",
                "track": "real_studio",
                "expected_defect": False,  # Zero critical defects (only ASR pending review)
                "video": os.path.join(WORKSPACE_ROOT, "outputs", "block-puzzle-burst", "30-day-challenge", "day-04-no-wifi-revision", "final", "Day_04_Final_Revised_Center_Text.mp4"),
                "project": "block-puzzle-burst",
                "profile": "instagram_reels",
                "manifest_path": os.path.join(WORKSPACE_ROOT, "config", "manifests", "manifest_bpb_day04_revision.json"),
                "target_issue": None,
            },
            {
                "id": "VAL_REAL_DAY04_SILENT_21",
                "split": "held_out",
                "track": "real_studio",
                "expected_defect": True,  # Remotion Day 04 has silent audio track (-70 LUFS)
                "video": os.path.join(WORKSPACE_ROOT, "outputs", "block-puzzle-burst", "30-day-challenge", "day-04-shared-exports", "artifacts", "VERTICAL_1080_1920", "day-04-shared-exports_VERTICAL_1080_1920.mp4"),
                "project": "block-puzzle-burst",
                "profile": "instagram_reels",
                "manifest_path": os.path.join(WORKSPACE_ROOT, "config", "manifests", "manifest_bpb_day04_revision.json"),
                "target_issue": "silent_audio_track",
            },
            {
                "id": "VAL_REAL_EZISALES_DEFECT_22",
                "split": "held_out",
                "track": "real_studio",
                "expected_defect": True,  # Placeholder non-ERP footage + unverified claim + missing CTA
                "video": os.path.join(WORKSPACE_ROOT, "outputs", "expand-ezisales", "quick-start-tutorials", "ezisales-tut-01-multiplatform-exports", "platform_exports", "instagram_reels", "ezisales-tut-01-multiplatform-exports_instagram_reels.mp4"),
                "project": "expand-ezisales",
                "profile": "instagram_reels",
                "manifest_path": os.path.join(WORKSPACE_ROOT, "config", "manifests", "manifest_ezisales_tut01_pilot.json"),
                "target_issue": "placeholder_or_non_erp_footage",
            },
        ]

        # Build no-CTA video cleanly so OCR doesn't read "Play Free" from clean_9x16
        p_no_cta_png = os.path.join(tmp_dir, "no_cta.png")
        _make_text_frame(p_no_cta_png, 1080, 1920, "Simple Title Only", x=220, y=820, font_size=56)
        v_no_cta = os.path.join(tmp_dir, "defect_no_cta.mp4")
        _build_moving_clean_video(v_no_cta, 1080, 1920, 3.5, "normal", "overlay_png", p_no_cta_png)
        for c in cases:
            if c["id"] == "VAL_DET_NOCTA_14":
                c["video"] = v_no_cta

        created_job_ids = []
        for c in cases:
            qc_sub = os.path.join(tmp_dir, "qc_" + c["id"])
            rep = orch.run_master_qc(
                video_path=c["video"],
                project_slug=c["project"],
                platform_profile_id=c["profile"],
                manifest_path=c.get("manifest_path"),
                manifest_data=c.get("manifest"),
                content_id=c["id"],
                qc_dir=qc_sub,
            )
            created_job_ids.append(rep["qc_job_id"])
            issue_types = [i["type"] for i in rep.get("issues", [])]

            if c["expected_defect"]:
                target = c["target_issue"]
                detected = (target in issue_types) or (rep["overall_result"] in ("FAIL", "BLOCKED", "REVIEW_REQUIRED") and target is None)
            else:
                # For clean cases, any FAIL or BLOCKED is a False Positive (ignore benign ASR-unavailable review on real studio VO)
                detected = rep["overall_result"] in ("FAIL", "BLOCKED")

            results.append({
                "id": c["id"],
                "split": c["split"],
                "track": c["track"],
                "expected_defect": c["expected_defect"],
                "target_issue": c["target_issue"],
                "overall_result": rep["overall_result"],
                "detected_issue_types": sorted(set(issue_types)),
                "detected_defect": detected,
                "correct": (detected == c["expected_defect"]),
            })

        # Clean temporary calibration job records from data/qc_jobs/ so production registry stays tidy
        from qc_orchestrator import QC_JOBS_DIR
        for jid in created_job_ids:
            jp = os.path.join(QC_JOBS_DIR, f"{jid}.json")
            if os.path.exists(jp):
                os.remove(jp)

        summary = {
            "executed_at": datetime.datetime.now().isoformat(),
            "elapsed_seconds": round(time.time() - t0, 2),
            "dataset_size": len(results),
            "metrics_overall": _compute_metrics(results),
            "metrics_calibration_split": _compute_metrics([r for r in results if r["split"] == "calibration"]),
            "metrics_held_out_split": _compute_metrics([r for r in results if r["split"] == "held_out"]),
            "metrics_deterministic_only": _compute_metrics([r for r in results if r["track"] == "deterministic"]),
            "metrics_ocr_only": _compute_metrics([r for r in results if r["track"] == "ocr"]),
            "metrics_real_studio_only": _compute_metrics([r for r in results if r["track"] == "real_studio"]),
            "cases": results,
        }

        out_path = os.path.join(WORKSPACE_ROOT, "data", "qc_calibration_results.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)
        return summary
    finally:
        if os.path.exists(tmp_dir):
            shutil.rmtree(tmp_dir, ignore_errors=True)


if __name__ == "__main__":
    rep = run_calibration_and_validation()
    print(f"\nPhase 5 Calibration & Held-Out Validation Complete ({rep['dataset_size']} labeled cases in {rep['elapsed_seconds']}s)")
    for k in ("metrics_overall", "metrics_calibration_split", "metrics_held_out_split", "metrics_deterministic_only", "metrics_ocr_only", "metrics_real_studio_only"):
        m = rep[k]
        print(f"  {k:<28}: TP={m['tp']} FP={m['fp']} TN={m['tn']} FN={m['fn']} | P={m['precision']:.3f} R={m['recall']:.3f} | FalsePass={m['critical_false_pass_rate']:.3f}")
    mismatches = [c for c in rep["cases"] if not c["correct"]]
    if mismatches:
        print("\nMismatched Cases:")
        for mm in mismatches:
            print(" ", mm)
    else:
        print("\nAll 22 labeled calibration & held-out cases classified accurately!")
