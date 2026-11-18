# Intelligent Reframing & Platform Safe Zones Guide
**Studio:** Pyapiras Games  
**Document:** `docs/REFRAMING_AND_SAFE_ZONES.md`  
**Config Sources:** `scripts/reframing_engine.py`, `config/production/safe_zones.json`  
**Date:** 2026-11-18  

---

## 1. Supported Reframing Strategies

The Phase 4 reframing engine (`scripts/reframing_engine.py`) provides six configurable strategies:

| Strategy | Behavior | Crop Loss | Best Use Case | Manual Review Flag |
|---|---|---|---|---|
| `BLURRED_BACKGROUND` | Preserves 100% of original subject centered over a darkened, softly blurred (`boxblur=24:4`) full-bleed ambient copy of the video. | **0%** | **Block Puzzle Burst** 9:16 → 16:9 (preserves complete 10×10 board, score header, piece tray, and text with zero black bars). | No |
| `FIT_WITH_BACKGROUND` | Preserves 100% of original subject centered over a clean project-branded background color (`#070B14`, `#0A1428`, etc.). | **0%** | Same-aspect exports (9:16 → 9:16) and **ERP tutorials** (EziSales, Expand HR, WMS, POS) 9:16 → 16:9 where crisp readability around text/UI is critical. | No (same orientation / vertical→horizontal); Yes (horizontal→vertical) |
| `CENTER_CROP` | Scales to fill canvas and center-crops excess edges. | Variable | Only when edge content is confirmed expendable. | **Yes** when crop loss > 15% |
| `SMART_CROP` | Samples master video frame to compute active visual bounding box & saliency centroid, anchoring the crop around primary activity. | Variable | Wide lifestyle/camera footage where subject is off-center. | **Yes** when crop loss > 15% |
| `MANUAL_FOCAL_POINT` | Anchors crop around explicit normalized coordinates `--focal-point x,y` (`0.0` to `1.0`). | Variable | Director-guided crops targeting a specific screen region. | **Yes** when crop loss > 15% |
| `CUSTOM_LAYOUT` | Places scaled video at explicit pixel `(x, y, width, height)` over branded or blurred background. | **0%** | Custom split-screen or tutorial side-panel layouts. | Optional |

---

## 2. Project-Specific Content Protection Rules

- **Block Puzzle Burst (`block-puzzle-burst`):** Never crops the 10×10 grid, score/streak bar, or piece tray. Default 16:9 strategy is `BLURRED_BACKGROUND`.
- **ERP Projects (`expand-ezisales`, `expand-hr`, `wms`, `pos`):** Never aggressively crops forms, tables, or navigation buttons. Default 16:9 strategy is `FIT_WITH_BACKGROUND` with corporate dark navy backdrop for maximum screen legibility.

---

## 3. Provisional Safe-Zone Configuration (`config/production/safe_zones.json`)

All safe-zone values are stored externally in `config/production/safe_zones.json` and explicitly labeled **`PROVISIONAL`**:

| Profile | Canvas | Top Margin | Bottom Margin | Left Margin | Right Margin | Safe Content Box |
|---|---|---|---|---|---|---|
| `instagram_reels` | 1080×1920 | 220 px | 340 px | 60 px | 150 px | `x=60, y=220, w=870, h=1360` |
| `youtube_shorts` | 1080×1920 | 180 px | 380 px | 60 px | 160 px | `x=60, y=180, w=860, h=1360` |
| `facebook_reels` | 1080×1920 | 200 px | 360 px | 60 px | 150 px | `x=60, y=200, w=870, h=1360` |
| `youtube_standard` | 1920×1080 | 70 px | 130 px | 90 px | 90 px | `x=90, y=70, w=1740, h=880` |

### Visual Safe-Zone Previews
Every export automatically generates `previews/<profile>_safe_zone.png` overlaying:
- **Red/Amber translucent boxes:** Platform UI occlusion zones (header chrome, right Like/Comment/Share buttons, bottom caption/navigation/scrubber bars, watermark corner).
- **Green rectangle:** Primary safe content region.
- **Cyan rectangle:** Recommended CTA safe region.
