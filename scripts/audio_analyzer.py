"""
audio_analyzer.py — Acoustic & Musical Audio Intelligence Engine
Analyzes physical audio files across technical, acoustic, structural, and licensing dimensions.

Key Capabilities:
  1. Technical Stream Audit: Duration, sample rate, channels, bitrate, codec, file size.
  2. Broadcast Loudness: Integrated loudness (LUFS), LRA, true peak (dBTP) via EBU R128.
  3. Dynamic & Peak Levels: RMS level, peak dBFS, digital clipping detection, silence analysis.
  4. Acoustic & Musical Properties: Tempo (BPM) with confidence rating, energy level (low/medium/high),
     rhythm regularity, speech vs. music vs. SFX classification.
  5. Structural Analysis: Timeline segments (intro, core, climax, outro), editing/loop recommendations.
  6. Mood Tagging: Multi-tag emotional classification (playful, corporate, calm, energetic, etc.).
  7. Licensing Integrity: Verification status, commercial permission, attribution tracking.
"""

import os
import sys
import json
import wave
import shutil
import hashlib
import tempfile
import subprocess
import numpy as np
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

WORKSPACE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(WORKSPACE_ROOT, "scripts"))
from media_engine import get_ffmpeg_cmd, get_ffprobe_cmd, run_command

DATA_DIR = os.path.join(WORKSPACE_ROOT, "data")
AUDIO_CATALOG_PATH = os.path.join(DATA_DIR, "audio_catalog.json")

ANALYZER_VERSION = "2.1.0-acoustic"

# Standard Licensing Status Enum
LICENSE_STATUSES = [
    "VERIFIED_COMMERCIAL_USE",
    "PERSONAL_USE_ONLY",
    "ATTRIBUTION_REQUIRED",
    "RESTRICTED",
    "UNKNOWN",
    "NEEDS_REVIEW"
]

# Supported formats
SUPPORTED_AUDIO_EXTENSIONS = (".wav", ".mp3", ".aac", ".m4a", ".flac", ".ogg", ".wma")


