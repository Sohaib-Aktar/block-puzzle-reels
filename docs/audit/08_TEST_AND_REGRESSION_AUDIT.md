# 08 — Test and Regression Audit

**Studio:** Social Media Video Production Studio  
**Machine-Readable Source:** `data/audit/test_matrix.json`  
**Audit Date:** 2026-11-18

---

## 1. Live Test Execution Results (Post-Cleanup & Post-Renaming)

All 5 automated suites were executed independently on `2026-11-18`:

| Suite | Collected | Passed | Failed | Skipped | Runtime | Production-Isolated? |
|---|---:|---:|---:|---:|---:|---|
| `scripts/test_studio_suite.py` (Phase 1 active tests A, B, D, E) | 4 | 4 | 0 | 0 | 9.95s | **NO (`AUD-008`)** |
| `tests/test_phase2_intake_audio.py` | 15 | 15 | 0 | 0 | 11.54s | **NO** (via Test 11) |
| `tests/test_phase3_production_pipeline.py` | 13 | 13 | 0 | 0 | 2.60s | **YES** |
| `tests/test_phase4_multi_platform_export.py` | 24 | 24 | 0 | 0 | 33.50s | **YES** |
| `tests/test_phase5_automated_qc.py` | 13 | 13 | 0 | 0 | 1.66s | **NO (`AUD-008`)** |
| **Total Automated Tests** | **69** | **69** | **0** | **0** | **59.25s** | **3/5 partial or non-isolated** |

- **Labeled QC Calibration & Held-Out Benchmark (`scripts/qc_calibration.py`):** **22/22 accurate** (`TP=17, FP=0, TN=5, FN=0`, Precision `1.000`, Recall `1.000`, Critical False-Pass Rate `0.000`, `67.93s`).

---

## 2. Comparison Against Previously Reported Counts

| Suite | Previously Reported | Actual Audited Count | Discrepancy Explanation |
|---|---:|---:|---|
| Phase 1 (`test_studio_suite.py`) | 5 | **4** | Intentional: Test C (`run_test_c_expandhr.py`) removed during authorized Expand HR deletion (Part 1). |
| Phase 2 (`test_phase2_intake_audio.py`) | 15 | **15** | Exact match (`test_14` updated to test active 2-project studio). |
| Phase 3 (`test_phase3_production_pipeline.py`) | 13 | **13** | Exact match. |
| Phase 4 (`test_phase4_multi_platform_export.py`) | 24 (numbered `01`–`26`) | **24** | Reconciled: `test_15` & `test_18` were merged during Phase 4 implementation; actual collected count is 24. |
| Phase 5 (`test_phase5_automated_qc.py`) | 13 | **13** | Exact match. |

---

## 3. Critical Test Isolation & Coverage Gaps

### `AUD-008` — Tests Mutate Production State (`MEDIUM`, `P1`)
- `scripts/test_studio_suite.py` (Tests A, B, E) overwrites live files in `outputs/block-puzzle-burst/` and `outputs/expand-ezisales/` and mutates live `data/campaign_tracker.sqlite` (leaving synthetic `test-lifecycle-01` marked `PUBLISHED` inside the real campaign DB).
- `tests/test_phase5_automated_qc.py:test_11_human_approval_gate_and_override_audit` appends synthetic `OVERRIDE_APPROVE` records by `"Studio Director"` directly into live `data/qc_approval_audit.jsonl` and drops test JSONs into live `data/qc_jobs/` on every run.
- **Impact:** Pollutes compliance audit logs and creates dirty Git diffs after every test run.

### `AUD-018` — 11 Scripts Without Direct Unit Test Coverage (`MEDIUM`, `P2`)
- **Zero direct unit tests:** `scripts/drive_sync.py`, `scripts/content_workflow.py`, `scripts/marketing_director.py`, `scripts/inspect_footage.py`, `scripts/inspect_real_audio.py`, `scripts/qc_verifier.py`, `scripts/creative_qc.py`, `scripts/footage_analyzer.py` CLI, `scripts/audio_mixer.py` edge cases, `scripts/render_manager.py` failure recovery paths, and `scripts/win_ocr.ps1` failure paths.
- **Unverified Bug Assertions:** Existing tests did NOT assert against cross-project hashtag leakage (`AUD-003`), `campaign_manager.py` `QC_APPROVED` bypass (`AUD-002`), or `audio_engine.py` PowerShell quote injection (`AUD-001`).

---

## 4. Platform & Environment Assumptions in Tests
- **Windows-Only Dependencies:** Phase 1/3 TTS tests require Windows SAPI5 (`System.Speech`), and Phase 5 OCR tests require Windows WinRT (`Windows.Media.Ocr.OcrEngine`). Tests will fail on Linux/macOS CI runners without conditional skips or cross-platform backends.
- **Bundled FFmpeg Dependency:** Tests cleanly rely on `imageio-ffmpeg` (`9.0.2`), requiring zero system `PATH` FFmpeg install.
