"""
drive_sync.py — Google Drive Sync Integration
Synchronizes generated final video packages to Google Drive for Desktop (G:\\My Drive\\Vids\\generated).
Provides instant phone access for social media posting.
"""

import os
import sys
import shutil
import argparse
from typing import Dict, Any

WORKSPACE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GDRIVE_ROOT = r"G:\My Drive\Vids\generated"


def sync_to_drive(
    content_id: str,
    project_id: str = "block-puzzle-burst",
    source_dir: str = None
) -> Dict[str, Any]:
    """
    Copies the rendered video, captions, and editing plan to Google Drive.
    """
    if not os.path.exists(r"G:\My Drive"):
        raise FileNotFoundError("Google Drive for Desktop is not detected at G:\\My Drive.")

    if not source_dir:
        # Default source mappings
        candidates = [
            os.path.join(WORKSPACE_ROOT, "outputs", project_id, "30-day-challenge", "day-05-puzzle-break"),
            os.path.join(WORKSPACE_ROOT, "generated_outputs", project_id, "day-04"),
            os.path.join(WORKSPACE_ROOT, "generated_outputs", project_id, content_id),
            os.path.join(WORKSPACE_ROOT, "outputs", project_id, content_id),
        ]
        for c in candidates:
            if os.path.exists(c):
                source_dir = c
                break

    if not source_dir or not os.path.exists(source_dir):
        raise FileNotFoundError(f"Source output directory not found: {source_dir}")

    dest_folder = os.path.join(GDRIVE_ROOT, content_id)
    os.makedirs(dest_folder, exist_ok=True)

    synced_files = []
    for item in os.listdir(source_dir):
        src_item = os.path.join(source_dir, item)
        dst_item = os.path.join(dest_folder, item)
        if os.path.isfile(src_item) and item.endswith((".mp4", ".txt", ".md", ".json")):
            shutil.copy2(src_item, dst_item)
            synced_files.append(item)
        elif os.path.isdir(src_item):
            shutil.copytree(src_item, dst_item, dirs_exist_ok=True)
            synced_files.append(f"{item}/ (folder)")

    return {
        "status": "success",
        "content_id": content_id,
        "destination": dest_folder,
        "synced_files": synced_files
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Sync deliverables to Google Drive")
    parser.add_argument("--content-id", required=True, help="Content ID e.g. BPB_DAY_04")
    parser.add_argument("--project", default="block-puzzle-burst", help="Project name")
    parser.add_argument("--source-dir", default=None, help="Explicit source directory")
    args = parser.parse_args()

    try:
        res = sync_to_drive(args.content_id, args.project, args.source_dir)
        print(f"✅ Successfully synced {len(res['synced_files'])} items to Google Drive:")
        print(f"📁 Destination: {res['destination']}")
        for f in res["synced_files"]:
            print(f"   • {f}")
        print("\nGoogle Drive is now syncing these files to your phone in real-time!")
    except Exception as e:
        print(f"❌ Error syncing to Google Drive: {e}")
        sys.exit(1)