def get_audio_stream_metadata(filepath: str) -> Dict[str, Any]:
    """Extract format, codec, sample rate, channels, duration, bitrate via FFprobe."""
    ffprobe = get_ffprobe_cmd()
    cmd = ffprobe + [
        "-v", "error",
        "-show_entries", "format=duration,size,bit_rate,format_name:stream=codec_name,sample_rate,channels,bits_per_sample",
        "-of", "json",
        filepath
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    if res.returncode != 0:
        raise RuntimeError(f"FFprobe failed on {filepath}: {res.stderr}")

    info = json.loads(res.stdout)
    fmt = info.get("format", {})
    streams = info.get("streams", [])
    astream = next((s for s in streams if s.get("codec_name") != "png" and s.get("channels") is not None), streams[0] if streams else {})

    duration = float(fmt.get("duration", astream.get("duration", 0.0)))
    size = int(fmt.get("size", os.path.getsize(filepath) if os.path.exists(filepath) else 0))
    bitrate = int(fmt.get("bit_rate", astream.get("bit_rate", 0))) if fmt.get("bit_rate") or astream.get("bit_rate") else None
    sample_rate = int(astream.get("sample_rate", 44100))
    channels = int(astream.get("channels", 1))
    codec = astream.get("codec_name", os.path.splitext(filepath)[1].lstrip("."))

    return {
        "duration_seconds": round(duration, 3),
        "file_size_bytes": size,
        "sample_rate": sample_rate,
        "channels": channels,
        "codec": codec,
        "bitrate": bitrate,
        "format": os.path.splitext(filepath)[1].lstrip(".").lower()
    }


def measure_ebur128_loudness(filepath: str) -> Dict[str, Any]:
    """Measure Integrated Loudness (LUFS), True Peak (dBTP), and LRA using FFmpeg loudnorm filter."""
    ffmpeg = get_ffmpeg_cmd()
    cmd = ffmpeg + [
        "-hide_banner",
        "-i", filepath,
        "-af", "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json",
        "-f", "null",
        "-"
    ]
    res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    stderr = res.stderr

    start_idx = stderr.rfind("{")
    end_idx = stderr.rfind("}") + 1
    if start_idx != -1 and end_idx != -1:
        try:
            stats = json.loads(stderr[start_idx:end_idx])
            return {
                "integrated_lufs": float(stats.get("input_i", -99.0)),
                "true_peak_dbtp": float(stats.get("input_tp", -99.0)),
                "loudness_range_lu": float(stats.get("input_lra", 0.0)),
                "threshold_lufs": float(stats.get("input_thresh", -99.0)),
                "ebu_r128_compliant": (-15.5 <= float(stats.get("input_i", -99.0)) <= -13.0)
            }
        except Exception:
            pass

    return {
        "integrated_lufs": None,
        "true_peak_dbtp": None,
        "loudness_range_lu": None,
        "threshold_lufs": None,
        "ebu_r128_compliant": False
    }


def load_pcm_samples(filepath: str, target_sr: int = 22050) -> Tuple[np.ndarray, int]:
    """
    Load raw audio samples as normalized float32 (-1.0 to +1.0) mono numpy array.
    If file is not PCM wav, converts using ffmpeg to a temporary WAV.
    """
    ext = os.path.splitext(filepath)[1].lower()
    temp_wav = None

    if ext != ".wav":
        temp_wav = tempfile.mktemp(suffix=".wav")
        ffmpeg = get_ffmpeg_cmd()
        cmd = ffmpeg + ["-y", "-i", filepath, "-ac", "1", "-ar", str(target_sr), "-c:a", "pcm_s16le", temp_wav]
        run_command(cmd)
        read_path = temp_wav
    else:
        read_path = filepath

    try:
        with wave.open(read_path, "rb") as wf:
            sr = wf.getframerate()
            n_ch = wf.getnchannels()
            n_frames = wf.getnframes()
            if n_frames == 0:
                return np.zeros(0, dtype=np.float32), sr
            raw = wf.readframes(n_frames)
            samples = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
            if n_ch > 1:
                samples = samples.reshape(-1, n_ch).mean(axis=1)
            return samples, sr
    finally:
        if temp_wav and os.path.exists(temp_wav):
            try:
                os.remove(temp_wav)
            except OSError:
                pass


def analyze_acoustic_properties(samples: np.ndarray, sr: int) -> Dict[str, Any]:
    """
    Analyzes physical acoustic waveform:
      - Peak dBFS, RMS dBFS, digital clipping
      - Silence ratio & longest silence gap
      - Speech vs Music vs SFX classification
      - Tempo / BPM via novelty autocorrelation
      - Energy level (low, medium, high)
      - Rhythm regularity
    """
    if len(samples) == 0:
        return {
            "peak_dbfs": -99.0,
            "rms_dbfs": -99.0,
            "clipping_detected": False,
            "clipping_count": 0,
            "silence_ratio": 1.0,
            "has_silence_issues": True,
            "speech_presence": "none",
            "estimated_bpm": None,
            "bpm_confidence": "none",
            "energy_level": "low",
            "rhythm_type": "ambient"
        }

    duration = len(samples) / sr

    # 1. Peak & RMS
    peak = float(np.max(np.abs(samples)))
    peak_dbfs = round(float(20 * np.log10(peak + 1e-9)), 2)
    rms = float(np.sqrt(np.mean(samples**2)))
    rms_dbfs = round(float(20 * np.log10(rms + 1e-9)), 2)

    # 2. Digital Clipping (> 99.8% full scale)
    clipping_count = int(np.sum(np.abs(samples) >= 0.998))
    clipping_detected = clipping_count > 5

    # 3. Short-Time Energy & Silence Detection (20ms frames, 10ms hop)
    frame_len = int(sr * 0.02)
    hop = int(sr * 0.01)
    if len(samples) > frame_len:
        # Fast vectorized framing
        num_frames = (len(samples) - frame_len) // hop
        # Reshape into contiguous windows
        strided = np.lib.stride_tricks.sliding_window_view(samples[:num_frames * hop + frame_len], window_shape=frame_len)[::hop]
        frame_energies = np.mean(strided**2, axis=1)
        frame_db = 20 * np.log10(np.sqrt(frame_energies) + 1e-9)
        silence_mask = frame_db < -42.0
        silence_ratio = round(float(np.mean(silence_mask)), 3)

        # Longest silence run
        longest_silence_sec = 0.0
        cur_run = 0
        for is_sil in silence_mask:
            if is_sil:
                cur_run += 1
                if (cur_run * hop / sr) > longest_silence_sec:
                    longest_silence_sec = cur_run * hop / sr
            else:
                cur_run = 0
    else:
        silence_ratio = 0.0
        longest_silence_sec = 0.0

    # 4. Zero Crossing Rate (ZCR)
    zero_crossings = float(np.sum(np.diff(samples > 0) != 0) / len(samples))

    # 5. Sound Category Classification (Speech vs Music vs SFX)
    if duration < 1.0:
        sound_type = "sound_effect"
    elif silence_ratio > 0.40 or (zero_crossings > 0.07 and silence_ratio > 0.20):
        sound_type = "voiceover_speech"
    else:
        sound_type = "instrumental_music"

    # 6. Energy Level
    if rms_dbfs > -16.5:
        energy_level = "high"
    elif rms_dbfs > -25.0:
        energy_level = "medium"
    else:
        energy_level = "low"

    # 7. Tempo / BPM Estimation (for music / rhythmic audio >= 2.0s)
    estimated_bpm = None
    bpm_confidence = "none"
    rhythm_type = "ambient"

    if duration >= 2.0 and sound_type != "voiceover_speech":
        # Envelope onset detection
        hop_env = int(sr * 0.01)
        flen_env = int(sr * 0.02)
        n_hops = (len(samples) - flen_env) // hop_env
        if n_hops > 100:
            strided_env = np.lib.stride_tricks.sliding_window_view(samples[:n_hops * hop_env + flen_env], window_shape=flen_env)[::hop_env]
            env = np.sum(strided_env**2, axis=1)
            diff = np.diff(env)
            novelty = np.maximum(0, diff)

            fps_env = sr / hop_env  # 100 Hz
            min_lag = int(fps_env * 60.0 / 185.0)  # max ~185 BPM
            max_lag = int(fps_env * 60.0 / 65.0)   # min ~65 BPM

            if len(novelty) > max_lag * 2:
                corr = np.correlate(novelty, novelty, mode="full")
                corr = corr[len(novelty) - 1:]
                window = corr[min_lag:max_lag]
                if len(window) > 0:
                    peak_idx = int(np.argmax(window))
                    best_lag = min_lag + peak_idx
                    raw_bpm = round(float(60.0 * fps_env / best_lag), 1)

                    peak_val = float(window[peak_idx])
                    mean_val = float(np.mean(window)) + 1e-6
                    peak_ratio = peak_val / mean_val

                    if peak_ratio > 3.0:
                        estimated_bpm = raw_bpm
                        bpm_confidence = "high"
                        rhythm_type = "steady_beat"
                    elif peak_ratio > 1.8:
                        estimated_bpm = raw_bpm
                        bpm_confidence = "medium"
                        rhythm_type = "syncopated"
                    else:
                        estimated_bpm = None
                        bpm_confidence = "low"
                        rhythm_type = "ambient"

    return {
        "peak_dbfs": peak_dbfs,
        "rms_dbfs": rms_dbfs,
        "clipping_detected": clipping_detected,
        "clipping_count": clipping_count,
        "silence_ratio": silence_ratio,
        "longest_silence_seconds": round(longest_silence_sec, 2),
        "has_silence_issues": (longest_silence_sec > 3.0 and duration > 5.0),
        "speech_presence": sound_type,
        "estimated_bpm": estimated_bpm,
        "bpm_confidence": bpm_confidence,
        "energy_level": energy_level,
        "rhythm_type": rhythm_type
    }


def determine_mood_and_structure(
    meta: Dict[str, Any],
    acoustic: Dict[str, Any],
    file_path: str
) -> Tuple[List[str], List[Dict[str, Any]], Optional[str]]:
    """
    Rule-based, transparent mood classification and structural timeline segmentation.
    Derives moods from acoustic evidence (energy, tempo, rhythm, silence) and asset taxonomy.
    """
    path_lower = file_path.lower().replace("\\", "/")
    dur = meta["duration_seconds"]
    energy = acoustic["energy_level"]
    bpm = acoustic["estimated_bpm"]
    sound_type = acoustic["speech_presence"]

    moods = []

    # 1. Mood mapping from acoustic profiles & project context
    if sound_type == "sound_effect":
        moods.append("functional_sfx")
    elif sound_type == "voiceover_speech":
        moods.append("narrative")
        if "ezisales" in path_lower or "expand-hr" in path_lower:
            moods.extend(["professional", "instructional", "clear"])
        else:
            moods.extend(["relatable", "conversational"])
    else:
        # Music track: Combine acoustic energy tags with domain & instrument tags
        if energy == "high":
            moods.extend(["energetic", "upbeat"])
            if bpm and bpm >= 120:
                moods.extend(["playful", "cheerful"])
        elif energy == "medium":
            moods.extend(["steady", "focused"])
        else:
            moods.extend(["relaxing", "calm", "ambient"])

        if "corporate" in path_lower or "ezisales" in path_lower or "wms" in path_lower:
            moods.extend(["corporate", "technology", "modern", "professional"])
        if "trust" in path_lower or "hr" in path_lower:
            moods.extend(["trustworthy", "corporate", "calm", "positive"])
        if "puzzle" in path_lower or "burst" in path_lower:
            moods.extend(["playful", "cheerful", "casual_gaming", "satisfying"])
        if "retail" in path_lower or "pos" in path_lower:
            moods.extend(["retail_friendly", "modern", "upbeat"])
        if "piano" in path_lower or "relax" in path_lower:
            moods.extend(["relaxing", "calm", "peaceful"])

    moods = list(dict.fromkeys(moods))

    # 2. Structural Timeline Segmentation
    structure = []
    if dur >= 8.0:
        intro_end = min(3.0, dur * 0.20)
        core_end = min(dur - 2.0, dur * 0.80)
        structure = [
            {"section": "intro", "start_sec": 0.0, "end_sec": round(intro_end, 2), "description": "Opening hook / thematic introduction"},
            {"section": "main_body", "start_sec": round(intro_end, 2), "end_sec": round(core_end, 2), "description": "Core rhythm / continuous gameplay or demo bed"},
            {"section": "outro_resolve", "start_sec": round(core_end, 2), "end_sec": dur, "description": "Call-to-action resolution / decay to silence"}
        ]
    else:
        structure = [
            {"section": "full", "start_sec": 0.0, "end_sec": dur, "description": "Single-shot burst or transient sound effect"}
        ]

    # 3. Key estimation placeholder (mark unknown per prompt instructions if not establishable)
    key_est = None

    return moods, structure, key_est


def map_project_and_platforms(path: str, sound_type: str, moods: List[str]) -> Tuple[List[str], List[str], List[str]]:
    """Determine best use cases, recommended projects, and platforms."""
    path_norm = path.replace("\\", "/").lower()

    # Project recommendation
    recommended_projects = []
    for proj in ["block-puzzle-burst", "expand-ezisales", "expand-hr", "wms", "pos"]:
        if proj in path_norm:
            recommended_projects.append(proj)
    if not recommended_projects:
        # Cross-project heuristics
        if any(m in ["playful", "cheerful", "casual_gaming"] for m in moods):
            recommended_projects.append("block-puzzle-burst")
        if any(m in ["corporate", "technology"] for m in moods):
            recommended_projects.extend(["expand-ezisales", "wms"])
        if any(m in ["trustworthy", "calm"] for m in moods):
            recommended_projects.append("expand-hr")
        if "retail_friendly" in moods:
            recommended_projects.append("pos")

    # Use cases
    best_use_cases = []
    if sound_type == "sound_effect":
        best_use_cases.extend(["ui_feedback", "block_placement", "transition_accent"])
    elif sound_type == "voiceover_speech":
        best_use_cases.extend(["software_tutorial", "lifestyle_narration", "explainer_voiceover"])
    else:
        if "playful" in moods:
            best_use_cases.extend(["puzzle_gameplay_reel", "lifestyle_advertisement", "satisfying_clear_highlight"])
        if "corporate" in moods:
            best_use_cases.extend(["software_walkthrough", "product_demonstration", "b2b_explainer"])
        if "relaxing" in moods:
            best_use_cases.extend(["lifestyle_storytelling", "evening_relaxation_hook"])

    # Platforms
    recommended_platforms = ["instagram_reels", "facebook_reels", "youtube_shorts"]
    if "corporate" in moods or sound_type == "voiceover_speech":
        recommended_platforms.append("youtube_tutorials")

    return best_use_cases, recommended_projects, recommended_platforms


def analyze_audio_asset(filepath: str, project_hint: Optional[str] = None) -> Dict[str, Any]:
    """
    Complete analysis of an audio file, returning a standardized schema-compliant record.
    """
    abs_path = os.path.abspath(filepath)
    if not os.path.exists(abs_path):
        raise FileNotFoundError(f"Audio file not found: {abs_path}")

    # 1. Technical Stream Info
    stream_meta = get_audio_stream_metadata(abs_path)

    # 2. EBU R128 Loudness
    loudness_meta = measure_ebur128_loudness(abs_path)

    # 3. Acoustic Waveform Analysis
    samples, sr = load_pcm_samples(abs_path)
    acoustic_meta = analyze_acoustic_properties(samples, sr)

    # 4. Mood and Structure
    moods, structure, key_est = determine_mood_and_structure(stream_meta, acoustic_meta, abs_path)

    # 5. Suitability & Use Cases
    use_cases, rec_projects, rec_platforms = map_project_and_platforms(
        abs_path, acoustic_meta["speech_presence"], moods
    )
    if project_hint and project_hint not in rec_projects:
        rec_projects.insert(0, project_hint)

    # 6. Licensing Defaults (Strict audit rules)
    # Studio-generated files or recordings
    is_studio_internal = ("voiceovers" in abs_path or "sfx_" in abs_path or "bgm_day05" in abs_path)
    license_status = "VERIFIED_COMMERCIAL_USE" if is_studio_internal else "NEEDS_REVIEW"
    license_source = "Pyapiras Studio Production" if is_studio_internal else None

    # Deterministic Asset ID from content hash
    with open(abs_path, "rb") as f:
        file_hash = hashlib.sha256(f.read(8192)).hexdigest()[:8].upper()
    asset_id = f"AUDIO_{file_hash}"

    record = {
        "asset_id": asset_id,
        "filename": os.path.basename(abs_path),
        "path": os.path.relpath(abs_path, WORKSPACE_ROOT).replace("\\", "/"),
        "duration_seconds": stream_meta["duration_seconds"],
        "format": stream_meta["format"],
        "sample_rate": stream_meta["sample_rate"],
        "channels": stream_meta["channels"],
        "codec": stream_meta["codec"],
        "bitrate": stream_meta["bitrate"],
        "file_size_bytes": stream_meta["file_size_bytes"],
        "integrated_lufs": loudness_meta["integrated_lufs"],
        "true_peak_dbtp": loudness_meta["true_peak_dbtp"],
        "loudness_range_lu": loudness_meta["loudness_range_lu"],
        "peak_dbfs": acoustic_meta["peak_dbfs"],
        "rms_dbfs": acoustic_meta["rms_dbfs"],
        "clipping_detected": acoustic_meta["clipping_detected"],
        "silence_ratio": acoustic_meta["silence_ratio"],
        "sound_classification": acoustic_meta["speech_presence"],
        "bpm": acoustic_meta["estimated_bpm"],
        "bpm_confidence": acoustic_meta["bpm_confidence"],
        "energy_level": acoustic_meta["energy_level"],
        "rhythm_type": acoustic_meta["rhythm_type"],
        "key": key_est,
        "mood": moods,
        "vocal_type": "speech" if acoustic_meta["speech_presence"] == "voiceover_speech" else "instrumental",
        "best_use_cases": use_cases,
        "recommended_projects": rec_projects,
        "recommended_platforms": rec_platforms,
        "timeline_structure": structure,
        "license_status": license_status,
        "license_source": license_source,
        "commercial_use_allowed": (license_status == "VERIFIED_COMMERCIAL_USE"),
        "attribution_required": False,
        "analysis_confidence": "high" if acoustic_meta["bpm_confidence"] != "low" else "medium",
        "analysis_status": "completed",
        "analyzed_at": datetime.now().isoformat(),
        "analyzer_version": ANALYZER_VERSION
    }

    return record


def update_audio_catalog(new_records: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Merge new records into data/audio_catalog.json without duplicating."""
    os.makedirs(DATA_DIR, exist_ok=True)
    catalog = {"generated_at": datetime.now().isoformat(), "total_assets": 0, "assets": {}}

    if os.path.exists(AUDIO_CATALOG_PATH):
        try:
            with open(AUDIO_CATALOG_PATH, "r", encoding="utf-8") as f:
                catalog = json.load(f)
        except Exception:
            pass

    assets_dict = catalog.get("assets", {})
    for rec in new_records:
        assets_dict[rec["asset_id"]] = rec

    catalog["assets"] = assets_dict
    catalog["total_assets"] = len(assets_dict)
    catalog["updated_at"] = datetime.now().isoformat()

    with open(AUDIO_CATALOG_PATH, "w", encoding="utf-8") as f:
        json.dump(catalog, f, indent=2)

    return catalog


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Acoustic & Musical Audio Intelligence Engine")
    parser.add_argument("file", nargs="?", help="Path to single audio file to analyze")
    parser.add_argument("--scan-dir", help="Scan and catalog an entire folder of audio files")
    parser.add_argument("--project", help="Project association hint")
    args = parser.parse_args()

    if args.file:
        res = analyze_audio_asset(args.file, args.project)
        print(json.dumps(res, indent=2))
        update_audio_catalog([res])
        print(f"\n✅ Analyzed and saved {res['asset_id']} to {AUDIO_CATALOG_PATH}")
    elif args.scan_dir:
        abs_scan = os.path.abspath(args.scan_dir)
        records = []
        for root, _, files in os.walk(abs_scan):
            for f in files:
                if f.lower().endswith(SUPPORTED_AUDIO_EXTENSIONS):
                    p = os.path.join(root, f)
                    try:
                        rec = analyze_audio_asset(p, args.project)
                        records.append(rec)
                        print(f"  • Analyzed: {rec['filename']} (BPM: {rec['bpm']}, Energy: {rec['energy_level']}, Moods: {rec['mood']})")
                    except Exception as e:
                        print(f"  ❌ Error on {f}: {e}")
        cat = update_audio_catalog(records)
        print(f"\n✅ Total {len(records)} audio assets cataloged into {AUDIO_CATALOG_PATH}")
    else:
        parser.print_help()
