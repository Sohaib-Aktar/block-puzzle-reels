# QC Result Model & Severity Classification Guide

**Studio:** Social Media Video Production Studio  
**Implementation:** `scripts/qc_report_builder.py`

---

## 1. Unified QC Result Statuses

Every individual check and every overall QC job resolves to one of five canonical statuses:

| Status | Blocks Progression? | Meaning | Required Action |
|---|---|---|---|
| **`PASS`** | No | All deterministic, OCR, and documentary checks passed with zero defects and zero unresolved review gates. | Proceed to mandatory human approval (`AWAITING_HUMAN_APPROVAL`). |
| **`PASS_WITH_WARNINGS`** | No | No critical failures or unresolved mandatory reviews, but one or more minor/non-blocking advisories occurred (e.g., slight loudness variance, intentional static hold, minor audio tail gap). | Human reviewer inspects warnings before signing off. |
| **`REVIEW_REQUIRED`** | No (blocks auto-clearance; requires human sign-off) | Automated checks could not deterministically certify one or more requirements (e.g., offline ASR unavailable, audio license marked `NEEDS_REVIEW`, unverified marketing claim, or subjective creative dimensions). | Human reviewer must verify flagged items and explicitly `APPROVE` or `REJECT`. |
| **`FAIL`** | **Yes** (`blocks_progression: true`) | One or more `CRITICAL` technical, audio, visual, brand, content, platform, or licensing failures occurred. | Fix source/render defect and re-run QC, or provide documented `OVERRIDE_APPROVE` justification (never auto-approved). |
| **`BLOCKED`** | **Yes** (`blocks_progression: true`) | Required inputs are missing or unreadable (missing video file, corrupt container, unreadable manifest, missing export pack). | Restore missing inputs before QC can run. |

---

## 2. Critical-Failure Override Rule

**Hard Rule:** A high creative score or high ratio of passing checks can **NEVER** mask a critical defect.

Aggregation precedence in `scripts/qc_report_builder.py`:
1. Any `BLOCKED` check -> Overall **`BLOCKED`** (`blocks_progression = true`).
2. Any `FAIL` check or any `CRITICAL` issue -> Overall **`FAIL`** (`blocks_progression = true`).
3. Any `REVIEW_REQUIRED` check or `VERIFICATION_REQUIRED` / `REVIEW` issue -> Overall **`REVIEW_REQUIRED`** (`blocks_progression = false`, human review mandatory).
4. Any `PASS_WITH_WARNINGS` check or `WARNING` issue -> Overall **`PASS_WITH_WARNINGS`**.
5. Otherwise -> Overall **`PASS`**.

---

## 3. Issue Severity Tiers & Check Catalog

### `CRITICAL` (Forces Overall `FAIL`)
- **Technical (`TECH_*`):** Missing/empty file, ffprobe read failure, decode error, resolution/aspect/FPS/codec mismatch against platform profile, SAR distortion, frame corruption, opening/ending truncation.
- **Audio (`AUD_001`–`AUD_006`):** Missing audio stream, `A/V sync delta > 0.35s`, digital clipping (`max_volume >= -0.05 dB` or `true_peak > -0.1 dBTP`), effectively silent track (`integrated_lufs <= -55 LUFS`), excessive silence (`silence_ratio >= 65%` or `max_gap >= 8.0s`).
- **Visual & OCR (`VIS_*`, `OCR_*`):** Unexpected black frames (`>= 0.5s`), unintended freeze frames (`>= 4.0s`), blank/solid sampled frames, missing expected overlay text, frame-edge clipped text (`x <= 4px` or `x+w >= W-4px`), overlay text intruding into platform UI danger zones.
- **Content & Brand (`BRD_001`, `CNT_001`, `CRV_001`):** Cross-project brand contamination (e.g., Expand eziSales terms in a Block Puzzle Burst video), non-ERP/placeholder UI footage when ERP screen recordings are absent, missing closing CTA when required.
- **Licensing (`LIC_001`, `LIC_003`):** Missing/tampered SHA-256 media provenance, audio asset marked `RESTRICTED` or `UNKNOWN` commercial license status.

### `VERIFICATION_REQUIRED` / `REVIEW` (Forces `REVIEW_REQUIRED` if no `CRITICAL` present)
- `AUD_007 (asr_unavailable_manual_review)` — Offline ASR engine not installed; human listen-through required.
- `CLM_001` / `CLM_002 (unsupported_marketing_claim)` — Quantitative, percentage, time-saving, or guarantee claim (e.g., `"Under 30s"`, `"100% guaranteed"`, `"3x faster"`) not substantiated in `projects/<project>/knowledge/verified_features.md` or `marketing_claims.md`.
- `LIC_002 (unverified_audio_licensing)` — Audio catalog entry marked `NEEDS_REVIEW` (missing written license documentation).
- `OCR_004 (ocr_low_confidence)` — Low fuzzy match score on expected text requiring visual inspection.
- Subjective Creative Rubric dimensions 2 (*Story Clarity*) and 3 (*Audience Relevance*).

### `WARNING` (Forces `PASS_WITH_WARNINGS` if no `CRITICAL` or `REVIEW` present)
- `AUD_004 (loudness_out_of_target_range)` — Loudness outside target `-16` to `-12 LUFS` window (but audible and unclipped).
- `AUD_005 (audio_gap_detected)` — Silent interval between `2.5s` and `8.0s` (e.g., intentional outro tail).
- `AUD_006 (abrupt_audio_ending)` — Audio energy remains high in the final `0.3s` without fade-out.
- `VIS_002 (static_hold_detected)` — Static hold between `2.0s` and `4.0s` (often an intentional intro board or outro card).

---

## 4. Machine-Readable Check Schema

Every check item in `qc_report.json` follows a uniform schema:
```json
{
  "category": "audio",
  "check_id": "integrated_loudness_ebur128",
  "method": "deterministic",
  "status": "PASS",
  "expected": "-16.0 to -12.0 LUFS",
  "actual": "-14.8 LUFS (LRA=3.3 LU, mean=-20.3 dB)",
  "confidence": 1.0,
  "evidence": {
    "integrated_lufs": -14.8,
    "true_peak_dbtp": -1.3
  }
}
```
- `method`: `deterministic` | `image_analysis` | `ocr` | `asr_pending` | `hybrid_automated_plus_human` | `human_subjective_review` | `orchestrated`.
- `confidence`: `1.0` for deterministic DSP/metadata checks, `0.0–1.0` fuzzy similarity for OCR matches, `0.0` for unavailable/human-only checks.
