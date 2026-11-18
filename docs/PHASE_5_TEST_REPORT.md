# Phase 5 — Automated QC Test & Studio Regression Report

**Studio:** Pyapiras Games — AI Marketing & Creative Content Production Studio  
**Date:** 2026-11-18  
**Environment:** Windows 11, Python 3.x, FFmpeg `9.0.2` (`imageio-ffmpeg`), Pillow `13.0.0`, NumPy `2.4.2`, Windows WinRT OCR (`en-US`)

---

## 1. Executive Test Summary

| Test Suite | Command | Collected / Executed | Passed | Failed | Runtime | Status |
|---|---|---:|---:|---:|---:|---|
| **Phase 5 — Automated QC** | `python tests/test_phase5_automated_qc.py` | 13 | 13 | 0 | 1.92s | **PASS** |
| **Phase 5 — Calibration & Held-Out Benchmark** | `python scripts/qc_calibration.py` | 22 cases (9 cal + 13 held-out) | 22 | 0 | 67.93s | **PASS** |
| **Phase 4 + Shared-Artifact Regression** | `python tests/test_phase4_multi_platform_export.py` | 24 (`test_01`–`test_26`, minus merged `15` & `18`) | 24 | 0 | 32.57s | **PASS** |
| **Phase 3 — Production Pipeline Regression** | `python tests/test_phase3_production_pipeline.py` | 13 | 13 | 0 | 2.37s | **PASS** |
| **Phase 2 — Media Intake & Audio Regression** | `python tests/test_phase2_intake_audio.py` | 15 (includes Phase 1 suite) | 15 | 0 | 14.94s | **PASS** |
| **Phase 1 — Foundation Standalone Suite** | `python scripts/test_studio_suite.py` | 5 | 5 | 0 | ~15s | **PASS** |

- **Total Unit / Integration Tests Executed:** **70 / 70 PASS** (13 Phase 5 + 24 Phase 4 + 13 Phase 3 + 15 Phase 2 + 5 Phase 1 standalone).
- **Total Labeled QC Benchmark Cases:** **22 / 22 accurate** (`TP=17, FP=0, TN=5, FN=0`, Precision `1.000`, Recall `1.000`, Critical False-Pass Rate `0.000`, False-Failure Rate `0.000`).
- **Failed or Incomplete Tests:** `0` failed. Offline ASR (`AUD_007`) and subjective creative rubric dimensions 2 & 3 remain explicitly flagged `REVIEW_REQUIRED` due to absence of local ASR/LLM models.

---

## 2. Phase 5 Automated Test Suite Breakdown (`tests/test_phase5_automated_qc.py`)

