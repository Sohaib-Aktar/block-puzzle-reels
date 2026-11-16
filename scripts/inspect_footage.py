"""
inspect_footage.py
Inspect video files using the FFprobe bundled inside Remotion.

Usage:
  python scripts/inspect_footage.py <path_to_video>

Requires:
  - my-video/node_modules installed (run: cd my-video && npm install)
  - Python 3.8+

Output:
  Duration, dimensions, fps, codec, audio track info (JSON)
"""

import subprocess
import json
import sys
import os

WORKSPACE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MY_VIDEO_DIR = os.path.join(WORKSPACE_ROOT, "my-video")

def get_ffprobe_cmd():
    # 1. System ffprobe on PATH
    import shutil
    if shutil.which("ffprobe"):
        return ["ffprobe"]
    # 2. Bundled inside my-video via npx remotion ffprobe
    return ["cmd", "/c", "npx", "remotion", "ffprobe"]


def inspect(video_path: str) -> dict:
    """Run ffprobe and return parsed metadata dict."""
    cmd_base = get_ffprobe_cmd()
    abs_path = os.path.abspath(video_path)
    cmd = cmd_base + [
        "-v", "quiet",
        "-print_format", "json",
        "-show_format",
        "-show_streams",
        abs_path,
    ]
    result = subprocess.run(cmd, cwd=MY_VIDEO_DIR, capture_output=True, text=True, encoding="utf-8")
    if result.returncode != 0:
        print(f"ERROR: ffprobe failed\n{result.stderr}", file=sys.stderr)
        sys.exit(1)
    return json.loads(result.stdout)


def summarise(meta: dict) -> None:
    fmt = meta.get("format", {})
    streams = meta.get("streams", [])

    print(f"\n=== File: {fmt.get('filename', 'unknown')} ===")
    print(f"  Duration : {float(fmt.get('duration', 0)):.2f}s")
    print(f"  Size     : {int(fmt.get('size', 0)) / 1_048_576:.2f} MB")
    print(f"  Format   : {fmt.get('format_long_name', 'unknown')}")

    for s in streams:
        ctype = s.get("codec_type", "?")
        codec = s.get("codec_name", "?")
        if ctype == "video":
            w = s.get("width", "?")
            h = s.get("height", "?")
            fps_raw = s.get("r_frame_rate", "?/1")
            try:
                num, den = fps_raw.split("/")
                fps = round(int(num) / int(den), 2)
            except Exception:
                fps = fps_raw
            print(f"  Video    : {codec}  {w}x{h}  {fps} fps")
            pix_fmt = s.get("pix_fmt", "?")
            print(f"             pix_fmt={pix_fmt}")
        elif ctype == "audio":
            sr = s.get("sample_rate", "?")
            ch = s.get("channels", "?")
            print(f"  Audio    : {codec}  {sr} Hz  {ch}ch")
    print()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/inspect_footage.py <video_file>")
        sys.exit(1)
    target = sys.argv[1]
    if not os.path.exists(target):
        print(f"File not found: {target}", file=sys.stderr)
        sys.exit(1)
    meta = inspect(target)
    summarise(meta)
