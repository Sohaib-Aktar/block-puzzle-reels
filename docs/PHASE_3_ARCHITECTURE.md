# Phase 3 Architecture: FFmpeg Video Production Pipeline
**Pyapiras Games Social Media Content Studio**  
**Document:** `docs/PHASE_3_ARCHITECTURE.md`  
**Date:** 2026-11-17  
**Author:** Senior Video Production Pipeline Architect & Media Systems Engineer  
**Status:** Approved for Implementation  

---

## 1. Executive Summary & Objective

The objective of **Phase 3** is to transition the Pyapiras Games studio from ad-hoc script rendering into an enterprise-grade, configuration-driven, reusable **FFmpeg Production Pipeline**.

The pipeline accepts an approved **Creative Editing Manifest** (`manifest.json`), resolves real media assets from Phase 2 catalogs (`data/media_catalog.json`, `data/audio_catalog.json`), normalizes visual and audio streams, executes multi-shot scene assemblies with professional graphic overlays and ducked audio, renders production-ready MP4 deliverables, and verifies them through automated Technical & Creative QC.

### Multi-Project Support
The pipeline natively serves all five studio projects without branding cross-contamination:
1. **Block Puzzle Burst (`block-puzzle-burst`):** High-retention mobile casual puzzle game reels, offline proof demos, gameplay challenges. Strict gameplay integrity rules apply (zero synthetic moves/scores).
2. **Expand EziSales (`expand-ezisales`):** Field sales automation (SFA) enterprise B2B tutorials, order booking speed runs, retail distribution pain points.
3. **Expand HR (`expand-hr`):** Cloud HRMS & payroll software instructional guides, compliance automation, statutory deduction demos.
4. **WMS (`wms`):** Warehouse management system workflows, barcode/RFID picking, inventory cycle count demos.
5. **POS (`pos`):** Retail point-of-sale rapid checkout, offline billing, cash drawer reconciliation.

---

## 2. Existing Architecture Audit & Investigation Findings

An exhaustive audit of the workspace was conducted prior to designing Phase 3. Below are the technical findings answering the 11 mandatory architectural questions:

### 1. FFmpeg Executable Resolution
- **Actual Binary:** Remotion's bundled static FFmpeg binary located at:  
  `C:\Users\Dell\Downloads\video gen\my-video\node_modules\@remotion\compositor-win32-x64-msvc\ffmpeg.exe`.
- **System PATH:** System `ffmpeg` is not present in Windows PATH (`shutil.which("ffmpeg")` returns `None`).
- **Resolution Strategy:** Direct binary discovery in `media_engine.get_ffmpeg_cmd()` locates the compositor binary directly on disk. This avoids slow Node.js `npx remotion ffmpeg` overhead (saving 1.5–2.5s per execution).

### 2. FFprobe Executable Resolution
- **Actual Binary:** Remotion's bundled static FFprobe binary located at:  
  `C:\Users\Dell\Downloads\video gen\my-video\node_modules\@remotion\compositor-win32-x64-msvc\ffprobe.exe`.
- **Resolution Strategy:** `media_engine.get_ffprobe_cmd()` finds and executes the same bundled binary directly.

### 3. Binary Execution vs. NPX Fallback
- Direct binary execution is used for all core video and audio operations.
- `npx remotion render` is reserved strictly for React/Remotion compositions when high-level spring physics or programmatic DOM layout is specified in the manifest (`"renderer": "remotion"`).
- Pure video trimming, concatenation, filtering, audio mixing, and platform encoding execute directly through the bundled FFmpeg binary.

### 4. Windows Paths with Spaces
- **Subprocess Execution:** Passing arguments as a list of strings (`subprocess.run(["C:\\Path With Space\\ffmpeg.exe", ...], shell=False)`) relies on the OS API (`CreateProcessW`), preventing space-splitting errors.
- **Concat Demuxer Files:** File paths inside concat demuxer text files must be normalized with forward slashes (`file 'C:/Path/With/Spaces/clip.mp4'`) to avoid Windows backslash escape errors in FFmpeg.
- **Font Paths for drawtext:** Colons in Windows drive letters (`C:`) and backslashes must be escaped for FFmpeg filtergraphs: `C\\:/Windows/Fonts/arial.ttf` or normalized via forward slashes.

