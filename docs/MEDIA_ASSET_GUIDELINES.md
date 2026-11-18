# Media Asset Guidelines & Production Standards

**Studio:** Social Media Video Production Studio  
**Date:** 2026-11-16  
**Status:** Active Production Standard  
**Workspace Root:** `Social Media Video Production Studio`

---

## 1. Directory Structure & Project Hierarchy

All media assets must be organized within `source_assets/` under their respective project slug and functional media subfolder. Loose files placed in workspace roots or flat input directories are prohibited.

```
source_assets/
├── <project-slug>/
│   ├── gameplay/           # In-game footage and device screen recordings
│   ├── screenshots/        # Static UI and gameplay screenshots
│   ├── logos/              # Transparent badges, watermarks, and app icons
│   ├── music/              # Background soundtracks and loopable music beds
│   ├── sound-effects/      # Gameplay, interface, and punctuation SFX
│   ├── voiceovers/         # Spoken narration and dialogue recordings
│   ├── lifestyle-footage/  # Contextual B-roll, keyframes, and relatable photography
│   └── other/              # Uncategorized reference material
```

### Supported Project Slugs:
- `block-puzzle-burst` (Mobile casual puzzle game)
- `expand-ezisales` (B2B mobile sales order booking application)

---

## 2. Naming Conventions

All assets must use clean, lowercase, hyphen-or-underscore-separated filenames with functional type prefixes:

| Category | Prefix | Examples |
|---|---|---|
| **Gameplay Video** | `gameplay_` / `rec_` | `gameplay_airplane_mode_15s.mp4`, `recording_board_clear.mp4` |
| **Screenshot** | `screen_` / `sample_` | `screen_combo_multiplier.jpg`, `sample_offline_indicator.jpg` |
| **Logo / Icon** | `logo_` / `icon_` | `logo_block_puzzle_transparent.png`, `icon_pyapiras_games.png` |
| **Background Music** | `bgm_` | `bgm_upbeat_puzzle_bounce.wav`, `bgm_calm_corporate_trust.wav` |
| **Sound Effect** | `sfx_` | `sfx_block_place.wav`, `sfx_line_clear.wav`, `sfx_combo_burst.wav` |
| **Voiceover** | `vo_` | `vo_scene01_hook.wav`, `vo_scene02_demo.wav`, `vo_day04_complete.wav` |
| **Lifestyle Keyframe** | `lifestyle_` / `scene_` | `lifestyle_office_fatigue.jpg`, `scene_03_home_sofa.jpg` |

---

## 3. Video Specifications & Technical Standards

### 3.1 Dimensions & Aspect Ratios
- **Vertical Reels / Shorts / Stories (Primary):**
  - Standard: `1080 × 1920` (9:16 portrait)
  - Native Device Capture Support: `720 × 1600` (9:20 portrait; pillarboxed or scaled to 9:16 canvas)
- **Horizontal Tutorials / Longform:**
  - Standard: `1920 × 1080` (16:9 landscape)
- **Feed Square (Legacy / Adaptations):**
  - Standard: `1080 × 1080` (1:1 square)

### 3.2 Frame Rate & Timebase
- **Constant Frame Rate (CFR) Required:** Exact `30.0 fps` or `60.0 fps`.
- **Warning on Variable Frame Rate (VFR):** Screen recordings from mobile phones frequently use VFR, which causes audio de-synchronization during Remotion or FFmpeg concatenation.
- **Transcoding VFR to CFR:**
  ```powershell
  npx remotion ffmpeg -i input_vfr.mp4 -vf "fps=30" -vsync cfr -c:v libx264 -preset fast -crf 18 -c:a aac -b:a 192k output_cfr30.mp4
  ```

### 3.3 Video & Audio Codecs
- **Video Codec:** H.264 / AVC, High Profile, Level 4.1 or 4.2.
- **Pixel Format:** `yuv420p` (strict requirement for cross-platform Instagram/Facebook compatibility).
- **Audio Codec:** AAC-LC (Stereo or Mono), sample rate 44.1 kHz or 48.0 kHz, bit rate >= 160 kbps.

---

## 4. Image Specifications & Transparency Standards

### 4.1 Formats & Color Modes
- **Logos & Badges:** PNG with 8-bit Alpha Channel (`RGBA` or `P` mode with transparency). Must have transparent background to overlay on gameplay footage without solid borders.
- **Screenshots & Lifestyle Keyframes:** JPEG (quality 90+) or PNG (24-bit RGB).
- **Color Space:** Standard sRGB. CMYK images are strictly prohibited as they cause FFmpeg rendering crashes.

### 4.2 Minimum Resolutions
- **Logos / App Icons:** Minimum `512 × 512` px; recommended `1080 × 1080` px.
- **Keyframes / B-Roll:** Minimum `720 × 1280` px; recommended `1080 × 1920` px.

---

## 5. Intake & Ingestion Procedures

When introducing new raw footage or creative assets into the studio:

### Step 1: Place Asset in Canonical Folder
Copy raw file into the appropriate directory under `source_assets/<project>/<category>/`.

### Step 2: Run Unified Scan
Execute the media intake scan:
```powershell
python scripts/media_intake.py scan --project <project-slug>
```
This automatically:
1. Detects new files.
2. Checks for byte-level duplicates using SHA-256.
3. Extracts visual and acoustic metadata.
4. Updates `data/media_catalog.json` and `data/audio_catalog.json`.

### Step 3: Inspect the Ingested Asset
Verify technical parameters using:
```powershell
python scripts/media_intake.py analyze source_assets/<project>/<category>/<filename>
```

### Step 4: Check Duplicates
Verify no redundant storage was created:
```powershell
python scripts/media_intake.py check-duplicates
```
