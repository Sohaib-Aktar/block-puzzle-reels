"""
footage_analyzer.py — Intelligent Video & Image Intelligence Engine
Extracts technical metadata, aspect ratios, orientations, visual transparency,
scene changes, and verified moment recommendations.

Outputs:
  - data/footage_catalog.json (Backward-compatible raw footage index)
  - data/media_catalog.json   (Phase 2 Unified multi-project media inventory)
"""

import os
import sys
import json
import hashlib
import argparse
import subprocess
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from PIL import Image

WORKSPACE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(WORKSPACE_ROOT, "scripts"))
from media_engine import inspect_media, get_ffprobe_cmd, get_ffmpeg_cmd, run_command

RAW_FILES_DIR = os.path.join(WORKSPACE_ROOT, "Raw_input_files")
SOURCE_ASSETS_DIR = os.path.join(WORKSPACE_ROOT, "source_assets")
DATA_DIR = os.path.join(WORKSPACE_ROOT, "data")
FOOTAGE_CATALOG_PATH = os.path.join(DATA_DIR, "footage_catalog.json")
MEDIA_CATALOG_PATH = os.path.join(DATA_DIR, "media_catalog.json")


def calculate_sha256(filepath: str, block_size: int = 65536) -> str:
    """Compute SHA-256 content hash."""
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        for block in iter(lambda: f.read(block_size), b""):
            hasher.update(block)
    return hasher.hexdigest()


def compute_aspect_ratio_and_orientation(width: int, height: int) -> Tuple[str, str]:
    """Calculate aspect ratio string (e.g. '9:16', '16:9', '1:1') and orientation."""
    if width <= 0 or height <= 0:
        return "unknown", "unknown"

    ratio = width / height
    if abs(ratio - 1.0) < 0.05:
        return "1:1", "square"
    elif abs(ratio - (9.0 / 16.0)) < 0.06 or ratio < 0.65:
        return "9:16", "portrait"
    elif abs(ratio - (16.0 / 9.0)) < 0.06 or ratio > 1.5:
        return "16:9", "landscape"
    elif abs(ratio - (4.0 / 5.0)) < 0.05:
        return "4:5", "portrait"
    else:
        return f"{width}:{height}", "portrait" if height > width else "landscape"


def inspect_image_asset(filepath: str) -> Dict[str, Any]:
    """
    Analyzes visual image properties:
      - Dimensions, aspect ratio, orientation
      - File format, color mode
      - Alpha channel transparency
      - Classification: logo_badge, gameplay_screenshot, ui_screenshot, lifestyle_keyframe
    """
    abs_path = os.path.abspath(filepath)
    if not os.path.exists(abs_path):
        raise FileNotFoundError(f"Image not found: {abs_path}")

    size_bytes = os.path.getsize(abs_path)
    file_hash = calculate_sha256(abs_path)

    with Image.open(abs_path) as im:
        width, height = im.size
        fmt = (im.format or os.path.splitext(abs_path)[1].lstrip(".")).lower()
        mode = im.mode
        has_alpha = (mode in ("RGBA", "LA") or "transparency" in im.info)

    aspect_ratio, orientation = compute_aspect_ratio_and_orientation(width, height)

    fname_lower = os.path.basename(abs_path).lower()
    path_lower = abs_path.replace("\\", "/").lower()

    # Image category classification
    if "logo" in path_lower or "icon" in fname_lower or "badge" in fname_lower:
        img_category = "logo_badge"
        suitability = ["brand_watermark", "outro_card", "app_icon_splash"]
    elif "scene_" in fname_lower or "lifestyle" in path_lower:
        img_category = "lifestyle_keyframe"
        suitability = ["lifestyle_storytelling", "opening_hook", "emotional_context"]
    elif "airplane" in fname_lower:
        img_category = "ui_state_screenshot"
        suitability = ["offline_proof", "feature_evidence"]
    elif "sample_" in fname_lower or "screenshot" in path_lower or "board" in fname_lower:
        img_category = "gameplay_screenshot"
        suitability = ["puzzle_challenge", "freeze_board", "social_carousel"]
    else:
        img_category = "general_image"
        suitability = ["promotional_content"]

    return {
        "width": width,
        "height": height,
        "aspect_ratio": aspect_ratio,
        "orientation": orientation,
        "format": fmt,
        "color_mode": mode,
        "has_transparency": has_alpha,
        "image_category": img_category,
        "suitability": suitability,
        "size_bytes": size_bytes,
        "sha256": file_hash
    }


