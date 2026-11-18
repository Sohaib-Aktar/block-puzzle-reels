# Automated QC Summary — day-04-shared-exports

**QC Job ID:** `QC_PACK_BLOCK-PUZZLE-BURST_day-04-shared-exports_20261118_114642_760CDC`  
**Project:** `block-puzzle-burst`  
**Platform Destination:** `instagram_reels, youtube_shorts, facebook_reels, youtube_standard`  
**Rendering Profile:** `2 unique physical artifact(s)`  
**Overall QC Result:** **`FAIL`**  
**Blocks Progression:** `True`  
**Timestamp:** `2026-11-18T11:47:00.194185`  

## 1. Check Breakdown
- Total Checks: **4** | PASS: **0** | PASS_WITH_WARNINGS: **0** | REVIEW_REQUIRED: **0** | FAIL: **4** | BLOCKED: **0**

| Category | Check | Method | Status | Actual Result |
|---|---|---|---|---|
| platform | `platform_qc_instagram_reels` | orchestrated | **FAIL** | FAIL (artifact=VERTICAL_1080_1920, reused_scan=False) |
| platform | `platform_qc_youtube_shorts` | orchestrated | **FAIL** | FAIL (artifact=VERTICAL_1080_1920, reused_scan=True) |
| platform | `platform_qc_facebook_reels` | orchestrated | **FAIL** | FAIL (artifact=VERTICAL_1080_1920, reused_scan=True) |
| platform | `platform_qc_youtube_standard` | orchestrated | **FAIL** | FAIL (artifact=HORIZONTAL_1920_1080, reused_scan=False) |

## 2. Detected Issues & Evidence

- **[CRITICAL] `AUD_004` (silent_audio_track)** @ `0.0s-15.02s`: integrated_lufs=-70.0 LUFS (effectively silent) — *Recommendation:* Verify audio stem routing; track is silent.
- **[CRITICAL] `AUD_005` (excessive_silence)** @ `0.0s-15.019s`: silence_ratio=100.0%, max_gap=15.02s (1 event(s)) — *Recommendation:* Check missing BGM/VO segments or audio dropouts.
- **[REVIEW] `AUD_007` (asr_unavailable_manual_review)** @ `0.0s-15.02s`: No offline ASR model installed in workspace environment — *Recommendation:* Human reviewer must listen to verify voiceover intelligibility and script accuracy.
- **[CRITICAL] `AUD_004` (silent_audio_track)** @ `0.0s-15.02s`: integrated_lufs=-70.0 LUFS (effectively silent) — *Recommendation:* Verify audio stem routing; track is silent.
- **[CRITICAL] `AUD_005` (excessive_silence)** @ `0.0s-15.019s`: silence_ratio=100.0%, max_gap=15.02s (1 event(s)) — *Recommendation:* Check missing BGM/VO segments or audio dropouts.
- **[REVIEW] `AUD_007` (asr_unavailable_manual_review)** @ `0.0s-15.02s`: No offline ASR model installed in workspace environment — *Recommendation:* Human reviewer must listen to verify voiceover intelligibility and script accuracy.
- **[CRITICAL] `AUD_004` (silent_audio_track)** @ `0.0s-15.02s`: integrated_lufs=-70.0 LUFS (effectively silent) — *Recommendation:* Verify audio stem routing; track is silent.
- **[CRITICAL] `AUD_005` (excessive_silence)** @ `0.0s-15.019s`: silence_ratio=100.0%, max_gap=15.02s (1 event(s)) — *Recommendation:* Check missing BGM/VO segments or audio dropouts.
- **[REVIEW] `AUD_007` (asr_unavailable_manual_review)** @ `0.0s-15.02s`: No offline ASR model installed in workspace environment — *Recommendation:* Human reviewer must listen to verify voiceover intelligibility and script accuracy.
- **[CRITICAL] `AUD_004` (silent_audio_track)** @ `0.0s-15.02s`: integrated_lufs=-70.0 LUFS (effectively silent) — *Recommendation:* Verify audio stem routing; track is silent.
- **[CRITICAL] `AUD_005` (excessive_silence)** @ `0.0s-15.019s`: silence_ratio=100.0%, max_gap=15.02s (1 event(s)) — *Recommendation:* Check missing BGM/VO segments or audio dropouts.
- **[REVIEW] `AUD_007` (asr_unavailable_manual_review)** @ `0.0s-15.02s`: No offline ASR model installed in workspace environment — *Recommendation:* Human reviewer must listen to verify voiceover intelligibility and script accuracy.
- **[WARNING] `VIS_002` (static_hold_detected)** @ `5.2s-8.433s`: Static segment of 3.23s — *Recommendation:* Verify static hold (e.g. opening board pause or outro card) is intentional.

## 3. Evidence-Based Creative Rubric (9 Dimensions)

| Dimension | Method | Auto Status | Score | Evidence |
|---|---|---|---|---|
| 1. Hook Strength (0-2s) | hybrid_automated_plus_human | **PASS** | 8/10 | Opening hook text detected within first 2.5s |
| 2. Story Clarity | human_subjective_review | **REVIEW_REQUIRED** | Human Review | Timeline checkpoints sampled: 5; narrative clarity requires human editorial sign-off. |
| 3. Audience Relevance | human_subjective_review | **REVIEW_REQUIRED** | Human Review | Emotional appeal and audience resonance cannot be verified deterministically. |
| 4. Product Accuracy & Ground Truth | automated_evidence | **PASS** | 10/10 | Verified against project knowledge repository & screen OCR. |
| 5. Brand Consistency | automated_evidence | **PASS** | 9/10 | Zero foreign project branding detected. |
| 6. Text Readability & Safe Areas | automated_evidence | **PASS** | 9/10 | Local OCR extracted 56 text lines with bounding-box safe-zone verification. |
| 7. Pacing & Momentum | automated_evidence | **PASS** | 9/10 | max_freeze=0.0s, max_black=0.0s |
| 8. CTA Singularity | automated_evidence | **PASS** | 9/10 | Approved closing CTA verified. |
| 9. Platform Suitability | automated_evidence | **PASS** | 9/10 | Matches platform profile resolution, fps, duration, and codecs. |

## 4. Mandatory Human Approval Policy
- Automated QC never auto-publishes any video.
- Record final human approval, rejection, or justified override via `python scripts/qc_orchestrator.py approve ...`.
