# Automated QC Summary — day-04-no-wifi-revision

**QC Job ID:** `QC_BLOCK-PUZZLE-BURST_day-04-no-wifi-revision_20261118_114728_1BCB60`  
**Project:** `block-puzzle-burst`  
**Platform Destination:** `instagram_reels`  
**Rendering Profile:** `VERTICAL_1080_1920`  
**Overall QC Result:** **`REVIEW_REQUIRED`**  
**Blocks Progression:** `False`  
**Timestamp:** `2026-11-18T11:47:36.411415`  

## 1. Check Breakdown
- Total Checks: **35** | PASS: **33** | PASS_WITH_WARNINGS: **1** | REVIEW_REQUIRED: **1** | FAIL: **0** | BLOCKED: **0**

| Category | Check | Method | Status | Actual Result |
|---|---|---|---|---|
| technical | `tech_file_exists_non_empty` | deterministic | **PASS** | 1327339 bytes |
| technical | `tech_ffprobe_readable` | deterministic | **PASS** | Readable JSON streams |
| technical | `tech_full_video_decode` | deterministic | **PASS** | Clean full decode |
| technical | `tech_resolution_match` | deterministic | **PASS** | 1080x1920 |
| technical | `tech_aspect_ratio_match` | deterministic | **PASS** | 0.5625 |
| technical | `tech_frame_rate_match` | deterministic | **PASS** | 30.00 fps |
| technical | `tech_codec_and_container_match` | deterministic | **PASS** | h264 / mov,mp4,m4a,3gp,3g2,mj2 / yuv420p |
| technical | `tech_audio_stream_present` | deterministic | **PASS** | Present (aac) |
| technical | `tech_audio_sample_rate_and_channels` | deterministic | **PASS** | aac / 48000 Hz / 2ch |
| technical | `tech_duration_consistent_with_master` | deterministic | **PASS** | 15.03s |
| technical | `tech_no_accidental_stretching` | deterministic | **PASS** | SAR=1:1 |
| technical | `tech_no_missing_or_corrupted_frames` | deterministic | **PASS** | 450 frames (diff=1) |
| technical | `tech_no_unexpected_watermark` | deterministic | **PASS** | Clean filtergraph (manual visual confirmation recommended) |
| technical | `tech_no_opening_or_ending_truncation` | deterministic | **PASS** | start_time=0.000s, duration=15.03s |
| audio | `audio_stream_presence` | deterministic | **PASS** | aac 2ch @ 48000Hz |
| audio | `audio_video_sync` | deterministic | **PASS** | delta=0.033s |
| audio | `audio_clipping_and_true_peak` | deterministic | **PASS** | max_vol=-1.4 dB, true_peak=-1.3 dBTP |
| audio | `integrated_loudness_ebur128` | deterministic | **PASS** | -14.8 LUFS (LRA=3.3 LU, mean=-20.3 dB) |
| audio | `silence_and_audio_gaps` | deterministic | **PASS_WITH_WARNINGS** | silence_ratio=29.5%, max_gap=4.43s |
| audio | `audio_ending_fade_check` | deterministic | **PASS** | tail_mean=-91.0 dB |
| audio | `voiceover_transcript_alignment` | asr_pending | **REVIEW_REQUIRED** | Local ASR engine not installed (Whisper/SAPI ASR unavailable); human audio listen-through required. |
| visual | `unexpected_black_frames` | deterministic | **PASS** | max_black=0.00s |
| visual | `freeze_frame_detection` | deterministic | **PASS** | max_freeze=0.00s (0 event(s)) |
| visual | `multi_frame_blank_check` | image_analysis | **PASS** | 5/5 frames contain active visual content |
| visual | `scene_timeline_structure` | deterministic | **PASS** | Sampled 5 timeline checkpoints; detected 0 visual cut(s) |
| visual_ocr | `ocr_expected_text_presence` | ocr | **PASS** | 4/4 overlays verified (avg conf=1.0) |
| visual_ocr | `ocr_text_edge_clipping` | ocr | **PASS** | Zero edge-clipped text boxes detected |
| visual_ocr | `ocr_safe_zone_placement` | ocr | **PASS** | All detected overlay text within configured safe bounds |
| content | `project_knowledge_availability` | deterministic | **PASS** | Loaded 5 docs (project_profile, verified_features, marketing_claims, brand_guidelines, missing_information) |
| brand | `brand_isolation_compliance` | deterministic | **PASS** | Zero cross-project brand leaks detected for 'block-puzzle-burst' |
| brand | `bpb_english_only_onscreen_policy` | ocr | **PASS** | On-screen text conforms to English-only rule |
| content | `marketing_claims_verification` | deterministic | **PASS** | No unsupported quantitative/guarantee claims detected |
| creative | `cta_presence_check` | deterministic | **PASS** | Closing CTA present and detected |
| licensing | `source_media_provenance` | deterministic | **PASS** | 5 media reference(s) verified intact |
| licensing | `audio_documentary_licensing` | deterministic | **PASS** | cleared=3, review_required=0, blocked=0 |

## 2. Detected Issues & Evidence

- **[WARNING] `AUD_005` (audio_gap_detected)** @ `10.603s-15.033s`: silence_ratio=29.5%, max_gap=4.43s — *Recommendation:* Review silent intervals to ensure they are intentional.
- **[REVIEW] `AUD_007` (asr_unavailable_manual_review)** @ `0.0s-15.03s`: No offline ASR model installed in workspace environment — *Recommendation:* Human reviewer must listen to verify voiceover intelligibility and script accuracy.

## 3. Evidence-Based Creative Rubric (9 Dimensions)

| Dimension | Method | Auto Status | Score | Evidence |
|---|---|---|---|---|
| 1. Hook Strength (0-2s) | hybrid_automated_plus_human | **PASS** | 8/10 | Opening hook text detected within first 2.5s |
| 2. Story Clarity | human_subjective_review | **REVIEW_REQUIRED** | Human Review | Timeline checkpoints sampled: 5; narrative clarity requires human editorial sign-off. |
| 3. Audience Relevance | human_subjective_review | **REVIEW_REQUIRED** | Human Review | Emotional appeal and audience resonance cannot be verified deterministically. |
| 4. Product Accuracy & Ground Truth | automated_evidence | **PASS** | 10/10 | Verified against project knowledge repository & screen OCR. |
| 5. Brand Consistency | automated_evidence | **PASS** | 9/10 | Zero foreign project branding detected. |
| 6. Text Readability & Safe Areas | automated_evidence | **PASS** | 9/10 | Local OCR extracted 57 text lines with bounding-box safe-zone verification. |
| 7. Pacing & Momentum | automated_evidence | **PASS** | 9/10 | max_freeze=0.0s, max_black=0.0s |
| 8. CTA Singularity | automated_evidence | **PASS** | 9/10 | Approved closing CTA verified. |
| 9. Platform Suitability | automated_evidence | **PASS** | 9/10 | Matches platform profile resolution, fps, duration, and codecs. |

## 4. Mandatory Human Approval Policy
- Automated QC never auto-publishes any video.
- Record final human approval, rejection, or justified override via `python scripts/qc_orchestrator.py approve ...`.