### 5. Safe Subprocess Arguments & Shell Injection
- All FFmpeg commands use `subprocess.run(cmd, shell=False, capture_output=True)`.
- User-supplied texts for drawtext overlays are written into text files or passed via dedicated escaped parameters to prevent filtergraph injection.
- Windows SAPI5 TTS in `audio_engine.py` sanitizes quotation characters (`'` and `"`) before passing text to PowerShell speech synthesis.

### 6. Intermediate Video Storage & Cleanup
- *Previous State:* Phase 1 created temporary files in the target directory with suffixes like `.shot_0.mp4`, which could leave orphaned files if a job crashed.
- *Phase 3 Architecture:* Dedicated `intermediate/` directories under each production job (`outputs/<project>/<campaign>/<content_id>/intermediate/`). All temporary shot trims, audio stems, and filter graphs are created here with unique job IDs and cleaned up safely upon job completion (or preserved with `--keep-intermediate` for debugging).

### 7. Audio Synchronization During Scene Assembly
- *Previous State:* Used `-f concat` demuxer, which can cause A/V drift or desynchronization when input clips have slight audio duration mismatches or missing audio streams.
- *Phase 3 Architecture:* 
  1. For simple cuts of identical codec/stream formats: Concat demuxer with audio stream verification.
  2. For multi-shot assemblies with transitions: Complex filtergraph concatenation (`[0:v][0:a][1:v][1:a]concat=n=N:v=1:a=1[v][a]`) which strictly enforces frame-accurate A/V synchronization.
  3. For silent video clips (common in screen recordings): An explicit silent audio stream (`aevalsrc=0:d=...`) is injected so every video scene has an aligned audio track before concatenation.

### 8. Resolution, Aspect Ratio & Frame Rate Normalization
- *Previous State:* Basic `scale=W:H` stretched footage without letterbox/pillarbox padding.
- *Phase 3 Architecture:* Normalization filter pipeline:
  ```text
  scale=w={W}:h={H}:force_original_aspect_ratio=decrease,pad={W}:{H}:(ow-iw)/2:(oh-ih)/2:color=black
  ```
  - Mode `fit`: Preserves aspect ratio with letterboxing/pillarboxing.
  - Mode `fill` / `cover`: Scales to fill canvas and crops excess (`force_original_aspect_ratio=increase,crop={W}:{H}`).
  - Mode `stretch`: Direct stretch (used only if explicitly requested).
  - Frame rate: Enforces constant frame rate (CFR) at 30.0 fps via `fps=fps=30` filter and `-r 30`.
  - Pixel format: Standardizes to `yuv420p` with `-pix_fmt yuv420p` for 100% universal mobile playback.

### 9. Rotation Metadata & SAR Normalization
- Phone screen recordings often include rotation tags (`rotate=90`, `rotate=270`) or non-square pixel aspect ratios (SAR != 1:1).
- Normalization includes:
  - `-noautorotate` with explicit rotation filters when needed, or standardizing via `setsar=1` to guarantee square pixels.
  - Video stream tagging with `display_aspect_ratio=9:16` and `color_space=bt709` / `color_range=tv`.

### 10. Role of Remotion vs. Pure FFmpeg
| Capability | Remotion Engine | Phase 3 FFmpeg Pipeline |
|---|---|---|
| **Primary Use** | Complex React motion design, spring physics, dynamic DOM layouts (e.g. Day 4/5 full reels) | Headless batch video production, automated multi-shot assembly, software tutorials, fast re-renders |
| **Execution** | Node.js / Puppeteer browser rendering (`npx remotion render`) | Direct binary FFmpeg execution (5–10x faster) |
| **Overlays** | React JSX components, CSS filters, Tailwind tokens | FFmpeg `drawtext`, `overlay` filtergraphs, PNG asset badges |
| **Audio** | Remotion `<Audio>` sequences | FFmpeg `amix`, `volume`, `loudnorm`, SAPI5 TTS, auto-ducking |
| **Integration** | Manifest specifies `"renderer": "remotion"` | Manifest specifies `"renderer": "ffmpeg"` (default) |

