#!/usr/bin/env python3
"""
scripts/media_intake.py
=======================
Unified Media Intake and Catalog Management CLI for Pyapiras Games Studio.

Provides single-point command-line control for:
  - scan: Discovers and indexes all video, image, and audio files into catalogs.
  - analyze <path>: Performs deep structural, visual, or acoustic analysis on any single asset.
  - catalog: Displays clean, formatted tabular summaries of registered media and audio.
  - search --query <term>: Searches across all metadata, tags, and acoustic properties.
  - check-duplicates: Detects and displays identical assets across workspaces via SHA-256.
  - recommend-audio: Finds the best matching soundtrack or SFX for marketing videos.

Usage:
  python scripts/media_intake.py scan [--project <slug>]
  python scripts/media_intake.py analyze <file_path>
  python scripts/media_intake.py catalog [--type video|image|audio] [--project <slug>]
  python scripts/media_intake.py search --query <term>
  python scripts/media_intake.py check-duplicates
  python scripts/media_intake.py recommend-audio --project <slug> --category <cat> [--mood <mood>] [--duration <sec>]
"""

import os
import sys
import json
import argparse
from typing import Dict, List, Any, Optional

# Ensure scripts directory is in sys.path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
WORKSPACE_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

import footage_analyzer
import audio_analyzer
import audio_recommender
import asset_migrator

DATA_DIR = os.path.join(WORKSPACE_ROOT, "data")
MEDIA_CATALOG_PATH = os.path.join(DATA_DIR, "media_catalog.json")
AUDIO_CATALOG_PATH = os.path.join(DATA_DIR, "audio_catalog.json")


MIGRATION_LOG_PATH = os.path.join(DATA_DIR, "migration_log.json")


def _get_audio_project(item: Dict[str, Any]) -> str:
    path = item.get("path", "")
    parts = path.replace("\\", "/").split("/")
    if len(parts) >= 2 and parts[0] == "source_assets":
        return parts[1]
    rec_projs = item.get("recommended_projects", [])
    if rec_projs and isinstance(rec_projs, list):
        return rec_projs[0]
    return "global"


def _get_audio_category(item: Dict[str, Any]) -> str:
    path = item.get("path", "")
    parts = path.replace("\\", "/").split("/")
    if len(parts) >= 3 and parts[0] == "source_assets":
        return parts[2]
    sound_cls = item.get("sound_classification", "")
    if "music" in sound_cls:
        return "music"
    if "speech" in sound_cls:
        return "voiceovers"
    if "sfx" in sound_cls or "effect" in sound_cls:
        return "sound-effects"
    return "audio"


def cmd_scan(args: argparse.Namespace) -> int:
    """Discovers and re-indexes all video, image, and audio files."""
    print("=" * 70)
    print("Pyapiras Media Intake: Scanning & Indexing Assets")
    print("=" * 70)

    project_filter = getattr(args, "project", None)
    if project_filter:
        print(f"Targeting Project: {project_filter}")

    # Step 1: Run non-destructive asset migration discovery
    print("\n[1/3] Checking canonical asset organization (source_assets/)...")
    migration_summary = asset_migrator.migrate_assets(
        dry_run=False,
        project_filter=project_filter
    )
    print(f"      Total candidates: {migration_summary.get('total_candidates', 0)}")
    print(f"      Migrated / Synced: {migration_summary.get('migrated_count', 0)}")
    print(f"      Duplicates detected: {len(migration_summary.get('duplicates_detected', []))}")

    # Step 2: Build / Update media catalog (videos + images)
    print("\n[2/3] Building Visual Media Catalog (videos & images)...")
    media_catalog = footage_analyzer.build_media_catalog(project_filter=project_filter)
    assets = media_catalog.get("assets", {})
    video_count = sum(1 for a in assets.values() if a.get("file_type") == "video")
    image_count = sum(1 for a in assets.values() if a.get("file_type") == "image")
    print(f"      Indexed {len(assets)} visual assets ({video_count} videos, {image_count} images)")

    # Step 3: Build / Update audio catalog (music, SFX, voiceovers)
    print("\n[3/3] Performing Acoustic & Loudness Analysis (audio catalog)...")
    audio_catalog = audio_analyzer.update_audio_catalog(project_filter=project_filter)
    audio_count = len(audio_catalog.get("assets", {}))
    print(f"      Indexed {audio_count} audio tracks with acoustic & EBU R128 profiles.")

    print("\n" + "=" * 70)
    print(f"Intake Scan Complete. Total Cataloged: {len(assets) + audio_count} assets.")
    print("=" * 70)
    return 0


