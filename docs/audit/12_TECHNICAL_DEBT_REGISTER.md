# 12 — Technical Debt Register

**Studio:** Social Media Video Production Studio  
**Audit Date:** 2026-11-18

---

## 1. Consolidated Technical Debt Inventory

| Debt Item | Linked Finding(s) | Affected Components | Debt Type | Interest / Cost Over Time | Estimated Paydown |
|---|---|---|---|---|---|
| **TD-01: Duplicate Core Utilities** | `AUD-019` | `asset_migrator.py`, `footage_analyzer.py`, `audit_export_duplicates.py`, `content_qc.py`, `multi_platform_exporter.py`, `qc_orchestrator.py`, `inspect_footage.py`, `media_engine.py` | Code Duplication | SHA-256 hashing repeated 6× and `get_ffprobe_cmd` repeated 2×; bug fixes must be applied in 6 places. | 3 hours |
| **TD-02: Monolithic Orchestration Functions (300–479L)** | `AUD-019` | `multi_platform_exporter.py:export_master` (479L), `visual_qc.py:run` (447L), `export_validator.py:validate_export` (365L), `content_qc.py:run` (348L), `audio_qc.py:run` (301L) | Structural Complexity | Hard to unit-test sub-steps cleanly; high cognitive load during maintenance. | 2 days |
| **TD-03: Dual Phase 1 Legacy & Phase 4/5 Modern Engines** | `AUD-012` | `creative_qc.py`, `qc_verifier.py`, `platform_adapter.py`, `config/platform_presets/*.json`, `config/production/video_profiles.json` | Architectural Drift | Operators risk invoking static 80/90 Phase 1 QC or singular `instagram_reel` slugs instead of Phase 4/5 canonical profiles. | 1–2 days |
| **TD-04: Non-Isolated Legacy & Phase 5 Approval Tests** | `AUD-008` | `scripts/test_studio_suite.py`, `run_test_a_day4.py`, `run_test_b_ezisales.py`, `run_test_e_lifecycle.py`, `tests/test_phase5_automated_qc.py:test_11` | Test Debt | Every test execution pollutes live SQLite DB, live `outputs/`, and live `data/qc_approval_audit.jsonl`. | 4 hours |
| **TD-05: Fragile FFmpeg Filter String Re-Parsing** | `AUD-009` | `scripts/video_processor.py:L74-108` | Brittle Implementation | Blocks animated overlays or multi-flag FFmpeg inputs without breaking `audio_input_idx`. | 2 hours |
| **TD-06: Silent `except Exception: pass` Blocks (9×)** | `AUD-020` | `audio_analyzer.py`, `audit_export_duplicates.py`, `media_engine.py`, `media_intake.py`, `multi_platform_exporter.py` | Observability Debt | Masks I/O and parse anomalies silently. | 2 hours |
| **TD-07: Per-Frame PowerShell OCR Process Spawning** | `AUD-016` (Perf) | `scripts/visual_qc.py` -> `scripts/win_ocr.ps1` | Performance Debt | 5–10 PowerShell launches per video adds ~5–10s fixed overhead; slows batch QC and calibration. | 2 hours |
| **TD-08: Orphan Scratch & Empty Legacy Files** | `AUD-021` | `data/footage_catalog.json`, `data/check_video0/`, `outputs/test-project/` | Workspace Hygiene | Ambiguous state alongside active studio assets. | 30 min |
| **TD-09: Unpinned Python Dependencies & No `requirements.txt`** | `AUD-015` | Workspace root, `pyproject.toml` | Environment Debt | Fragile setup on new workstations or CI runners. | 1 hour |
| **TD-10: 224.58 MB Cross-Folder Binary Duplication** | `AUD-016` | `Raw_input_files/`, `my-video/public/`, `source_assets/`, `generated_outputs/` | Storage Debt | 33% redundant binary footprint across 66 SHA-256 groups. | 2 hours |
