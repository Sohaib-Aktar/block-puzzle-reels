"""
media_engine.py — Core Media Processing Engine for AI Social Media Content Studio
Deterministic video editing using FFmpeg (System or Remotion bundled) and Python.

Capabilities:
  1. inspect          - Extract technical metadata (duration, streams, codecs, fps)
  2. trim             - Fast accurate cut
  3. concat           - Stitch multiple clips seamlessly
  4. resize_and_crop  - Standardize to platform dimensions (9:16, 16:9, etc.)
  5. speed_adjust     - Speed up or slow down footage
  6. mix_audio        - Combine gameplay/screen audio with voiceover and BGM
  7. export_platform  - Re-encode video strictly adhering to platform presets JSON
  8. process_manifest - Execute a complete EditingManifest JSON pipeline
"""

import os
import sys
import json
import shutil
import subprocess
import argparse
from typing import List, Dict, Any, Optional

WORKSPACE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MY_VIDEO_DIR = os.path.join(WORKSPACE_ROOT, "my-video")
CONFIG_DIR = os.path.join(WORKSPACE_ROOT, "config", "platform_presets")


def get_ffmpeg_cmd() -> List[str]:
    """Find system ffmpeg or fallback to Remotion's bundled ffmpeg binary."""
    if shutil.which("ffmpeg"):
        return ["ffmpeg"]
    # Direct bundled binary check (orders of magnitude faster than npx subprocess)
    remotion_dir = os.path.join(MY_VIDEO_DIR, "node_modules", "@remotion")
    if os.path.exists(remotion_dir):
        for entry in os.listdir(remotion_dir):
            if entry.startswith("compositor-"):
                candidate = os.path.join(remotion_dir, entry, "ffmpeg.exe" if os.name == "nt" else "ffmpeg")
                if os.path.exists(candidate):
                    return [candidate]
    # Fallback to npx remotion ffmpeg inside my-video
    return ["cmd", "/c", "npx", "--prefix", MY_VIDEO_DIR, "remotion", "ffmpeg"]


def get_ffprobe_cmd() -> List[str]:
    """Find system ffprobe or fallback to Remotion's bundled ffprobe binary."""
    if shutil.which("ffprobe"):
        return ["ffprobe"]
    # Direct bundled binary check (orders of magnitude faster than npx subprocess)
    remotion_dir = os.path.join(MY_VIDEO_DIR, "node_modules", "@remotion")
    if os.path.exists(remotion_dir):
        for entry in os.listdir(remotion_dir):
            if entry.startswith("compositor-"):
                candidate = os.path.join(remotion_dir, entry, "ffprobe.exe" if os.name == "nt" else "ffprobe")
                if os.path.exists(candidate):
                    return [candidate]
    # Fallback to npx remotion ffprobe inside my-video
    return ["cmd", "/c", "npx", "--prefix", MY_VIDEO_DIR, "remotion", "ffprobe"]


def run_command(cmd: List[str]) -> subprocess.CompletedProcess:
    """Execute a CLI command safely and raise error on failure."""
    res = subprocess.run(cmd, cwd=MY_VIDEO_DIR, capture_output=True, text=True, encoding="utf-8")
    if res.returncode != 0:
        raise RuntimeError(f"Command failed with exit code {res.returncode}:\n{' '.join(cmd)}\n\nStderr:\n{res.stderr}")
    return res


