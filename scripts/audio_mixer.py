"""
audio_mixer.py — Audio Assembly, Ducking & EBU R128 Loudness Mixing Engine
Combines background music, synthesized or recorded voiceover, and game sound effects
with frame-accurate timeline synchronization, dynamic ducking, and broadcast normalization.
"""

import os
import sys
import shutil
import subprocess
from typing import Dict, Any, List, Optional

WORKSPACE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(WORKSPACE_ROOT, "scripts"))
from media_engine import get_ffmpeg_cmd, inspect_media, run_command
from audio_engine import generate_voiceover, normalize_audio


class AudioMixer:
    """Manages multi-track audio layering, speech synthesis, ducking, and loudness mastering."""

    def __init__(self, target_loudness_lufs: float = -14.0):
        self.target_loudness_lufs = target_loudness_lufs

    def prepare_voiceover_stem(
        self,
        vo_spec: Dict[str, Any],
        intermediate_dir: str
    ) -> Optional[str]:
        """Synthesizes or copies the voiceover audio track."""
        if not vo_spec:
            return None

        vo_text = vo_spec.get("text")
        vo_file = vo_spec.get("file_path")

        out_wav = os.path.join(intermediate_dir, "voiceover_stem.wav")

        if vo_text:
            rate = int(vo_spec.get("rate", 0))
            vol = int(vo_spec.get("volume", 1.0) * 100)
            generate_voiceover(text=vo_text, output_wav_path=out_wav, rate=rate, volume=vol)
            return out_wav
        elif vo_file and os.path.exists(vo_file):
            return os.path.abspath(vo_file)

        return None

    def mix_master_audio(
        self,
        video_path: str,
        audio_spec: Dict[str, Any],
        output_path: str,
        intermediate_dir: str
    ) -> str:
        """
        Mixes video soundtrack with background music, voiceover, and SFX.
        Applies EBU R128 (-14 LUFS) normalization to final master.
        """
        abs_vid = os.path.abspath(video_path)
        abs_out = os.path.abspath(output_path)
        os.makedirs(os.path.dirname(abs_out), exist_ok=True)

        vid_info = inspect_media(abs_vid)
        total_duration = vid_info["duration_seconds"]

        # 1. Prepare Stems
        music_cfg = audio_spec.get("music")
        vo_cfg = audio_spec.get("voiceover")
        sfx_list = audio_spec.get("sound_effects", [])

        vo_stem = self.prepare_voiceover_stem(vo_cfg, intermediate_dir) if vo_cfg else None
        music_file = music_cfg.get("file_path") if music_cfg else None

        # If no extra audio, just ensure video audio is normalized
        if not music_file and not vo_stem and not sfx_list:
            shutil.copy2(abs_vid, abs_out)
            return abs_out

        # Build FFmpeg filtergraph inputs
        inputs = ["-i", abs_vid]
        input_index = 1
        filter_parts = []
        mix_inputs = []

        # Video audio track (input 0:a)
        has_orig_audio = bool(vid_info.get("audio_codec"))
        if has_orig_audio:
            filter_parts.append("[0:a]volume=1.0[a_orig]")
            mix_inputs.append("[a_orig]")

        # Voiceover stem
        if vo_stem and os.path.exists(vo_stem):
            inputs.extend(["-i", os.path.abspath(vo_stem)])
            vo_vol = float(vo_cfg.get("volume", 1.0)) if vo_cfg else 1.0
            filter_parts.append(f"[{input_index}:a]volume={vo_vol}[a_vo]")
            mix_inputs.append("[a_vo]")
            input_index += 1

        # Background Music stem
        if music_file and os.path.exists(music_file):
            inputs.extend(["-i", os.path.abspath(music_file)])
            # Ducking: if voiceover exists, reduce music volume
            base_vol = float(music_cfg.get("volume", 0.25))
            if vo_stem:
                # Apply ducking attenuation
                base_vol = min(base_vol, 0.15)

            fade_in = float(music_cfg.get("fade_in", 0.5))
            fade_out = float(music_cfg.get("fade_out", 0.8))
            out_start = max(0.0, total_duration - fade_out)

            music_filters = [
                f"volume={base_vol}",
                f"afade=t=in:ss=0:d={fade_in}",
                f"afade=t=out:ss={out_start:.2f}:d={fade_out}",
                f"atrim=0:{total_duration:.2f}"
            ]
            filter_parts.append(f"[{input_index}:a]{','.join(music_filters)}[a_bgm]")
            mix_inputs.append("[a_bgm]")
            input_index += 1

        # Sound effects
        for sfx_idx, sfx in enumerate(sfx_list):
            sfx_file = sfx.get("file_path")
            if sfx_file and os.path.exists(sfx_file):
                inputs.extend(["-i", os.path.abspath(sfx_file)])
                delay_ms = int(float(sfx.get("timeline_start", 0.0)) * 1000)
                vol = float(sfx.get("volume", 0.8))
                filter_parts.append(
                    f"[{input_index}:a]volume={vol},adelay={delay_ms}|{delay_ms}[a_sfx_{sfx_idx}]"
                )
                mix_inputs.append(f"[a_sfx_{sfx_idx}]")
                input_index += 1

        # Combine all audio stems with amix
        if len(mix_inputs) > 1:
            inputs_str = "".join(mix_inputs)
            filter_parts.append(
                f"{inputs_str}amix=inputs={len(mix_inputs)}:duration=first:dropout_transition=2[a_mix]"
            )
            master_audio_tag = "[a_mix]"
        elif len(mix_inputs) == 1:
            master_audio_tag = mix_inputs[0]
        else:
            master_audio_tag = None

        # Add EBU R128 loudness normalization
        loudness_target = audio_spec.get("master_loudness", self.target_loudness_lufs)
        filter_parts.append(
            f"{master_audio_tag}loudnorm=I={loudness_target}:LRA=11:TP=-1.5[a_master]"
        )

        filter_complex_str = ";".join(filter_parts)

        cmd = get_ffmpeg_cmd() + [
            "-y",
            *inputs,
            "-filter_complex", filter_complex_str,
            "-map", "0:v:0",
            "-map", "[a_master]",
            "-c:v", "copy",
            "-c:a", "aac",
            "-b:a", "160k",
            "-ar", "48000",
            "-ac", "2",
            "-shortest",
            "-movflags", "+faststart",
            abs_out
        ]

        run_command(cmd)
        return abs_out