### 11. Existing Working Systems Reused Without Re-implementation
- `scripts/media_engine.py`: Reused for `get_ffmpeg_cmd()`, `get_ffprobe_cmd()`, `inspect_media()`, and base process execution.
- `scripts/audio_engine.py`: Reused for Windows SAPI5 voiceover synthesis (`generate_voiceover`) and EBU R128 loudness normalization (`normalize_audio`).
- `data/media_catalog.json` & `data/audio_catalog.json`: Reused for catalog-based Asset ID resolution (`VID_*`, `AUDIO_*`).
- `scripts/qc_verifier.py` & `scripts/creative_qc.py`: Reused for post-render technical and creative gating.
- `scripts/campaign_manager.py`: Reused for content status tracking in the SQLite database.
- `config/platform_presets/`: Reused for platform export specifications (`instagram_reel.json`, `youtube_tutorial.json`, etc.).

---

## 3. Production Pipeline Modular Architecture

To ensure high maintainability, clear separation of concerns, and zero duplication, the Phase 3 production architecture is organized into specialized, cohesive modules:

```text
scripts/
├── media_engine.py          # [Existing] Binary discovery & low-level FFmpeg primitives
├── audio_engine.py          # [Existing] SAPI5 TTS & EBU R128 loudness routines
├── production_pipeline.py   # [New] Master CLI & orchestrator entry point
├── production_job.py        # [New] Job state machine, lifecycle management & execution context
├── timeline_builder.py      # [New] Manifest parser, catalog asset resolver & preflight validator
├── video_processor.py       # [New] Scene trimmer, scaler, aspect-ratio normalizer & assembler
├── overlay_engine.py        # [New] Typography, badge cards, safe-zone graphic overlay generator
├── audio_mixer.py           # [New] Multi-track BGM/VO/SFX mixing, licensing gate & ducking
├── render_manager.py        # [New] Subprocess execution, logging, progress capture & temp cleanup
└── render_validator.py      # [New] Post-render FFprobe integrity verification & QC bridge

config/
└── production/
    ├── defaults.json        # Global pipeline defaults (crf, codecs, timeouts, sample rates)
    ├── video_profiles.json  # Platform & canvas specs (9:16, 16:9, 1:1)
    └── audio_profiles.json  # Loudness targets (-14 LUFS), ducking thresholds (-18dB)

outputs/
└── <project>/
    └── <campaign>/
        └── <content_id>/
            ├── intermediate/ # Scratch clips, temporary audio stems, list files
            ├── final/        # Verified, production-ready MP4 deliverable
            ├── logs/         # Full FFmpeg execution logs & stderr traces
            └── report/       # Technical validation & Creative QC reports
```

---

## 4. Component Responsibilities & Data Flow

```mermaid
flowchart TD
    A["Approved Creative Brief / Manifest JSON"] --> B["production_pipeline.py CLI"]
    B --> C["timeline_builder.py: Validate & Resolve Assets"]
    C -->|Catalog Lookup| D["Phase 2 Catalogs (media & audio)"]
    C -->|Licensing Gate| E{"Music Clearance Check"}
    E -->|RESTRICTED / UNKNOWN| F["Job Aborted: Licensing Violation"]
    E -->|COMMERCIAL / REVIEW (with flag)| G["production_job.py: Job Context Created"]
    G --> H["video_processor.py: Trim & Normalize Scenes"]
    H --> I["overlay_engine.py: Graphic & Text Filters"]
    G --> J["audio_mixer.py: VO Synthesis, SFX & BGM Ducking"]
    I --> K["render_manager.py: FFmpeg Execution"]
    J --> K
    K --> L["outputs/.../intermediate/ Rendering"]
    L --> M["render_validator.py: Technical Post-Validation"]
    M -->|PASS| N["outputs/.../final/ Deliverable Staged"]
    M -->|FAIL| O["Error Report & Safe Rollback"]
    N --> P["Creative QC & Campaign Manager Lifecycle Update"]
```