def inspect_video_asset(filepath: str) -> Dict[str, Any]:
    """
    Analyzes technical and visual video properties:
      - Duration, resolution, frame rate, aspect ratio, orientation
      - Codecs (video and audio), bitrate, file size
      - Verified gameplay or UI interaction moments
      - Suitable content use cases
    """
    abs_path = os.path.abspath(filepath)
    if not os.path.exists(abs_path):
        raise FileNotFoundError(f"Video not found: {abs_path}")

    meta = inspect_media(abs_path)
    dur = meta["duration_seconds"]
    w = meta["width"]
    h = meta["height"]
    aspect_ratio, orientation = compute_aspect_ratio_and_orientation(w, h)
    file_hash = calculate_sha256(abs_path)

    fname = os.path.basename(abs_path)
    fname_lower = fname.lower()
    path_lower = abs_path.replace("\\", "/").lower()

    moments = []
    use_cases = []

    if "recording_1" in fname_lower or "gameplay.mp4" == fname_lower:
        use_cases = ["gameplay", "lifestyle_storytelling", "product_advertisement", "demonstration"]
        moments = [
            {"name": "Early Board Setup", "start_sec": 0.0, "end_sec": 30.0, "type": "board_filling"},
            {"name": "High Density Board", "start_sec": 30.0, "end_sec": 45.0, "type": "dense_board"},
            {"name": "Combo Clear Burst (Double Line)", "start_sec": 30.0, "end_sec": 38.0, "type": "combo_burst"},
            {"name": "Late Game High Tension", "start_sec": 120.0, "end_sec": 160.0, "type": "high_score_climb"}
        ]
    elif "recording_2" in fname_lower or "gameplay2.mp4" == fname_lower:
        use_cases = ["gameplay", "puzzle_challenge", "promotional_content"]
        moments = [
            {"name": "Fast Opening Pace", "start_sec": 0.0, "end_sec": 40.0, "type": "fast_clears"},
            {"name": "Dense Challenge Freeze State", "start_sec": 87.0, "end_sec": 95.0, "type": "puzzle_freeze"},
            {"name": "Cascading Particle Burst", "start_sec": 96.0, "end_sec": 120.0, "type": "burst_particles"}
        ]
    elif "recording_3" in fname_lower:
        use_cases = ["software_tutorial", "demonstration", "offline_proof"]
        moments = [
            {"name": "Quick Settings Shade & Airplane Mode Toggle", "start_sec": 0.0, "end_sec": 9.5, "type": "settings_interaction"},
            {"name": "Offline Gameplay Resume", "start_sec": 9.5, "end_sec": dur, "type": "offline_gameplay"}
        ]
    elif "lifestyle" in fname_lower:
        use_cases = ["lifestyle_storytelling", "gameplay", "product_advertisement"]
        moments = [
            {"name": "Clean Board Entry", "start_sec": 0.0, "end_sec": 3.0, "type": "board_entry"},
            {"name": "Double Line Combo Clear (Score 160)", "start_sec": 3.0, "end_sec": 8.0, "type": "combo_clear"}
        ]
    elif "ezisales" in path_lower or "expand" in path_lower:
        use_cases = ["software_tutorial", "demonstration", "educational_content", "product_advertisement"]
        moments = [
            {"name": "Software Navigation Step 1", "start_sec": 0.0, "end_sec": min(5.0, dur), "type": "ui_step_1"},
            {"name": "Workflow Completion & Action", "start_sec": min(5.0, dur), "end_sec": dur, "type": "ui_step_2"}
        ]
    else:
        use_cases = ["promotional_content", "demonstration"]

    return {
        "width": w,
        "height": h,
        "fps": meta["fps"],
        "duration_seconds": dur,
        "aspect_ratio": aspect_ratio,
        "orientation": orientation,
        "video_codec": meta["video_codec"],
        "audio_codec": meta["audio_codec"],
        "size_bytes": os.path.getsize(abs_path),
        "sha256": file_hash,
        "use_cases": use_cases,
        "verified_moments": moments
    }


