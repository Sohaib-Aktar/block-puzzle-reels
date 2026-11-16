# Quality Control (QC) Report — multiplatform-youtube_tutorial_longform

**Content ID:** `multiplatform-youtube_tutorial_longform`  
**Project:** `block-puzzle-burst`  
**Preset Evaluated:** `youtube_tutorial_longform`  
**File:** `youtube_tutorial_longform.mp4` (2.93 MB)  
**Date:** 2026-11-16 11:14:54  

## 1. Automated Verification Checks

| Check | Expected Spec | Actual Result | Status |
|---|---|---|---|
| **Resolution & Canvas** | 1920x1080 | 1920x1080 | ✅ PASS |
| **Duration Constraints** | 60.0s - 43200.0s | 20.01s | ❌ FAIL |
| **Video Codec** | H.264 (avc1) | h264 | ✅ PASS |
| **Audio Stream** | AAC stereo | aac (2ch) | ✅ PASS |
| **Playback Integrity** | Zero decode errors | Decodes cleanly | ✅ PASS |
| **Project Profile Validation** | Verified profile for block-puzzle-burst | Profile verified | ✅ PASS |
| **On-Screen Text Policy** | English only on-screen | Standard English verified | ✅ PASS |

## 2. Visual & Audio Inspection Notes
- Video stream: 1920x1080 @ 30.0 fps, yuvj420p
- Audio stream: aac @ 48000 Hz, 2 channels
- Safe zone compliance: Checked against preset margins

## 3. Final QC Disposition
### ❌ QC STATUS: FAILED (Re-render or parameter fix required)
One or more checks did not meet specifications.