### Module Responsibilities:

1. **`timeline_builder.py`:**
   - Parses the input editing manifest (`manifest.json`).
   - Resolves asset references: converts Asset IDs (`VID_2B4C0018`, `AUDIO_B07B2992`) to canonical disk paths via `data/media_catalog.json` and `data/audio_catalog.json`.
   - Validates timestamps against media bounds (`source_in < source_out <= duration`).
   - Performs licensing preflight: blocks `RESTRICTED` or `UNKNOWN` audio from entering production. Flags `NEEDS_REVIEW` tracks with warnings for internal previews.

2. **`video_processor.py`:**
   - Normalizes input footage: scales, letterboxes/pillarboxes, converts to CFR 30 fps, standardizes `yuv420p` pixel format.
   - Builds scene assembly commands: handles hard cuts, crossfades, freeze frames, and duration enforcement.
   - Generates intermediate normalized clips in the job's intermediate directory.

3. **`overlay_engine.py`:**
   - Constructs FFmpeg filtergraphs for text overlays (`drawtext`).
   - Supports typography styling (font family, weight, size, color, drop shadow, outline).
   - Generates high-visibility background badges (rounded translucent cards, gold borders) using PNG overlays or FFmpeg `drawbox`.
   - Strictly enforces safe margins: Top ≥ 220px, Bottom ≥ 280px (Instagram/TikTok/Shorts UI protection).

4. **`audio_mixer.py`:**
   - Slices and positions audio events (BGM, VO, sound effects) along the timeline.
   - Synthesizes offline voiceover using Windows SAPI5 if raw text is provided in the manifest.
   - Performs voiceover auto-ducking: dynamically attenuates background music by ~18dB during voiceover speech.
   - Applies EBU R128 loudness normalization: targets -14.0 LUFS integrated loudness and -1.5 dBTP true peak.

5. **`render_manager.py`:**
   - Manages subprocess execution with real-time log capturing.
   - Monitors execution duration, exit codes, and memory safety.
   - Manages temporary file lifecycle: safely cleans intermediate files upon success; preserves them if `--debug` is passed.

6. **`render_validator.py`:**
   - Runs post-render FFprobe inspection against expected profile specs (resolution, duration, fps, codecs, stream presence).
   - Verifies decodability (detects corruption or frame drops).
   - Triggers the existing `qc_verifier.py` and `creative_qc.py` to ensure complete compliance.

---

## 5. Creative Editing Manifest Specification

The manifest schema is strictly structured to be configuration-driven and reproducible. Below is the production schema definition:

```json
{
  "$schema": "http://pyapirasgames.com/schemas/production-manifest-v1.json",
  "project": "block-puzzle-burst",
  "campaign": "30-day-challenge",
  "content_id": "BPB_DAY_04",
  "output_profile": "instagram_reel",
  "renderer": "ffmpeg",
  "allow_review_audio": false,
  "canvas": {
    "width": 1080,
    "height": 1920,
    "fps": 30,
    "duration_seconds": 15.0
  },
  "timeline": [
    {
      "scene_id": "scene_01_opening",
      "asset_id": "VID_672154F1",
      "source_in": 0.0,
      "source_out": 2.0,
      "duration": 2.0,
      "fit_mode": "contain",
      "overlays": [
        {
          "type": "badge",
          "title": "No WiFi? No problem.",
          "subtitle": "100% Offline Gameplay",
          "position": "center",
          "position_y": 700,
          "start_time": 0.0,
          "end_time": 1.9,
          "style": "purple_gold_badge"
        }
      ]
    },
    {
      "scene_id": "scene_02_gameplay",
      "asset_id": "VID_672154F1",
      "source_in": 9.5,
      "source_out": 17.5,
      "duration": 8.0,
      "fit_mode": "contain",
      "overlays": [
        {
          "type": "pill",
          "text": "Zero Data • Zero Lag ⚡",
          "position_y": 220,
          "start_time": 0.0,
          "end_time": 3.0
        }
      ]
    }
  ],
  "audio": {
    "music": {
      "asset_id": "AUDIO_753DE70D",
      "volume": 0.25,
      "start_time": 0.0,
      "fade_in": 0.5,
      "fade_out": 0.8
    },
    "voiceover": {
      "text": "Play anywhere, anytime. 100% offline block puzzle action.",
      "volume": 1.0,
      "ducking": true,
      "duck_level_db": -18
    },
    "sound_effects": [
      {
        "asset_id": "AUDIO_92744730",
        "timeline_start": 2.5,
        "volume": 0.8
      }
    ],
    "master_loudness_target": -14.0
  }
}
```