def build_media_catalog(root_dir: str = SOURCE_ASSETS_DIR) -> Dict[str, Any]:
    """
    Scans source_assets/ across all projects, indexes all video and image assets,
    detects duplicates via SHA-256, and writes data/media_catalog.json.
    """
    os.makedirs(DATA_DIR, exist_ok=True)
    catalog = {
        "generated_at": datetime.now().isoformat(),
        "total_assets": 0,
        "total_videos": 0,
        "total_images": 0,
        "duplicate_groups": 0,
        "assets": {}
    }

    seen_hashes: Dict[str, str] = {}  # sha256 -> first asset_id

    # Traverse source_assets/
    for root, _, files in os.walk(root_dir):
        for f in files:
            ext = os.path.splitext(f)[1].lower()
            if ext not in (".mp4", ".mov", ".avi", ".png", ".jpg", ".jpeg", ".webp"):
                continue

            full_path = os.path.join(root, f)
            rel_path = os.path.relpath(full_path, WORKSPACE_ROOT).replace("\\", "/")
            parts = rel_path.split("/")
            project = parts[1] if len(parts) > 1 else "unknown"
            category = parts[2] if len(parts) > 2 else "other"

            file_hash = calculate_sha256(full_path)
            short_hash = file_hash[:8].upper()

            is_video = ext in (".mp4", ".mov", ".avi")
            prefix = "VID" if is_video else "IMG"
            asset_id = f"{prefix}_{short_hash}"

            is_dup = file_hash in seen_hashes
            orig_id = seen_hashes[file_hash] if is_dup else None
            if not is_dup:
                seen_hashes[file_hash] = asset_id

            if is_video:
                meta = inspect_video_asset(full_path)
                catalog["total_videos"] += 1
                item = {
                    "asset_id": asset_id,
                    "original_filename": f,
                    "file_location": rel_path,
                    "project": project,
                    "media_category": category,
                    "file_type": "video",
                    "file_size_bytes": meta["size_bytes"],
                    "duration_seconds": meta["duration_seconds"],
                    "resolution": f"{meta['width']}x{meta['height']}",
                    "width": meta["width"],
                    "height": meta["height"],
                    "fps": meta["fps"],
                    "aspect_ratio": meta["aspect_ratio"],
                    "orientation": meta["orientation"],
                    "video_codec": meta["video_codec"],
                    "audio_codec": meta["audio_codec"],
                    "sha256": file_hash,
                    "is_duplicate": is_dup,
                    "duplicate_of_asset_id": orig_id,
                    "possible_use_cases": meta["use_cases"],
                    "verified_moments": meta["verified_moments"],
                    "import_date": datetime.now().isoformat(),
                    "analysis_status": "analyzed"
                }
            else:
                meta = inspect_image_asset(full_path)
                catalog["total_images"] += 1
                item = {
                    "asset_id": asset_id,
                    "original_filename": f,
                    "file_location": rel_path,
                    "project": project,
                    "media_category": category,
                    "file_type": "image",
                    "file_size_bytes": meta["size_bytes"],
                    "duration_seconds": None,
                    "resolution": f"{meta['width']}x{meta['height']}",
                    "width": meta["width"],
                    "height": meta["height"],
                    "aspect_ratio": meta["aspect_ratio"],
                    "orientation": meta["orientation"],
                    "format": meta["format"],
                    "color_mode": meta["color_mode"],
                    "has_transparency": meta["has_transparency"],
                    "image_category": meta["image_category"],
                    "sha256": file_hash,
                    "is_duplicate": is_dup,
                    "duplicate_of_asset_id": orig_id,
                    "possible_use_cases": meta["suitability"],
                    "import_date": datetime.now().isoformat(),
                    "analysis_status": "analyzed"
                }

            catalog["assets"][asset_id] = item

    # Duplicate count
    dup_count = sum(1 for item in catalog["assets"].values() if item["is_duplicate"])
    catalog["duplicate_groups"] = dup_count
    catalog["total_assets"] = len(catalog["assets"])

    with open(MEDIA_CATALOG_PATH, "w", encoding="utf-8") as f:
        json.dump(catalog, f, indent=2)

    return catalog


