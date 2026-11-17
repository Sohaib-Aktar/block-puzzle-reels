#!/usr/bin/env python3
"""
scripts/inspect_real_audio.py
=============================
Discovers, verifies, and analyzes all real MP3 files in Raw_input_files/audio/.
Extracts complete technical, acoustic, loudness, and licensing provenance metadata.
"""

import os
import sys
import json
import hashlib
import tempfile
import subprocess
from datetime import datetime
from typing import Dict, Any, List, Tuple

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
WORKSPACE_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

import audio_analyzer
import media_engine

RAW_AUDIO_DIR = os.path.join(WORKSPACE_ROOT, "Raw_input_files", "audio")
AUDIT_OUTPUT_PATH = os.path.join(WORKSPACE_ROOT, "data", "real_audio_inspection.json")


def calculate_full_sha256(filepath: str, block_size: int = 65536) -> str:
    """Calculate true full content SHA-256 hash."""
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(block_size), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def test_decode_integrity(filepath: str) -> Tuple[bool, str]:
    """Tests if audio stream decodes cleanly via FFmpeg with zero decode errors."""
    ffmpeg = media_engine.get_ffmpeg_cmd()
    cmd = ffmpeg + ["-v", "error", "-i", filepath, "-f", "null", "-"]
    res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    is_valid = (res.returncode == 0 and len(res.stderr.strip()) == 0)
    return is_valid, res.stderr.strip()


def inspect_all_mp3_samples() -> List[Dict[str, Any]]:
    if not os.path.exists(RAW_AUDIO_DIR):
        print(f"Error: {RAW_AUDIO_DIR} not found.", file=sys.stderr)
        return []

    files = sorted([f for f in os.listdir(RAW_AUDIO_DIR) if f.lower().endswith(".mp3")])
    print(f"Discovered {len(files)} MP3 files in {RAW_AUDIO_DIR}\n")

    results = []
    seen_hashes: Dict[str, str] = {}  # sha256 -> canonical_asset_id

    for idx, fname in enumerate(files, 1):
        fpath = os.path.join(RAW_AUDIO_DIR, fname)
        rel_path = os.path.relpath(fpath, WORKSPACE_ROOT).replace("\\", "/")
        file_size = os.path.getsize(fpath)

        print(f"[{idx:02d}/{len(files)}] Inspecting {fname} ({file_size / (1024*1024):.2f} MB)...")

        # 1. Zero-byte check
        if file_size == 0:
            results.append({
                "filename": fname,
                "path": rel_path,
                "file_size_bytes": 0,
                "error": "EMPTY_FILE_ZERO_BYTES",
                "analysis_status": "FAILED"
            })
            continue

        # 2. SHA-256 Full Content Hash
        sha256 = calculate_full_sha256(fpath)
        short_hash = sha256[:8].upper()

        # 3. Duplicate check
        is_dup = sha256 in seen_hashes
        orig_canonical_id = seen_hashes[sha256] if is_dup else None

        if not is_dup:
            asset_id = f"AUDIO_{short_hash}"
            seen_hashes[sha256] = asset_id
        else:
            asset_id = f"AUDIO_{short_hash}_DUP"

        # 4. Stream decode verification
        can_decode, decode_err = test_decode_integrity(fpath)
        if not can_decode and decode_err:
            print(f"    ⚠️ Decode error: {decode_err}")

        # 5. Technical Stream Metadata
        try:
            stream_meta = audio_analyzer.get_audio_stream_metadata(fpath)
        except Exception as e:
            results.append({
                "asset_id": asset_id,
                "filename": fname,
                "path": rel_path,
                "file_size_bytes": file_size,
                "sha256": sha256,
                "error": f"STREAM_METADATA_ERROR: {str(e)}",
                "analysis_status": "FAILED"
            })
            continue

        # 6. EBU R128 Loudness
        try:
            loudness = audio_analyzer.measure_ebur128_loudness(fpath)
        except Exception as e:
            loudness = {"integrated_lufs": -99.0, "true_peak_dbtp": 0.0, "loudness_range_lu": 0.0, "error": str(e)}

        # 7. Acoustic Waveform Processing
        try:
            samples, sr = audio_analyzer.load_pcm_samples(fpath)
            acoustic = audio_analyzer.analyze_acoustic_properties(samples, sr)
        except Exception as e:
            acoustic = {
                "peak_dbfs": -99.0, "rms_dbfs": -99.0, "clipping_detected": False,
                "silence_ratio": 1.0, "speech_presence": "unknown", "estimated_bpm": None,
                "bpm_confidence": "unknown", "energy_level": "unknown", "rhythm_type": "unknown",
                "error": str(e)
            }

        # 8. Mood & Structure Prediction
        try:
            moods, structure, key_est = audio_analyzer.determine_mood_and_structure(
                stream_meta, acoustic, fpath
            )
        except Exception as e:
            moods, structure, key_est = ["unclassified"], [], None

        # Project Suitability Mapping
        use_cases, rec_projects, rec_platforms = audio_analyzer.map_project_and_platforms(
            fpath, acoustic["speech_presence"], moods
        )

        record = {
            "asset_id": asset_id,
            "filename": fname,
            "path": rel_path,
            "file_size_bytes": file_size,
            "sha256": sha256,
            "is_duplicate": is_dup,
            "duplicate_of_asset_id": orig_canonical_id,
            "can_decode": can_decode,
            "decode_error": decode_err if not can_decode else None,
            "stream": stream_meta,
            "loudness": loudness,
            "acoustic": acoustic,
            "musical": {
                "bpm": acoustic["estimated_bpm"],
                "bpm_confidence": acoustic["bpm_confidence"],
                "energy_level": acoustic["energy_level"],
                "rhythm_type": acoustic["rhythm_type"],
                "key_estimate": key_est,
                "predicted_moods": moods,
                "mood_prediction_method": "acoustic_energy_spectral_heuristics",
                "mood_confidence": "medium" if acoustic["bpm_confidence"] != "low" else "low",
                "sound_classification": acoustic["speech_presence"],
                "vocal_type": "instrumental" if acoustic["speech_presence"] == "instrumental_music" else "unknown"
            },
            "timeline_structure": structure,
            "provenance": {
                "source_type": "USER_SUPPLIED",
                "source_directory": "Raw_input_files/audio",
                "license_claim": "USER_DECLARED_NO_COPYRIGHT",
                "license_status": "NEEDS_REVIEW",
                "commercial_use_allowed": False,
                "attribution_required": False,
                "clearance_notes": "User-supplied sample soundtrack. Commercial publishing restricted until provenance clearance is verified."
            },
            "recommendations": {
                "suitable_projects": rec_projects,
                "use_cases": use_cases,
                "platforms": rec_platforms
            },
            "analysis_status": "ANALYZED",
            "inspected_at": datetime.now().isoformat()
        }

        results.append(record)
        bpm_str = f"{acoustic['estimated_bpm']:.1f}" if acoustic['estimated_bpm'] else "N/A"
        print(f"    ✓ {record['asset_id']}: {stream_meta['duration_seconds']}s | {bpm_str} BPM ({acoustic['bpm_confidence']}) | {loudness.get('integrated_lufs', -99):.1f} LUFS | Moods: {', '.join(moods[:3])}")

    os.makedirs(os.path.dirname(AUDIT_OUTPUT_PATH), exist_ok=True)
    with open(AUDIT_OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print(f"\nSaved complete inspection report of {len(results)} assets to {AUDIT_OUTPUT_PATH}")
    return results


if __name__ == "__main__":
    inspect_all_mp3_samples()
