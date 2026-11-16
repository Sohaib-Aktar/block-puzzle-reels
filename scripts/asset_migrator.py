"""
asset_migrator.py — Safe, Non-Destructive Source Asset Migration Engine
Organizes media files into canonical project-based directory structures:
  source_assets/<project>/<category>/<filename>

Guarantees:
  1. Zero Data Loss: Never deletes original files.
  2. Non-Destructive: Copies (shutil.copy2) while preserving timestamps & metadata.
  3. Deduplication: Calculates SHA-256 hashes to identify redundant files across folders.
  4. Dry-Run Verification: Previews all operations before disk writes.
  5. Audit Logging: Records all actions into data/migration_log.json.
"""

import os
import sys
import json
import shutil
import hashlib
import argparse
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

WORKSPACE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SOURCE_ASSETS_DIR = os.path.join(WORKSPACE_ROOT, "source_assets")
DATA_DIR = os.path.join(WORKSPACE_ROOT, "data")
MIGRATION_LOG_PATH = os.path.join(DATA_DIR, "migration_log.json")
MEDIA_CATALOG_PATH = os.path.join(DATA_DIR, "media_catalog.json")

PROJECT_CATEGORIES = {
    "block-puzzle-burst": [
        "gameplay", "screenshots", "logos", "music", "sound-effects",
        "voiceovers", "lifestyle-footage", "other"
    ],
    "expand-ezisales": [
        "screenshots", "screen-recordings", "logos", "music",
        "sound-effects", "voiceovers", "other"
    ],
    "expand-hr": [
        "screenshots", "screen-recordings", "logos", "music",
        "sound-effects", "voiceovers", "other"
    ],
    "wms": [
        "screenshots", "screen-recordings", "logos", "music",
        "sound-effects", "voiceovers", "other"
    ],
    "pos": [
        "screenshots", "screen-recordings", "logos", "music",
        "sound-effects", "voiceovers", "other"
    ]
}


def calculate_sha256(filepath: str, block_size: int = 65536) -> str:
    """Calculate SHA-256 hash of a file."""
    hasher = hashlib.sha256()
    with open(filepath, "rb") as f:
        for block in iter(lambda: f.read(block_size), b""):
            hasher.update(block)
    return hasher.hexdigest()


def ensure_folder_structure(base_dir: str = SOURCE_ASSETS_DIR) -> Dict[str, List[str]]:
    """Create directory structure for all projects and categories."""
    created = {}
    for project, categories in PROJECT_CATEGORIES.items():
        created[project] = []
        for cat in categories:
            p = os.path.join(base_dir, project, cat)
            os.makedirs(p, exist_ok=True)
            created[project].append(p)
    return created


def scan_known_sources() -> List[Dict[str, Any]]:
    """Identify candidate source files across known workspace folders."""
    candidates = []

    # 1. Raw_input_files/
    raw_dir = os.path.join(WORKSPACE_ROOT, "Raw_input_files")
    if os.path.exists(raw_dir):
        for fname in os.listdir(raw_dir):
            fpath = os.path.join(raw_dir, fname)
            if not os.path.isfile(fpath):
                continue
            cat = "other"
            if fname.endswith(".mp4"):
                cat = "gameplay"
            elif fname.endswith(".png"):
                cat = "logos"
            elif fname.endswith((".jpg", ".jpeg")):
                cat = "screenshots"
            candidates.append({
                "source_path": fpath,
                "project": "block-puzzle-burst",
                "category": cat,
                "target_filename": fname
            })

    # 2. Files in my-video/public/
    pub_dir = os.path.join(WORKSPACE_ROOT, "my-video", "public")
    if os.path.exists(pub_dir):
        for fname in os.listdir(pub_dir):
            fpath = os.path.join(pub_dir, fname)
            if not os.path.isfile(fpath):
                continue
            if fname.startswith("scene_0") and fname.endswith(".jpg"):
                candidates.append({
                    "source_path": fpath,
                    "project": "block-puzzle-burst",
                    "category": "lifestyle-footage",
                    "target_filename": fname
                })
            elif fname in ["gameplay.mp4", "gameplay2.mp4", "recording_3.mp4", "recording_3_cfr30.mp4"]:
                candidates.append({
                    "source_path": fpath,
                    "project": "block-puzzle-burst",
                    "category": "gameplay",
                    "target_filename": fname
                })
            elif fname == "gameplay_lifestyle_cfr30.mp4":
                candidates.append({
                    "source_path": fpath,
                    "project": "block-puzzle-burst",
                    "category": "gameplay",
                    "target_filename": fname
                })
            elif fname.startswith("vo_") and fname.endswith(".wav"):
                candidates.append({
                    "source_path": fpath,
                    "project": "block-puzzle-burst",
                    "category": "voiceovers",
                    "target_filename": fname
                })
            elif fname == "day05_voiceover.wav":
                candidates.append({
                    "source_path": fpath,
                    "project": "block-puzzle-burst",
                    "category": "voiceovers",
                    "target_filename": fname
                })
            elif fname == "bgm_day05.wav":
                candidates.append({
                    "source_path": fpath,
                    "project": "block-puzzle-burst",
                    "category": "music",
                    "target_filename": "bgm_day05_relaxing_piano.wav"
                })
            elif fname.endswith((".png", ".jpg", ".jpeg")) and fname not in ["sample_1.jpg", "sample_2.jpg", "sample_airplane.jpg"]:
                candidates.append({
                    "source_path": fpath,
                    "project": "block-puzzle-burst",
                    "category": "logos" if "icon" in fname else "screenshots",
                    "target_filename": fname
                })

    # 3. Tutorial VO & recordings from outputs/
    ezisales_vo = os.path.join(WORKSPACE_ROOT, "outputs", "expand-ezisales", "quick-start-tutorials",
                               "ezisales-tut-01-order-booking", "voiceover.wav")
    if os.path.exists(ezisales_vo):
        candidates.append({
            "source_path": ezisales_vo,
            "project": "expand-ezisales",
            "category": "voiceovers",
            "target_filename": "ezisales_tut01_voiceover.wav"
        })

    expandhr_vo = os.path.join(WORKSPACE_ROOT, "outputs", "expand-hr", "payroll-quick-guides",
                               "expandhr-tut-01-one-click-payroll", "voiceover.wav")
    if os.path.exists(expandhr_vo):
        candidates.append({
            "source_path": expandhr_vo,
            "project": "expand-hr",
            "category": "voiceovers",
            "target_filename": "expandhr_tut01_voiceover.wav"
        })

    return candidates