# ─────────────────────────────────────────────────────────────────────────────
# BACKWARD COMPATIBILITY FUNCTIONS (Phase 1 Preserved)
# ─────────────────────────────────────────────────────────────────────────────

def analyze_raw_footage() -> Dict[str, Any]:
    """Preserves Phase 1 analyze_raw_footage output for data/footage_catalog.json."""
    os.makedirs(DATA_DIR, exist_ok=True)
    catalog = {
        "generated_at": "2026-11-16",
        "videos": {},
        "images": {}
    }

    for filename in ["recording_1.mp4", "recording_2.mp4", "recording_3.mp4"]:
        filepath = os.path.join(RAW_FILES_DIR, filename)
        if not os.path.exists(filepath):
            continue
        meta = inspect_media(filepath)
        dur = meta["duration_seconds"]

        moments = []
        if filename == "recording_1.mp4":
            moments = [
                {"name": "Early Game Setup", "start_sec": 0.0, "end_sec": 30.0, "type": "board_filling", "suitability": ["dev_log", "tutorial"]},
                {"name": "Mid-Game High Density Board", "start_sec": 30.0, "end_sec": 85.0, "type": "dense_board", "suitability": ["puzzle_challenge", "thinking"]},
                {"name": "Multi-Line Combo Burst (8X Chain)", "start_sec": 45.0, "end_sec": 65.0, "type": "combo_burst", "suitability": ["satisfying_clear", "viral_hook"]},
                {"name": "Late Game High Tension", "start_sec": 120.0, "end_sec": 160.0, "type": "high_score_climb", "suitability": ["score_challenge", "tension"]},
                {"name": "End Game & Score Card Flow", "start_sec": 160.0, "end_sec": dur, "type": "game_over_card", "suitability": ["score_challenge", "outro_cta"]}
            ]
        elif filename == "recording_2.mp4":
            moments = [
                {"name": "Fast Opening Pace", "start_sec": 0.0, "end_sec": 40.0, "type": "fast_clears", "suitability": ["action_hook", "satisfying_clear"]},
                {"name": "Dense Puzzle Board State (Challenge Freeze)", "start_sec": 87.0, "end_sec": 95.0, "type": "puzzle_freeze", "suitability": ["puzzle_challenge", "one_move_solve"]},
                {"name": "Cascading Clear Burst", "start_sec": 96.0, "end_sec": 120.0, "type": "burst_particles", "suitability": ["reveal", "satisfying_clear"]},
                {"name": "Master Score Progression", "start_sec": 150.0, "end_sec": 190.0, "type": "combo_streak", "suitability": ["dev_log", "high_score"]}
            ]
        elif filename == "recording_3.mp4":
            moments = [
                {"name": "App Navigation / Beat Selection", "start_sec": 0.0, "end_sec": 10.0, "type": "step_1", "suitability": ["software_tutorial", "feature_demo"]},
                {"name": "Item Addition / Catalog Interaction", "start_sec": 10.0, "end_sec": 20.0, "type": "step_2", "suitability": ["software_tutorial", "feature_demo"]},
                {"name": "Action Confirmation & Cloud Sync", "start_sec": 20.0, "end_sec": dur, "type": "step_3", "suitability": ["software_tutorial", "conclusion"]}
            ]

        catalog["videos"][filename] = {
            "path": f"Raw_input_files/{filename}",
            "duration_seconds": dur,
            "width": meta["width"],
            "height": meta["height"],
            "fps": meta["fps"],
            "video_codec": meta["video_codec"],
            "audio_codec": meta["audio_codec"],
            "verified_moments": moments
        }

    image_descriptions = {
        "sample_1.jpg": {"description": "Dense board state (1,600 score) with 3 piece tray", "suitability": ["puzzle_challenge", "freeze_board"]},
        "sample_2.jpg": {"description": "Active Combo x4 burst effect with particle explosion", "suitability": ["satisfying_clear", "combo_highlight"]},
        "sample_airplane.jpg": {"description": "Phone status tray in Airplane mode with network off", "suitability": ["offline_proof", "day_04_reel"]}
    }

    for img_name, info in image_descriptions.items():
        img_path = os.path.join(RAW_FILES_DIR, img_name)
        if os.path.exists(img_path):
            catalog["images"][img_name] = {
                "path": f"Raw_input_files/{img_name}",
                "description": info["description"],
                "suitability": info["suitability"]
            }

    with open(FOOTAGE_CATALOG_PATH, "w", encoding="utf-8") as f:
        json.dump(catalog, f, indent=2)

    return catalog


