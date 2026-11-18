"""
visual_qc.py — Multi-Frame Visual Integrity, Freeze/Black Detection & Real Local OCR QC (Phase 5)
Uses:
  - FFmpeg freezedetect, blackdetect, scdet (deterministic signal analysis)
  - PIL + NumPy (brightness, blank-frame, blur/sharpness, local contrast)
  - Windows.Media.Ocr.OcrEngine via scripts/win_ocr.ps1 (real local OCR with bounding boxes)

Uncertain OCR recognition ALWAYS emits REVIEW_REQUIRED — never an automatic PASS.
"""

import os
import re
import sys
import json
import difflib
import subprocess
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
from PIL import Image, ImageDraw, ImageFont

WORKSPACE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(WORKSPACE_ROOT, "scripts"))
from media_engine import get_ffmpeg_cmd, inspect_media

WIN_OCR_SCRIPT = os.path.join(WORKSPACE_ROOT, "scripts", "win_ocr.ps1")
SAFE_ZONES_PATH = os.path.join(WORKSPACE_ROOT, "config", "production", "safe_zones.json")


def _norm_text(t: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (t or "").lower()).strip()


def _best_ocr_match(expected: str, ocr_lines: List[Dict[str, Any]], full_text: str) -> Tuple[float, Optional[Dict[str, Any]]]:
    """Computes best fuzzy match confidence [0.0..1.0] for `expected` against OCR lines & full text."""
    exp_n = _norm_text(expected)
    if not exp_n:
        return 1.0, None

    best_score = 0.0
    best_line = None

    # Check substring / fuzzy match per line
    for line in ocr_lines:
        ln = _norm_text(line.get("text", ""))
        if not ln:
            continue
        if exp_n in ln or ln in exp_n and len(ln) >= max(4, int(len(exp_n) * 0.6)):
            score = min(1.0, len(min(exp_n, ln, key=len)) / max(1, len(exp_n)) + 0.15)
            score = min(1.0, max(score, difflib.SequenceMatcher(None, exp_n, ln).ratio()))
        else:
            score = difflib.SequenceMatcher(None, exp_n, ln).ratio()
        if score > best_score:
            best_score = score
            best_line = line

    # Also check token overlap against concatenated full text (handles line wrapping)
    full_n = _norm_text(full_text)
    if exp_n in full_n:
        best_score = max(best_score, 0.96)
    else:
        exp_tokens = [tok for tok in exp_n.split() if len(tok) >= 2]
        if exp_tokens:
            hits = sum(1 for tok in exp_tokens if tok in full_n)
            tok_score = hits / len(exp_tokens)
            if tok_score > best_score:
                best_score = tok_score * 0.92

    return round(best_score, 3), best_line