def plan_migration() -> Tuple[List[Dict[str, Any]], Dict[str, List[str]]]:
    """Analyze source candidates, compute hashes, and detect duplicates."""
    candidates = scan_known_sources()
    operations = []
    hash_map: Dict[str, List[str]] = {}

    for c in candidates:
        src = c["source_path"]
        if not os.path.exists(src):
            continue

        file_size = os.path.getsize(src)
        sha256 = calculate_sha256(src)

        if sha256 not in hash_map:
            hash_map[sha256] = []
        hash_map[sha256].append(src)

        target_dir = os.path.join(SOURCE_ASSETS_DIR, c["project"], c["category"])
        target_path = os.path.join(target_dir, c["target_filename"])

        is_duplicate = len(hash_map[sha256]) > 1
        original_source = hash_map[sha256][0]

        operations.append({
            "source_path": src,
            "target_path": target_path,
            "project": c["project"],
            "category": c["category"],
            "filename": c["target_filename"],
            "size_bytes": file_size,
            "sha256": sha256,
            "is_duplicate": is_duplicate,
            "duplicate_of": original_source if is_duplicate else None
        })

    return operations, hash_map


def execute_migration(dry_run: bool = True) -> Dict[str, Any]:
    """
    Executes safe asset migration.
    If dry_run=True, prints the proposed operations without touching files.
    """
    operations, hash_map = plan_migration()
    duplicates_found = {k: v for k, v in hash_map.items() if len(v) > 1}

    results = {
        "timestamp": datetime.now().isoformat(),
        "dry_run": dry_run,
        "total_candidates": len(operations),
        "unique_files": len(hash_map),
        "duplicate_groups": len(duplicates_found),
        "operations": []
    }

    if not dry_run:
        ensure_folder_structure(SOURCE_ASSETS_DIR)

    for op in operations:
        status = "planned"
        src = op["source_path"]
        dst = op["target_path"]

        if dry_run:
            status = "dry_run_preview"
        else:
            try:
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                if os.path.exists(dst):
                    dst_sha256 = calculate_sha256(dst)
                    if dst_sha256 == op["sha256"]:
                        status = "already_synced"
                    else:
                        # Collision with different content: preserve existing with timestamp suffix
                        base, ext = os.path.splitext(op["filename"])
                        stamped = f"{base}_{int(datetime.now().timestamp())}{ext}"
                        dst = os.path.join(os.path.dirname(dst), stamped)
                        shutil.copy2(src, dst)
                        status = "copied_with_collision_rename"
                else:
                    shutil.copy2(src, dst)
                    status = "copied"
            except Exception as e:
                status = f"error: {str(e)}"

        rec = dict(op)
        rec["status"] = status
        rec["actual_destination"] = dst
        results["operations"].append(rec)

    if not dry_run:
        os.makedirs(DATA_DIR, exist_ok=True)
        with open(MIGRATION_LOG_PATH, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)

    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Source Asset Migration Engine")
    parser.add_argument("--execute", action="store_true", help="Execute actual copy (default is dry-run)")
    parser.add_argument("--init-folders", action="store_true", help="Only initialize source_assets/ folders")
    args = parser.parse_args()

    if args.init_folders:
        created = ensure_folder_structure()
        print("✅ Initialized source_assets/ folders for all projects:")
        for proj, dirs in created.items():
            print(f"  • {proj} ({len(dirs)} categories)")
        sys.exit(0)

    is_dry = not args.execute
    print(f"\n======================================================================")
    print(f"ASSET MIGRATION ENGINE — {'DRY RUN PREVIEW' if is_dry else 'EXECUTING LIVE'}")
    print(f"======================================================================\n")

    res = execute_migration(dry_run=is_dry)
    print(f"Total Candidate Assets : {res['total_candidates']}")
    print(f"Unique Content Hashes  : {res['unique_files']}")
    print(f"Duplicate Groups       : {res['duplicate_groups']}")
    print(f"Status                 : {'Preview Only (Dry Run)' if is_dry else 'Live Migration Completed'}\n")

    for idx, op in enumerate(res["operations"], 1):
        rel_src = os.path.relpath(op["source_path"], WORKSPACE_ROOT)
        rel_dst = os.path.relpath(op["target_path"], WORKSPACE_ROOT)
        dup_flag = " [DUPLICATE]" if op["is_duplicate"] else ""
        print(f"[{idx:02d}] {rel_src} -> {rel_dst}{dup_flag} ({op['status']})")

    if is_dry:
        print("\n💡 Run with --execute to perform non-destructive copy into source_assets/.")
    else:
        print(f"\n✅ Migration log saved to: {MIGRATION_LOG_PATH}")
