# Phase 2 Technical Implementation Document: Media Intake & Audio Intelligence System

**Studio:** Pyapiras Games  
**Date:** 2026-11-16  
**Status:** Completed & 100% Verified  
**Workspace:** `C:\Users\Dell\Downloads\video gen`

---

## 1. System Overview

Phase 2 transitions the Pyapiras Games Social Media Video Studio from a rendering framework into an intelligent, content-aware media intake and acoustic intelligence system. It establishes:
1. **Canonical Asset Architecture:** A standardized multi-project directory structure (`source_assets/`) across all active projects.
2. **Deterministic Deduplication:** SHA-256 content hashing that detects identical assets across raw and public folders, preventing disk bloat while maintaining backward compatibility with Remotion builds.
3. **Visual Media Intelligence:** Automated extraction of video metrics (duration, resolution, aspect ratio, orientation, frame rate, container codecs) and image analysis (dimensions, color mode, alpha transparency, category classification).
4. **Deep Acoustic Engine:** Waveform-level audio analysis extracting Peak dBFS, RMS dBFS, digital clipping, silence ratios, EBU R128 broadcast loudness (Integrated LUFS, True Peak dBTP, Loudness Range LU), and vectorized envelope autocorrelation for BPM estimation.
5. **Explainable Audio Recommendation Engine:** Multi-factor scoring matching project brand identity, emotional tone/mood, pacing, and reel durations with human-readable rationale and multi-scene timeline breakdown.
6. **Unified Media Intake CLI:** A single entrypoint (`scripts/media_intake.py`) for scanning, analyzing, searching, cataloging, and duplicate tracking.

---

## 2. Directory Taxonomy & Asset Hierarchy

Assets are organized canonically under `source_assets/` segmented by project slug and functional category:

```
source_assets/
├── block-puzzle-burst/
│   ├── gameplay/           # Original device screen recordings (CFR 30/60 fps)
│   ├── screenshots/        # Verified in-game UI captures (portrait 9:16)
│   ├── logos/              # Transparent game badges and studio icons (PNG RGBA)
│   ├── music/              # Casual gaming, upbeat, and relaxing soundtracks
│   ├── sound-effects/      # Block placements, line clears, combo bursts, UI pops
│   ├── voiceovers/         # Scene-segmented spoken narration (.wav)
│   └── lifestyle-footage/  # Relatable B-roll keyframes (office, commute, sofa, unlock)
├── expand-ezisales/
│   ├── screenshots/
│   ├── screen-recordings/
│   ├── logos/
│   ├── music/              # Modern corporate tech background tracks
│   ├── sound-effects/      # Notification chimes, button clicks
│   └── voiceovers/
├── expand-hr/
│   ├── screenshots/
│   ├── screen-recordings/
│   ├── logos/
│   ├── music/              # Calm, corporate trust acoustic tracks
│   └── voiceovers/
├── wms/
│   ├── screenshots/
│   ├── screen-recordings/
│   └── music/              # Operational efficiency background rhythm
└── pos/
    ├── screenshots/
    ├── screen-recordings/
    └── music/              # Retail energetic groove soundtrack
```

---

## 3. Core Subsystems & Components

### 3.1 Non-Destructive Asset Migration Engine (`scripts/asset_migrator.py`)
- Discovers existing assets scattered across legacy folders (`Raw_input_files/`, `my-video/public/`, `generated_outputs/`).
- Computes SHA-256 content hashes to identify identical files regardless of filename.
- Migrates candidates into canonical `source_assets/` directories non-destructively (source files remain intact).
- Supports `--dry-run` for previewing file moves and `--project` for targeted migration.
- Writes full migration logs to `data/migration_log.json`.

### 3.2 Visual Footage & Image Intelligence (`scripts/footage_analyzer.py`)
- **Video Inspection (`inspect_video_asset`)**:
  - Uses FFprobe to inspect stream width, height, duration, frame rate, pix_fmt, video codec (`h264`, `hevc`), and audio codec (`aac`, `pcm`).
  - Classifies aspect ratio (`9:16`, `16:9`, `1:1`, `4:5`) and orientation (`portrait`, `landscape`, `square`).
  - Detects key verified gameplay moments (board filling, combos, tension arcs) without fabricating false claims.