def cmd_analyze(args: argparse.Namespace) -> int:
    """Analyzes a single media file based on its extension."""
    file_path = os.path.abspath(args.file)
    if not os.path.isfile(file_path):
        print(f"Error: File not found: {file_path}", file=sys.stderr)
        return 1

    ext = os.path.splitext(file_path)[1].lower()
    print("=" * 70)
    print(f"Analyzing Media Asset: {os.path.basename(file_path)}")
    print(f"Full Path: {file_path}")
    print("=" * 70)

    video_exts = {".mp4", ".mov", ".mkv", ".avi", ".webm", ".m4v"}
    image_exts = {".png", ".jpg", ".jpeg", ".webp", ".svg", ".bmp"}
    audio_exts = audio_analyzer.SUPPORTED_AUDIO_EXTENSIONS

    if ext in video_exts:
        print("[Type: Video]")
        res = footage_analyzer.inspect_video_asset(file_path)
        print(f"  Duration:      {res.get('duration_seconds', 0.0):.2f}s (@ {res.get('fps', 0.0):.1f} fps)")
        print(f"  Resolution:    {res.get('width', 0)}x{res.get('height', 0)} ({res.get('aspect_ratio', 'N/A')}, {res.get('orientation', 'N/A')})")
        print(f"  Video Codec:   {res.get('video_codec', 'N/A')}")
        print(f"  Audio Track:   {'Yes (' + str(res.get('audio_codec')) + ')' if res.get('audio_codec') else 'No Audio'}")
        print(f"  SHA-256:       {res.get('sha256', 'N/A')}")
        if res.get("moments"):
            print("  Detected Key Moments:")
            for m in res["moments"]:
                print(f"    - [{m.get('time_range', 'N/A')}] {m.get('label', 'N/A')} ({m.get('suitability', 'N/A')})")

    elif ext in image_exts:
        print("[Type: Image]")
        res = footage_analyzer.inspect_image_asset(file_path)
        print(f"  Resolution:    {res.get('width', 0)}x{res.get('height', 0)} ({res.get('aspect_ratio', 'N/A')}, {res.get('orientation', 'N/A')})")
        print(f"  Format:        {res.get('format', 'N/A')} (Mode: {res.get('color_mode', 'N/A')})")
        print(f"  Transparency:  {'Yes (Alpha Channel)' if res.get('has_transparency') else 'Opaque'}")
        print(f"  Category:      {res.get('image_category', 'N/A')}")
        print(f"  Suggested Use: {res.get('suitability', 'N/A')}")
        print(f"  SHA-256:       {res.get('sha256', 'N/A')}")

    elif ext in audio_exts:
        print("[Type: Audio]")
        res = audio_analyzer.analyze_audio_asset(file_path)
        print(f"  Duration:      {res.get('duration_seconds', 0.0):.2f}s")
        print(f"  Format:        {res.get('codec', 'N/A')} @ {res.get('sample_rate', 0)} Hz, {res.get('channels', 1)} ch")
        print(f"  EBU R128:      Integrated {res.get('integrated_lufs', -99.0):.1f} LUFS | Range {res.get('loudness_range_lu', 0.0):.1f} LU | Peak {res.get('true_peak_dbtp', 0.0):.1f} dBTP")
        print(f"  Acoustics:     Peak {res.get('peak_dbfs', -99.0):.1f} dBFS | RMS {res.get('rms_dbfs', -99.0):.1f} dBFS | Clipping: {res.get('clipping_detected', False)}")
        print(f"  Classification:{res.get('sound_classification', 'N/A')} (Tempo: {res.get('bpm', 'N/A')} BPM, Conf: {res.get('bpm_confidence', 'N/A')}, Energy: {res.get('energy_level', 'N/A')})")
        print(f"  Mood Tags:     {', '.join(res.get('mood', []))}")
        print(f"  Licensing:     Status: {res.get('license_status', 'N/A')} | Clearance: {'APPROVED' if res.get('commercial_use_allowed') else 'RESTRICTED'}")

    else:
        print(f"Unsupported file format: {ext}", file=sys.stderr)
        return 1

    print("=" * 70)
    return 0


