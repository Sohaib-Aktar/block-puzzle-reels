"""
overlay_engine.py — Text and Graphic Overlay Engine for FFmpeg Pipeline
Generates broadcast-grade on-screen text, badges, and safe-zone overlays.
Supports dynamic PIL badge rendering (high aesthetic fidelity) and native drawtext filters.
"""

import os
import sys
from typing import Dict, Any, List, Optional, Tuple
from PIL import Image, ImageDraw, ImageFont

WORKSPACE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_system_font(bold: bool = True, size: int = 48) -> ImageFont.ImageFont:
    """Safely retrieves standard Windows fonts with cross-platform fallback."""
    font_candidates = [
        r"C:\Windows\Fonts\arialbd.ttf" if bold else r"C:\Windows\Fonts\arial.ttf",
        r"C:\Windows\Fonts\segoeuib.ttf" if bold else r"C:\Windows\Fonts\segoeui.ttf",
        r"C:\Windows\Fonts\calibrib.ttf" if bold else r"C:\Windows\Fonts\calibri.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    ]
    for font_path in font_candidates:
        if os.path.exists(font_path):
            try:
                return ImageFont.truetype(font_path, size)
            except Exception:
                continue
    return ImageFont.load_default()


class OverlayEngine:
    """Builds visual graphic overlays, cards, badges, and text treatments."""

    def __init__(self, canvas_width: int = 1080, canvas_height: int = 1920):
        self.canvas_width = canvas_width
        self.canvas_height = canvas_height

    def render_badge_card(
        self,
        output_png_path: str,
        title: str,
        subtitle: Optional[str] = None,
        style: str = "purple_gold_badge",
        badge_width: Optional[int] = None
    ) -> str:
        """
        Renders a photorealistic, high-contrast UI badge card with rounded corners,
        gold/accent border, drop shadow, and typography.
        """
        abs_out = os.path.abspath(output_png_path)
        os.makedirs(os.path.dirname(abs_out), exist_ok=True)

        # Style themes
        themes = {
            "purple_gold_badge": {
                "bg_start": (88, 28, 135, 245),
                "bg_end": (30, 15, 60, 245),
                "border_color": (255, 215, 0, 255),
                "border_width": 4,
                "title_color": (255, 255, 255, 255),
                "title_size": 52,
                "sub_color": (255, 215, 0, 255),
                "sub_size": 30,
                "corner_radius": 44
            },
            "corporate_blue_badge": {
                "bg_start": (15, 30, 70, 245),
                "bg_end": (5, 12, 35, 245),
                "border_color": (59, 130, 246, 255),
                "border_width": 3,
                "title_color": (255, 255, 255, 255),
                "title_size": 48,
                "sub_color": (147, 197, 253, 255),
                "sub_size": 28,
                "corner_radius": 36
            },
            "pill_badge": {
                "bg_start": (123, 47, 190, 245),
                "bg_end": (74, 26, 122, 245),
                "border_color": (255, 215, 0, 255),
                "border_width": 3,
                "title_color": (255, 255, 255, 255),
                "title_size": 40,
                "sub_color": (255, 255, 255, 220),
                "sub_size": 26,
                "corner_radius": 50
            }
        }
        theme = themes.get(style, themes["purple_gold_badge"])

        font_title = get_system_font(bold=True, size=theme["title_size"])
        font_sub = get_system_font(bold=True, size=theme["sub_size"])

        # Measure text sizes
        dummy_img = Image.new("RGBA", (1, 1))
        draw_dummy = ImageDraw.Draw(dummy_img)

        bbox_title = draw_dummy.textbbox((0, 0), title, font=font_title)
        title_w = bbox_title[2] - bbox_title[0]
        title_h = bbox_title[3] - bbox_title[1]

        sub_w, sub_h = 0, 0
        if subtitle:
            bbox_sub = draw_dummy.textbbox((0, 0), subtitle, font=font_sub)
            sub_w = bbox_sub[2] - bbox_sub[0]
            sub_h = bbox_sub[3] - bbox_sub[1]

        # Calculate badge dimensions
        pad_x = 54
        pad_y = 24
        content_w = max(title_w, sub_w)
        badge_w = badge_width or min(content_w + pad_x * 2, self.canvas_width - 80)
        badge_h = pad_y * 2 + title_h + (sub_h + 10 if subtitle else 0)

        # Create image with transparent padding for drop shadow
        shadow_pad = 20
        total_w = badge_w + shadow_pad * 2
        total_h = badge_h + shadow_pad * 2
        card = Image.new("RGBA", (total_w, total_h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(card)

        # Draw drop shadow
        shadow_rect = [
            shadow_pad + 4,
            shadow_pad + 8,
            shadow_pad + badge_w + 4,
            shadow_pad + badge_h + 8
        ]
        draw.rounded_rectangle(
            shadow_rect,
            radius=theme["corner_radius"],
            fill=(0, 0, 0, 160)
        )

        # Draw badge body
        badge_rect = [
            shadow_pad,
            shadow_pad,
            shadow_pad + badge_w,
            shadow_pad + badge_h
        ]
        draw.rounded_rectangle(
            badge_rect,
            radius=theme["corner_radius"],
            fill=theme["bg_start"],
            outline=theme["border_color"],
            width=theme["border_width"]
        )

        # Draw text with drop shadow
        center_x = shadow_pad + badge_w // 2
        title_y = shadow_pad + pad_y + title_h // 2

        # Title shadow
        draw.text(
            (center_x + 2, title_y + 2),
            title,
            fill=(0, 0, 0, 220),
            font=font_title,
            anchor="mm"
        )
        # Title text
        draw.text(
            (center_x, title_y),
            title,
            fill=theme["title_color"],
            font=font_title,
            anchor="mm"
        )

        # Subtitle
        if subtitle:
            sub_y = title_y + title_h // 2 + 10 + sub_h // 2
            # Subtitle shadow
            draw.text(
                (center_x + 2, sub_y + 2),
                subtitle,
                fill=(0, 0, 0, 220),
                font=font_sub,
                anchor="mm"
            )
            # Subtitle text
            draw.text(
                (center_x, sub_y),
                subtitle,
                fill=theme["sub_color"],
                font=font_sub,
                anchor="mm"
            )

        card.save(abs_out, "PNG")
        return abs_out

    def build_overlay_filters(
        self,
        overlays: List[Dict[str, Any]],
        intermediate_dir: str,
        scene_start_time: float = 0.0
    ) -> Tuple[List[str], List[str]]:
        """
        Builds FFmpeg filtergraph inputs and overlay filter chains for a scene.
        Returns: (input_args, filtergraph_strings)
        """
        extra_inputs: List[str] = []
        filter_chains: List[str] = []

        for idx, ov in enumerate(overlays):
            ov_type = ov.get("type", "badge")
            start_t = float(ov.get("start_time", 0.0))
            end_t = float(ov.get("end_time", 999.0))
            pos_y = ov.get("position_y")

            # Determine position
            if pos_y is None:
                pos = ov.get("position", "center")
                if pos == "top":
                    pos_y = 220
                elif pos == "bottom":
                    pos_y = 1550
                else:  # center
                    pos_y = 700

            title = ov.get("title") or ov.get("text") or ""
            subtitle = ov.get("subtitle")
            style = ov.get("style", "purple_gold_badge")

            badge_png = os.path.join(intermediate_dir, f"overlay_badge_{idx}_{start_t}.png")
            self.render_badge_card(
                output_png_path=badge_png,
                title=title,
                subtitle=subtitle,
                style=style
            )

            # Get generated badge dimensions
            with Image.open(badge_png) as bimg:
                bw, bh = bimg.size

            pos_x = (self.canvas_width - bw) // 2
            input_idx = len(extra_inputs) // 2 + 1

            extra_inputs.extend(["-i", badge_png])
            # Enable condition
            enable_expr = f"between(t,{start_t},{end_t})"
            filter_chains.append(
                f"[{input_idx}:v]format=rgba[ov{idx}];[base][ov{idx}]overlay={pos_x}:{pos_y}:enable='{enable_expr}'"
            )

        return extra_inputs, filter_chains