def inspect_media(file_path: str) -> Dict[str, Any]:
    """Extract format and stream metadata using ffprobe."""
    abs_path = os.path.abspath(file_path)
    if not os.path.exists(abs_path):
        raise FileNotFoundError(f"Media file not found: {abs_path}")

    cmd = get_ffprobe_cmd() + [
        "-v", "quiet",
        "-print_format", "json",
        "-show_format",
        "-show_streams",
        abs_path
    ]
    res = run_command(cmd)
    data = json.loads(res.stdout)
    
    # Parse high level summary
    fmt = data.get("format", {})
    streams = data.get("streams", [])
    
    video_stream = next((s for s in streams if s.get("codec_type") == "video"), None)
    audio_stream = next((s for s in streams if s.get("codec_type") == "audio"), None)
    
    duration = float(fmt.get("duration", 0.0))
    width = int(video_stream.get("width", 0)) if video_stream else 0
    height = int(video_stream.get("height", 0)) if video_stream else 0
    
    fps = 30.0
    if video_stream and "r_frame_rate" in video_stream:
        parts = video_stream["r_frame_rate"].split("/")
        if len(parts) == 2 and int(parts[1]) > 0:
            fps = round(int(parts[0]) / int(parts[1]), 2)
            
    return {
        "file_path": abs_path,
        "file_size_bytes": int(fmt.get("size", 0)),
        "duration_seconds": duration,
        "width": width,
        "height": height,
        "fps": fps,
        "video_codec": video_stream.get("codec_name") if video_stream else None,
        "pix_fmt": video_stream.get("pix_fmt") if video_stream else None,
        "audio_codec": audio_stream.get("codec_name") if audio_stream else None,
        "audio_sample_rate": int(audio_stream.get("sample_rate", 0)) if audio_stream else None,
        "audio_channels": int(audio_stream.get("channels", 0)) if audio_stream else None,
        "raw_ffprobe": data
    }


def trim_clip(input_path: str, output_path: str, start_sec: float, duration_sec: float) -> str:
    """Trim a section of a video file with frame accuracy."""
    abs_in = os.path.abspath(input_path)
    abs_out = os.path.abspath(output_path)
    os.makedirs(os.path.dirname(abs_out), exist_ok=True)

    cmd = get_ffmpeg_cmd() + [
        "-y",
        "-ss", str(start_sec),
        "-i", abs_in,
        "-t", str(duration_sec),
        "-c:v", "libx264",
        "-crf", "22",
        "-preset", "fast",
        "-c:a", "aac",
        "-b:a", "128k",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        abs_out
    ]
    run_command(cmd)
    return abs_out


def resize_and_crop(input_path: str, output_path: str, target_width: int, target_height: int) -> str:
    """Scale video to target resolution."""
    abs_in = os.path.abspath(input_path)
    abs_out = os.path.abspath(output_path)
    os.makedirs(os.path.dirname(abs_out), exist_ok=True)

    scale_filter = f"scale={target_width}:{target_height}"
    cmd = get_ffmpeg_cmd() + [
        "-y",
        "-i", abs_in,
        "-vf", scale_filter,
        "-c:v", "libx264",
        "-crf", "22",
        "-preset", "fast",
        "-c:a", "copy",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        abs_out
    ]
    run_command(cmd)
    return abs_out


def adjust_speed(input_path: str, output_path: str, speed_factor: float) -> str:
    """
    Adjust playback rate of video and audio.
    speed_factor > 1.0 speeds up; < 1.0 slows down.
    """
    if speed_factor <= 0:
        raise ValueError("speed_factor must be positive")

    abs_in = os.path.abspath(input_path)
    abs_out = os.path.abspath(output_path)
    os.makedirs(os.path.dirname(abs_out), exist_ok=True)

    video_pts = 1.0 / speed_factor
    vf = f"setpts={video_pts}*PTS"
    af = f"atempo={speed_factor}"

    cmd = get_ffmpeg_cmd() + [
        "-y",
        "-i", abs_in,
        "-filter:v", vf,
        "-filter:a", af,
        "-c:v", "libx264",
        "-crf", "22",
        "-preset", "fast",
        "-c:a", "aac",
        "-b:a", "128k",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        abs_out
    ]
    run_command(cmd)
    return abs_out


