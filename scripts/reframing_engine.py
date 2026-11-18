"""
reframing_engine.py — Content-Aware Video Reframing & Layout Adaptation Engine
Implements 6 configurable adaptation strategies:
  1. CENTER_CROP
  2. SMART_CROP
  3. FIT_WITH_BACKGROUND
  4. BLURRED_BACKGROUND
  5. CUSTOM_LAYOUT
  6. MANUAL_FOCAL_POINT

Never silently produces a destructive crop on gameplay or ERP interfaces; flags
exports for manual review whenever critical content preservation cannot be guaranteed.
"""

import os
import sys
import tempfile
import subprocess
from enum import Enum
from typing import Dict, Any, Optional, Tuple
from PIL import Image, ImageStat

WORKSPACE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(WORKSPACE_ROOT, "scripts"))
from media_engine import get_ffmpeg_cmd


class ReframeStrategy(str, Enum):
    CENTER_CROP = "CENTER_CROP"
    SMART_CROP = "SMART_CROP"
    FIT_WITH_BACKGROUND = "FIT_WITH_BACKGROUND"
    BLURRED_BACKGROUND = "BLURRED_BACKGROUND"
    CUSTOM_LAYOUT = "CUSTOM_LAYOUT"
    MANUAL_FOCAL_POINT = "MANUAL_FOCAL_POINT"


ERP_PROJECTS = {"expand-ezisales", "expand-hr", "wms", "pos"}
GAMEPLAY_PROJECTS = {"block-puzzle-burst"}


