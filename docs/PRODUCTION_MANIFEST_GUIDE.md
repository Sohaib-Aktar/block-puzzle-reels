# Production Manifest Authoring Guide
**Social Media Video Production Studio**  
**Document:** `docs/PRODUCTION_MANIFEST_GUIDE.md`  
**Date:** 2026-11-17  
**Version:** 3.0.0  

---

## 1. Overview

The **Creative Editing Manifest** (`manifest.json`) is the configuration-driven source of truth for the Phase 3 FFmpeg production pipeline. It decouples creative direction and editing instructions from Python scripts, ensuring deterministic, reproducible, and auditable rendering across all 5 studio projects.

---

## 2. Complete Manifest Schema Specification

```json
{
  "project": "<project-slug>",
  "campaign": "<campaign-slug>",
  "content_id": "<unique-content-id>",
  "output_profile": "<profile-name>",
  "renderer": "ffmpeg",
  "allow_review_audio": false,
  "canvas": {
    "width": 1080,
    "height": 1920,
    "fps": 30.0,
    "duration_seconds": 15.0
  },
  "timeline": [
    {
      "scene_id": "scene_01",
      "asset_id": "VID_0DD488E3",
      "source_file": "optional/fallback/path.mp4",
      "source_in": 0.0,
      "source_out": 3.0,
      "duration": 3.0,
      "fit_mode": "contain",
      "overlays": [
        {
          "type": "badge",
          "title": "Main Headline Text",
          "subtitle": "Secondary Description",
          "position": "center",
          "position_y": 700,
          "start_time": 0.0,
          "end_time": 2.5,
          "style": "purple_gold_badge"
        }
      ]
    }
  ],
  "audio": {
    "music": {
      "asset_id": "AUDIO_753DE70D",
      "volume": 0.25,
      "start_time": 0.0,
      "fade_in": 0.4,
      "fade_out": 0.8
    },
    "voiceover": {
      "text": "Narrative speech synthesized via Windows SAPI5.",
      "volume": 1.0,
      "ducking": true,
      "duck_level_db": -18.0,
      "rate": 0
    },
    "sound_effects": [
      {
        "asset_id": "AUDIO_92744730",
        "timeline_start": 1.5,
        "volume": 0.8
      }
    ],
    "master_loudness_target": -14.0
  }
}
```

---

## 3. Field Definitions & Best Practices

### Top-Level Fields
| Field | Type | Required | Description |
|---|---|---|---|
| `project` | string | **Yes** | Target studio project: `block-puzzle-burst`, `expand-ezisales`. |
| `campaign` | string | **Yes** | Marketing campaign name (e.g. `30-day-challenge`, `quick-start-tutorials`). |
| `content_id` | string | **Yes** | Unique identifier (e.g. `BPB_DAY_04`, `ezisales-tut-01`). |
| `output_profile` | string | **Yes** | Video profile: `instagram_reel`, `youtube_short`, `facebook_reel`, `software_tutorial_vertical`, `product_demo_horizontal`. |
| `renderer` | string | No | Engine: `"ffmpeg"` (default) or `"remotion"`. |
| `allow_review_audio` | boolean | No | Set to `true` to permit `NEEDS_REVIEW` sample audio for internal test renders. Defaults to `false`. |

### Timeline & Scenes
- **`asset_id`**: Canonical Asset ID from `data/media_catalog.json` (e.g. `VID_0DD488E3`).
- **`source_in` / `source_out`**: In and out timestamps in seconds within the source footage. Must satisfy `0 <= source_in < source_out <= media_duration`.
- **`fit_mode`**:
  - `contain`: Preserves aspect ratio with letterboxing/pillarboxing (default).
  - `cover`: Fills canvas, cropping excess.
  - `stretch`: Stretches footage to canvas.
- **`overlays`**:
  - `type`: `"badge"` (rounded card) or `"pill"` (safe-area banner).
  - `position`: `"top"` (`y=220`), `"center"` (`y=700`), or `"bottom"` (`y=1550`).
  - `style`:
    - `purple_gold_badge`: Royal purple with gold border (Block Puzzle Burst).
    - `corporate_blue_badge`: Deep navy with electric blue border (Expand ERP).
    - `pill_badge`: High-contrast pill.

### Audio Specification
- **`music.asset_id`**: Canonical Asset ID from `data/audio_catalog.json`.
- **`voiceover`**:
  - `text`: Script synthesized offline via Windows SAPI5 System.Speech.
  - `ducking`: Automatically attenuates background music by `duck_level_db` (default -18 dB) while speech is active.
- **`sound_effects`**: List of SFX cues with `timeline_start` offsets.
- **`master_loudness_target`**: Broadcast EBU R128 integrated loudness target (default: `-14.0` LUFS).

---

## 4. Project Examples

### A. Block Puzzle Burst (`block-puzzle-burst`)
```json
{
  "project": "block-puzzle-burst",
  "campaign": "30-day-challenge",
  "content_id": "day-04-no-wifi-revision",
  "output_profile": "instagram_reel",
  "timeline": [
    {
      "scene_id": "scene_01_hook",
      "asset_id": "VID_0DD488E3",
      "source_in": 0.0,
      "source_out": 2.0,
      "overlays": [
        {
          "type": "badge",
          "title": "No WiFi? No problem.",
          "subtitle": "100% Offline Gameplay",
          "position_y": 700,
          "style": "purple_gold_badge"
        }
      ]
    }
  ],
  "audio": {
    "music": {"asset_id": "AUDIO_753DE70D", "volume": 0.25},
    "voiceover": {"text": "Play Block Puzzle Burst completely offline with zero lag!"}
  }
}
```

### B. Expand EziSales (`expand-ezisales`)
```json
{
  "project": "expand-ezisales",
  "campaign": "quick-start-tutorials",
  "content_id": "ezisales-tut-01-order-booking",
  "output_profile": "software_tutorial_vertical",
  "timeline": [
    {
      "scene_id": "scene_01_retailer",
      "source_file": "outputs/expand-ezisales/quick-start-tutorials/ezisales-tut-01-order-booking/final/software_tutorial_vertical.mp4",
      "source_in": 0.0,
      "source_out": 3.0,
      "overlays": [
        {
          "type": "badge",
          "title": "Expand eziSales SFA",
          "subtitle": "Step 1: Select Retailer",
          "position_y": 200,
          "style": "corporate_blue_badge"
        }
      ]
    }
  ],
  "audio": {
    "music": {"asset_id": "AUDIO_80A69D7B", "volume": 0.18},
    "voiceover": {"text": "Book field retail orders in under 30 seconds with Expand eziSales."}
  }
}
```
