# 01 — Complete Workspace Inventory

**Studio:** Social Media Video Production Studio  
**Machine-Readable Source:** `data/audit/workspace_inventory.json` & `data/audit/dependency_inventory.json`  
**Audit Date:** 2026-11-18  
**Scope:** Entire local repository excluding `.git/`, `node_modules/`, `__pycache__/`, and `.agents/`.

---

## 1. High-Level Footprint Summary

- **Total Tracked Files (excluding `.git/` & `node_modules/`):** **825 files**
- **Total Tracked Size:** **681.31 MB** (`714,405,274` bytes)
- **Exact Duplicate SHA-256 Groups:** **66 groups** (**224.58 MB** reclaimable — `33.0%` of tracked storage)
- **Python Source & Test Files:** **43 files** (`39` scripts in `scripts/` + `4` test suites in `tests/`) + `1` PowerShell OCR script (`scripts/win_ocr.ps1`)
- **Configuration Files (`config/`):** **16 JSON files** (all valid JSON)
- **Active Projects (`projects/`):** **2 active projects** (`block-puzzle-burst`, `expand-ezisales`) + `projects/_template/`

---

## 2. Directory Inventory & Purpose Breakdown

| Directory / Bucket | Purpose | Key Contents | Health Notes |
|---|---|---|---|
| `(root)` | Studio metadata, rules, prompts, Node/Python configs | `README.md`, `package.json`, `pyproject.toml`, `.gitignore`, `MASTER_SOCIAL_VIDEO_STUDIO_PROMPT.md`, `MASTER_REEL_RULES.md`, `ANTIGRAVITY_FIRST_RUN_PROMPT.md`, `prompt.md`, `skills-lock.json` | Missing `requirements.txt` (`AUD-015`); `.gitignore` lacks `.env`/`*.key` rules. |
| `scripts/` | Core Python production, intake, audio, export, QC, and campaign engines | 39 `.py` modules, `win_ocr.ps1`, `README.md` | 12 standalone/unimported CLI scripts; 6 duplicate SHA-256 helper copies (`AUD-019`). |
| `tests/` | Automated Phase 2–5 `unittest` suites | `test_phase2_intake_audio.py`, `test_phase3_production_pipeline.py`, `test_phase4_multi_platform_export.py`, `test_phase5_automated_qc.py` | All 65 methods pass; Phase 5 `test_11` writes to live `data/qc_approval_audit.jsonl` (`AUD-008`). |
| `config/` | Production profiles, platform presets, safe zones, manifests, global defaults | `production/` (6 JSON), `platform_presets/` (7 JSON), `manifests/` (2 JSON), `studio_settings/global_defaults.json` | Schema overlap & singular/plural slug drift (`AUD-012`); cross-project hashtags in `export_profiles.json` (`AUD-003`). |
| `projects/` | Isolated project knowledge bases & profiles | `block-puzzle-burst/`, `expand-ezisales/`, `_template/` | Clean after Expand HR/POS/WMS removal. |
| `source_assets/` | Curated production media organized by project & `shared/` | `block-puzzle-burst/`, `expand-ezisales/`, `shared/` | `source_assets/expand-ezisales/screen-recordings/` is empty (`AUD-007`). |
| `Raw_input_files/` | Immutable raw input archive (recordings, screenshots, 23 real MP3s) | 3 MP4s, 5 images, 23 MP3s | Heavily duplicated in `source_assets/` and `my-video/public/` (`AUD-016`). |
| `outputs/` | Structured production outputs, multi-platform exports, Phase 5 QC evidence | `block-puzzle-burst/`, `expand-ezisales/`, `test-project/` | `outputs/test-project/` is an orphan scratch folder (`AUD-021`). |
| `generated_outputs/` | Legacy first-session rendered videos, storyboards, plans | Day 02–04 legacy renders, `SolveItReel_Puzzle_Challenge.mp4`, plans | Contains exact duplicates of `outputs/` (`AUD-016`). |
| `data/` | SQLite tracker, media/audio catalogs, job records, QC calibration & audit logs | `campaign_tracker.sqlite`, `media_catalog.json` (18), `audio_catalog.json` (38), `footage_catalog.json` (0), `migration_log.json` (49), `production_jobs/`, `export_jobs/`, `qc_jobs/`, `qc_approval_audit.jsonl`, `qc_calibration_results.json`, `check_video0/`, `audit/` | 12 JSON files + 3 SQLite rows contain hardcoded `C:\Users\Dell\Downloads\video gen` (`AUD-005`); `footage_catalog.json` empty & `check_video0/` orphan (`AUD-021`). |
| `my-video/` | Remotion React/TypeScript motion-graphics sub-project | `src/` compositions, `public/` media copies, `build/`, `package.json` | `DayFourOfflineReel.tsx` produces silent audio (`AUD-006`). |
| `renderers/` | Legacy FFmpeg batch script & renderer READMEs | `ffmpeg/trim_and_scale.bat`, `ffmpeg/README.md`, `remotion/README.md` | `trim_and_scale.bat:L39` distorts aspect ratio (`AUD-010`). |
| `templates/` | Markdown & JSON manifest templates | 7 `.template.md`, 2 `.json` templates/schemas | Clean; `editing_manifest.schema.json` does not enforce Phase 3/4 extended fields. |
| `docs/` | Architecture, guides, Phase 2–5 reports, and `docs/audit/` | 25+ Markdown documents + `docs/audit/` | 6 broken file references + stale Phase 3–4 status in `docs/architecture.md` (`AUD-017`). |