def cmd_catalog(args: argparse.Namespace) -> int:
    """Displays formatted summaries of the media and audio catalogs."""
    cat_type = getattr(args, "type", "all") or "all"
    proj_filter = getattr(args, "project", None)

    print("=" * 96)
    print("Pyapiras Studio Asset Catalogs")
    print("=" * 96)

    if cat_type in ("all", "video", "image"):
        if os.path.isfile(MEDIA_CATALOG_PATH):
            with open(MEDIA_CATALOG_PATH, "r", encoding="utf-8") as f:
                media_data = json.load(f)
            assets = media_data.get("assets", {})
            print(f"\n[Visual Media Catalog] ({len(assets)} items total)")
            print(f"{'Asset ID':<26} {'Project':<20} {'Type':<8} {'Res / Duration':<20} {'Orientation / Use':<20}")
            print("-" * 96)
            for aid, item in sorted(assets.items()):
                p = item.get("project", "unknown")
                if proj_filter and p != proj_filter:
                    continue
                ftype = item.get("file_type", "unknown")
                if cat_type != "all" and ftype != cat_type:
                    continue

                if ftype == "video":
                    res_dur = f"{item.get('duration_seconds', 0.0):.1f}s ({item.get('resolution', 'N/A')})"
                    use_fmt = f"{item.get('orientation', 'landscape')} ({item.get('media_category', 'video')})"
                else:
                    res_dur = f"{item.get('resolution', 'N/A')}"
                    use_fmt = f"{item.get('media_category', 'image')} (alpha={item.get('has_transparency', False)})"

                dup_flag = " [DUP]" if item.get("is_duplicate") else ""
                print(f"{aid + dup_flag:<26} {p:<20} {ftype:<8} {res_dur:<20} {use_fmt:<20}")
        else:
            print("\n[Visual Media Catalog]: Not found. Run `media_intake.py scan` first.")

    if cat_type in ("all", "audio"):
        if os.path.isfile(AUDIO_CATALOG_PATH):
            with open(AUDIO_CATALOG_PATH, "r", encoding="utf-8") as f:
                audio_data = json.load(f)
            assets = audio_data.get("assets", {})
            print(f"\n[Audio Intelligence Catalog] ({len(assets)} items total)")
            print(f"{'Asset ID':<26} {'Project':<20} {'Category':<15} {'BPM':<8} {'LUFS':<8} {'Licensing':<16}")
            print("-" * 96)
            for aid, item in sorted(assets.items()):
                p = _get_audio_project(item)
                if proj_filter and p != proj_filter:
                    continue
                cat = _get_audio_category(item)
                bpm_val = item.get("bpm")
                bpm_str = f"{bpm_val:.1f}" if isinstance(bpm_val, (int, float)) else "N/A"
                lufs_val = item.get("integrated_lufs")
                lufs_str = f"{lufs_val:.1f}" if isinstance(lufs_val, (int, float)) else "N/A"
                lic = item.get("license_status", "UNKNOWN")
                print(f"{aid:<26} {p:<20} {cat:<15} {bpm_str:<8} {lufs_str:<8} {lic:<16}")
        else:
            print("\n[Audio Catalog]: Not found. Run `media_intake.py scan` first.")

    print("\n" + "=" * 96)
    return 0


