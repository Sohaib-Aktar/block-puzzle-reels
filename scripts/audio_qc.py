"""
audio_qc.py — Automated Audio Quality Control Engine (Phase 5)
Reuses media_engine.py and audio_analyzer.py patterns to evaluate:
  - Audio stream presence & format
  - EBU R128 integrated loudness (LUFS) & true peak (dBTP)
  - Peak, RMS, and clipping detection (volumedetect + ebur128)
  - Excessive silence & unexpected audio gaps (silencedetect)
  - Abrupt audio ending check (tail energy check)
  - Audio/video duration synchronization
  - Voiceover script alignment status (honestly flags REVIEW_REQUIRED when local ASR is absent)
"""

import os
import re
import sys
import json
import subprocess
from typing import Dict, Any, List, Optional

WORKSPACE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(WORKSPACE_ROOT, "scripts"))
from media_engine import get_ffmpeg_cmd, inspect_media


class AudioQC:
    """Runs deterministic acoustic & stream checks on rendered video/audio files."""

    def __init__(
        self,
        target_lufs: float = -14.0,
        lufs_tolerance_warn: float = 5.0,
        max_silence_ratio_fail: float = 0.75,
        max_silence_gap_warn_sec: float = 2.5,
        max_silence_gap_fail_sec: float = 4.5,
    ):
        self.target_lufs = target_lufs
        self.lufs_tolerance_warn = lufs_tolerance_warn
        self.max_silence_ratio_fail = max_silence_ratio_fail
        self.max_silence_gap_warn_sec = max_silence_gap_warn_sec
        self.max_silence_gap_fail_sec = max_silence_gap_fail_sec

    def _run_ffmpeg(self, args: List[str]) -> subprocess.CompletedProcess:
        return subprocess.run(
            get_ffmpeg_cmd() + args,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )

    def _measure_ebur128(self, abs_path: str) -> Dict[str, Optional[float]]:
        res = self._run_ffmpeg(["-i", abs_path, "-af", "ebur128=peak=true", "-vn", "-f", "null", "-"])
        stderr = res.stderr or ""
        lufs = None
        lra = None
        true_peak = None
        # Parse final summary block of ebur128
        m_i = re.findall(r"^\s*I:\s*([-\d.]+)\s*LUFS", stderr, flags=re.MULTILINE)
        if m_i:
            lufs = float(m_i[-1])
        m_lra = re.findall(r"^\s*LRA:\s*([-\d.]+)\s*LU", stderr, flags=re.MULTILINE)
        if m_lra:
            lra = float(m_lra[-1])
        m_tp = re.findall(r"^\s*Peak:\s*([-\d.]+)\s*dBFS", stderr, flags=re.MULTILINE)
        if m_tp:
            true_peak = float(m_tp[-1])
        return {"integrated_lufs": lufs, "lra_lu": lra, "true_peak_dbtp": true_peak}

    def _measure_volume(self, abs_path: str) -> Dict[str, Optional[float]]:
        res = self._run_ffmpeg(["-i", abs_path, "-af", "volumedetect", "-vn", "-f", "null", "-"])
        stderr = res.stderr or ""
        mean_db = None
        max_db = None
        m_mean = re.search(r"mean_volume:\s*([-\d.]+)\s*dB", stderr)
        m_max = re.search(r"max_volume:\s*([-\d.]+)\s*dB", stderr)
        if m_mean:
            mean_db = float(m_mean.group(1))
        if m_max:
            max_db = float(m_max.group(1))
        return {"mean_volume_db": mean_db, "max_volume_db": max_db}

    def _detect_silence(self, abs_path: str, noise_db: str = "-48dB", min_dur: float = 1.2) -> List[Dict[str, float]]:
        res = self._run_ffmpeg([
            "-i", abs_path,
            "-af", f"silencedetect=noise={noise_db}:d={min_dur}",
            "-vn", "-f", "null", "-"
        ])
        stderr = res.stderr or ""
        starts = [float(x) for x in re.findall(r"silence_start:\s*([-\d.]+)", stderr)]
        ends = re.findall(r"silence_end:\s*([-\d.]+)\s*\|\s*silence_duration:\s*([-\d.]+)", stderr)
        events = []
        for idx, (e_str, d_str) in enumerate(ends):
            st = starts[idx] if idx < len(starts) else max(0.0, float(e_str) - float(d_str))
            events.append({"start": round(st, 3), "end": round(float(e_str), 3), "duration": round(float(d_str), 3)})
        # Handle trailing unclosed silence_start
        if len(starts) > len(ends):
            events.append({"start": round(starts[-1], 3), "end": -1.0, "duration": -1.0})
        return events

    def _measure_tail_volume(self, abs_path: str, total_duration: float) -> Optional[float]:
        if total_duration < 0.6:
            return None
        tail_start = max(0.0, total_duration - 0.25)
        res = self._run_ffmpeg([
            "-ss", f"{tail_start:.3f}",
            "-i", abs_path,
            "-af", "volumedetect",
            "-vn", "-f", "null", "-"
        ])
        m = re.search(r"mean_volume:\s*([-\d.]+)\s*dB", res.stderr or "")
        return float(m.group(1)) if m else None

    def run(
        self,
        video_path: str,
        manifest: Optional[Dict[str, Any]] = None,
        audio_required: bool = True,
        evidence_dir: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Executes complete automated Audio QC and returns checks, issues, and acoustic metrics."""
        abs_path = os.path.abspath(video_path)
        checks: List[Dict[str, Any]] = []
        issues: List[Dict[str, Any]] = []

        info = inspect_media(abs_path)
        raw = info.get("raw_ffprobe", {})
        streams = raw.get("streams", [])
        vstream = next((s for s in streams if s.get("codec_type") == "video"), None)
        astream = next((s for s in streams if s.get("codec_type") == "audio"), None)
        duration = float(info.get("duration_seconds", 0.0))

        # 1. Audio stream presence
        has_audio = astream is not None
        if not has_audio:
            status = "FAIL" if audio_required else "PASS"
            checks.append({
                "name": "audio_stream_presence",
                "category": "audio",
                "method": "deterministic",
                "status": status,
                "severity": "CRITICAL" if audio_required else "INFO",
                "actual": "Missing audio stream",
                "expected": "Audio stream present" if audio_required else "Optional",
            })
            if audio_required:
                issues.append({
                    "issue_id": "AUD_001",
                    "severity": "CRITICAL",
                    "type": "missing_audio",
                    "timestamp": "0.0s",
                    "expected": "AAC audio stream present",
                    "actual": "No audio stream found in media container",
                    "confidence": 1.0,
                    "recommendation": "Mix audio track or attach approved soundtrack before re-rendering.",
                })
            return {"checks": checks, "issues": issues, "metrics": {"has_audio": False}}

        checks.append({
            "name": "audio_stream_presence",
            "category": "audio",
            "method": "deterministic",
            "status": "PASS",
            "severity": "INFO",
            "actual": f"{info.get('audio_codec')} {info.get('audio_channels')}ch @ {info.get('audio_sample_rate')}Hz",
            "expected": "Valid audio stream",
        })

        # 2. A/V sync duration check
        v_dur = float(vstream.get("duration", duration)) if vstream else duration
        a_dur = float(astream.get("duration", duration))
        av_delta = abs(v_dur - a_dur)
        if av_delta > 0.50:
            sync_status, sync_sev = "FAIL", "CRITICAL"
            issues.append({
                "issue_id": "AUD_002",
                "severity": "CRITICAL",
                "type": "av_sync_mismatch",
                "timestamp": f"0.0s-{duration:.2f}s",
                "expected": "A/V stream duration delta <= 0.35s",
                "actual": f"video={v_dur:.3f}s, audio={a_dur:.3f}s (delta={av_delta:.3f}s)",
                "confidence": 1.0,
                "recommendation": "Re-mux or re-encode with -shortest and synchronized timestamps.",
            })
        elif av_delta > 0.35:
            sync_status, sync_sev = "PASS_WITH_WARNINGS", "WARNING"
            issues.append({
                "issue_id": "AUD_002",
                "severity": "WARNING",
                "type": "av_sync_drift",
                "timestamp": f"0.0s-{duration:.2f}s",
                "expected": "A/V delta <= 0.35s",
                "actual": f"delta={av_delta:.3f}s",
                "confidence": 1.0,
                "recommendation": "Inspect audio/video alignment at clip boundaries.",
            })
        else:
            sync_status, sync_sev = "PASS", "INFO"

        checks.append({
            "name": "audio_video_sync",
            "category": "audio",
            "method": "deterministic",
            "status": sync_status,
            "severity": sync_sev,
            "actual": f"delta={av_delta:.3f}s",
            "expected": "<= 0.35s",
        })

        # 3. Loudness (EBU R128) & Volume / Clipping
        ebur = self._measure_ebur128(abs_path)
        vol = self._measure_volume(abs_path)
        lufs = ebur["integrated_lufs"]
        tp = ebur["true_peak_dbtp"]
        max_db = vol["max_volume_db"]
        mean_db = vol["mean_volume_db"]

        # Clipping check: true peak > +0.2 dBTP OR max_volume == 0.0 dBFS with hot loudness (> -8 LUFS)
        is_clipping = (tp is not None and tp > 0.2) or (max_db is not None and max_db >= -0.01 and (lufs is None or lufs > -9.0))
        if is_clipping:
            clip_status, clip_sev = "FAIL", "CRITICAL"
            issues.append({
                "issue_id": "AUD_003",
                "severity": "CRITICAL",
                "type": "audio_clipping",
                "timestamp": f"0.0s-{duration:.2f}s",
                "expected": "True peak <= 0.0 dBTP and no digital clipping",
                "actual": f"true_peak={tp} dBTP, max_volume={max_db} dBFS, integrated={lufs} LUFS",
                "confidence": 0.98,
                "recommendation": "Apply limiter / EBU R128 loudnorm (TP=-1.5 dBTP) and reduce input gain.",
            })
        else:
            clip_status, clip_sev = "PASS", "INFO"

        checks.append({
            "name": "audio_clipping_and_true_peak",
            "category": "audio",
            "method": "deterministic",
            "status": clip_status,
            "severity": clip_sev,
            "actual": f"max_vol={max_db} dB, true_peak={tp} dBTP",
            "expected": "true_peak <= 0.0 dBTP (target -1.5 dBTP)",
        })

        # Integrated loudness check
        if lufs is None or lufs <= -60.0:
            loud_status, loud_sev = "FAIL", "CRITICAL"
            issues.append({
                "issue_id": "AUD_004",
                "severity": "CRITICAL",
                "type": "silent_audio_track",
                "timestamp": f"0.0s-{duration:.2f}s",
                "expected": f"Audible mix near {self.target_lufs} LUFS",
                "actual": f"integrated_lufs={lufs} LUFS (effectively silent)",
                "confidence": 1.0,
                "recommendation": "Verify audio stem routing; track is silent.",
            })
        elif abs(lufs - self.target_lufs) > self.lufs_tolerance_warn:
            loud_status, loud_sev = "PASS_WITH_WARNINGS", "WARNING"
            issues.append({
                "issue_id": "AUD_004",
                "severity": "WARNING",
                "type": "loudness_out_of_target_range",
                "timestamp": f"0.0s-{duration:.2f}s",
                "expected": f"{self.target_lufs} LUFS (±{self.lufs_tolerance_warn} LU)",
                "actual": f"{lufs} LUFS (mean={mean_db} dB)",
                "confidence": 1.0,
                "recommendation": "Normalize audio via EBU R128 loudnorm=I=-14:LRA=11:TP=-1.5.",
            })
        else:
            loud_status, loud_sev = "PASS", "INFO"

        checks.append({
            "name": "integrated_loudness_ebur128",
            "category": "audio",
            "method": "deterministic",
            "status": loud_status,
            "severity": loud_sev,
            "actual": f"{lufs} LUFS (LRA={ebur['lra_lu']} LU, mean={mean_db} dB)",
            "expected": f"{self.target_lufs} LUFS (±{self.lufs_tolerance_warn} LU)",
        })

        # 4. Excessive silence & unexpected audio gaps
        silence_events = self._detect_silence(abs_path)
        total_silence = 0.0
        max_gap = 0.0
        for ev in silence_events:
            d = ev["duration"] if ev["duration"] >= 0 else max(0.0, duration - ev["start"])
            ev["duration"] = round(d, 3)
            if ev["end"] < 0:
                ev["end"] = round(duration, 3)
            total_silence += d
            if d > max_gap:
                max_gap = d
        silence_ratio = total_silence / max(0.01, duration)

        if silence_ratio >= self.max_silence_ratio_fail or max_gap >= self.max_silence_gap_fail_sec:
            sil_status, sil_sev = "FAIL", "CRITICAL"
            issues.append({
                "issue_id": "AUD_005",
                "severity": "CRITICAL",
                "type": "excessive_silence",
                "timestamp": f"{silence_events[0]['start']}s-{silence_events[0]['end']}s" if silence_events else "0.0s",
                "expected": f"Silence ratio < {self.max_silence_ratio_fail*100:.0f}% and max gap < {self.max_silence_gap_fail_sec}s",
                "actual": f"silence_ratio={silence_ratio*100:.1f}%, max_gap={max_gap:.2f}s ({len(silence_events)} event(s))",
                "confidence": 1.0,
                "recommendation": "Check missing BGM/VO segments or audio dropouts.",
            })
        elif max_gap >= self.max_silence_gap_warn_sec or silence_ratio >= 0.40:
            sil_status, sil_sev = "PASS_WITH_WARNINGS", "WARNING"
            issues.append({
                "issue_id": "AUD_005",
                "severity": "WARNING",
                "type": "audio_gap_detected",
                "timestamp": f"{silence_events[0]['start']}s-{silence_events[0]['end']}s" if silence_events else "0.0s",
                "expected": f"Max silence gap < {self.max_silence_gap_warn_sec}s",
                "actual": f"silence_ratio={silence_ratio*100:.1f}%, max_gap={max_gap:.2f}s",
                "confidence": 1.0,
                "recommendation": "Review silent intervals to ensure they are intentional.",
            })
        else:
            sil_status, sil_sev = "PASS", "INFO"

        checks.append({
            "name": "silence_and_audio_gaps",
            "category": "audio",
            "method": "deterministic",
            "status": sil_status,
            "severity": sil_sev,
            "actual": f"silence_ratio={silence_ratio*100:.1f}%, max_gap={max_gap:.2f}s",
            "expected": f"ratio < {self.max_silence_ratio_fail*100:.0f}%, gap < {self.max_silence_gap_fail_sec}s",
        })

        # 5. Abrupt audio ending check
        tail_db = self._measure_tail_volume(abs_path, duration)
        if tail_db is not None and mean_db is not None and tail_db > mean_db + 3.0 and tail_db > -12.0:
            end_status, end_sev = "PASS_WITH_WARNINGS", "WARNING"
            issues.append({
                "issue_id": "AUD_006",
                "severity": "WARNING",
                "type": "abrupt_audio_ending",
                "timestamp": f"{max(0.0, duration-0.25):.2f}s-{duration:.2f}s",
                "expected": "Smooth audio fade-out at ending",
                "actual": f"Tail mean volume ({tail_db:.1f} dB) exceeds track mean ({mean_db:.1f} dB)",
                "confidence": 0.85,
                "recommendation": "Add 0.4s-0.8s audio fade-out at the end of the timeline.",
            })
        else:
            end_status, end_sev = "PASS", "INFO"

        checks.append({
            "name": "audio_ending_fade_check",
            "category": "audio",
            "method": "deterministic",
            "status": end_status,
            "severity": end_sev,
            "actual": f"tail_mean={tail_db} dB",
            "expected": "No abrupt loud ending spike",
        })

        # 6. Voiceover transcript alignment (honest ASR capability reporting)
        vo_text = None
        if manifest:
            vo_cfg = (manifest.get("audio") or {}).get("voiceover") or {}
            vo_text = vo_cfg.get("text") or (manifest.get("audio") or {}).get("voiceover_text")

        if vo_text:
            checks.append({
                "name": "voiceover_transcript_alignment",
                "category": "audio",
                "method": "asr_pending",
                "status": "REVIEW_REQUIRED",
                "severity": "REVIEW",
                "confidence": 0.0,
                "actual": "Local ASR engine not installed (Whisper/SAPI ASR unavailable); human audio listen-through required.",
                "expected": f"Verify spoken script matches: \"{vo_text[:80]}...\"",
            })
            issues.append({
                "issue_id": "AUD_007",
                "severity": "REVIEW",
                "type": "asr_unavailable_manual_review",
                "timestamp": f"0.0s-{duration:.2f}s",
                "expected": "Automated speech-to-text alignment against voiceover script",
                "actual": "No offline ASR model installed in workspace environment",
                "confidence": 0.0,
                "recommendation": "Human reviewer must listen to verify voiceover intelligibility and script accuracy.",
            })

        metrics = {
            "has_audio": True,
            "codec": info.get("audio_codec"),
            "sample_rate": info.get("audio_sample_rate"),
            "channels": info.get("audio_channels"),
            "video_duration": v_dur,
            "audio_duration": a_dur,
            "av_sync_delta_sec": round(av_delta, 4),
            "integrated_lufs": lufs,
            "loudness_range_lu": ebur["lra_lu"],
            "true_peak_dbtp": tp,
            "mean_volume_db": mean_db,
            "max_volume_db": max_db,
            "tail_volume_db": tail_db,
            "silence_ratio": round(silence_ratio, 4),
            "max_silence_gap_sec": round(max_gap, 3),
            "silence_events": silence_events,
            "asr_available": False,
        }

        if evidence_dir:
            os.makedirs(evidence_dir, exist_ok=True)
            with open(os.path.join(evidence_dir, "audio_metrics.json"), "w", encoding="utf-8") as f:
                json.dump(metrics, f, indent=2)

        return {"checks": checks, "issues": issues, "metrics": metrics}
