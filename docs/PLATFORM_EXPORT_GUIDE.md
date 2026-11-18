# Platform Export Configuration Guide
**Studio:** Social Media Video Production Studio  
**Document:** `docs/PLATFORM_EXPORT_GUIDE.md`  
**Config Source:** `config/production/export_profiles.json`  
**Date:** 2026-11-18  

---

## 1. Configured Studio Export Profiles

All platform parameters are externally configured in [export_profiles.json](file:///c:/Users/Dell/Downloads/video gen/config/production/export_profiles.json) so new platforms or aspect ratios (e.g., LinkedIn 1:1, TikTok 9:16, X 16:9) can be added without modifying Python code.

| Profile ID | Target Platform | Resolution | Aspect Ratio | FPS | Video Codec / CRF / Maxrate | Audio Codec / Rate | Status |
|---|---|---|---|---|---|---|---|
| `instagram_reels` | Instagram Reels | 1080 × 1920 | 9:16 | 30.0 | H.264 High L4.1 / CRF 21 / 5000k | AAC 160k 48kHz Stereo | Provisional Target |
| `youtube_shorts` | YouTube Shorts | 1080 × 1920 | 9:16 | 30.0 | H.264 High L4.1 / CRF 20 / 6000k | AAC 160k 48kHz Stereo | Provisional Target |
| `facebook_reels` | Facebook Reels | 1080 × 1920 | 9:16 | 30.0 | H.264 High L4.1 / CRF 21 / 5000k | AAC 160k 48kHz Stereo | Provisional Target |
| `youtube_standard` | YouTube Standard / Tutorials | 1920 × 1080 | 16:9 | 30.0 | H.264 High L4.2 / CRF 19 / 8000k | AAC 192k 48kHz Stereo | Provisional Target |

> **Specification Uncertainty Notice:** Social media platforms periodically revise maximum durations, bitrate ceilings, and player chrome geometry. All profiles carry `"spec_status": "PROVISIONAL_STUDIO_TARGET"` and should be checked against current platform publishing guidelines before commercial release.

---

## 2. Adding a New Platform Profile

To add a new platform (for example, `linkedin_square` 1080×1080):
1. Add a new key under `"profiles"` in `config/production/export_profiles.json` with `width`, `height`, `aspect_ratio`, `fps`, `crf`, `audio_bitrate`, and `safe_zone_profile`.
2. Add the matching safe-zone entry under `"profiles"` in `config/production/safe_zones.json`.
3. Run `python scripts/multi_platform_exporter.py --list-profiles` to verify discovery.

---

## 3. Manual Approval Process

Automated technical validation (`18/18` checks) guarantees codec, container, sync, and decode health — it does **not** grant creative or publishing approval. Before uploading any export:
1. Open `previews/multi_platform_contact_sheet.png` to inspect all adaptations side-by-side.
2. Open `previews/<profile>_safe_zone.png` to verify no critical text, logo, CTA, or gameplay/ERP element is occluded by platform UI.
3. Play back the actual MP4 file in `platform_exports/<profile>/` to confirm smooth playback, audio clarity, and zero visual distortion.
4. Confirm commercial music licensing and factual marketing claims against the project's `knowledge/verified_features.md`.