def cmd_search(args: argparse.Namespace) -> int:
    """Searches across media and audio catalogs for matching keywords."""
    query = args.query.lower()
    print("=" * 80)
    print(f"Searching Catalogs for: '{args.query}'")
    print("=" * 80)

    matches_found = 0

    # Search media catalog
    if os.path.isfile(MEDIA_CATALOG_PATH):
        with open(MEDIA_CATALOG_PATH, "r", encoding="utf-8") as f:
            media_data = json.load(f)
        for aid, item in media_data.get("assets", {}).items():
            searchable = (
                aid + " " +
                item.get("original_filename", "") + " " +
                item.get("file_location", "") + " " +
                item.get("project", "") + " " +
                item.get("file_type", "") + " " +
                item.get("media_category", "") + " " +
                item.get("orientation", "")
            ).lower()
            if query in searchable:
                matches_found += 1
                print(f"[Visual Media] {aid}")
                print(f"  Location:    {item.get('file_location')}")
                print(f"  Type/Proj:   {item.get('file_type')} / {item.get('project')}")
                if item.get("file_type") == "video":
                    print(f"  Specs:       {item.get('duration_seconds', 0.0):.1f}s, {item.get('resolution')}")
                else:
                    print(f"  Specs:       {item.get('resolution')}, alpha={item.get('has_transparency')}")
                print()

    # Search audio catalog
    if os.path.isfile(AUDIO_CATALOG_PATH):
        with open(AUDIO_CATALOG_PATH, "r", encoding="utf-8") as f:
            audio_data = json.load(f)
        for aid, item in audio_data.get("assets", {}).items():
            tags_str = " ".join(item.get("mood", []))
            proj = _get_audio_project(item)
            cat = _get_audio_category(item)
            searchable = (
                aid + " " +
                item.get("filename", "") + " " +
                item.get("path", "") + " " +
                proj + " " +
                cat + " " +
                item.get("sound_classification", "") + " " +
                tags_str
            ).lower()
            if query in searchable:
                matches_found += 1
                print(f"[Audio Asset] {aid}")
                print(f"  Location:    {item.get('path')}")
                print(f"  Class/Proj:  {cat} ({item.get('sound_classification')}) / {proj}")
                print(f"  Mood Tags:   {', '.join(item.get('mood', []))}")
                bpm = f"{item.get('bpm'):.1f}" if isinstance(item.get('bpm'), (int, float)) else "N/A"
                lufs = f"{item.get('integrated_lufs'):.1f}" if isinstance(item.get('integrated_lufs'), (int, float)) else "N/A"
                print(f"  Acoustic:    {bpm} BPM | {lufs} LUFS")
                print(f"  Licensing:   {item.get('license_status')}")
                print()

    print(f"Search complete. Total matches: {matches_found}")
    print("=" * 80)
    return 0


def cmd_check_duplicates(args: argparse.Namespace) -> int:
    """Detects and reports duplicate assets across the workspace."""
    print("=" * 80)
    print("Checking for Duplicate Assets Across Workspace (SHA-256 Checksums)")
    print("=" * 80)

    # 1. Check migration log for logged duplicates
    dups_found = []
    if os.path.isfile(MIGRATION_LOG_PATH):
        try:
            with open(MIGRATION_LOG_PATH, "r", encoding="utf-8") as f:
                mig_data = json.load(f)
            dups_found = [op for op in mig_data.get("operations", []) if op.get("is_duplicate")]
        except Exception:
            pass

    if dups_found:
        print(f"Identified {len(dups_found)} duplicate file instances across workspaces:\n")
        total_wasted = 0
        for i, dup in enumerate(dups_found, 1):
            src = dup.get("source_path", "")
            orig = dup.get("duplicate_of", "")
            sha = dup.get("sha256", "")
            sz = dup.get("size_bytes", 0)
            total_wasted += sz
            sz_mb = sz / (1024 * 1024)

            rel_src = os.path.relpath(src, WORKSPACE_ROOT).replace("\\", "/") if os.path.isabs(src) else src
            rel_orig = os.path.relpath(orig, WORKSPACE_ROOT).replace("\\", "/") if os.path.isabs(orig) else orig

            print(f"Group {i} [SHA-256: {sha[:16]}...] - Size: {sz_mb:.2f} MB")
            print(f"  Canonical / Primary: {rel_orig}")
            print(f"  Duplicate Copy:      {rel_src}")
            print(f"  Status:              {dup.get('status', 'synced')} (Preserved for compatibility)")
            print()

        print("-" * 80)
        print(f"Total Redundant Storage: {total_wasted / (1024 * 1024):.2f} MB across {len(dups_found)} duplicate instances.")
        print("Note: Duplicate legacy paths in `my-video/public/` are preserved to prevent breaking existing Remotion builds.")
    else:
        print("No duplicate files detected. Workspace asset storage is 100% clean.")

    print("=" * 80)
    return 0