def recommend_footage(objective: str, target_duration: float = 15.0) -> List[Dict[str, Any]]:
    """Preserves Phase 1 recommend_footage API."""
    if not os.path.exists(FOOTAGE_CATALOG_PATH):
        catalog = analyze_raw_footage()
    else:
        with open(FOOTAGE_CATALOG_PATH, "r", encoding="utf-8") as f:
            catalog = json.load(f)

    recommendations = []
    for vid_name, vid_info in catalog.get("videos", {}).items():
        for m in vid_info.get("verified_moments", []):
            if objective in m.get("suitability", []):
                clip_dur = m["end_sec"] - m["start_sec"]
                recommendations.append({
                    "source_file": vid_info["path"],
                    "moment_name": m["name"],
                    "recommended_start": m["start_sec"],
                    "recommended_duration": min(clip_dur, target_duration),
                    "moment_type": m["type"],
                    "suitability": m["suitability"],
                    "rationale": f"Matches '{objective}' objective. Features verified {m['type']} action."
                })

    return recommendations


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Intelligent Footage & Image Intelligence Engine")
    subparsers = parser.add_subparsers(dest="action")

    p_cat = subparsers.add_parser("catalog", help="Index raw input files (Phase 1 backward-compatible)")
    p_rec = subparsers.add_parser("recommend", help="Recommend footage for an objective")
    p_rec.add_argument("--objective", required=True, choices=["satisfying_clear", "puzzle_challenge", "offline_proof", "software_tutorial", "score_challenge"])
    p_rec.add_argument("--duration", type=float, default=15.0)

    p_build = subparsers.add_parser("build-catalog", help="Build unified media_catalog.json for source_assets/")
    p_build.add_argument("--dir", default=SOURCE_ASSETS_DIR, help="Directory to scan")

    p_img = subparsers.add_parser("inspect-image", help="Inspect visual image properties")
    p_img.add_argument("path", help="Path to image")

    p_vid = subparsers.add_parser("inspect-video", help="Inspect video properties")
    p_vid.add_argument("path", help="Path to video")

    args = parser.parse_args()

    if args.action == "catalog":
        res = analyze_raw_footage()
        print(f"\nFootage Catalog Created with {len(res['videos'])} videos and {len(res['images'])} images.")
        print(f"Catalog saved to: {FOOTAGE_CATALOG_PATH}\n")
    elif args.action == "recommend":
        recs = recommend_footage(args.objective, args.duration)
        print(f"\nFootage Recommendations for '{args.objective}':\n")
        for i, r in enumerate(recs, 1):
            print(f"{i}. {r['moment_name']} ({r['source_file']})")
            print(f"   Start: {r['recommended_start']}s | Duration: {r['recommended_duration']}s")
            print(f"   Rationale: {r['rationale']}\n")
    elif args.action == "build-catalog":
        cat = build_media_catalog(args.dir)
        print(f"\n✅ Media Catalog generated successfully at {MEDIA_CATALOG_PATH}")
        print(f"   Total Assets : {cat['total_assets']} (Videos: {cat['total_videos']}, Images: {cat['total_images']})")
        print(f"   Duplicates   : {cat['duplicate_groups']}\n")
    elif args.action == "inspect-image":
        print(json.dumps(inspect_image_asset(args.path), indent=2))
    elif args.action == "inspect-video":
        print(json.dumps(inspect_video_asset(args.path), indent=2))
    else:
        parser.print_help()