---

## 6. Real-World Pilot Execution Strategy

### Pilot 1: BPB_DAY_04 Reel Revision
- **Target:** Block Puzzle Burst Day 04 Offline Reel (`BPB_DAY_04`).
- **Creative Focus:** Verify the central hook presentation ("No WiFi? No problem. / 100% Offline Gameplay" centered at `y=700`).
- **Asset Ground Truth:** Sourced from `source_assets/block-puzzle-burst/gameplay/recording_3.mp4` / `recording_3_cfr30.mp4`.
- **Output Destination:** `outputs/block-puzzle-burst/30-day-challenge/day-04-no-wifi-revision/final/Day_04_Final_Revised_Center_Text.mp4`.
- **Validation:** 7/7 Technical QC, Creative QC Score ≥ 80/90, FFprobe metadata check, before/after visual inspection.

### Pilot 2: Software Tutorial Pilot (EziSales / Expand HR)
- **Target:** Enterprise ERP software quick-start guide (`ezisales-tut-01-order-booking`).
- **Creative Focus:** 15-second vertical tutorial demonstrating rapid order booking.
- **Asset Ground Truth:** Sourced from canonical ERP screen recordings and icons.
- **Audio Integration:** Synthesize professional SAPI5 TTS narration and mix with corporate BGM.
- **Output Destination:** `outputs/expand-ezisales/quick-start-tutorials/ezisales-tut-01-order-booking/final/software_tutorial_vertical.mp4`.
- **Validation:** Technical & Creative QC verification proving multi-project pipeline generality.

---

## 7. Testing Strategy & Phase Gates

The implementation will be verified through 5 specialized test suites:
1. `tests/test_production_manifest.py`: Manifest validation, asset resolution, licensing checks, bad timestamps detection.
2. `tests/test_video_processor.py`: Trimming, scaling, aspect ratio modes, CFR 30 normalization, concatenation.
3. `tests/test_audio_mixer.py`: Multi-track mixing, ducking, EBU R128 normalization, licensing blocks.
4. `tests/test_render_manager.py`: Subprocess execution, job lifecycle states, error handling, temp file cleanup.
5. `tests/test_production_pipeline_e2e.py`: End-to-end rendering and verification of the two real production pilots.

### Regression Protection:
- All Phase 1 tests (`scripts/test_studio_suite.py`) must pass (5/5).
- All Phase 2 tests (`tests/test_phase2_intake_audio.py`) must pass (15/15).

---

## 8. Implementation Roadmap

1. **Step 1:** Establish production configuration files (`defaults.json`, `video_profiles.json`, `audio_profiles.json`).
2. **Step 2:** Build core pipeline modules:
   - `scripts/production_job.py`
   - `scripts/timeline_builder.py`
   - `scripts/overlay_engine.py`
   - `scripts/video_processor.py`
   - `scripts/audio_mixer.py`
   - `scripts/render_validator.py`
   - `scripts/render_manager.py`
   - `scripts/production_pipeline.py`
3. **Step 3:** Implement unit and integration test suites.
4. **Step 4:** Execute Pilot 1 (BPB_DAY_04 Reel Revision) and generate visual/technical proof.
5. **Step 5:** Execute Pilot 2 (EziSales Software Tutorial) and generate verification proof.
6. **Step 6:** Run full Phase 1 and Phase 2 regression suites.
7. **Step 7:** Compile documentation deliverables (`PHASE_3_IMPLEMENTATION.md`, `PHASE_3_TEST_REPORT.md`, `PRODUCTION_MANIFEST_GUIDE.md`, `PHASE_3_OPERATIONS_GUIDE.md`).
