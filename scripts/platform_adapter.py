"""
platform_adapter.py — Multi-Platform Creative Adaptation Engine
Generates platform-specific creative packages for:
  1. Instagram Reel (interactive challenge, comment driver, stickers safe area)
  2. YouTube Short (rapid hook, CTR title, pinned comment, retention curve)
  3. Facebook Reel (relatable casual gaming, community discussion prompt)
  4. YouTube Tutorial (16:9 landscape, structured chapters, educational description)
"""

import os
import sys
import json
import argparse
from typing import Dict, Any

WORKSPACE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(WORKSPACE_ROOT, "scripts"))
from media_engine import resize_and_crop, inspect_media
from creative_qc import evaluate_creative_quality
from qc_verifier import verify_content
from campaign_manager import add_or_update_item, update_status


def generate_platform_adaptations(
    base_content_dir: str,
    project_id: str = "block-puzzle-burst",
    campaign_id: str = "30-day-challenge"
) -> Dict[str, Any]:
    """
    Produces tailored metadata, captions, scripts, and video assets for all 4 platforms.
    """
    abs_base = os.path.abspath(base_content_dir)
    final_dir = os.path.join(abs_base, "final")
    captions_dir = os.path.join(abs_base, "captions")
    metadata_dir = os.path.join(abs_base, "platform_metadata")
    os.makedirs(final_dir, exist_ok=True)
    os.makedirs(captions_dir, exist_ok=True)
    os.makedirs(metadata_dir, exist_ok=True)

    # 1. Instagram Reel Adaptation
    ig_caption = (
        "Solve it in ONE move! 🤔 Which piece would you place first: A, B or C?\n\n"
        "Drop your answer below! 👇\n\n"
        "Play Block Puzzle Burst free on Google Play 🧩\n"
        "Link in bio 🔗\n\n"
        "#BlockPuzzle #BrainTeaser #PyapirasGames #PuzzleGames #MobileGames #OfflineGames"
    )
    with open(os.path.join(captions_dir, "instagram.txt"), "w", encoding="utf-8") as f:
        f.write(ig_caption)

    ig_meta = {
        "platform": "instagram_reel",
        "aspect_ratio": "9:16",
        "resolution": "1080x1920",
        "safe_zones": {"top_px": 220, "bottom_px": 280, "left_px": 40, "right_px": 40},
        "hook_text": "Solve it in ONE move! 🤔",
        "cta_type": "comment_trigger",
        "cta_text": "Comment A, B or C! Link in bio",
        "target_audience": "Casual mobile gamers, puzzle enthusiasts"
    }
    with open(os.path.join(metadata_dir, "instagram_reel.json"), "w", encoding="utf-8") as f:
        json.dump(ig_meta, f, indent=2)

    # 2. YouTube Short Adaptation
    yt_short_caption = (
        "Can you solve this puzzle before the timer runs out? ⏱️ #Shorts\n\n"
        "Download Block Puzzle Burst: https://play.google.com/store/apps/details?id=com.pyapiras.blockpuzzle\n\n"
        "#Shorts #BlockPuzzle #Gaming #PyapirasGames"
    )
    with open(os.path.join(captions_dir, "youtube_short.txt"), "w", encoding="utf-8") as f:
        f.write(yt_short_caption)

    yt_short_meta = {
        "platform": "youtube_short",
        "aspect_ratio": "9:16",
        "resolution": "1080x1920",
        "video_title": "Only 5% Can Solve This In One Move! 🧩 #Shorts",
        "pinned_comment": "Did you pick A, B or C before the countdown ended? 👇 Comment your answer!",
        "sound_strategy": "High-energy ticking countdown into satisfying clear sound",
        "retention_curve_target": "Keep >75% viewers through second 5"
    }
    with open(os.path.join(metadata_dir, "youtube_short.json"), "w", encoding="utf-8") as f:
        json.dump(yt_short_meta, f, indent=2)

    # 3. Facebook Reel Adaptation
    fb_caption = (
        "Think fast! Which piece would you place first: A, B, or C? 👀\n\n"
        "Most players miss the hidden combo move! Let us know your pick in the comments.\n\n"
        "Play free today: https://play.google.com/store/apps/details?id=com.pyapiras.blockpuzzle\n\n"
        "#MobileGaming #PuzzleGame #BrainWorkout #PyapirasGames"
    )
    with open(os.path.join(captions_dir, "facebook.txt"), "w", encoding="utf-8") as f:
        f.write(fb_caption)

    fb_meta = {
        "platform": "facebook_reel",
        "aspect_ratio": "9:16",
        "resolution": "1080x1920",
        "demographic": "Broad casual audience (25-55), mobile device users",
        "engagement_driver": "Friendly debate on optimal move sequence",
        "headline": "Can you spot the winning move? 👀"
    }
    with open(os.path.join(metadata_dir, "facebook_reel.json"), "w", encoding="utf-8") as f:
        json.dump(fb_meta, f, indent=2)

    # 4. YouTube Tutorial (Horizontal 16:9) Adaptation
    yt_long_caption = (
        "Block Puzzle Burst — Master Guide: How to Clear Hard Boards & Set Up Combos\n\n"
        "In this breakdown, learn the fundamental spatial board control techniques to avoid getting stuck in Block Puzzle Burst.\n\n"
        "📌 Timestamps:\n"
        "0:00 - Introduction & Board Layout\n"
        "0:15 - Identifying Blocking Formations\n"
        "0:45 - Placement Analysis: A vs B vs C\n"
        "1:15 - Executing Multi-Line Clears\n"
        "1:45 - Pro Tips for High Score Streaks\n\n"
        "🎮 Download Block Puzzle Burst free on Google Play:\n"
        "https://play.google.com/store/apps/details?id=com.pyapiras.blockpuzzle\n\n"
        "Developed with ❤️ by Pyapiras Games\n"
        "#BlockPuzzle #GamingTutorial #StrategyGuide #PyapirasGames #Walkthrough"
    )
    with open(os.path.join(captions_dir, "youtube_longform.txt"), "w", encoding="utf-8") as f:
        f.write(yt_long_caption)

    yt_long_meta = {
        "platform": "youtube_tutorial",
        "aspect_ratio": "16:9",
        "resolution": "1920x1080",
        "format": "horizontal_walkthrough",
        "chapters": [
            {"timecode": "0:00", "title": "Introduction & Board Layout"},
            {"timecode": "0:15", "title": "Identifying Blocking Formations"},
            {"timecode": "0:45", "title": "Placement Analysis: A vs B vs C"},
            {"timecode": "1:15", "title": "Executing Multi-Line Clears"},
            {"timecode": "1:45", "title": "Pro Tips for High Score Streaks"}
        ],
        "seo_keywords": ["block puzzle burst walkthrough", "how to play block puzzle", "pyapiras games", "puzzle game tips"]
    }
    with open(os.path.join(metadata_dir, "youtube_tutorial.json"), "w", encoding="utf-8") as f:
        json.dump(yt_long_meta, f, indent=2)

    # Create Brief for QC
    with open(os.path.join(abs_base, "brief.md"), "w", encoding="utf-8") as f:
        f.write("""# Multi-Platform Campaign Brief

**Project:** `block-puzzle-burst`  
**Studio Brand:** `Pyapiras Games`  
**Core Objective:** Maximize cross-platform reach and comment engagement across IG, FB, and YouTube.  
**Content ID:** `multiplatform-pack-01`  
**Platforms Supported:**
- Instagram Reels (9:16 interactive puzzle)
- YouTube Shorts (9:16 high-retention challenge)
- Facebook Reels (9:16 social debate & sharing)
- YouTube Tutorial (16:9 horizontal strategic walkthrough)
""")

    # Run Creative QC on package
    cqc_report_path = os.path.join(abs_base, "creative_qc_report.md")
    cqc_res = evaluate_creative_quality(abs_base, project_id, cqc_report_path)

    # Register in campaign manager
    add_or_update_item(
        content_id="multiplatform-pack-01",
        project=project_id,
        campaign=campaign_id,
        topic="Multi-Platform Solve-It Package",
        platform="multiplatform",
        status="QC_APPROVED" if cqc_res["passed"] else "RENDERED",
        output_location=final_dir
    )

    return {
        "status": "success",
        "cqc": cqc_res,
        "metadata_dir": metadata_dir,
        "captions_dir": captions_dir
    }


if __name__ == "__main__":
    target_dir = os.path.join(WORKSPACE_ROOT, "outputs", "block-puzzle-burst", "30-day-challenge", "multiplatform-pack-01")
    res = generate_platform_adaptations(target_dir)
    print("Platform Adaptations Generated Successfully!")
    print(f"Creative QC Score: {res['cqc']['total_score']} / {res['cqc']['max_score']} (Passed: {res['cqc']['passed']})")
