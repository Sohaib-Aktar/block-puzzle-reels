# Phase 5 — QC Calibration & Held-Out Validation Report

**Studio:** Pyapiras Games — AI Marketing & Creative Content Production Studio  
**Harness Script:** `scripts/qc_calibration.py`  
**Raw Results Artifact:** `data/qc_calibration_results.json`  
**Executed At:** `2026-11-18T11:53:36` (`67.93s` total runtime)

---

## 1. Benchmark Design & Split Separation

To empirically measure false-pass and false-failure behavior without overfitting thresholds to a single dataset, the Phase 5 benchmark evaluates **22 labeled video cases** divided cleanly across:

1. **Calibration Split (9 cases):** Used to validate threshold behavior on core clean and defective patterns.
2. **Held-Out Validation Split (13 cases):** Unseen defect combinations, alternate aspect ratios (`16:9`), OCR safe-zone/missing-text failures, unverified claims, pending licensing, and **3 real studio renders** from Phases 3–4.

Results are also tracked separately across three evaluation tracks so deterministic precision is never conflated with OCR or real-world studio noise:
- **Deterministic Only:** 14 cases
- **WinRT OCR Only:** 5 cases
- **Real Studio Renders Only:** 3 cases

---

## 2. Empirical Confusion Matrix & Error Rates

| Evaluation Slice | Cases | TP | FP | TN | FN | Precision | Recall | Critical False-Pass Rate | False-Failure Rate |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **Overall (All 22 Cases)** | **22** | **17** | **0** | **5** | **0** | **1.000** | **1.000** | **0.000** | **0.000** |
| Calibration Split | 9 | 7 | 0 | 2 | 0 | 1.000 | 1.000 | 0.000 | 0.000 |
| **Held-Out Validation Split** | **13** | **10** | **0** | **3** | **0** | **1.000** | **1.000** | **0.000** | **0.000** |
| Deterministic Track Only | 14 | 12 | 0 | 2 | 0 | 1.000 | 1.000 | 0.000 | 0.000 |
| Local WinRT OCR Track Only | 5 | 3 | 0 | 2 | 0 | 1.000 | 1.000 | 0.000 | 0.000 |
| Real Studio Renders Only | 3 | 2 | 0 | 1 | 0 | 1.000 | 1.000 | 0.000 | 0.000 |

**Definitions:**
- **TP (True Positive):** Ground-truth defective case where QC detected the target defect (returning `FAIL` or `REVIEW_REQUIRED` for verification-gated defects).
- **TN (True Negative):** Ground-truth clean case where QC did NOT raise a false `FAIL` or spurious defect.
- **FP (False Positive / False Failure):** Ground-truth clean case incorrectly flagged as defective.
- **FN (False Negative / Critical False Pass):** Ground-truth defective case missed by automated QC.

---

## 3. Calibration Iteration Log (Transparent Engineering Note)

During the initial calibration run, 4 synthetic clean fixtures triggered `frozen_frames_detected` (`FP=4`). Root-cause inspection revealed a defect in the **fixture generator** (`_make_text_frame` drew an opaque static PNG covering 99.3% of the frame with only a `120x120` moving corner box, making the fixture genuinely frozen across 99.3% of pixels). Fixing `_make_text_frame` to composite a transparent RGBA text badge over animated `testsrc2` background motion resolved all 4 false positives **without relaxing any QC detector threshold**.

---

## 4. Complete 22-Case Labeled Dataset Breakdown

### 4.1 Calibration Split (9 Cases)

| Case ID | Track | Expected Defect | Target Issue | Overall Result | Correct |
|---|---|---|---|---|---|
| `CAL_DET_CLEAN_01` | deterministic | No | `None` | `PASS_WITH_WARNINGS` | Yes |
| `CAL_DET_BLACK_02` | deterministic | Yes | `unexpected_black_frames` | `FAIL` | Yes |
| `CAL_DET_FREEZE_03` | deterministic | Yes | `frozen_frames_detected` | `FAIL` | Yes |
| `CAL_DET_CLIP_04` | deterministic | Yes | `audio_clipping` | `FAIL` | Yes |
| `CAL_DET_NOAUD_05` | deterministic | Yes | `missing_audio` | `FAIL` | Yes |
| `CAL_DET_BRAND_06` | deterministic | Yes | `incorrect_project_branding` | `FAIL` | Yes |
| `CAL_DET_LIC_07` | deterministic | Yes | `restricted_or_unknown_audio_license` | `FAIL` | Yes |
| `CAL_OCR_CLEAN_08` | ocr | No | `None` | `PASS_WITH_WARNINGS` | Yes |
| `CAL_OCR_CLIPTXT_09` | ocr | Yes | `clipped_text` | `FAIL` | Yes |

### 4.2 Held-Out Validation Split (13 Cases)

| Case ID | Track | Expected Defect | Target Issue | Overall Result | Correct |
|---|---|---|---|---|---|
| `VAL_DET_CLEAN16X9_10` | deterministic | No | `None` | `PASS_WITH_WARNINGS` | Yes |
| `VAL_DET_SILENCE_11` | deterministic | Yes | `excessive_silence` | `FAIL` | Yes |
| `VAL_DET_AVSYNC_12` | deterministic | Yes | `av_sync_mismatch` | `FAIL` | Yes |
| `VAL_DET_WRONGPROF_13` | deterministic | Yes | `resolution_match` | `FAIL` | Yes |
| `VAL_DET_NOCTA_14` | deterministic | Yes | `missing_cta` | `FAIL` | Yes |
| `VAL_DET_CLAIM_15` | deterministic | Yes | `unsupported_marketing_claim` | `REVIEW_REQUIRED` | Yes |
| `VAL_DET_REVLIC_16` | deterministic | Yes | `unverified_audio_licensing` | `REVIEW_REQUIRED` | Yes |
| `VAL_OCR_CLEAN16X9_17` | ocr | No | `None` | `PASS_WITH_WARNINGS` | Yes |
| `VAL_OCR_UNSAFE_18` | ocr | Yes | `unsafe_text_placement` | `FAIL` | Yes |
| `VAL_OCR_MISSTXT_19` | ocr | Yes | `expected_text_missing` | `FAIL` | Yes |
| `VAL_REAL_DAY04_CLEAN_20` | real_studio | No | `None` (Phase 3 Day 04 mixed audio) | `REVIEW_REQUIRED` (ASR pending only) | Yes |
| `VAL_REAL_DAY04_SILENT_21` | real_studio | Yes | `silent_audio_track` (Remotion Day 04 master) | `FAIL` | Yes |
| `VAL_REAL_EZISALES_DEFECT_22` | real_studio | Yes | `placeholder_or_non_erp_footage` (Pilot B) | `FAIL` | Yes |

---

## 5. Statistical Scope & Honest Limitations

- **Sample Size Caveat:** While all 22/22 cases scored `1.000` precision and `1.000` recall with `0.000` critical false-pass rate, 19 cases are controlled FFmpeg synthetic renders and 3 are real studio assets. As the studio produces real screen-recorded ERP tutorials (`expand-ezisales`, `expand-hr`, `wms`, `pos`) and more gameplay reels, additional real-world labeled examples should be added to `scripts/qc_calibration.py` to track edge cases (e.g., low-contrast stylized fonts, rapid gameplay particle effects over text, background noise in human voiceovers).
- **Unmeasured Capabilities:** Offline speech-to-text accuracy and subjective creative rubric correlation cannot be measured locally because no offline ASR model or external LLM critic is installed; both remain mandatory human review gates.