| # | Test Method | Verified Behavior | Result |
|---|---|---|---|
| 1 | `test_01_critical_failure_overrides_positive_checks` | High passing count cannot mask a single `CRITICAL` failure (`overall_status == FAIL`, `blocks_progression == True`). | PASS |
| 2 | `test_02_review_required_never_silently_passes` | Unresolved `REVIEW_REQUIRED` checks never collapse to `PASS` or `PASS_WITH_WARNINGS`. | PASS |
| 3 | `test_03_missing_input_returns_blocked` | Missing video file returns `BLOCKED` with `blocks_progression == True`. | PASS |
| 4 | `test_04_audio_qc_detects_silent_vs_mixed_audio` | Live Audio QC flags Remotion Day 04 silent master (`-70.0 LUFS`, `FAIL`) vs. Phase 3 Day 04 mixed audio (`-14.8 LUFS`, `PASS` on loudness). | PASS |
| 5 | `test_05_visual_qc_real_winrt_ocr_extraction` | Offline Windows WinRT OCR extracts exact text and bounding boxes on live studio frame. | PASS |
| 6 | `test_06_content_qc_brand_isolation_catches_cross_project_leak` | Foreign brand terms (e.g., `Expand HR` inside `block-puzzle-burst`) trigger `CRITICAL FAIL (BRD_001)`. | PASS |
| 7 | `test_07_content_qc_flags_unsupported_marketing_claims` | Unverified quantitative/guarantee claims trigger `VERIFICATION_REQUIRED` (`REVIEW_REQUIRED`). | PASS |
| 8 | `test_08_documentary_licensing_enforcement` | `CLEARED -> PASS`, `NEEDS_REVIEW -> REVIEW_REQUIRED`, `RESTRICTED/UNKNOWN -> FAIL`. | PASS |
| 9 | `test_09_shared_artifact_pack_qc_deduplicates_physical_scans` | Verifies `day-04-shared-exports` scanned 2 unique physical files while producing 4 independent platform QC records (`instagram_reels`, `facebook_reels`, `youtube_shorts`, `youtube_standard`). | PASS |
| 10 | `test_10_pilot_b_ezisales_catches_placeholder_and_unverified_claim` | Verifies Pilot B QC caught `placeholder_or_non_erp_footage`, `unsupported_marketing_claim` (`Under 30s`), and `missing_cta`. | PASS |
| 11 | `test_11_human_approval_gate_and_override_audit` | Rejects standard `APPROVE` on `BLOCKED`/`FAIL`, enforces override justification, writes `auto_published: false` to `data/qc_approval_audit.jsonl`. | PASS |
| 12 | `test_12_compare_reports` | Compares before/after QC JSON reports and classifies resolved vs. persistent defects accurately. | PASS |
| 13 | `test_13_calibration_and_held_out_metrics_verified` | Verifies `data/qc_calibration_results.json` meets precision, recall, and `0.000` critical false-pass criteria across calibration and held-out splits. | PASS |

---

## 3. Live Studio QC Execution Evidence

| Target | QC Job ID | Physical Scans / Platforms | Overall Result | Key Findings |
|---|---|---|---|---|
| `day-04-shared-exports` (Block Puzzle Burst) | `QC_PACK_BLOCK-PUZZLE-BURST_day-04-shared-exports_20261118_114642_760CDC` | 2 unique artifacts / 4 platforms | **`FAIL`** | Caught `-70.0 LUFS` (`100%` silent) AAC track on Remotion master across all 4 destinations (`AUD_004`, `AUD_005`). Visual/OCR checks passed (`56` OCR lines). |
| `day-04-no-wifi-revision` (Block Puzzle Burst, Phase 3) | `QC_BLOCK-PUZZLE-BURST_day-04-no-wifi-revision_20261118_114728_1BCB60` | 1 master / `instagram_reels` | **`REVIEW_REQUIRED`** | `33/35` checks `PASS` (`-14.8 LUFS`, `-1.3 dBTP`, `4/4` OCR overlays matched, `3/3` cleared audio licenses); 1 warning (`AUD_005` tail gap `4.43s`); 1 review gate (`AUD_007` offline ASR unavailable). |
| `ezisales-tut-01-multiplatform-exports` (Expand EziSales, Pilot B) | `QC_PACK_EXPAND-EZISALES_ezisales-tut-01-multiplatform-exports_20261118_114749_A86FC5` | 4 artifacts / 4 platforms | **`FAIL`** | Caught `CNT_001 (placeholder_or_non_erp_footage)` via Android settings OCR + empty `screen-recordings/`, `CLM_001/002` (`"Under 30s"` unverified claim in manifest & OCR), and `CRV_001 (missing_cta)`. |

---

## 4. Regression & Safety Verification Checklist

- Existing approved masters unchanged: **Verified** (all Phase 1–4 deliverables intact).
- Shared video artifacts remain reusable: **Verified** (`test_22`–`test_26` in Phase 4 suite PASS).
- Platform delivery records remain intact: **Verified**.
- Duplicate detection remains functional: **Verified** (`test_08` Phase 2, `test_25`–`test_26` Phase 4).
- Existing manifests and job states remain compatible: **Verified** (Phase 3 `13/13` PASS).
- No existing generated files deleted: **Verified**.
- Zero automatic publishing introduced: **Verified** (`auto_published: false` enforced in code and audited by `test_11`).
- `SolveItReel` untouched during Phase 5: **Verified**.
