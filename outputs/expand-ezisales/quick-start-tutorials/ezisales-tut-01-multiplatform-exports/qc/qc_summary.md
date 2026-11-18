# Automated QC Summary — ezisales-tut-01-multiplatform-exports

**QC Job ID:** `QC_PACK_EXPAND-EZISALES_ezisales-tut-01-multiplatform-exports_20261118_114749_A86FC5`  
**Project:** `expand-ezisales`  
**Platform Destination:** `instagram_reels, youtube_shorts, facebook_reels, youtube_standard`  
**Rendering Profile:** `4 unique physical artifact(s)`  
**Overall QC Result:** **`FAIL`**  
**Blocks Progression:** `True`  
**Timestamp:** `2026-11-18T11:48:16.180775`  

## 1. Check Breakdown
- Total Checks: **4** | PASS: **0** | PASS_WITH_WARNINGS: **0** | REVIEW_REQUIRED: **0** | FAIL: **4** | BLOCKED: **0**

| Category | Check | Method | Status | Actual Result |
|---|---|---|---|---|
| platform | `platform_qc_instagram_reels` | orchestrated | **FAIL** | FAIL (artifact=VERTICAL_1080_1920, reused_scan=False) |
| platform | `platform_qc_youtube_shorts` | orchestrated | **FAIL** | FAIL (artifact=VERTICAL_1080_1920, reused_scan=False) |
| platform | `platform_qc_facebook_reels` | orchestrated | **FAIL** | FAIL (artifact=VERTICAL_1080_1920, reused_scan=False) |
| platform | `platform_qc_youtube_standard` | orchestrated | **FAIL** | FAIL (artifact=HORIZONTAL_1920_1080, reused_scan=False) |

## 2. Detected Issues & Evidence