---

## 3. Top Exact Binary Duplicate Groups (`AUD-016`)

| Size Each | Copies | Reclaimable | Paths |
|---:|---:|---:|---|
| 28.98 MB | 4 | 86.94 MB | `Raw_input_files/recording_1.mp4`, `my-video/public/gameplay.mp4`, `source_assets/block-puzzle-burst/gameplay/gameplay.mp4`, `source_assets/block-puzzle-burst/gameplay/recording_1.mp4` |
| 5.27 MB | 3 | 10.54 MB | `Raw_input_files/recording_3.mp4`, `my-video/public/recording_3.mp4`, `source_assets/block-puzzle-burst/gameplay/recording_3.mp4` |
| 3.27 MB | 4 | 9.81 MB | `Raw_input_files/audio/sigmamusicart-no-copyright-music-619322 (1).mp3`, `...619322.mp3`, `source_assets/shared/music/...619322 (1).mp3`, `...619322.mp3` |
| 5.36 MB | 2 | 5.36 MB | `Raw_input_files/audio/no-copyright-music-2026-acoustic-acoustic-music-611654.mp3` & `source_assets/shared/music/...` |
| 5.07 MB | 2 | 5.07 MB | `generated_outputs/videos/SolveItReel_Puzzle_Challenge.mp4` & `outputs/block-puzzle-burst/30-day-challenge/solve-it-reel/final/instagram_reel.mp4` |
| 1.66 MB | 4 | 4.98 MB | `Raw_input_files/pyapiras games icon.png`, `my-video/public/pyapiras_games_icon.png`, `source_assets/block-puzzle-burst/logos/pyapiras games icon.png`, `.../pyapiras_games_icon.png` |

---

## 4. Unused / Standalone / Orphan Components Identified

- **Standalone CLI / Test Entry Scripts (12, never imported by other modules):** `content_workflow.py`, `drive_sync.py`, `inspect_footage.py`, `inspect_real_audio.py`, `marketing_director.py`, `platform_adapter.py`, `production_pipeline.py`, `qc_calibration.py`, `run_test_a_day4.py`, `run_test_b_ezisales.py`, `run_test_e_lifecycle.py`, `test_studio_suite.py`.
- **Legacy / Superseded Components:** `data/footage_catalog.json` (0 entries; replaced by `data/media_catalog.json`), `scripts/creative_qc.py` (static 80/90 Phase 1 scorer; replaced by Phase 5 `content_qc.py`), `scripts/platform_adapter.py` (Phase 1 basic adapter; replaced by Phase 4 `multi_platform_exporter.py`).
- **Orphan Artifacts:** `outputs/test-project/`, `data/check_video0/`.
- **Missing Expected Files:** `requirements.txt`, `data/licenses/` directory (referenced in `docs/AUDIO_LICENSING_GUIDELINES.md:L81`), `.github/workflows/`.
