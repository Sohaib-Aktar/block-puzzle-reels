# Architecture — Social Media Video Production Studio

**Version:** 1.0  
**Updated:** 2026-11-18  
**Workspace:** `Social Media Video Production Studio`

## Purpose
Multi-project Social Media Video Production Studio. Supports games, apps, ERP/software, tutorials, and brands across Instagram Reels, Facebook Reels, YouTube Shorts, and YouTube longform.

## Folder structure

```
video gen/
│
├── MASTER_SOCIAL_VIDEO_STUDIO_PROMPT.md  ← Global studio rules (read this first)
├── MASTER_REEL_RULES.md                 ← Block Puzzle-specific permanent rules
├── README.md                            ← Studio entry point
├── package.json                         ← Root orchestrator (npm scripts only, no node_modules)
│
├── config/                              ← Platform and studio settings
│   ├── studio_settings/
│   │   └── global_defaults.json         ← English-only, codec defaults, naming rules
│   └── platform_presets/
│       ├── instagram_reel.json          ← 1080×1920, ≤90s, H.264
│       ├── facebook_reel.json           ← 1080×1920, ≤60s, H.264
│       ├── youtube_short.json           ← 1080×1920, ≤180s, H.264
│       └── youtube_longform.json        ← 1920×1080, H.264
│
├── projects/                            ← One folder per game/app/product
│   └── block-puzzle-burst/
│       ├── PROJECT_PROFILE.md           ← Developer, game facts, brand guidelines
│       └── campaigns/
│           └── 30-day-challenge/
│               ├── campaign_brief.md    ← Campaign strategy, rules, KPIs
│               ├── content_calendar.md  ← 30-day posting plan
│               └── briefs/
│                   ├── day-01.md        ← Per-day creative brief
│                   ├── day-02.md
│                   ├── day-03.md
│                   └── solve-it-reel.md
│
├── outputs/                             ← All rendered and approved video assets
│   └── block-puzzle-burst/
│       └── 30-day-challenge/
│           └── <content-id>/
│               ├── brief.md             ← (link or copy from projects/)
│               ├── captions/
│               │   └── instagram.txt    ← Ready-to-paste EN + BN + HI captions
│               ├── final/
│               │   └── instagram_reel.mp4  ← Approved final. Never overwrite.
│               └── qc_report.md         ← Render metadata + compliance check
│
├── scripts/                             ← Utility scripts
│   ├── inspect_footage.py               ← FFprobe wrapper for file metadata
│   └── README.md
│
├── renderers/                           ← Rendering engines
│   ├── ffmpeg/
│   │   ├── trim_and_scale.bat           ← Trim + scale to 1080×1920
│   │   └── README.md
│   └── remotion/
│       └── README.md                    ← When to use Remotion vs FFmpeg
│
├── docs/
│   └── architecture.md                  ← This file
│
├── Raw_input_files/                     ← Original raw assets (never delete)
│   ├── recording_1.mp4  (720×1600, 201s, Block Puzzle gameplay A)
│   ├── recording_2.mp4  (720×1600, 201s, Block Puzzle gameplay B)
│   ├── recording_3.mp4  (720×1600, 30s, Block Puzzle gameplay C)
│   ├── sample_1.jpg     (Board state screenshot — 1,600 score)
│   ├── sample_2.jpg     (Board state screenshot — 955 score + COMBO ×4)
│   └── sample_airplane.jpg  (Likely Day 4 offline/airplane proof asset)
│
├── my-video/                            ← Remotion sub-project (Node.js)
│   ├── package.json                     ← Real Node dependencies (Remotion 4.0.543)
│   ├── remotion.config.ts
│   ├── public/
│   │   ├── gameplay.mp4                 ← Copy of recording_1.mp4
│   │   └── gameplay2.mp4               ← Copy of recording_2.mp4
│   └── src/
│       ├── Root.tsx                     ← Registers all compositions
│       ├── index.ts
│       ├── MyDayTwoReel.tsx
│       ├── MyDayThreeReel.tsx
│       ├── SolveItReel.tsx
│       ├── FrameFinder.tsx
│       ├── components/                  ← Reusable React components
│       └── theme/tokens.ts             ← Design tokens
│
└── generated_outputs/                   ← Legacy output folder (preserved, read-only)
    ├── videos/  (4 MP4 files — originals of the first renders)
    ├── previews/ (8 PNG verification frames)
    └── plans/   (6 markdown plan docs — preserved archive)
```

## Two-node-project rule
The root `package.json` contains orchestration scripts only. It has **no** `node_modules`.  
Remotion packages live exclusively in `my-video/node_modules/`.

**To run Remotion from workspace root:**
```
npm --prefix my-video exec remotion -- render src/index.ts <CompositionId> <output>
```

**Never** run `npx remotion ...` from the workspace root — it will fail.

## Renderer decision tree

```
Task → FFmpeg if:         ordinary trim, scale, text overlay, platform re-encode
Task → Remotion if:       spring animations, React overlays, countdown timers, badge transitions
```

## Adding a new project
1. Create `projects/<project-slug>/PROJECT_PROFILE.md`
2. Create `projects/<project-slug>/campaigns/<campaign-id>/campaign_brief.md`
3. Create `outputs/<project-slug>/<campaign-id>/` structure
4. Source assets go in `Raw_input_files/` (or a project-specific sub-folder)
5. Register any new Remotion composition in `my-video/src/Root.tsx`

## English-only rule
On-screen text in all rendered videos: **English only**.  
Bengali and Hindi belong in:
- `captions/instagram.txt` (social post copy)
- Story text stickers (applied manually in Instagram app)
- Facebook/YouTube caption fields
Never burn non-English text into a video file.

## Git repository
Target Remote: `https://github.com/Sohaib-Aktar/social-media-video-production-studio.git` *(currently `block-puzzle-reels.git` pending manual GitHub rename)*  
Branch: `main`

## Status (2026-11-17)
| Phase | Status |
|---|---|
| Phase 1 — Foundation (config, projects, outputs structure) | ✅ DONE |
| Phase 2 — Media intake & Audio Intelligence (source_assets, catalogs, DSP analysis) | ✅ COMPLETED & FULLY VERIFIED (15/15 Tests Passed) |
| Phase 3 — FFmpeg pipeline test | 🔲 Planned / Not Started |
| Phase 4 — Multi-platform exports | 🔲 Planned / Not Started |
| Phase 5 — QC automation | 🔲 Planned / Not Started |
| SolveItReel compliance re-render | ✅ COMPLETED & READY_TO_PUBLISH (Dual QC passed 80/90; confirmed solved by user) |
