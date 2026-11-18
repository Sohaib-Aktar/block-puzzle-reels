"""
video_processor.py — Video Normalization, Scene Trimming & Visual Assembly Engine
Prepares source video clips to exact canvas specifications (9:16 vertical, 30fps CFR, yuv420p),
applies visual overlays, and stitches scenes into a seamless master visual timeline.
"""

import os
import sys
import shutil
import subprocess
from typing import Dict, Any, List, Optional

WORKSPACE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(WORKSPACE_ROOT, "scripts"))
from media_engine import get_ffmpeg_cmd, get_ffprobe_cmd, inspect_media, run_command
from overlay_engine import OverlayEngine


class VideoProcessor:
    """Processes video clips, normalizes geometry, and renders multi-scene assemblies."""

    def __init__(self, canvas_width: int = 1080, canvas_height: int = 1920, fps: float = 30.0):
        self.canvas_width = canvas_width
        self.canvas_height = canvas_height
        self.fps = fps
        self.overlay_engine = OverlayEngine(canvas_width, canvas_height)

    def normalize_and_trim_scene(
        self,
        scene: Dict[str, Any],
        output_path: str,
        intermediate_dir: str
    ) -> str:
        """
        Trims a single scene to source_in/duration, normalizes to canvas resolution & fps,
        adds silent audio if missing, and applies graphic overlays.
        """
        abs_in = os.path.abspath(scene["file_path"])
        abs_out = os.path.abspath(output_path)
        os.makedirs(os.path.dirname(abs_out), exist_ok=True)

        source_in = float(scene.get("source_in", 0.0))
        duration = float(scene.get("duration", 3.0))
        fit_mode = scene.get("fit_mode", "contain")
        overlays = scene.get("overlays", [])

        # Check if input has audio
        info = inspect_media(abs_in)
        has_audio = bool(info.get("audio_codec"))

        # Base scaling and aspect ratio filter
        w, h = self.canvas_width, self.canvas_height
        if fit_mode == "cover":
            vf_scale = f"scale=w={w}:h={h}:force_original_aspect_ratio=increase,crop={w}:{h}"
        elif fit_mode == "stretch":
            vf_scale = f"scale={w}:{h}"
        else:  # contain (letterbox/pillarbox)
            vf_scale = f"scale=w={w}:h={h}:force_original_aspect_ratio=decrease,pad=w={w}:h={h}:x=(ow-iw)/2:y=(oh-ih)/2:color=black"

        vf_norm = f"{vf_scale},setsar=1,fps=fps={self.fps},format=yuv420p"

        # Check for overlays
        if overlays:
            extra_inputs, filter_chains = self.overlay_engine.build_overlay_filters(
                overlays=overlays,
                intermediate_dir=intermediate_dir,
                scene_start_time=0.0
            )
            # Chain overlays: [0:v]vf_norm[base]; [base][ov0]overlay=...[v1]; ...
            filter_complex_parts = [f"[0:v]{vf_norm}[base]"]
            last_tag = "base"
            for idx, chain in enumerate(filter_chains):
                next_tag = f"v_ov_{idx}"
                # e.g. [1:v]format=rgba[ov0];[base][ov0]overlay=...[v_ov_0]
                ov_input_tag = f"ov{idx}"
                parts = chain.split(";")
                setup_part = parts[0]
                overlay_action = parts[1].split("[ov")[1].split("]overlay=")[1]
                filter_complex_parts.append(setup_part)
                filter_complex_parts.append(f"[{last_tag}][{ov_input_tag}]overlay={overlay_action}[{next_tag}]")
                last_tag = next_tag

            vf_string = ";".join(filter_complex_parts)
            video_map_tag = f"[{last_tag}]"
        else:
            extra_inputs = []
            vf_string = vf_norm
            video_map_tag = None

        # Build FFmpeg command
        cmd = get_ffmpeg_cmd() + [
            "-y",
            "-ss", str(source_in),
            "-i", abs_in,
            "-t", str(duration)
        ]

        if extra_inputs:
            cmd.extend(extra_inputs)

        # Audio handling: if input has no audio, add nullsrc
        if not has_audio:
            cmd.extend([
                "-f", "lavfi",
                "-i", f"anullsrc=channel_layout=stereo:sample_rate=48000"
            ])
            audio_input_idx = 1 + (len(extra_inputs) // 2)
            audio_map_args = ["-map", f"{audio_input_idx}:a:0"]
        else:
            audio_map_args = ["-map", "0:a:0?"]

        if video_map_tag:
            cmd.extend([
                "-filter_complex", vf_string,
                "-map", video_map_tag
            ])
        else:
            cmd.extend([
                "-vf", vf_string,
                "-map", "0:v:0"
            ])

        cmd.extend(audio_map_args)
        cmd.extend([
            "-c:v", "libx264",
            "-crf", "22",
            "-preset", "fast",
            "-c:a", "aac",
            "-b:a", "160k",
            "-ar", "48000",
            "-ac", "2",
            "-t", str(duration),
            "-movflags", "+faststart",
            abs_out
        ])

        run_command(cmd)
        return abs_out

    def assemble_timeline(
        self,
        scenes: List[Dict[str, Any]],
        output_path: str,
        intermediate_dir: str
    ) -> str:
        """
        Assembles a list of validated scenes into a single cohesive video.
        """
        if not scenes:
            raise ValueError("No scenes provided for assembly.")

        abs_out = os.path.abspath(output_path)
        os.makedirs(os.path.dirname(abs_out), exist_ok=True)

        # Process each scene into intermediate normalized clip
        processed_clips: List[str] = []
        for idx, scene in enumerate(scenes):
            scene_out = os.path.join(intermediate_dir, f"scene_{idx:02d}_norm.mp4")
            self.normalize_and_trim_scene(scene, scene_out, intermediate_dir)
            processed_clips.append(scene_out)

        # If only 1 scene, copy directly
        if len(processed_clips) == 1:
            shutil.copy2(processed_clips[0], abs_out)
            return abs_out

        # Multi-shot concatenation via concat demuxer
        list_file = os.path.join(intermediate_dir, "assembly_concat_list.txt")
        with open(list_file, "w", encoding="utf-8") as f:
            for clip in processed_clips:
                clean_path = os.path.abspath(clip).replace("\\", "/")
                f.write(f"file '{clean_path}'\n")

        cmd = get_ffmpeg_cmd() + [
            "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", list_file,
            "-c:v", "libx264",
            "-crf", "22",
            "-preset", "fast",
            "-c:a", "aac",
            "-b:a", "160k",
            "-movflags", "+faststart",
            abs_out
        ]
        run_command(cmd)
        return abs_out
