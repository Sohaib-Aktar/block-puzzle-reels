# Social Media Video Production Studio

Multi-project video production, multi-platform export, and automated QC studio for Instagram Reels, Facebook Reels, YouTube Shorts, and YouTube longform.

## Quick start

### Preview in Remotion Studio
```
npm run dev
```

### Render a specific composition
```
npm --prefix my-video exec remotion -- render src/index.ts SolveItReel outputs/block-puzzle-burst/30-day-challenge/solve-it-reel/final/instagram_reel.mp4
```

### Inspect a source video
```
python scripts/inspect_footage.py Raw_input_files/recording_1.mp4
```

## Studio structure

| Folder | Purpose |
|---|---|
| `config/` | Platform presets and global defaults |
| `projects/` | Project profiles and campaign briefs |
| `outputs/` | Rendered and approved videos (structured per project/campaign/content-id) |
| `scripts/` | Utility scripts (ffprobe, batch QC) |
| `renderers/` | FFmpeg scripts and Remotion documentation |
| `docs/` | Architecture docs |
| `Raw_input_files/` | Raw source recordings and screenshots (never delete) |
| `my-video/` | Remotion renderer (Node.js sub-project) |
| `generated_outputs/` | Legacy first-session outputs (preserved archive) |

## Active projects
- **Block Puzzle Burst** — 30-day Instagram launch campaign (`projects/block-puzzle-burst/`)
- **Expand eziSales** — Field sales automation product tutorials (`projects/expand-ezisales/`)

## Key rules (always follow)
1. **English on-screen text only.** BN/HI go in caption files only.
2. **Authentic gameplay only.** Never fabricate screens or gameplay.
3. **Never auto-publish.** All files require manual review.
4. **Never overwrite approved finals.** Use `_v2`, `_v3` suffixes.
5. **FFmpeg first** for ordinary edits; Remotion for motion graphics.

## Full architecture
See [`docs/architecture.md`](docs/architecture.md).

## GitHub
Repository: https://github.com/Sohaib-Aktar/social-media-video-production-studio  
Branch: `main`
