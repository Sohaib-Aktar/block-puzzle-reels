# 06 — Configuration and Data Integrity Audit

**Studio:** Social Media Video Production Studio  
**Audit Date:** 2026-11-18

---

## 1. JSON / TOML Syntax & Schema Verification

- **All Workspace JSON Files Valid:** **100% PASS** (`0` parse errors across `config/`, `data/`, `templates/`, `package.json`, `my-video/package.json`, `outputs/`).
- **`pyproject.toml` Valid:** **PASS** (verified with `tomllib`).
- **Active Project Isolation:** **PASS** after Part 1 cleanup — zero references to `expand-hr`, `pos`, or `wms` remain in `config/`, `data/`, `projects/`, `source_assets/`, or `scripts/`.

---

## 2. Catalog & Database Referential Integrity

| Data Store | Entries | Missing Disk Paths | Hardcoded Absolute Paths | Integrity Status |
|---|---:|---:|---:|---|
| `data/media_catalog.json` | 18 | 0 | 0 | **CLEAN** (relative paths, all 18 exist on disk) |
| `data/audio_catalog.json` | 38 | 0 | 0 | **CLEAN** (relative paths, all 38 exist on disk, valid canonical duplicate links) |
| `data/footage_catalog.json` | 0 | 0 | 0 | **ORPHAN / EMPTY** (`AUD-021`, superseded by `media_catalog.json`) |
| `data/migration_log.json` | 49 ops | 0 | **153 occurrences** | **PORTABILITY RISK** (`AUD-005`) |
| `data/campaign_tracker.sqlite` | 9 rows | 0 | **3 rows** | **STATE & PATH ISSUES** (`AUD-002`, `AUD-005`) |
| `data/production_jobs/*.json` | 4 files | 0 | **31 occurrences** | **PORTABILITY RISK** (`AUD-005`) |
| `data/export_jobs/*.json` | 3 files | 0 | **88 occurrences** | **PORTABILITY RISK** (`AUD-005`) |
| `data/qc_jobs/*.json` | 3+ files | 0 | **12+ occurrences** | **PORTABILITY RISK** (`AUD-005`) + test pollution (`AUD-008`) |
| `data/qc_approval_audit.jsonl` | 2+ lines | N/A | 0 | **POLLUTED BY UNIT TESTS** (`AUD-008`) |

---

## 3. Specific Configuration & Data Integrity Findings

### `AUD-003` — Cross-Project Hashtag Contamination in `config/production/export_profiles.json`
- Lines 16, 28, 40, 52 embed `#BlockPuzzle` and `#PyapirasGames` globally across all 4 platform export profiles, contaminating B2B/ERP delivery records (`expand-ezisales`).

### `AUD-005` — Hardcoded Absolute Paths Persisted in SQLite & Job JSONs
- **Severity:** `HIGH` | **Category:** `DATA_INTEGRITY_RISK` | **Confidence:** `HIGH` | **Priority:** `P1`
- **Affected Files:** `data/campaign_tracker.sqlite` (3 rows), `data/migration_log.json` (153), `data/export_jobs/*.json` (88), `data/production_jobs/*.json` (31), `data/qc_jobs/*.json` (12), `data/project_removal_manifest.json` (1).
- **Evidence:** Total of **291** persisted occurrences of `C:\Users\Dell\Downloads\video gen\...` across 12 JSON files + 3 SQLite `output_location` columns.
- **Current Behavior:** Renaming the local workspace folder to `Social Media Video Production Studio` immediately invalidates every stored absolute path in historical job and campaign records.
- **Expected Behavior:** Persist workspace-relative POSIX paths (like `data/media_catalog.json` and `data/audio_catalog.json` already do!) and resolve via `WORKSPACE_ROOT` at load time.
- **Impact:** Broken historical lookup, broken `qc_orchestrator.py compare` references, and non-portable studio backups.
- **Reproduction:** Inspect `output_location` in `data/campaign_tracker.sqlite` and `master_path` in `data/export_jobs/*.json`.
- **Recommended Solution:** Implement shared `to_workspace_relative()` / `resolve_workspace_path()` helpers and run a one-time non-destructive migration script on `data/`.
- **Risks of Fixing:** Medium; ensure tests resolve relative paths before calling `os.path.exists()`.
- **Estimated Effort:** 4 hours.

### `AUD-012` — Fragmented Profile Configs & Singular/Plural Slug Drift
- **Severity:** `MEDIUM` | **Category:** `ARCHITECTURE_WEAKNESS` | **Confidence:** `HIGH` | **Priority:** `P2`
- **Evidence:**
  - `config/platform_presets/`: `instagram_reel.json`, `facebook_reel.json`, `youtube_short.json`, `youtube_longform.json`, `youtube_tutorial_longform.json`, `software_tutorial_vertical.json`, `product_demo_horizontal.json`
  - `config/production/video_profiles.json`: singular slugs (`instagram_reel`, `youtube_short`, `facebook_reel`)
  - `config/production/export_profiles.json` & `safe_zones.json`: plural slugs (`instagram_reels`, `youtube_shorts`, `facebook_reels`, `youtube_standard`)
  - `config/production/render_profiles.json`: physical specs (`VERTICAL_1080_1920`, `HORIZONTAL_1920_1080`)
- **Impact:** Operators and scripts must map between `instagram_reel` (Phase 1/3) and `instagram_reels` (Phase 4/5).

### `AUD-014` — Non-Atomic JSON Writes & Missing SQLite WAL / Busy Timeout
- **Severity:** `MEDIUM` | **Category:** `DATA_INTEGRITY_RISK` | **Confidence:** `HIGH` | **Priority:** `P2`
- **Evidence:** Direct `open(path, "w")` JSON writes across `media_engine.py`, `audio_analyzer.py`, `production_job.py`, `qc_orchestrator.py`; default SQLite rollback journal without `busy_timeout` in `campaign_manager.py:L30-34`.
- **Recommended Solution:** Atomic temp-file + `os.replace()` JSON writer + SQLite `PRAGMA journal_mode=WAL; PRAGMA busy_timeout=5000`.
- **Estimated Effort:** 3 hours.

### `AUD-021` — Empty Legacy Catalog & Orphan Scratch Folders
- **Severity:** `LOW` | **Category:** `DATA_INTEGRITY_RISK` | **Confidence:** `HIGH` | **Priority:** `P3`
- **Affected Paths:** `data/footage_catalog.json` (0 entries), `data/check_video0/`, `outputs/test-project/`.
- **Recommended Solution:** Archive or remove after confirming no legacy script requires them.
- **Estimated Effort:** 30 minutes.

---

## 4. Artifact Fingerprinting & Deduplication Verification
- **Phase 4.1 Fingerprinting (`multi_platform_exporter.py`):** Verified sound — fingerprints incorporate master SHA-256, manifest hash, render profile config hash, source asset/version info, overlays, and audio config (`test_22`–`test_25` PASS).
- **Phase 2 SHA-256 Catalog Dedup (`audio_catalog.json`):** Verified sound — canonical IDs intact, zero self-references (`test_13` PASS).