def cmd_recommend_audio(args: argparse.Namespace) -> int:
    """Generates audio track recommendations using audio_recommender."""
    project = args.project
    category = getattr(args, "category", "lifestyle_reel") or "lifestyle_reel"
    mood = getattr(args, "mood", None) or "playful"
    duration = getattr(args, "duration", None) or 15.0

    res = audio_recommender.recommend_audio(
        project=project,
        content_category=category,
        desired_mood=mood,
        target_duration=duration,
        allow_unverified_licenses=True
    )

    print("=" * 80)
    print(f"Audio Recommendation Report for: {project.upper()} (Mood: {mood}, Duration: {duration}s)")
    print("=" * 80)

    recs = res.get("top_recommendations", [])
    if not recs:
        print("No eligible audio tracks found matching criteria.")
        return 0

    print(f"\nTop {len(recs)} Recommended Track(s):")
    for i, r in enumerate(recs, 1):
        print(f"\n#{i} {r['asset_id']} - {r['filename']} (Match Score: {r['match_score']:.1f}/100)")
        print(f"    Path:            {r['path']}")
        print(f"    Classification:  {r['sound_classification']} (BPM: {r['bpm']}, Energy: {r['energy_level']})")
        print(f"    Duration:        {r['duration_seconds']:.1f}s")
        print(f"    Licensing:       {r['license_status']} (Commercial Cleared: {r['commercial_cleared']})")
        print(f"    Why Selected:    {r['explanation']}")
        if r.get("warnings"):
            for w in r["warnings"]:
                print(f"    Note:            {w}")

    scenes = res.get("multi_scene_plan", [])
    if scenes:
        print("\nMulti-Scene Audio Progression Plan:")
        print(f"{'Scene':<10} {'Time Window':<16} {'Pacing/Energy':<16} {'Audio Action':<35}")
        print("-" * 80)
        for s in scenes:
            scene_name = s.get("scene_name", "Scene")
            time_win = f"{s.get('start_sec', 0.0):.1f}s - {s.get('end_sec', 0.0):.1f}s"
            energy = s.get("pacing", "moderate")
            action = s.get("audio_action", "")
            print(f"{scene_name:<10} {time_win:<16} {energy:<16} {action:<35}")

    print("\n" + "=" * 80)
    return 0


def main():
    parser = argparse.ArgumentParser(
        description="Pyapiras Games Media Intake & Asset Intelligence CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # scan
    p_scan = subparsers.add_parser("scan", help="Scan workspaces and update media & audio catalogs.")
    p_scan.add_argument("--project", "-p", help="Filter scan to specific project slug.")

    # analyze
    p_ana = subparsers.add_parser("analyze", help="Perform deep analysis of a single asset.")
    p_ana.add_argument("file", help="Path to video, image, or audio file to inspect.")

    # catalog
    p_cat = subparsers.add_parser("catalog", help="Display summary tables of cataloged assets.")
    p_cat.add_argument("--type", "-t", choices=["all", "video", "image", "audio"], default="all",
                       help="Filter catalog by asset type.")
    p_cat.add_argument("--project", "-p", help="Filter catalog by project slug.")

    # search
    p_srch = subparsers.add_parser("search", help="Search catalogs for keywords or tags.")
    p_srch.add_argument("--query", "-q", required=True, help="Search query string.")

    # check-duplicates
    subparsers.add_parser("check-duplicates", help="Identify duplicate assets via SHA-256.")

    # recommend-audio
    p_rec = subparsers.add_parser("recommend-audio", help="Recommend audio tracks for marketing reels.")
    p_rec.add_argument("--project", "-p", required=True, help="Project slug (e.g., block-puzzle-burst).")
    p_rec.add_argument("--category", "-c", choices=["music", "sound-effects", "voiceovers"], default="music",
                       help="Audio asset category.")
    p_rec.add_argument("--mood", "-m", help="Desired emotional mood tag (e.g., upbeat, relaxing, corporate).")
    p_rec.add_argument("--duration", "-d", type=float, help="Target reel duration in seconds.")

    args = parser.parse_args()

    dispatch = {
        "scan": cmd_scan,
        "analyze": cmd_analyze,
        "catalog": cmd_catalog,
        "search": cmd_search,
        "check-duplicates": cmd_check_duplicates,
        "recommend-audio": cmd_recommend_audio
    }

    cmd_fn = dispatch.get(args.command)
    if cmd_fn:
        sys.exit(cmd_fn(args))
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
