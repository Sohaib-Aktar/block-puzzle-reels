# Phase 2 — Real Audio Sample Analysis & Licensing Clearance Report

**Studio:** Pyapiras Games  
**Workspace:** `C:\Users\Dell\Downloads\video gen\`  
**Date:** 2026-11-17  
**Sample Source:** `Raw_input_files/audio/`  
**Total Samples Evaluated:** 23 MP3 Files  
**Decoding Integrity:** 23/23 Cleanly Decoded (0 Errors)  
**Duplicate Assets Identified:** 1 Byte-Identical Duplicate Pair  
**Licensing Provenance:** User-Supplied Sample Soundtrack (`NEEDS_REVIEW`)  

---

## 1. Executive Summary

All 23 MP3 files provided in `Raw_input_files/audio/` were discovered, ingested, and inspected using the Phase 2 Media Intake and Audio Intelligence system. Each audio stream underwent:
1. **Byte-Level Integrity & SHA-256 Hashing:** Calculation of true 64-character content hashes and canonical deduplication.
2. **FFmpeg Stream Verification:** Decoding stream check ensuring zero corrupt packets or decoding errors.
3. **EBU R128 Broadcast Loudness Measurement:** Measurement of Integrated Loudness (LUFS), True Peak (dBTP), and Loudness Range (LU).
4. **Acoustic Waveform Analysis:** Peak dBFS, RMS dBFS, clipping detection, silence duration ratio, and spectral energy levels.
5. **Musical DSP Analysis:** Envelope autocorrelation BPM estimation with confidence ratings (`high`, `medium`, `low`), rhythm classification, and heuristic mood tagging.
6. **Licensing Provenance Gatekeeping:** Strict assignment of `USER_SUPPLIED`, `USER_DECLARED_NO_COPYRIGHT`, `NEEDS_REVIEW`, and `commercial_use_allowed: false`.

---

## 2. Technical Inspection Matrix (All 23 Tracks)

| # | Filename | Asset ID | Dur (s) | BPM (Conf) | LUFS | Peak dBTP | Energy | Moods | Duplicate Status |
|---|---|---|---|---|---|---|---|---|---|
| 01 | `absolutesound-no-copyright-background-music-559491.mp3` | `AUDIO_C9B3EDFF` | 159.3 | 133.6 (medium) | -14.9 | -2.95 | medium | steady, focused | Canonical |
| 02 | `alex-morgan-no-copyright-music-578487.mp3` | `AUDIO_2E409E09` | 132.7 | 109.3 (high) | -10.7 | 0.08 | high | energetic, upbeat | Canonical |
| 03 | `andriih-no-copyright-music-601653.mp3` | `AUDIO_794D6896` | 134.3 | 130.7 (high) | -17.5 | -3.17 | medium | steady, focused | Canonical |
| 04 | `apalonbeats-no-copyright-music-576332.mp3` | `AUDIO_F0CA9F25` | 86.0 | 120.3 (high) | -15.9 | 0.07 | medium | steady, focused | Canonical |
| 05 | `apalonbeats-no-copyright-music-597079.mp3` | `AUDIO_18396EB7` | 122.7 | 182.2 (medium) | -16.5 | -1.74 | medium | steady, focused | Canonical |
| 06 | `leberch-no-copyright-music-594951.mp3` | `AUDIO_E23988CF` | 152.0 | 162.5 (high) | -18.4 | -2.52 | medium | steady, focused | Canonical |
| 07 | `loksii-no-copyright-music-211881.mp3` | `AUDIO_AEE77C43` | 131.2 | 158.3 (high) | -11.6 | 0.02 | high | energetic, upbeat, playful, cheerful | Canonical |
| 08 | `mondamusic-no-copyright-music-597183.mp3` | `AUDIO_771A5949` | 60.8 | 100.2 (high) | -8.6 | 0.80 | high | energetic, upbeat | Canonical |
| 09 | `monume-no-copyright-music-603959.mp3` | `AUDIO_0EB2323E` | 105.6 | N/A (low) | -16.4 | -0.23 | medium | steady, focused | Canonical |
| 10 | `monume-no-copyright-music-629801.mp3` | `AUDIO_5CA9E857` | 128.0 | 120.3 (high) | -16.0 | -1.13 | medium | steady, focused | Canonical |
| 11 | `nastelbom-no-copyright-music-602456.mp3` | `AUDIO_07A901E6` | 133.4 | 92.5 (high) | -13.1 | 0.07 | high | energetic, upbeat | Canonical |
| 12 | `nastelbom-no-copyright-music-606703.mp3` | `AUDIO_CCB76B9C` | 139.4 | 115.6 (high) | -13.6 | 0.04 | high | energetic, upbeat | Canonical |
| 13 | `no-copyright-music-2026-acoustic-acoustic-music-611654.mp3` | `AUDIO_5C803A0D` | 175.6 | 120.3 (medium) | -10.8 | 1.01 | high | energetic, upbeat, playful, cheerful | Canonical |
| 14 | `prettyjohn1-no-copyright-music-487929.mp3` | `AUDIO_78BB7B59` | 60.6 | 105.5 (high) | -13.0 | -0.10 | high | energetic, upbeat | Canonical |
| 15 | `prettyjohn1-no-copyright-music-591301.mp3` | `AUDIO_0C06EE23` | 66.0 | 91.1 (medium) | -9.3 | 0.64 | high | energetic, upbeat | Canonical |
| 16 | `sigmamusicart-no-copyright-music-537751.mp3` | `AUDIO_632A4576` | 123.2 | 150.3 (medium) | -9.5 | 0.79 | high | energetic, upbeat, playful, cheerful | Canonical |
| 17 | `sigmamusicart-no-copyright-music-604196.mp3` | `AUDIO_2E75EFA8` | 102.3 | 154.2 (medium) | -9.2 | -0.06 | high | energetic, upbeat, playful, cheerful | Canonical |
| 18 | `sigmamusicart-no-copyright-music-619322 (1).mp3` | `AUDIO_AC1F9F82` | 107.1 | 69.9 (high) | -10.5 | 0.29 | high | energetic, upbeat | Canonical |
| 19 | `sigmamusicart-no-copyright-music-619322.mp3` | `AUDIO_AC1F9F82_DUP` | 107.1 | 69.9 (high) | -10.5 | 0.29 | high | energetic, upbeat | ⚠️ DUP of `AUDIO_AC1F9F82` |
| 20 | `studiokolomna-no-copyright-music-632665.mp3` | `AUDIO_3E566446` | 131.4 | 79.1 (medium) | -7.9 | 0.43 | high | energetic, upbeat | Canonical |
| 21 | `sub_clair-no-copyright-music-instrumental-621220.mp3` | `AUDIO_64253D28` | 111.0 | 122.7 (high) | -10.5 | -0.51 | high | energetic, upbeat, playful, cheerful | Canonical |
| 22 | `verclub_music-no-copyright-music-550940.mp3` | `AUDIO_EDE199CA` | 48.0 | 87.2 (high) | -10.2 | 1.88 | high | energetic, upbeat | Canonical |
| 23 | `vibemode-no-copyright-music-581670.mp3` | `AUDIO_AFBF2B76` | 81.3 | 76.1 (high) | -10.7 | -0.13 | high | energetic, upbeat | Canonical |

---

## 3. Deduplication & Canonical Asset Resolution

During inspection, items #18 and #19 were identified with identical byte sizes and identical SHA-256 hashes:
- **Canonical File:** `Raw_input_files/audio/sigmamusicart-no-copyright-music-619322 (1).mp3`
  - **Asset ID:** `AUDIO_AC1F9F82`
  - **SHA-256:** `ac1f9f8298a2bfbeaae09ca6be179cb5146229a1b9476172ec04c6056648dc85`
  - **Duplicate Flag:** `is_duplicate: False`, `duplicate_of_asset_id: None`
- **Duplicate File:** `Raw_input_files/audio/sigmamusicart-no-copyright-music-619322.mp3`
  - **Asset ID:** `AUDIO_AC1F9F82_DUP` (or `AUDIO_AC1F9F82_DUP1` in catalog)
  - **SHA-256:** `ac1f9f8298a2bfbeaae09ca6be179cb5146229a1b9476172ec04c6056648dc85`
  - **Duplicate Flag:** `is_duplicate: True`, `duplicate_of_asset_id: AUDIO_AC1F9F82`

> [!IMPORTANT]
> **Defect Correction Verified:** The previous self-referencing bug (`duplicate_of_asset_id == asset_id`) has been completely eliminated. The canonical asset remains the primary recommendation candidate, while duplicate instances are safely preserved for filesystem compatibility without polluting recommendation rankings.

---

## 4. Acoustic DSP & Mood Heuristics

### BPM Estimation via Envelope Autocorrelation
Tempo extraction uses onset envelope detection filtered through an autocorrelation lag window (60–180 BPM range):
- Tracks with prominent rhythmic percussion (e.g., `loksii-no-copyright-music-211881.mp3`, `158.3 BPM`) achieve `high` confidence.
- Ambient/drone tracks lacking strong transient peaks (e.g., `monume-no-copyright-music-603959.mp3`) correctly report `N/A BPM` with `low` confidence rather than hallucinating an inaccurate tempo.

### EBU R128 Broadcast Loudness Profiles
- Standard social media platforms (Instagram, TikTok, YouTube Shorts) normalize audio to **-14.0 LUFS** (±1.0 LUFS).
- Several sample tracks exhibit heavy modern commercial compression (-8.0 to -11.0 LUFS), requiring studio gain attenuation (-3 dB to -6 dB) during video mixing to prevent clipping and platform algorithmic penalty.
- Measured Integrated Loudness range: **-7.9 LUFS** (most aggressive) to **-18.4 LUFS** (gentlest).

---

## 5. Licensing Provenance & Commercial Gatekeeping

All 23 tracks carry the following metadata in `data/audio_catalog.json` and `data/real_audio_inspection.json`:
```json
{
  "source_type": "USER_SUPPLIED",
  "license_claim": "USER_DECLARED_NO_COPYRIGHT",
  "license_status": "NEEDS_REVIEW",
  "commercial_use_allowed": false,
  "attribution_required": false,
  "clearance_notes": "User-supplied sample soundtrack. Commercial publishing restricted until provenance clearance is verified."
}
```

### Clearance Policy Enforcement
1. **Production Mode (`allow_unverified_licenses=False`):** Tracks with `NEEDS_REVIEW` are strictly gated and will NOT appear in production recommendations.
2. **Preview Mode (`allow_unverified_licenses=True`):** Tracks are ranked based on artistic and acoustic fit, accompanied by prominent human-in-the-loop compliance warnings.
3. **Commercial Publishing Rule:** Zero unverified user tracks may be burned into commercial marketing outputs without explicit human editorial sign-off.

---

## 6. Project & Reel Recommendations

### Block Puzzle Burst (`BPB_DAY_05` 22s Lifestyle Reel)
- **Top Recommended Sample:** `sub_clair-no-copyright-music-instrumental-621220.mp3` (111.0s, 122.7 BPM, energetic/upbeat/playful) — **95.6/100**
- **Secondary Runner-Up:** `no-copyright-music-2026-acoustic-acoustic-music-611654.mp3` (175.6s, 120.3 BPM, energetic/upbeat/playful) — **94.0/100**
- **Studio Cleared Asset:** `bgm_day05_relaxing_piano.wav` (22.0s, 113.2 BPM, VERIFIED_COMMERCIAL_USE) — **100.0/100** (Seamless fit without trimming)

### ERP & Business Projects
- **Expand EziSales (Modern Tech / B2B):** `apalonbeats-no-copyright-music-576332.mp3` (86.0s, 120.3 BPM, steady/focused)
- **Expand HR (Calm / Trustworthy):** `absolutesound-no-copyright-background-music-559491.mp3` (159.3s, 133.6 BPM, steady/focused)
- **WMS (Warehouse Operational Pace):** `nastelbom-no-copyright-music-606703.mp3` (139.4s, 115.6 BPM, energetic/upbeat)
- **POS (Retail Cheerful / High Turnover):** `sigmamusicart-no-copyright-music-604196.mp3` (102.3s, 154.2 BPM, playful/upbeat)

---
Report generated and verified on 2026-11-17 by Pyapiras Studio Audio Intelligence Engine.