- **Image Inspection (`inspect_image_asset`)**:
  - Leverages PIL and FFprobe to detect image dimensions, format (`png`, `jpeg`, `webp`), color mode (`RGB`, `RGBA`, `P`), and alpha channel transparency.
  - Classifies images into `logo_badge`, `gameplay_screenshot`, `ui_screenshot`, or `lifestyle_keyframe`.
- **Media Catalog Builder (`build_media_catalog`)**:
  - Scans `source_assets/` and writes `data/media_catalog.json` indexing all visual media.

### 3.3 Acoustic & Loudness Intelligence Engine (`scripts/audio_analyzer.py`)
- **Container Stream Parsing (`get_audio_stream_metadata`)**:
  - Extracts duration, sample rate (Hz), channel count, bit rate, and audio codec.
- **EBU R128 Broadcast Loudness (`measure_ebur128_loudness`)**:
  - Executes FFmpeg `loudnorm=print_format=json` dual-pass measurement.
  - Extracts Integrated Loudness (`integrated_lufs`), True Peak (`true_peak_dbtp`), and Loudness Range (`loudness_range_lu`).
- **Waveform Acoustic Processing (`analyze_acoustic_properties`)**:
  - Loads 16-bit PCM samples via native Python `wave` module (fast path) or FFmpeg temporary decode.
  - Computes exact sample-accurate Peak dBFS: $20 \log_{10}(\max |s| / 32768)$.
  - Computes RMS dBFS: $20 \log_{10}(\sqrt{\frac{1}{N} \sum s^2} / 32768)$.
  - Detects digital clipping (samples hitting $\pm 32767$).
  - Calculates silence ratio (frames below $-45\text{ dBFS}$).
- **Vectorized Tempo & Rhythm Autocorrelation**:
  - Uses `np.lib.stride_tricks.sliding_window_view` to extract a 100 Hz energy envelope.
  - Applies normalized autocorrelation across lag intervals corresponding to 60–180 BPM:
    $$r(k) = \frac{\sum (e_t - \bar{e})(e_{t+k} - \bar{e})}{\sum (e_t - \bar{e})^2}$$
  - Identifies peak tempo and calculates confidence metric based on prominence over baseline.
- **Mood & Structure Categorization (`determine_mood_and_structure`)**:
  - Combines acoustic energy, tempo, silence ratios, and path semantics to assign emotional mood tags (e.g., `energetic`, `playful`, `casual_gaming`, `corporate`, `trustworthy`).
  - Generates 3-part timeline structural segmentation (`intro`, `main_body`, `outro_resolve`).
- **Licensing Audit**:
  - Assigns strict clearance statuses (`VERIFIED_COMMERCIAL_USE`, `NEEDS_REVIEW`, `RESTRICTED`, `UNKNOWN`).

### 3.4 Audio Recommendation Engine (`scripts/audio_recommender.py`)
- Multi-dimensional scoring (0–100 points):
  - **Project Affinity (0–30 pts):** Direct brand association and avoidance of banned tones.
  - **Mood & Tone (0–35 pts):** Intersection ratio between target mood query and acoustic tags.
  - **Energy & BPM (0–15 pts):** Tempo alignment with project target BPM range.
  - **Duration Suitability (0–20 pts):** Proximity to reel target duration (exact match, short loopable, or cuttable bed).
- Multi-Scene Planning:
  - Dynamically synthesizes a 3-act marketing structure (Hook, Core Demo, CTA Outro) with volume ducking instructions (-18 dB under voiceover).
- Licensing Gatekeeper:
  - Strictly enforces `allow_unverified_licenses=False` for production publishing, blocking unvetted tracks and attaching warning flags when permissive mode is requested.

---

## 4. CLI Reference (`scripts/media_intake.py`)