def concat_clips(clip_paths: List[str], output_path: str) -> str:
    """Concatenate a list of video files."""
    if not clip_paths:
        raise ValueError("No clips provided for concatenation")

    abs_out = os.path.abspath(output_path)
    os.makedirs(os.path.dirname(abs_out), exist_ok=True)

    # Write concat manifest list file
    list_file_path = abs_out + ".concat_list.txt"
    with open(list_file_path, "w", encoding="utf-8") as f:
        for p in clip_paths:
            f.write(f"file '{os.path.abspath(p).replace(chr(92), '/')}'\n")

    cmd = get_ffmpeg_cmd() + [
        "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", list_file_path,
        "-c:v", "libx264",
        "-crf", "22",
        "-c:a", "aac",
        "-b:a", "128k",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        abs_out
    ]
    try:
        run_command(cmd)
    finally:
        if os.path.exists(list_file_path):
            os.remove(list_file_path)

    return abs_out


def mix_audio(video_path: str, output_path: str, bgm_path: Optional[str] = None, bgm_volume: float = 0.25, voiceover_path: Optional[str] = None) -> str:
    """Mix background music and/or voiceover into video file."""
    abs_vid = os.path.abspath(video_path)
    abs_out = os.path.abspath(output_path)
    os.makedirs(os.path.dirname(abs_out), exist_ok=True)

    if not bgm_path and not voiceover_path:
        shutil.copy2(abs_vid, abs_out)
        return abs_out

    inputs = ["-i", abs_vid]
    if bgm_path:
        inputs += ["-i", os.path.abspath(bgm_path)]
    if voiceover_path:
        inputs += ["-i", os.path.abspath(voiceover_path)]

    cmd = get_ffmpeg_cmd() + ["-y"] + inputs + [
        "-c:v", "copy",
        "-c:a", "aac",
        "-b:a", "160k",
        "-shortest",
        "-movflags", "+faststart",
        abs_out
    ]
    run_command(cmd)
    return abs_out


def export_platform_preset(input_path: str, output_path: str, preset_name: str) -> str:
    """
    Re-encode a video file adhering strictly to a JSON platform preset.
    """
    preset_file = os.path.join(CONFIG_DIR, f"{preset_name}.json")
    if not os.path.exists(preset_file):
        raise FileNotFoundError(f"Platform preset '{preset_name}' not found at {preset_file}")

    with open(preset_file, "r", encoding="utf-8") as f:
        preset = json.load(f)

    res = preset.get("resolution", {})
    target_w = res.get("width", 1080)
    target_h = res.get("height", 1920)
    fps = preset.get("frame_rate", 30)
    crf = str(preset.get("crf", 23))
    vcodec = preset.get("video_codec", "libx264")
    acodec = preset.get("audio_codec", "aac")
    abitrate = preset.get("audio_bitrate", "128k")

    abs_in = os.path.abspath(input_path)
    abs_out = os.path.abspath(output_path)
    os.makedirs(os.path.dirname(abs_out), exist_ok=True)

    cmd = get_ffmpeg_cmd() + [
        "-y",
        "-i", abs_in,
        "-vf", f"scale={target_w}:{target_h}",
        "-r", str(fps),
        "-c:v", vcodec,
        "-crf", crf,
        "-preset", "fast",
        "-c:a", acodec,
        "-b:a", abitrate,
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        abs_out
    ]
    run_command(cmd)
    return abs_out


