"""
export_preview_generator.py — Visual Preview, Safe-Zone Overlay & Contact Sheet Generator
Creates human-reviewable visual inspection assets for Phase 4 multi-platform exports:
  - Per-platform preview stills
  - Safe-zone UI overlay visualizations (provisional bounds from config/production/safe_zones.json)
  - Side-by-side reframing comparison (Master 9:16 vs 16:9 adaptation)
  - Full multi-platform contact sheet with technical spec strips
"""

import os
import sys
import json
import subprocess
from typing import Dict, Any, List, Optional
from PIL import Image, ImageDraw, ImageFont

WORKSPACE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(WORKSPACE_ROOT, "scripts"))
from media_engine import get_ffmpeg_cmd


def _load_font(size: int = 24, bold: bool = True) -> ImageFont.ImageFont:
    candidates = [
        r"C:\Windows\Fonts\arialbd.ttf" if bold else r"C:\Windows\Fonts\arial.ttf",
        r"C:\Windows\Fonts\segoeuib.ttf" if bold else r"C:\Windows\Fonts\segoeui.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ]
    for p in candidates:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                continue
    return ImageFont.load_default()


class ExportPreviewGenerator:
    """Generates preview frames, safe-zone overlays, and comparison contact sheets."""

    def __init__(self, safe_zones_config: Optional[Dict[str, Any]] = None):
        if safe_zones_config is None:
            sz_path = os.path.join(WORKSPACE_ROOT, "config", "production", "safe_zones.json")
            if os.path.exists(sz_path):
                with open(sz_path, "r", encoding="utf-8") as f:
                    safe_zones_config = json.load(f)
            else:
                safe_zones_config = {"profiles": {}}
        self.safe_zones_config = safe_zones_config

    def extract_frame(self, video_path: str, output_png: str, timestamp_sec: float = 1.0) -> str:
        """Extracts a single PNG frame at `timestamp_sec` from `video_path`."""
        abs_in = os.path.abspath(video_path)
        abs_out = os.path.abspath(output_png)
        os.makedirs(os.path.dirname(abs_out), exist_ok=True)

        cmd = get_ffmpeg_cmd() + [
            "-y", "-v", "error",
            "-ss", f"{max(0.0, timestamp_sec):.3f}",
            "-i", abs_in,
            "-vframes", "1",
            abs_out
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0 or not os.path.exists(abs_out):
            # Fallback to frame 0 if video is shorter than timestamp_sec
            cmd_fb = get_ffmpeg_cmd() + [
                "-y", "-v", "error",
                "-i", abs_in,
                "-vframes", "1",
                abs_out
            ]
            subprocess.run(cmd_fb, capture_output=True, text=True, check=True)
        return abs_out

    def generate_safe_zone_overlay(
        self,
        preview_png: str,
        profile_id: str,
        output_png: str
    ) -> str:
        """Draws translucent platform UI occlusion zones and safe boxes onto a preview frame."""
        abs_in = os.path.abspath(preview_png)
        abs_out = os.path.abspath(output_png)
        os.makedirs(os.path.dirname(abs_out), exist_ok=True)

        sz_spec = self.safe_zones_config.get("profiles", {}).get(profile_id)

        with Image.open(abs_in).convert("RGBA") as base:
            w, h = base.size
            overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
            draw = ImageDraw.Draw(overlay)

            font_title = _load_font(size=max(20, int(w * 0.022)), bold=True)
            font_small = _load_font(size=max(16, int(w * 0.017)), bold=False)

            if sz_spec:
                # Draw UI occlusion zones (red/amber translucent fill)
                for zone in sz_spec.get("ui_occlusion_zones", []):
                    zx, zy, zw, zh = zone["x"], zone["y"], zone["width"], zone["height"]
                    fill_col = (220, 38, 38, 95) if zone.get("severity") == "high" else (245, 158, 11, 80)
                    border_col = (248, 113, 113, 210)
                    draw.rectangle([zx, zy, zx + zw, zy + zh], fill=fill_col, outline=border_col, width=3)
                    label = zone.get("name", "UI Zone")
                    draw.text((zx + 14, zy + 12), label, fill=(255, 255, 255, 240), font=font_small)

                # Draw Safe Content Box (bright green outline)
                sb = sz_spec.get("safe_content_box")
                if sb:
                    sx, sy, sw, sh = sb["x"], sb["y"], sb["width"], sb["height"]
                    draw.rectangle([sx, sy, sx + sw, sy + sh], outline=(34, 197, 94, 245), width=5)
                    draw.text((sx + 14, sy + 10), f"SAFE CONTENT AREA ({profile_id} - PROVISIONAL)", fill=(74, 222, 128, 255), font=font_title)

                # Draw CTA Safe Box (cyan outline)
                cb = sz_spec.get("cta_safe_box")
                if cb:
                    cx, cy, cw, ch = cb["x"], cb["y"], cb["width"], cb["height"]
                    draw.rectangle([cx, cy, cx + cw, cy + ch], outline=(56, 189, 248, 230), width=3)
                    draw.text((cx + 12, cy + 8), "CTA Safe Region", fill=(125, 211, 252, 255), font=font_small)

            composed = Image.alpha_composite(base, overlay).convert("RGB")
            composed.save(abs_out, "PNG")

        return abs_out

    def generate_reframing_comparison(
        self,
        master_preview_png: str,
        adapted_preview_png: str,
        output_png: str,
        master_label: str = "Approved Master (9:16)",
        adapted_label: str = "YouTube Standard (16:9)",
        strategy_note: str = ""
    ) -> str:
        """Builds a clean side-by-side visual comparison for 9:16 vs 16:9 reframing review."""
        abs_out = os.path.abspath(output_png)
        os.makedirs(os.path.dirname(abs_out), exist_ok=True)

        with Image.open(master_preview_png).convert("RGB") as img_m, Image.open(adapted_preview_png).convert("RGB") as img_a:
            target_h = 640
            mw = int(round(img_m.width * target_h / max(1, img_m.height)))
            aw = int(round(img_a.width * target_h / max(1, img_a.height)))

            m_res = img_m.resize((mw, target_h), Image.Resampling.LANCZOS)
            a_res = img_a.resize((aw, target_h), Image.Resampling.LANCZOS)

            pad = 32
            header_h = 84
            footer_h = 56
            total_w = mw + aw + pad * 3
            total_h = header_h + target_h + footer_h

            canvas = Image.new("RGB", (total_w, total_h), (12, 17, 28))
            draw = ImageDraw.Draw(canvas)

            font_h = _load_font(size=24, bold=True)
            font_s = _load_font(size=18, bold=False)

            canvas.paste(m_res, (pad, header_h))
            canvas.paste(a_res, (pad * 2 + mw, header_h))

            # Borders
            draw.rectangle([pad - 2, header_h - 2, pad + mw + 1, header_h + target_h + 1], outline=(100, 116, 139), width=2)
            draw.rectangle([pad * 2 + mw - 2, header_h - 2, pad * 2 + mw + aw + 1, header_h + target_h + 1], outline=(255, 215, 0), width=3)

            draw.text((pad + mw // 2, 42), master_label, fill=(226, 232, 240), anchor="mm", font=font_h)
            draw.text((pad * 2 + mw + aw // 2, 42), adapted_label, fill=(255, 215, 0), anchor="mm", font=font_h)

            if strategy_note:
                draw.text((total_w // 2, header_h + target_h + 28), strategy_note, fill=(148, 163, 184), anchor="mm", font=font_s)

            canvas.save(abs_out, "PNG")
        return abs_out

    def generate_contact_sheet(
        self,
        items: List[Dict[str, Any]],
        output_png: str,
        title: str = "Phase 4 Multi-Platform Export Comparison Contact Sheet"
    ) -> str:
        """
        Generates a unified contact sheet comparing Master and all exported platform videos.
        Each item dict should contain: label, preview_png, specs_line, status.
        """
        abs_out = os.path.abspath(output_png)
        os.makedirs(os.path.dirname(abs_out), exist_ok=True)
        if not items:
            raise ValueError("No items supplied for contact sheet.")

        tile_h = 460
        pad = 24
        header_h = 72
        caption_h = 76

        resized_tiles = []
        total_w = pad
        for item in items:
            with Image.open(item["preview_png"]).convert("RGB") as im:
                tw = int(round(im.width * tile_h / max(1, im.height)))
                resized = im.resize((tw, tile_h), Image.Resampling.LANCZOS)
                resized_tiles.append((item, resized, tw))
                total_w += tw + pad

        total_h = header_h + tile_h + caption_h + pad
        canvas = Image.new("RGB", (total_w, total_h), (10, 14, 24))
        draw = ImageDraw.Draw(canvas)

        font_title = _load_font(size=26, bold=True)
        font_label = _load_font(size=18, bold=True)
        font_meta = _load_font(size=14, bold=False)

        draw.text((total_w // 2, 36), title, fill=(255, 215, 0), anchor="mm", font=font_title)

        cur_x = pad
        for item, img_tile, tw in resized_tiles:
            canvas.paste(img_tile, (cur_x, header_h))
            status = item.get("status", "VALIDATED")
            border_col = (34, 197, 94) if "PASS" in status or "VALID" in status or status == "MASTER" else (239, 68, 68)
            draw.rectangle([cur_x - 2, header_h - 2, cur_x + tw + 1, header_h + tile_h + 1], outline=border_col, width=2)

            cx = cur_x + tw // 2
            draw.text((cx, header_h + tile_h + 20), item.get("label", ""), fill=(248, 250, 252), anchor="mm", font=font_label)
            draw.text((cx, header_h + tile_h + 44), item.get("specs_line", ""), fill=(148, 163, 184), anchor="mm", font=font_meta)
            draw.text((cx, header_h + tile_h + 64), f"Status: {status}", fill=border_col, anchor="mm", font=font_meta)

            cur_x += tw + pad

        canvas.save(abs_out, "PNG")
        return abs_out
