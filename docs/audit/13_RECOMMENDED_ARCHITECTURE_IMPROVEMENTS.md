# 13 — Recommended Architecture Improvements

**Studio:** Social Media Video Production Studio  
**Audit Date:** 2026-11-18  
**Note:** Recommendations only — **not implemented** during this audit phase per Part 6 rules.

---

## 1. Introduce a Shared `scripts/studio_utils.py` Foundation Module
Consolidate cross-cutting primitives currently duplicated across 15+ scripts:
- `sha256_file(path)` (replaces 6 duplicate implementations)
- `to_workspace_relative(path)` & `resolve_workspace_path(rel_path)` (eliminates `AUD-005` hardcoded absolute paths)
- `atomic_write_json(path, payload)` (eliminates `AUD-014` partial-write corruption risk)
- `run_subprocess_safe(cmd, timeout_seconds=...)` (eliminates `AUD-013` unbounded hangs)
- `get_ffmpeg_cmd()` / `get_ffprobe_cmd()` (single canonical resolver)

## 2. Unify Campaign Lifecycle & Phase 5 QC Approval State
Currently, `data/campaign_tracker.sqlite` (`campaign_manager.py`) and Phase 5 `data/qc_jobs/` + `data/qc_approval_audit.jsonl` (`qc_orchestrator.py`) operate as two disconnected state machines.
- **Target State:** Make `qc_orchestrator.py` write back verified QC status (`qc_job_id`, `overall_status`, `human_decision_state`) into `campaign_tracker.sqlite` via gated methods, and fix `advance_state()` / `update_status()` (`AUD-002`) so `QC_APPROVED`, `READY_TO_PUBLISH`, and `PUBLISHED` cannot bypass Phase 5 QC or human sign-off.
- Enable SQLite `PRAGMA journal_mode=WAL; PRAGMA busy_timeout=5000` (`AUD-014`).

## 3. Canonical Profile Registry & Project-Scoped Metadata
Eliminate the 4-way profile overlap (`platform_presets/`, `video_profiles.json`, `export_profiles.json`, `render_profiles.json`) and singular/plural slug mismatch (`instagram_reel` vs `instagram_reels`):
- Keep physical rendering specs in `config/production/render_profiles.json` and platform destinations in `config/production/export_profiles.json` as the single source of truth with explicit alias resolution (`instagram_reel -> instagram_reels`).
- Strip all project-specific hashtags (`#BlockPuzzle`, `#PyapirasGames`) out of global configs (`AUD-003`) and load project-specific brand metadata (hashtags, background color, audio defaults, signature terms) dynamically from `projects/<project>/project_config.json` (so onboarding a future project requires zero edits to core Python scripts!).

## 4. Parameterized Windows PowerShell Helpers & Batch WinRT OCR
- Replace inline `-Command` PowerShell string interpolation in `scripts/audio_engine.py:generate_voiceover()` with a typed `scripts/win_tts.ps1` invoked via `-File` (`AUD-001`).
- Extend `scripts/win_ocr.ps1` to accept an array of image paths (`-ImagePaths`) in a single PowerShell session, cutting multi-frame OCR time by ~60–70%.

## 5. Strict Test Environment Isolation & CI Pipeline
- Support environment variable overrides (`STUDIO_DB_PATH`, `STUDIO_QC_JOBS_DIR`, `STUDIO_APPROVAL_AUDIT_LOG`, `STUDIO_OUTPUTS_DIR`) so Phase 1–5 tests run 100% inside `tempfile.TemporaryDirectory()` without touching live `data/` or `outputs/` (`AUD-008`).
- Add a lightweight `.github/workflows/ci.yml` on `windows-latest` once the GitHub repository rename is complete (`AUD-022`).

## 6. Optional Offline ASR Plugin Architecture
- Add a pluggable `ASREngine` interface in `scripts/audio_qc.py` supporting local `faster-whisper` when installed while preserving the current honest `AUD_007 (REVIEW_REQUIRED)` fallback when absent (`AUD-011`).