def process_manifest(manifest_path: str) -> str:
    """
    Execute a full deterministic EditingManifest JSON pipeline.
    """
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    renderer = manifest.get("renderer", "ffmpeg")
    output_target = os.path.abspath(manifest["output_target"])
    os.makedirs(os.path.dirname(output_target), exist_ok=True)

    if renderer == "remotion":
        comp_id = manifest.get("composition_id", "SolveItReel")
        rel_output = os.path.relpath(output_target, MY_VIDEO_DIR)
        cmd = ["cmd", "/c", "npx", "remotion", "render", "src/index.ts", comp_id, rel_output]
        run_command(cmd)
        return output_target

    # FFmpeg multi-shot pipeline
    timeline = manifest.get("timeline", [])
    temp_clips = []
    try:
        for idx, shot in enumerate(timeline):
            src_file = os.path.join(WORKSPACE_ROOT, shot["source_file"])
            shot_start = shot.get("source_start", 0.0)
            shot_dur = shot.get("duration", 3.0)
            temp_shot_out = output_target + f".shot_{idx}.mp4"
            trim_clip(src_file, temp_shot_out, shot_start, shot_dur)
            temp_clips.append(temp_shot_out)

        if len(temp_clips) == 1:
            shutil.copy2(temp_clips[0], output_target)
        else:
            concat_clips(temp_clips, output_target)

        # Scale to canvas
        canvas = manifest.get("canvas", {})
        if canvas:
            w = canvas.get("width", 1080)
            h = canvas.get("height", 1920)
            scaled_target = output_target + ".scaled.mp4"
            resize_and_crop(output_target, scaled_target, w, h)
            shutil.move(scaled_target, output_target)

    finally:
        for c in temp_clips:
            if os.path.exists(c):
                os.remove(c)

    return output_target


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AI Content Studio Media Processing Engine")
    subparsers = parser.add_subparsers(dest="action")

    # Inspect
    p_inspect = subparsers.add_parser("inspect", help="Inspect video metadata")
    p_inspect.add_argument("input", help="Path to video file")

    # Trim
    p_trim = subparsers.add_parser("trim", help="Trim video clip")
    p_trim.add_argument("input", help="Source video")
    p_trim.add_argument("output", help="Output destination")
    p_trim.add_argument("--start", type=float, required=True, help="Start time in seconds")
    p_trim.add_argument("--duration", type=float, required=True, help="Duration in seconds")

    # Resize
    p_resize = subparsers.add_parser("resize", help="Resize video")
    p_resize.add_argument("input", help="Source video")
    p_resize.add_argument("output", help="Output destination")
    p_resize.add_argument("--width", type=int, required=True, help="Width in px")
    p_resize.add_argument("--height", type=int, required=True, help="Height in px")

    # Speed
    p_speed = subparsers.add_parser("speed", help="Adjust playback speed")
    p_speed.add_argument("input", help="Source video")
    p_speed.add_argument("output", help="Output destination")
    p_speed.add_argument("--factor", type=float, required=True, help="Speed multiplier (e.g. 1.25)")

    # Export
    p_export = subparsers.add_parser("export", help="Export adhering to platform preset")
    p_export.add_argument("input", help="Source video")
    p_export.add_argument("output", help="Output destination")
    p_export.add_argument("--preset", required=True, help="Preset name (e.g. instagram_reel, youtube_short)")

    # Manifest
    p_manifest = subparsers.add_parser("manifest", help="Render video from editing manifest")
    p_manifest.add_argument("manifest_file", help="Path to manifest.json")

    args = parser.parse_args()

    if args.action == "inspect":
        info = inspect_media(args.input)
        print(f"\nMedia Report: {info['file_path']}")
        print(f"  Duration : {info['duration_seconds']:.2f}s")
        print(f"  Canvas   : {info['width']}x{info['height']} @ {info['fps']} fps")
        print(f"  Video    : {info['video_codec']} ({info['pix_fmt']})")
        print(f"  Audio    : {info['audio_codec']} ({info['audio_sample_rate']} Hz, {info['audio_channels']} ch)")
        print(f"  Size     : {info['file_size_bytes'] / (1024*1024):.2f} MB\n")
    elif args.action == "trim":
        out = trim_clip(args.input, args.output, args.start, args.duration)
        print(f"Trimmed clip saved to: {out}")
    elif args.action == "resize":
        out = resize_and_crop(args.input, args.output, args.width, args.height)
        print(f"Resized clip saved to: {out}")
    elif args.action == "speed":
        out = adjust_speed(args.input, args.output, args.factor)
        print(f"Speed adjusted clip saved to: {out}")
    elif args.action == "export":
        out = export_platform_preset(args.input, args.output, args.preset)
        print(f"Exported preset clip saved to: {out}")
    elif args.action == "manifest":
        out = process_manifest(args.manifest_file)
        print(f"Rendered manifest output to: {out}")
    else:
        parser.print_help()