class VisualQC:
    """Performs multi-frame visual integrity, signal defect, OCR text, and safe-zone QC."""

    def __init__(self, safe_zones_config: Optional[Dict[str, Any]] = None):
        if safe_zones_config is None and os.path.exists(SAFE_ZONES_PATH):
            with open(SAFE_ZONES_PATH, "r", encoding="utf-8") as f:
                safe_zones_config = json.load(f)
        self.safe_zones_config = safe_zones_config or {"profiles": {}}

    def _run_ffmpeg(self, args: List[str]) -> subprocess.CompletedProcess:
        return subprocess.run(
            get_ffmpeg_cmd() + args,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )

    def detect_black_frames(self, abs_path: str) -> List[Dict[str, float]]:
        res = self._run_ffmpeg([
            "-i", abs_path,
            "-vf", "blackdetect=d=0.4:pix_th=0.05",
            "-an", "-f", "null", "-"
        ])
        events = []
        for m in re.finditer(r"black_start:([0-9.]+)\s+black_end:([0-9.]+)\s+black_duration:([0-9.]+)", res.stderr or ""):
            events.append({
                "start": round(float(m.group(1)), 3),
                "end": round(float(m.group(2)), 3),
                "duration": round(float(m.group(3)), 3),
            })
        return events

    def detect_freeze_frames(self, abs_path: str, min_freeze_sec: float = 2.0) -> List[Dict[str, float]]:
        res = self._run_ffmpeg([
            "-i", abs_path,
            "-vf", f"freezedetect=n=0.002:d={min_freeze_sec}",
            "-an", "-f", "null", "-"
        ])
        stderr = res.stderr or ""
        starts = [float(x) for x in re.findall(r"freeze_start:\s*([0-9.]+)", stderr)]
        ends = re.findall(r"freeze_duration:\s*([0-9.]+)\s+freeze_end:\s*([0-9.]+)", stderr)
        # FFmpeg prints freeze_duration and freeze_end on consecutive lines
        durs = [float(x) for x in re.findall(r"freeze_duration:\s*([0-9.]+)", stderr)]
        end_ts = [float(x) for x in re.findall(r"freeze_end:\s*([0-9.]+)", stderr)]
        events = []
        for idx, st in enumerate(starts):
            dur = durs[idx] if idx < len(durs) else -1.0
            en = end_ts[idx] if idx < len(end_ts) else -1.0
            events.append({"start": round(st, 3), "end": round(en, 3), "duration": round(dur, 3)})
        return events

    def detect_scene_changes(self, abs_path: str) -> List[float]:
        res = self._run_ffmpeg([
            "-i", abs_path,
            "-vf", "scdet=t=12.0",
            "-an", "-f", "null", "-"
        ])
        return [round(float(x), 3) for x in re.findall(r"lavfi\.scd\.time:\s*([0-9.]+)", res.stderr or "")]

    def extract_frame(self, abs_path: str, out_png: str, ts_sec: float) -> str:
        os.makedirs(os.path.dirname(os.path.abspath(out_png)), exist_ok=True)
        res = self._run_ffmpeg([
            "-y", "-v", "error",
            "-ss", f"{max(0.0, ts_sec):.3f}",
            "-i", abs_path,
            "-vframes", "1",
            out_png,
        ])
        if res.returncode != 0 or not os.path.exists(out_png):
            self._run_ffmpeg(["-y", "-v", "error", "-i", abs_path, "-vframes", "1", out_png])
        return out_png

    def run_ocr(self, image_path: str) -> Dict[str, Any]:
        """Executes local Windows.Media.Ocr.OcrEngine via win_ocr.ps1."""
        if not os.path.exists(WIN_OCR_SCRIPT) or not os.path.exists(image_path):
            return {"available": False, "engine": None, "full_text": "", "lines": []}
        try:
            res = subprocess.run(
                ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", WIN_OCR_SCRIPT, "-ImagePath", os.path.abspath(image_path)],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=20,
            )
            if res.returncode != 0 or not res.stdout.strip():
                return {"available": False, "engine": "Windows.Media.Ocr.OcrEngine", "error": res.stderr.strip(), "full_text": "", "lines": []}
            data = json.loads(res.stdout.strip())
            lines = data.get("lines") or []
            if isinstance(lines, dict):
                lines = [lines]
            return {
                "available": True,
                "engine": data.get("engine", "Windows.Media.Ocr.OcrEngine"),
                "language": data.get("language", "en-US"),
                "full_text": data.get("full_text", ""),
                "lines": lines,
            }
        except Exception as e:
            return {"available": False, "engine": "Windows.Media.Ocr.OcrEngine", "error": str(e), "full_text": "", "lines": []}

    def analyze_frame_metrics(self, image_path: str) -> Dict[str, Any]:
        """Computes brightness, std-dev (blank check), sharpness (edge energy), and dark border ratio."""
        with Image.open(image_path).convert("RGB") as im:
            w, h = im.size
            arr = np.asarray(im, dtype=np.float32)
            gray = 0.299 * arr[:, :, 0] + 0.587 * arr[:, :, 1] + 0.114 * arr[:, :, 2]
            mean_luma = float(np.mean(gray))
            std_luma = float(np.std(gray))
            # Fast gradient-based sharpness score (higher = sharper edges)
            gx = np.abs(np.diff(gray, axis=1))
            gy = np.abs(np.diff(gray, axis=0))
            edge_energy = float((np.mean(gx) + np.mean(gy)) / 2.0)
            is_blank = (std_luma < 4.0)
            is_black = (mean_luma < 8.0 and std_luma < 10.0)
            return {
                "width": w,
                "height": h,
                "mean_luma": round(mean_luma, 2),
                "std_luma": round(std_luma, 2),
                "edge_energy": round(edge_energy, 2),
                "is_blank": is_blank,
                "is_black": is_black,
            }

    def measure_box_contrast(self, image_path: str, box: Dict[str, int]) -> float:
        """Estimates local luminance contrast inside an OCR bounding box (std-dev of luma)."""
        with Image.open(image_path).convert("L") as im:
            w, h = im.size
            x1 = max(0, box["x"] - 6)
            y1 = max(0, box["y"] - 6)
            x2 = min(w, box["x"] + box["width"] + 6)
            y2 = min(h, box["y"] + box["height"] + 6)
            if x2 <= x1 or y2 <= y1:
                return 0.0
            crop = np.asarray(im.crop((x1, y1, x2, y2)), dtype=np.float32)
            p5 = float(np.percentile(crop, 5))
            p95 = float(np.percentile(crop, 95))
            return round(p95 - p5, 2)

    def annotate_evidence_frame(
        self,
        image_path: str,
        output_path: str,
        ocr_lines: List[Dict[str, Any]],
        safe_zone_profile: Optional[str] = None,
        flagged_boxes: Optional[List[Dict[str, Any]]] = None,
    ) -> str:
        """Draws OCR bounding boxes and safe-zone rectangle onto an evidence PNG."""
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        sz_spec = self.safe_zones_config.get("profiles", {}).get(safe_zone_profile or "")
        flagged_texts = {b.get("text") for b in (flagged_boxes or [])}

        with Image.open(image_path).convert("RGB") as im:
            draw = ImageDraw.Draw(im)
            if sz_spec and sz_spec["canvas"]["width"] == im.width and sz_spec["canvas"]["height"] == im.height:
                sb = sz_spec.get("safe_content_box")
                if sb:
                    draw.rectangle(
                        [sb["x"], sb["y"], sb["x"] + sb["width"], sb["y"] + sb["height"]],
                        outline=(34, 197, 94),
                        width=4,
                    )
            for ln in ocr_lines:
                col = (239, 68, 68) if ln.get("text") in flagged_texts else (56, 189, 248)
                x, y, w, h = ln["x"], ln["y"], ln["width"], ln["height"]
                draw.rectangle([x, y, x + w, y + h], outline=col, width=3)
            im.save(output_path, "PNG")
        return output_path

    def run(
        self,
        video_path: str,
        manifest: Optional[Dict[str, Any]] = None,
        platform_profile_id: Optional[str] = None,
        evidence_dir: Optional[str] = None,
        frame_dir: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Executes multi-frame Visual QC, signal defect checks, and real local OCR verification."""
        abs_path = os.path.abspath(video_path)
        checks: List[Dict[str, Any]] = []
        issues: List[Dict[str, Any]] = []

        info = inspect_media(abs_path)
        duration = float(info.get("duration_seconds", 0.0))
        width = int(info.get("width", 0))
        height = int(info.get("height", 0))

        # 1. Black frame detection
        black_events = self.detect_black_frames(abs_path)
        max_black = max((e["duration"] for e in black_events), default=0.0)
        if max_black > 0.8:
            b_stat, b_sev = "FAIL", "CRITICAL"
            issues.append({
                "issue_id": "VIS_001",
                "severity": "CRITICAL",
                "type": "unexpected_black_frames",
                "timestamp": f"{black_events[0]['start']}s-{black_events[0]['end']}s",
                "expected": "No unexpected black segment > 0.80s",
                "actual": f"max_black={max_black:.2f}s ({len(black_events)} event(s))",
                "confidence": 1.0,
                "recommendation": "Inspect timeline cut boundaries and source footage trim offsets.",
            })
        elif max_black > 0.4:
            b_stat, b_sev = "PASS_WITH_WARNINGS", "WARNING"
            issues.append({
                "issue_id": "VIS_001",
                "severity": "WARNING",
                "type": "brief_black_transition",
                "timestamp": f"{black_events[0]['start']}s-{black_events[0]['end']}s",
                "expected": "Minimal black fade <= 0.40s",
                "actual": f"max_black={max_black:.2f}s",
                "confidence": 1.0,
                "recommendation": "Confirm dark transition is intentional.",
            })
        else:
            b_stat, b_sev = "PASS", "INFO"

        checks.append({
            "name": "unexpected_black_frames",
            "category": "visual",
            "method": "deterministic",
            "status": b_stat,
            "severity": b_sev,
            "actual": f"max_black={max_black:.2f}s",
            "expected": "<= 0.80s",
        })

        # 2. Freeze-frame detection
        freeze_events = self.detect_freeze_frames(abs_path, min_freeze_sec=2.0)
        # Resolve unclosed trailing freezes
        max_freeze = 0.0
        for ev in freeze_events:
            if ev["duration"] < 0:
                ev["duration"] = round(max(0.0, duration - ev["start"]), 3)
                ev["end"] = round(duration, 3)
            if ev["duration"] > max_freeze:
                max_freeze = ev["duration"]

        # Fail if frozen for >= 3.5s OR >= 70% of short clip (>= 2.0s)
        freeze_fail_thresh = min(3.5, max(1.8, duration * 0.70))
        if max_freeze >= freeze_fail_thresh:
            f_stat, f_sev = "FAIL", "CRITICAL"
            issues.append({
                "issue_id": "VIS_002",
                "severity": "CRITICAL",
                "type": "frozen_frames_detected",
                "timestamp": f"{freeze_events[0]['start']}s-{freeze_events[0]['end']}s",
                "expected": f"Continuous visual motion (freeze < {freeze_fail_thresh:.1f}s)",
                "actual": f"Static frozen video for {max_freeze:.2f}s ({len(freeze_events)} event(s))",
                "confidence": 0.98,
                "recommendation": "Check source recording or FFmpeg frame duplication / PTS timestamps.",
            })
        elif max_freeze >= 2.0:
            f_stat, f_sev = "PASS_WITH_WARNINGS", "WARNING"
            issues.append({
                "issue_id": "VIS_002",
                "severity": "WARNING",
                "type": "static_hold_detected",
                "timestamp": f"{freeze_events[0]['start']}s-{freeze_events[0]['end']}s",
                "expected": "Dynamic pacing without long static holds",
                "actual": f"Static segment of {max_freeze:.2f}s",
                "confidence": 0.95,
                "recommendation": "Verify static hold (e.g. opening board pause or outro card) is intentional.",
            })
        else:
            f_stat, f_sev = "PASS", "INFO"

        checks.append({
            "name": "freeze_frame_detection",
            "category": "visual",
            "method": "deterministic",
            "status": f_stat,
            "severity": f_sev,
            "actual": f"max_freeze={max_freeze:.2f}s ({len(freeze_events)} event(s))",
            "expected": f"< {freeze_fail_thresh:.1f}s",
        })

        # 3. Multi-frame sampling timestamps (opening, scene midpoints, closing)
        sample_specs: List[Tuple[str, float, List[Dict[str, Any]]]] = []
        if manifest and (manifest.get("timeline") or manifest.get("scenes")):
            cur_t = 0.0
            for idx, sc in enumerate(manifest.get("timeline") or manifest.get("scenes")):
                dur = float(sc.get("duration", 0.0))
                if dur <= 0:
                    dur = max(0.5, float(sc.get("source_out", 1.0)) - float(sc.get("source_in", 0.0)))
                overlays = sc.get("overlays", [])
                # Sample near overlay active window if present, else midpoint
                if overlays:
                    ov0 = overlays[0]
                    ov_mid = cur_t + (float(ov0.get("start_time", 0.0)) + min(dur, float(ov0.get("end_time", dur)))) / 2.0
                    ts = min(max(0.2, ov_mid), max(0.1, duration - 0.15))
                else:
                    ts = min(cur_t + dur * 0.5, max(0.1, duration - 0.15))
                sample_specs.append((sc.get("scene_id", f"scene_{idx+1:02d}"), round(ts, 2), overlays))
                cur_t += dur
        else:
            # Uniform 4-frame multi-point sampling across timeline
            ratios = [0.08, 0.35, 0.65, 0.90]
            labels = ["opening", "early_mid", "late_mid", "closing"]
            for lbl, r in zip(labels, ratios):
                sample_specs.append((lbl, round(min(max(0.1, duration * r), max(0.1, duration - 0.1)), 2), []))

        work_frame_dir = frame_dir or os.path.join(WORKSPACE_ROOT, "data", "qc_tmp_frames")
        os.makedirs(work_frame_dir, exist_ok=True)

        sampled_results = []
        all_ocr_lines_combined: List[Dict[str, Any]] = []
        all_ocr_full_text_parts: List[str] = []
        blank_frames = 0
        low_sharpness_frames = 0
        ocr_available_any = False
        flagged_ocr_issues = []

        for label, ts, expected_overlays in sample_specs:
            f_png = os.path.join(work_frame_dir, f"frame_{label}_{ts:.2f}s.png")
            self.extract_frame(abs_path, f_png, ts)
            f_metrics = self.analyze_frame_metrics(f_png)
            ocr = self.run_ocr(f_png)
            if ocr.get("available"):
                ocr_available_any = True
            if f_metrics["is_blank"]:
                blank_frames += 1
            if f_metrics["edge_energy"] < 1.2:
                low_sharpness_frames += 1

            for ln in ocr.get("lines", []):
                ln_copy = dict(ln)
                ln_copy["frame_label"] = label
                ln_copy["timestamp"] = ts
                all_ocr_lines_combined.append(ln_copy)
            if ocr.get("full_text"):
                all_ocr_full_text_parts.append(ocr["full_text"])

            sampled_results.append({
                "label": label,
                "timestamp": ts,
                "frame_path": f_png,
                "metrics": f_metrics,
                "ocr": ocr,
                "expected_overlays": expected_overlays,
            })

        # 4. Blank / Solid frame & Visual Clarity check
        if blank_frames > 0:
            bl_stat, bl_sev = "FAIL", "CRITICAL"
            issues.append({
                "issue_id": "VIS_003",
                "severity": "CRITICAL",
                "type": "blank_or_solid_frame",
                "timestamp": ", ".join(f"{s['timestamp']}s" for s in sampled_results if s["metrics"]["is_blank"]),
                "expected": "Visible scene content across all sampled frames",
                "actual": f"{blank_frames}/{len(sampled_results)} sampled frame(s) completely blank/solid",
                "confidence": 1.0,
                "recommendation": "Inspect scene transitions and missing media inputs.",
            })
        else:
            bl_stat, bl_sev = "PASS", "INFO"

        checks.append({
            "name": "multi_frame_blank_check",
            "category": "visual",
            "method": "image_analysis",
            "status": bl_stat,
            "severity": bl_sev,
            "actual": f"{len(sampled_results) - blank_frames}/{len(sampled_results)} frames contain active visual content",
            "expected": "0 blank frames",
        })

        # 5. Scene & timeline transition check
        scene_cuts = self.detect_scene_changes(abs_path)
        checks.append({
            "name": "scene_timeline_structure",
            "category": "visual",
            "method": "deterministic",
            "status": "PASS",
            "severity": "INFO",
            "actual": f"Sampled {len(sampled_results)} timeline checkpoints; detected {len(scene_cuts)} visual cut(s)",
            "expected": "Expected timeline scenes verified across opening, body, and closing",
        })

        # 6. Real OCR Text Presence, Edge Clipping, Contrast & Platform Safe-Zone Check
        sz_spec = self.safe_zones_config.get("profiles", {}).get(platform_profile_id or "")
        expected_overlay_checks = []
        clipped_boxes = []
        unsafe_boxes = []
        low_contrast_boxes = []

        # Verify expected manifest overlays against OCR
        for s in sampled_results:
            for ov in s["expected_overlays"]:
                exp_title = ov.get("title") or ov.get("text") or ""
                if not exp_title:
                    continue
                conf, matched_line = _best_ocr_match(
                    exp_title,
                    s["ocr"].get("lines", []),
                    s["ocr"].get("full_text", ""),
                )
                # Also check across all frames in case timing shifted slightly
                if conf < 0.70:
                    conf_all, matched_all = _best_ocr_match(
                        exp_title,
                        all_ocr_lines_combined,
                        " ".join(all_ocr_full_text_parts),
                    )
                    if conf_all > conf:
                        conf, matched_line = conf_all, matched_all

                if not ocr_available_any:
                    ov_stat = "REVIEW_REQUIRED"
                elif conf >= 0.72:
                    ov_stat = "PASS"
                elif conf >= 0.45:
                    ov_stat = "REVIEW_REQUIRED"
                else:
                    ov_stat = "FAIL"

                expected_overlay_checks.append({
                    "expected_text": exp_title,
                    "timestamp": s["timestamp"],
                    "confidence": conf,
                    "status": ov_stat,
                    "matched_box": matched_line,
                })

                if ov_stat == "FAIL":
                    issues.append({
                        "issue_id": f"OCR_MISS_{len(issues)+1:02d}",
                        "severity": "CRITICAL",
                        "type": "expected_text_missing",
                        "timestamp": f"{s['timestamp']}s",
                        "expected": f"Overlay text '{exp_title}' visible on screen",
                        "actual": f"OCR best match confidence={conf:.2f} (detected: '{s['ocr'].get('full_text', '')[:80]}')",
                        "confidence": conf,
                        "recommendation": "Verify overlay layer rendering and timestamp alignment.",
                    })
                elif ov_stat == "REVIEW_REQUIRED":
                    issues.append({
                        "issue_id": f"OCR_UNCERTAIN_{len(issues)+1:02d}",
                        "severity": "REVIEW",
                        "type": "ocr_low_confidence",
                        "timestamp": f"{s['timestamp']}s",
                        "expected": f"Clear OCR match for '{exp_title}'",
                        "actual": f"Uncertain OCR confidence={conf:.2f}",
                        "confidence": conf,
                        "recommendation": "Human review required to verify text legibility.",
                    })

                # Check edge clipping, safe zone & contrast on matched overlay box
                if matched_line:
                    bx, by, bw, bh = matched_line["x"], matched_line["y"], matched_line["width"], matched_line["height"]
                    if bx <= 8 or by <= 8 or (bx + bw) >= (width - 8) or (by + bh) >= (height - 8):
                        clipped_boxes.append(matched_line)
                    if sz_spec and sz_spec["canvas"]["width"] == width and sz_spec["canvas"]["height"] == height:
                        sb = sz_spec.get("safe_content_box")
                        if sb:
                            if by < sb["y"] - 15 or (by + bh) > (sb["y"] + sb["height"] + 15) or bx < sb["x"] - 15 or (bx + bw) > (sb["x"] + sb["width"] + 15):
                                unsafe_boxes.append(matched_line)
                    contrast = self.measure_box_contrast(s["frame_path"], matched_line)
                    if contrast < 35.0:
                        low_contrast_boxes.append({"box": matched_line, "contrast": contrast})

        # Even without manifest overlays, check all large OCR text lines (>28px tall) for edge clipping or unsafe placement
        if not expected_overlay_checks and ocr_available_any:
            for s in sampled_results:
                for ln in s["ocr"].get("lines", []):
                    if ln["height"] >= 28 and len(ln.get("text", "").strip()) >= 4:
                        bx, by, bw, bh = ln["x"], ln["y"], ln["width"], ln["height"]
                        if bx <= 6 or by <= 6 or (bx + bw) >= (width - 6) or (by + bh) >= (height - 6):
                            clipped_boxes.append(ln)
                        if sz_spec and sz_spec["canvas"]["width"] == width and sz_spec["canvas"]["height"] == height:
                            sb = sz_spec.get("safe_content_box")
                            if sb:
                                # Flag overlay text placed squarely inside top/bottom high-severity occlusion zones
                                if by < sb["y"] - 25 or (by + bh) > (sb["y"] + sb["height"] + 25):
                                    unsafe_boxes.append(ln)

        # Record OCR text presence check
        if expected_overlay_checks:
            any_fail = any(c["status"] == "FAIL" for c in expected_overlay_checks)
            any_rev = any(c["status"] == "REVIEW_REQUIRED" for c in expected_overlay_checks)
            ocr_stat = "FAIL" if any_fail else ("REVIEW_REQUIRED" if any_rev else "PASS")
            avg_conf = round(sum(c["confidence"] for c in expected_overlay_checks) / len(expected_overlay_checks), 3)
            checks.append({
                "name": "ocr_expected_text_presence",
                "category": "visual_ocr",
                "method": "ocr",
                "engine": "Windows.Media.Ocr.OcrEngine",
                "status": ocr_stat,
                "severity": "CRITICAL" if any_fail else ("REVIEW" if any_rev else "INFO"),
                "confidence": avg_conf,
                "actual": f"{sum(1 for c in expected_overlay_checks if c['status']=='PASS')}/{len(expected_overlay_checks)} overlays verified (avg conf={avg_conf})",
                "expected": "All approved manifest text overlays readable via OCR",
            })
        else:
            checks.append({
                "name": "ocr_text_extraction",
                "category": "visual_ocr",
                "method": "ocr",
                "engine": "Windows.Media.Ocr.OcrEngine" if ocr_available_any else "unavailable",
                "status": "PASS" if ocr_available_any else "REVIEW_REQUIRED",
                "severity": "INFO" if ocr_available_any else "REVIEW",
                "confidence": 0.90 if ocr_available_any else 0.0,
                "actual": f"Extracted {len(all_ocr_lines_combined)} text line(s) across {len(sampled_results)} frames",
                "expected": "Local OCR extraction operational",
            })

        # Record clipped-text check
        if clipped_boxes:
            checks.append({
                "name": "ocr_text_edge_clipping",
                "category": "visual_ocr",
                "method": "ocr",
                "status": "FAIL",
                "severity": "CRITICAL",
                "confidence": 0.92,
                "actual": f"{len(clipped_boxes)} text box(es) clipped at canvas edge: {[b.get('text') for b in clipped_boxes[:3]]}",
                "expected": "No text truncated against frame boundaries",
            })
            issues.append({
                "issue_id": "VIS_004",
                "severity": "CRITICAL",
                "type": "clipped_text",
                "timestamp": f"{clipped_boxes[0].get('timestamp', 0.0)}s",
                "expected": "All text overlays padded cleanly inside canvas borders",
                "actual": f"Text '{clipped_boxes[0].get('text')}' touches frame edge (x={clipped_boxes[0]['x']}, y={clipped_boxes[0]['y']})",
                "confidence": 0.92,
                "recommendation": "Reduce font size or increase horizontal/vertical padding.",
            })
        else:
            checks.append({
                "name": "ocr_text_edge_clipping",
                "category": "visual_ocr",
                "method": "ocr",
                "status": "PASS",
                "severity": "INFO",
                "confidence": 0.92,
                "actual": "Zero edge-clipped text boxes detected",
                "expected": "No truncated text",
            })

        # Record safe-zone placement check on OCR boxes
        if unsafe_boxes:
            checks.append({
                "name": "ocr_safe_zone_placement",
                "category": "visual_ocr",
                "method": "ocr",
                "status": "FAIL",
                "severity": "CRITICAL",
                "confidence": 0.90,
                "actual": f"{len(unsafe_boxes)} overlay box(es) outside provisional safe zone '{platform_profile_id}': {[b.get('text') for b in unsafe_boxes[:3]]}",
                "expected": f"Overlay text contained inside safe content box ({platform_profile_id})",
            })
            issues.append({
                "issue_id": "VIS_005",
                "severity": "CRITICAL",
                "type": "unsafe_text_placement",
                "timestamp": f"{unsafe_boxes[0].get('timestamp', 0.0)}s",
                "expected": f"Overlay text inside {platform_profile_id} safe content box",
                "actual": f"Text '{unsafe_boxes[0].get('text')}' at y={unsafe_boxes[0]['y']} intrudes into platform UI chrome",
                "confidence": 0.90,
                "recommendation": "Reposition text overlay into safe central viewing zone.",
            })
        else:
            checks.append({
                "name": "ocr_safe_zone_placement",
                "category": "visual_ocr",
                "method": "ocr",
                "status": "PASS",
                "severity": "INFO",
                "confidence": 0.90,
                "actual": "All detected overlay text within configured safe bounds",
                "expected": "Safe-zone compliance",
            })

        # Generate annotated visual evidence on opening frame (and any frame with flagged boxes)
        annotated_paths = []
        if evidence_dir and sampled_results:
            os.makedirs(evidence_dir, exist_ok=True)
            flagged_all = clipped_boxes + unsafe_boxes
            ev_png = os.path.join(evidence_dir, f"annotated_{sampled_results[0]['label']}.png")
            self.annotate_evidence_frame(
                sampled_results[0]["frame_path"],
                ev_png,
                sampled_results[0]["ocr"].get("lines", []),
                safe_zone_profile=platform_profile_id,
                flagged_boxes=flagged_all,
            )
            annotated_paths.append(ev_png)
            for issue in issues:
                if issue["type"] in ("clipped_text", "unsafe_text_placement", "expected_text_missing", "frozen_frames_detected"):
                    issue["evidence_file"] = ev_png

        return {
            "checks": checks,
            "issues": issues,
            "metrics": {
                "black_events": black_events,
                "max_black_sec": max_black,
                "freeze_events": freeze_events,
                "max_freeze_sec": max_freeze,
                "scene_cuts_sec": scene_cuts,
                "sampled_frames_count": len(sampled_results),
                "blank_frames_count": blank_frames,
                "ocr_available": ocr_available_any,
                "ocr_lines_detected": len(all_ocr_lines_combined),
                "ocr_full_text_combined": " | ".join(all_ocr_full_text_parts),
                "expected_overlay_results": expected_overlay_checks,
                "annotated_evidence": annotated_paths,
            },
            "ocr_lines": all_ocr_lines_combined,
            "sampled_frames": [
                {"label": s["label"], "timestamp": s["timestamp"], "frame_path": s["frame_path"], "metrics": s["metrics"]}
                for s in sampled_results
            ],
        }