class ReframingEngine:
    """Selects and builds FFmpeg filtergraphs for intelligent aspect-ratio adaptation."""

    def __init__(self, project_bg_colors: Optional[Dict[str, str]] = None):
        self.project_bg_colors = project_bg_colors or {
            "block-puzzle-burst": "#070B14",
            "expand-ezisales": "#0A1428",
            "expand-hr": "#0B192C",
            "wms": "#0F172A",
            "pos": "#111827",
            "default": "#0A0F1A",
        }

    def get_brand_bg_hex(self, project_slug: str) -> str:
        """Returns FFmpeg-compatible hex color (0xRRGGBB) for a project background."""
        raw = self.project_bg_colors.get(project_slug, self.project_bg_colors.get("default", "#0A0F1A"))
        return "0x" + raw.lstrip("#")

    def detect_active_content_box(
        self,
        video_path: str,
        sample_sec: float = 1.0
    ) -> Dict[str, Any]:
        """
        Samples a frame from the video and computes the active non-black bounding box
        and visual energy centroid in normalized coordinates [0.0, 1.0].
        """
        abs_in = os.path.abspath(video_path)
        tmp_png = None
        try:
            fd, tmp_png = tempfile.mkstemp(suffix=".png", prefix="reframe_sample_")
            os.close(fd)
            cmd = get_ffmpeg_cmd() + [
                "-y", "-v", "error",
                "-ss", f"{max(0.0, sample_sec):.2f}",
                "-i", abs_in,
                "-vframes", "1",
                tmp_png
            ]
            res = subprocess.run(cmd, capture_output=True, text=True)
            if res.returncode != 0 or not os.path.exists(tmp_png) or os.path.getsize(tmp_png) == 0:
                return {
                    "detected": False,
                    "bbox_norm": [0.0, 0.0, 1.0, 1.0],
                    "focal_norm": [0.5, 0.5],
                }

            with Image.open(tmp_png).convert("RGB") as img:
                w, h = img.size
                # Downsample for fast bounding-box & saliency computation
                small = img.resize((180, max(1, int(180 * h / max(1, w)))), Image.Resampling.BILINEAR)
                sw, sh = small.size
                pixels = small.load()

                min_x, min_y = sw, sh
                max_x, max_y = 0, 0
                sum_x, sum_y, weight_sum = 0.0, 0.0, 0.0

                for y in range(sh):
                    for x in range(sw):
                        r, g, b = pixels[x, y]
                        luma = 0.299 * r + 0.587 * g + 0.114 * b
                        if luma > 18:
                            if x < min_x:
                                min_x = x
                            if y < min_y:
                                min_y = y
                            if x > max_x:
                                max_x = x
                            if y > max_y:
                                max_y = y
                            # Higher weight for bright/saturated UI or gameplay elements
                            sat = max(r, g, b) - min(r, g, b)
                            weight = (luma / 255.0) + (sat / 255.0)
                            sum_x += x * weight
                            sum_y += y * weight
                            weight_sum += weight

                if max_x <= min_x or max_y <= min_y or weight_sum <= 0:
                    return {
                        "detected": False,
                        "bbox_norm": [0.0, 0.0, 1.0, 1.0],
                        "focal_norm": [0.5, 0.5],
                    }

                return {
                    "detected": True,
                    "bbox_norm": [
                        round(min_x / sw, 4),
                        round(min_y / sh, 4),
                        round((max_x + 1) / sw, 4),
                        round((max_y + 1) / sh, 4),
                    ],
                    "focal_norm": [
                        round((sum_x / weight_sum) / sw, 4),
                        round((sum_y / weight_sum) / sh, 4),
                    ],
                }
        finally:
            if tmp_png and os.path.exists(tmp_png):
                try:
                    os.remove(tmp_png)
                except OSError:
                    pass

    def recommend_strategy(
        self,
        src_width: int,
        src_height: int,
        target_width: int,
        target_height: int,
        project_slug: str = "default",
        requested_strategy: Optional[str] = None,
        focal_point: Optional[Tuple[float, float]] = None,
        custom_layout: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Determines the best reframing strategy based on aspect ratio delta and content domain.
        """
        src_ar = src_width / max(1, src_height)
        tgt_ar = target_width / max(1, target_height)
        ar_diff = abs(src_ar - tgt_ar)

        # Respect explicit manual overrides
        if custom_layout:
            return {
                "strategy": ReframeStrategy.CUSTOM_LAYOUT.value,
                "reason": "Explicit custom_layout coordinates supplied.",
                "requires_manual_review": False,
            }

        if focal_point is not None and not requested_strategy:
            return {
                "strategy": ReframeStrategy.MANUAL_FOCAL_POINT.value,
                "reason": f"Manual focal point ({focal_point[0]:.2f}, {focal_point[1]:.2f}) supplied.",
                "requires_manual_review": ar_diff > 0.25,
            }

        if requested_strategy:
            strat = ReframeStrategy(requested_strategy.upper())
            destructive_crop = strat in (
                ReframeStrategy.CENTER_CROP,
                ReframeStrategy.SMART_CROP,
                ReframeStrategy.MANUAL_FOCAL_POINT,
            ) and ar_diff > 0.25
            return {
                "strategy": strat.value,
                "reason": f"User-requested strategy '{strat.value}'.",
                "requires_manual_review": destructive_crop,
                "review_reason": (
                    f"Aspect ratio change ({src_width}x{src_height} -> {target_width}x{target_height}) "
                    f"with cropping strategy '{strat.value}' may discard gameplay or UI elements."
                ) if destructive_crop else None,
            }

        # Same or nearly identical aspect ratio (e.g., 9:16 -> 9:16)
        if ar_diff <= 0.03:
            return {
                "strategy": ReframeStrategy.FIT_WITH_BACKGROUND.value,
                "reason": "Source and target aspect ratios match; preserving 100% of original framing.",
                "requires_manual_review": False,
            }

        # Vertical 9:16 -> Horizontal 16:9
        if src_ar < 1.0 and tgt_ar > 1.0:
            if project_slug in ERP_PROJECTS:
                return {
                    "strategy": ReframeStrategy.FIT_WITH_BACKGROUND.value,
                    "reason": (
                        f"ERP/software project '{project_slug}' adapted from vertical to 16:9 using "
                        "clean branded backdrop to preserve 100% of readable UI controls without distracting motion blur."
                    ),
                    "requires_manual_review": False,
                }
            return {
                "strategy": ReframeStrategy.BLURRED_BACKGROUND.value,
                "reason": (
                    f"Vertical gameplay/social master ({src_width}x{src_height}) adapted to 16:9 ({target_width}x{target_height}) "
                    "using darkened blurred ambient fill to preserve 100% of game board, score, and overlays without black bars."
                ),
                "requires_manual_review": False,
            }

        # Horizontal 16:9 -> Vertical 9:16
        if src_ar > 1.0 and tgt_ar < 1.0:
            if project_slug in ERP_PROJECTS:
                return {
                    "strategy": ReframeStrategy.FIT_WITH_BACKGROUND.value,
                    "reason": "Horizontal ERP recording preserved completely on vertical canvas to avoid cropping interface controls.",
                    "requires_manual_review": True,
                    "review_reason": "Horizontal ERP recording scaled down to fit vertical frame; verify small text readability.",
                }
            return {
                "strategy": ReframeStrategy.BLURRED_BACKGROUND.value,
                "reason": "Horizontal master adapted to vertical canvas with blurred ambient backdrop to preserve full frame.",
                "requires_manual_review": True,
                "review_reason": "Horizontal-to-vertical adaptation requires visual check for subject size and safe-zone alignment.",
            }

        return {
            "strategy": ReframeStrategy.FIT_WITH_BACKGROUND.value,
            "reason": "Default non-destructive aspect-preserving fit.",
            "requires_manual_review": False,
        }

    def build_filter_plan(
        self,
        video_path: str,
        src_width: int,
        src_height: int,
        target_width: int,
        target_height: int,
        target_fps: float,
        project_slug: str = "default",
        strategy: Optional[str] = None,
        focal_point: Optional[Tuple[float, float]] = None,
        custom_layout: Optional[Dict[str, Any]] = None,
        sample_sec: float = 1.0,
    ) -> Dict[str, Any]:
        """
        Produces an FFmpeg filtergraph plan (using either -vf or -filter_complex)
        plus framing metadata and manual-review flags.
        """
        rec = self.recommend_strategy(
            src_width=src_width,
            src_height=src_height,
            target_width=target_width,
            target_height=target_height,
            project_slug=project_slug,
            requested_strategy=strategy,
            focal_point=focal_point,
            custom_layout=custom_layout,
        )
        chosen = ReframeStrategy(rec["strategy"])
        bg_hex = self.get_brand_bg_hex(project_slug)

        requires_manual_review = bool(rec.get("requires_manual_review", False))
        review_reasons = [rec["review_reason"]] if rec.get("review_reason") else []
        content_analysis = None
        crop_loss_pct = 0.0

        # Compute scaled cover dimensions for cropping strategies
        src_ar = src_width / max(1, src_height)
        tgt_ar = target_width / max(1, target_height)

        if chosen == ReframeStrategy.FIT_WITH_BACKGROUND:
            vf = (
                f"scale=w={target_width}:h={target_height}:force_original_aspect_ratio=decrease,"
                f"pad=w={target_width}:h={target_height}:x=(ow-iw)/2:y=(oh-ih)/2:color={bg_hex},"
                f"setsar=1,fps=fps={target_fps},format=yuv420p"
            )
            return {
                "strategy": chosen.value,
                "reason": rec["reason"],
                "uses_filter_complex": False,
                "vf": vf,
                "filter_complex": None,
                "video_map": "0:v:0",
                "crop_loss_percent": 0.0,
                "focal_point": [0.5, 0.5],
                "requires_manual_review": requires_manual_review,
                "review_reasons": review_reasons,
                "background_color": bg_hex,
            }

        if chosen == ReframeStrategy.BLURRED_BACKGROUND:
            # Split source into blurred ambient fill + crisp full-frame centered foreground
            # Compute crisp foreground dimensions preserving aspect ratio
            if src_ar < tgt_ar:
                fg_h = target_height
                fg_w = int(round(fg_h * src_ar))
                fg_w -= fg_w % 2
            else:
                fg_w = target_width
                fg_h = int(round(fg_w / max(0.01, src_ar)))
                fg_h -= fg_h % 2

            fc = (
                f"[0:v]split=2[bg_in][fg_in];"
                f"[bg_in]scale=w={target_width}:h={target_height}:force_original_aspect_ratio=increase,"
                f"crop={target_width}:{target_height},boxblur=24:4,eq=brightness=-0.20:saturation=1.08,setsar=1[bg];"
                f"[fg_in]scale=w={fg_w}:h={fg_h},setsar=1[fg];"
                f"[bg][fg]overlay=x=(W-w)/2:y=(H-h)/2,fps=fps={target_fps},format=yuv420p[v_reframed]"
            )
            return {
                "strategy": chosen.value,
                "reason": rec["reason"],
                "uses_filter_complex": True,
                "vf": None,
                "filter_complex": fc,
                "video_map": "[v_reframed]",
                "crop_loss_percent": 0.0,
                "foreground_box": {
                    "x": (target_width - fg_w) // 2,
                    "y": (target_height - fg_h) // 2,
                    "width": fg_w,
                    "height": fg_h,
                },
                "focal_point": [0.5, 0.5],
                "requires_manual_review": requires_manual_review,
                "review_reasons": review_reasons,
            }

        if chosen == ReframeStrategy.CUSTOM_LAYOUT:
            layout = custom_layout or {}
            fg_w = int(layout.get("width", target_width))
            fg_h = int(layout.get("height", target_height))
            fg_x = int(layout.get("x", (target_width - fg_w) // 2))
            fg_y = int(layout.get("y", (target_height - fg_h) // 2))
            use_blur_bg = bool(layout.get("blurred_background", False))

            if use_blur_bg:
                fc = (
                    f"[0:v]split=2[bg_in][fg_in];"
                    f"[bg_in]scale=w={target_width}:h={target_height}:force_original_aspect_ratio=increase,"
                    f"crop={target_width}:{target_height},boxblur=24:4,eq=brightness=-0.22,setsar=1[bg];"
                    f"[fg_in]scale=w={fg_w}:h={fg_h}:force_original_aspect_ratio=decrease,setsar=1[fg];"
                    f"[bg][fg]overlay=x={fg_x}:y={fg_y},fps=fps={target_fps},format=yuv420p[v_reframed]"
                )
                return {
                    "strategy": chosen.value,
                    "reason": rec["reason"],
                    "uses_filter_complex": True,
                    "vf": None,
                    "filter_complex": fc,
                    "video_map": "[v_reframed]",
                    "crop_loss_percent": 0.0,
                    "foreground_box": {"x": fg_x, "y": fg_y, "width": fg_w, "height": fg_h},
                    "focal_point": [0.5, 0.5],
                    "requires_manual_review": requires_manual_review,
                    "review_reasons": review_reasons,
                }
            else:
                vf = (
                    f"scale=w={fg_w}:h={fg_h}:force_original_aspect_ratio=decrease,"
                    f"pad=w={target_width}:h={target_height}:x={fg_x}:y={fg_y}:color={bg_hex},"
                    f"setsar=1,fps=fps={target_fps},format=yuv420p"
                )
                return {
                    "strategy": chosen.value,
                    "reason": rec["reason"],
                    "uses_filter_complex": False,
                    "vf": vf,
                    "filter_complex": None,
                    "video_map": "0:v:0",
                    "crop_loss_percent": 0.0,
                    "foreground_box": {"x": fg_x, "y": fg_y, "width": fg_w, "height": fg_h},
                    "focal_point": [0.5, 0.5],
                    "requires_manual_review": requires_manual_review,
                    "review_reasons": review_reasons,
                }

        # Cropping strategies: CENTER_CROP, SMART_CROP, MANUAL_FOCAL_POINT
        if chosen == ReframeStrategy.SMART_CROP:
            content_analysis = self.detect_active_content_box(video_path, sample_sec=sample_sec)
            fx, fy = content_analysis["focal_norm"]
        elif chosen == ReframeStrategy.MANUAL_FOCAL_POINT:
            if focal_point is None:
                fx, fy = 0.5, 0.5
            else:
                fx = max(0.0, min(1.0, float(focal_point[0])))
                fy = max(0.0, min(1.0, float(focal_point[1])))
        else:  # CENTER_CROP
            fx, fy = 0.5, 0.5

        # Compute cover-scaled dimensions
        if src_ar > tgt_ar:
            scaled_h = target_height
            scaled_w = int(round(scaled_h * src_ar))
            scaled_w += scaled_w % 2
        else:
            scaled_w = target_width
            scaled_h = int(round(scaled_w / max(0.01, src_ar)))
            scaled_h += scaled_h % 2

        crop_loss_pct = round(
            max(0.0, (1.0 - (target_width * target_height) / max(1, scaled_w * scaled_h)) * 100.0),
            2,
        )

        # Compute clamped crop origin around focal point
        crop_x = int(round(fx * scaled_w - target_width / 2.0))
        crop_y = int(round(fy * scaled_h - target_height / 2.0))
        crop_x = max(0, min(scaled_w - target_width, crop_x))
        crop_y = max(0, min(scaled_h - target_height, crop_y))

        if crop_loss_pct > 15.0:
            requires_manual_review = True
            review_reasons.append(
                f"Cropping strategy '{chosen.value}' discards {crop_loss_pct:.1f}% of source frame; "
                "verify gameplay board, ERP UI, and overlays are not cut off."
            )

        vf = (
            f"scale=w={scaled_w}:h={scaled_h},"
            f"crop=w={target_width}:h={target_height}:x={crop_x}:y={crop_y},"
            f"setsar=1,fps=fps={target_fps},format=yuv420p"
        )

        return {
            "strategy": chosen.value,
            "reason": rec["reason"],
            "uses_filter_complex": False,
            "vf": vf,
            "filter_complex": None,
            "video_map": "0:v:0",
            "crop_loss_percent": crop_loss_pct,
            "crop_box": {"x": crop_x, "y": crop_y, "width": target_width, "height": target_height, "scaled_w": scaled_w, "scaled_h": scaled_h},
            "focal_point": [round(fx, 4), round(fy, 4)],
            "content_analysis": content_analysis,
            "requires_manual_review": requires_manual_review,
            "review_reasons": review_reasons,
        }
