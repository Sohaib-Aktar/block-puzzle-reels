# Backup and Migration Plan

**Date:** 2026-11-16  
**Scope:** AI Social Media Content Studio migration from single-game Remotion setup to multi-project architecture.

## 1. Guiding Principles
1. **Zero Data Loss:** Never delete, overwrite, or displace existing gameplay recordings, project files, or legacy outputs without an explicit verified copy.
2. **Backward Compatibility:** All existing Remotion commands (`npm run dev`, `npm run render:day2`, etc.) must continue to function identically.
3. **Additive Architecture:** New directories (`projects/`, `config/`, `templates/`, `scripts/`, `outputs/`) expand capabilities alongside existing folders (`generated_outputs/`, `Raw_input_files/`, `my-video/`).
4. **Git Protection:** Every major structural milestone is committed to Git on branch `main` and pushed to GitHub remote `https://github.com/Sohaib-Aktar/block-puzzle-reels.git`.

## 2. Asset & Output Inventory
| Item | Location | Protection Status | Notes |
|---|---|---|---|
| Gameplay Recordings | `Raw_input_files/recording_1.mp4`, `recording_2.mp4`, `recording_3.mp4` | PRESERVED (Read-Only) | Authentic gameplay captures; never modified |
| Screenshots | `Raw_input_files/sample_1.jpg`, `sample_2.jpg`, `sample_airplane.jpg` | PRESERVED (Read-Only) | Reference UI states |
| Remotion Project | `my-video/` | PRESERVED & EXTENDED | Contains all 4 compositions + React component library |
| Legacy Rendered Videos | `generated_outputs/videos/` | PRESERVED (Archive) | 4 MP4 files from initial sessions |
| Campaign Plans | `generated_outputs/plans/` | PRESERVED (Archive) | 6 Markdown strategy docs |
| Structured Outputs | `outputs/<project>/<campaign>/<content-id>/` | ACTIVE TARGET | New canonical location for approved deliverables |

## 3. Migration Actions
1. **Project Separation:** Projects are isolated in `projects/<project-slug>/` with dedicated profiles.
2. **Output Standardization:** Each piece of content receives a dedicated folder containing `brief.md`, `manifest.json`, `captions/`, `final/`, `qc_report.md`, and `approval_record.md`.
3. **Template Preservation:** Standardized templates live in `templates/` for easy duplication.
4. **Tooling Decoupling:** General media processing functions (inspection, trimming, re-encoding) live in `scripts/media_engine.py` using FFmpeg, freeing Remotion to focus on motion graphics and interactive React overlays.