- **[REVIEW] `AUD_007` (asr_unavailable_manual_review)** @ `0.0s-15.53s`: No offline ASR model installed in workspace environment — *Recommendation:* Human reviewer must listen to verify voiceover intelligibility and script accuracy.
- **[WARNING] `VIS_002` (static_hold_detected)** @ `0.067s-2.133s`: Static segment of 2.07s — *Recommendation:* Verify static hold (e.g. opening board pause or outro card) is intentional.
- **[CRITICAL] `CNT_001` (placeholder_or_non_erp_footage)** @ `0.0s`: Detected non-ERP UI elements (['mobile data', 'aeroplane', 'bluetooth', 'torch', 'bedtime']) and empty screen-recordings folder — *Recommendation:* Supply genuine screen recordings in source_assets/expand-ezisales/screen-recordings/ and re-render.
- **[VERIFICATION_REQUIRED] `CLM_001` (unsupported_marketing_claim)** @ `11.0s`: Unverified claim 'Under 30s' in manifest_overlay:scene_03_cloud_sync: "Booked in Under 30s ⚡" — *Recommendation:* Claim 'Under 30s' is not substantiated in projects/expand-ezisales/knowledge/verified_features.md or marketing_claims.md. Obtain written approval or remove claim.
- **[VERIFICATION_REQUIRED] `CLM_002` (unsupported_marketing_claim)** @ `13.1s`: Unverified claim 'Under 30s' in ocr:scene_03_cloud_sync: "Booked in Under 30s" — *Recommendation:* Claim 'Under 30s' is not substantiated in projects/expand-ezisales/knowledge/verified_features.md or marketing_claims.md. Obtain written approval or remove claim.
- **[CRITICAL] `CRV_001` (missing_cta)** @ `closing`: No CTA keywords detected in closing overlays or OCR — *Recommendation:* Add approved closing CTA overlay matching the creative brief.
- **[REVIEW] `AUD_007` (asr_unavailable_manual_review)** @ `0.0s-15.53s`: No offline ASR model installed in workspace environment — *Recommendation:* Human reviewer must listen to verify voiceover intelligibility and script accuracy.
- **[WARNING] `VIS_002` (static_hold_detected)** @ `0.067s-2.133s`: Static segment of 2.07s — *Recommendation:* Verify static hold (e.g. opening board pause or outro card) is intentional.
- **[CRITICAL] `CNT_001` (placeholder_or_non_erp_footage)** @ `0.0s`: Detected non-ERP UI elements (['mobile data', 'aeroplane', 'bluetooth', 'torch', 'bedtime']) and empty screen-recordings folder — *Recommendation:* Supply genuine screen recordings in source_assets/expand-ezisales/screen-recordings/ and re-render.
- **[VERIFICATION_REQUIRED] `CLM_001` (unsupported_marketing_claim)** @ `11.0s`: Unverified claim 'Under 30s' in manifest_overlay:scene_03_cloud_sync: "Booked in Under 30s ⚡" — *Recommendation:* Claim 'Under 30s' is not substantiated in projects/expand-ezisales/knowledge/verified_features.md or marketing_claims.md. Obtain written approval or remove claim.
- **[VERIFICATION_REQUIRED] `CLM_002` (unsupported_marketing_claim)** @ `13.1s`: Unverified claim 'Under 30s' in ocr:scene_03_cloud_sync: "Booked in Under 30s" — *Recommendation:* Claim 'Under 30s' is not substantiated in projects/expand-ezisales/knowledge/verified_features.md or marketing_claims.md. Obtain written approval or remove claim.
- **[CRITICAL] `CRV_001` (missing_cta)** @ `closing`: No CTA keywords detected in closing overlays or OCR — *Recommendation:* Add approved closing CTA overlay matching the creative brief.
- **[REVIEW] `AUD_007` (asr_unavailable_manual_review)** @ `0.0s-15.53s`: No offline ASR model installed in workspace environment — *Recommendation:* Human reviewer must listen to verify voiceover intelligibility and script accuracy.
- **[WARNING] `VIS_002` (static_hold_detected)** @ `0.067s-2.133s`: Static segment of 2.07s — *Recommendation:* Verify static hold (e.g. opening board pause or outro card) is intentional.
- **[CRITICAL] `CNT_001` (placeholder_or_non_erp_footage)** @ `0.0s`: Detected non-ERP UI elements (['mobile data', 'aeroplane', 'bluetooth', 'torch', 'bedtime']) and empty screen-recordings folder — *Recommendation:* Supply genuine screen recordings in source_assets/expand-ezisales/screen-recordings/ and re-render.
- **[VERIFICATION_REQUIRED] `CLM_001` (unsupported_marketing_claim)** @ `11.0s`: Unverified claim 'Under 30s' in manifest_overlay:scene_03_cloud_sync: "Booked in Under 30s ⚡" — *Recommendation:* Claim 'Under 30s' is not substantiated in projects/expand-ezisales/knowledge/verified_features.md or marketing_claims.md. Obtain written approval or remove claim.
- **[VERIFICATION_REQUIRED] `CLM_002` (unsupported_marketing_claim)** @ `13.1s`: Unverified claim 'Under 30s' in ocr:scene_03_cloud_sync: "Booked in Under 30s" — *Recommendation:* Claim 'Under 30s' is not substantiated in projects/expand-ezisales/knowledge/verified_features.md or marketing_claims.md. Obtain written approval or remove claim.
- **[CRITICAL] `CRV_001` (missing_cta)** @ `closing`: No CTA keywords detected in closing overlays or OCR — *Recommendation:* Add approved closing CTA overlay matching the creative brief.
- **[REVIEW] `AUD_007` (asr_unavailable_manual_review)** @ `0.0s-15.53s`: No offline ASR model installed in workspace environment — *Recommendation:* Human reviewer must listen to verify voiceover intelligibility and script accuracy.
- **[WARNING] `VIS_002` (static_hold_detected)** @ `0.067s-2.5s`: Static segment of 2.43s — *Recommendation:* Verify static hold (e.g. opening board pause or outro card) is intentional.
- **[CRITICAL] `CNT_001` (placeholder_or_non_erp_footage)** @ `0.0s`: Detected non-ERP UI elements (['mobile data', 'aeroplane', 'bluetooth', 'torch', 'bedtime']) and empty screen-recordings folder — *Recommendation:* Supply genuine screen recordings in source_assets/expand-ezisales/screen-recordings/ and re-render.
- **[VERIFICATION_REQUIRED] `CLM_001` (unsupported_marketing_claim)** @ `11.0s`: Unverified claim 'Under 30s' in manifest_overlay:scene_03_cloud_sync: "Booked in Under 30s ⚡" — *Recommendation:* Claim 'Under 30s' is not substantiated in projects/expand-ezisales/knowledge/verified_features.md or marketing_claims.md. Obtain written approval or remove claim.
- **[VERIFICATION_REQUIRED] `CLM_002` (unsupported_marketing_claim)** @ `13.1s`: Unverified claim 'Under 30s' in ocr:scene_03_cloud_sync: "Booked in Under 30s D" — *Recommendation:* Claim 'Under 30s' is not substantiated in projects/expand-ezisales/knowledge/verified_features.md or marketing_claims.md. Obtain written approval or remove claim.
- **[CRITICAL] `CRV_001` (missing_cta)** @ `closing`: No CTA keywords detected in closing overlays or OCR — *Recommendation:* Add approved closing CTA overlay matching the creative brief.

## 3. Evidence-Based Creative Rubric (9 Dimensions)

| Dimension | Method | Auto Status | Score | Evidence |
|---|---|---|---|---|
| 1. Hook Strength (0-2s) | hybrid_automated_plus_human | **PASS** | 8/10 | Opening hook text detected within first 2.5s |
| 2. Story Clarity | human_subjective_review | **REVIEW_REQUIRED** | Human Review | Timeline checkpoints sampled: 3; narrative clarity requires human editorial sign-off. |
| 3. Audience Relevance | human_subjective_review | **REVIEW_REQUIRED** | Human Review | Emotional appeal and audience resonance cannot be verified deterministically. |
| 4. Product Accuracy & Ground Truth | automated_evidence | **FAIL** | 2/10 | Verified against project knowledge repository & screen OCR. |
| 5. Brand Consistency | automated_evidence | **PASS** | 9/10 | Zero foreign project branding detected. |
| 6. Text Readability & Safe Areas | automated_evidence | **PASS** | 9/10 | Local OCR extracted 34 text lines with bounding-box safe-zone verification. |
| 7. Pacing & Momentum | automated_evidence | **PASS** | 9/10 | max_freeze=2.067s, max_black=0.0s |
| 8. CTA Singularity | automated_evidence | **FAIL** | 0/10 | Missing closing CTA. |
| 9. Platform Suitability | automated_evidence | **PASS** | 9/10 | Matches platform profile resolution, fps, duration, and codecs. |

## 4. Mandatory Human Approval Policy
- Automated QC never auto-publishes any video.
- Record final human approval, rejection, or justified override via `python scripts/qc_orchestrator.py approve ...`.
