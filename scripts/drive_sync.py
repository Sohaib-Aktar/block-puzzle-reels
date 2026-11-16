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
        # Default source mapping
        if "DAY_04" in content_id.upper() or "DAY-04" in content_id.upper():
            source_dir = os.path.join(WORKSPACE_ROOT, "generated_outputs", project_id, "day-04")
        else:
            source_dir = os.path.join(WORKSPACE_ROOT, "generated_outputs", project_id, content_id)

    if not os.path.exists(source_dir):
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
    args = parser.parse_args()

    try:
        res = sync_to_drive(args.content_id, args.project)
        print(f"✅ Successfully synced {len(res['synced_files'])} files to Google Drive:")
        print(f"📁 Destination: {res['destination']}")
        for f in res["synced_files"]:
            print(f"   • {f}")
        print("\nGoogle Drive is now syncing these files to your phone in real-time!")
    except Exception as e:
        print(f"❌ Error syncing to Google Drive: {e}")
        sys.exit(1)