| Command | Arguments | Description |
|---|---|---|
| `scan` | `[--project <slug>]` | Discovers files, syncs `source_assets/`, rebuilds `media_catalog.json` and `audio_catalog.json`. |
| `analyze` | `<file_path>` | Performs deep structural, visual, or acoustic analysis on any single asset. |
| `catalog` | `[--type video\|image\|audio]` `[--project <slug>]` | Displays clean formatted summary tables of registered assets. |
| `search` | `--query <term>` | Performs full-text search across visual metadata, acoustic metrics, and mood tags. |
| `check-duplicates` | *(none)* | Identifies byte-for-byte duplicate files via SHA-256 and calculates wasted storage. |
| `recommend-audio` | `--project <slug>` `[--mood <tag>]` `[--duration <sec>]` | Recommends top matching soundtracks and generates multi-scene audio plans. |

---

## 5. Catalog Schema Definitions

### 5.1 Visual Media Catalog (`data/media_catalog.json`)
```json
{
  "asset_id": "VID_2B4C0018",
  "original_filename": "recording_1.mp4",
  "file_location": "source_assets/block-puzzle-burst/gameplay/recording_1.mp4",
  "project": "block-puzzle-burst",
  "media_category": "gameplay",
  "file_type": "video",
  "file_size_bytes": 30385860,
  "duration_seconds": 169.52,
  "resolution": "720x1600",
  "width": 720,
  "height": 1600,
  "fps": 60.0,
  "aspect_ratio": "9:16",
  "orientation": "portrait",
  "video_codec": "h264",
  "audio_codec": "aac",
  "sha256": "2b4c0018a41e163f97126a4ade5c4ff58fe6dd56635cea7dd3d6b9ee1ead634c",
  "is_duplicate": false,
  "duplicate_of_asset_id": null,
  "verified_moments": [ ... ]
}
```
*Note on Duplicate Records:* Duplicate file instances receive unique IDs (e.g. `VID_2B4C0018_DUP1`) with `is_duplicate: true` and `duplicate_of_asset_id: "VID_2B4C0018"` referencing the canonical asset. Self-referencing is strictly prevented.

### 5.2 Audio Intelligence Catalog (`data/audio_catalog.json`)
```json
{
  "asset_id": "AUDIO_92741287",
  "filename": "bgm_upbeat_puzzle_bounce.wav",
  "path": "source_assets/block-puzzle-burst/music/bgm_upbeat_puzzle_bounce.wav",
  "duration_seconds": 15.0,
  "format": "wav",
  "sample_rate": 44100,
  "channels": 1,
  "codec": "pcm_s16le",
  "integrated_lufs": -15.8,
  "true_peak_dbtp": -2.5,
  "loudness_range_lu": 0.1,
  "peak_dbfs": -2.5,
  "rms_dbfs": -15.3,
  "clipping_detected": false,
  "silence_ratio": 0.28,
  "sound_classification": "instrumental_music",
  "bpm": 120.0,
  "bpm_confidence": "high",
  "energy_level": "high",
  "rhythm_type": "steady_beat",
  "mood": ["energetic", "upbeat", "playful", "casual_gaming", "satisfying"],
  "recommended_projects": ["block-puzzle-burst"],
  "license_status": "NEEDS_REVIEW",
  "commercial_use_allowed": false
}
```

---

## 6. Integration & Backward Compatibility

- **Phase 1 Protection:** All existing scripts (`scripts/run_test_a_day4.py` through `scripts/run_test_e_lifecycle.py`), FFmpeg pipelines, and SQLite records (`data/campaign_tracker.sqlite`) remain fully functional.
- **Remotion Stability:** Assets referenced in `my-video/public/` were not deleted or moved; instead, duplicate entries are logged and cross-referenced to ensure zero build errors in Remotion.
- **Separate Task Status:** `SolveItReel` compliance re-render remains marked `⏳ PENDING` per explicit user instruction. Do not mark this separate task complete during Phase 2.
- **Real Audio Integration:** All 23 user-supplied MP3 files from `Raw_input_files/audio/` are mapped to `source_assets/shared/music/`, analyzed for EBU R128 loudness and autocorrelation BPM, and cataloged with provenance tracking.
