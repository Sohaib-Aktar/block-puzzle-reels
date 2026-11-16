# Audio Licensing & Commercial Clearance Guidelines

**Date:** 2026-11-16  
**Auditor / Policy Author:** AI Creative Director & Legal Media Compliance Engineer  
**Workspace:** `C:\Users\Dell\Downloads\video gen`  
**Studio Brand:** Pyapiras Games  
**Applies To:** All music, background ambience, sound effects, voiceovers, and stems across Instagram Reels, Facebook Reels, YouTube Shorts, and YouTube Longform.

---

## 1. Core Principles & Strict Commercial Policies

1. **Royalty-Free $\neq$ Universally Cleared:**  
   "Royalty-free" merely means ongoing royalties are not owed after initial acquisition. It does **not** guarantee unrestricted commercial synchronization rights for paid advertisements, digital app store promos, or cross-platform distribution.

2. **No Acoustic Clearance:**  
   Acoustic and waveform algorithms cannot prove legal copyright ownership or licensing rights. Clearance requires verified legal provenance.

3. **Metadata is Not Evidence:**  
   ID3 tags, MP3 comment fields, or friendly filenames like `free_commercial_bgm.mp3` do **not** constitute legal license documentation.

4. **Zero Unauthorized Publishing Gatekeeping:**  
   Any track bearing `UNKNOWN`, `NEEDS_REVIEW`, or `RESTRICTED` status is blocked by the campaign gatekeeper from `PUBLISHED` state until human legal or editorial sign-off is recorded in `data/campaign_tracker.sqlite`.

5. **Internal Studio Exemption:**  
   Assets created in-house by Pyapiras Games (e.g. offline TTS voiceovers, proprietary sound effect generators, gameplay recordings) are classified as `VERIFIED_COMMERCIAL_USE` under the Pyapiras Games studio copyright.

---

## 2. Six-Tier Licensing Status Classification

| Status | Definition | Publishing Eligibility | Studio Action |
|---|---|---|---|
| `VERIFIED_COMMERCIAL_USE` | Legally verified commercial sync rights with written license, invoice, or in-house studio generation. | **Fully Eligible** across all commercial channels. | Cleared for automated rendering and scheduling. |
| `PERSONAL_USE_ONLY` | Permitted exclusively for non-commercial internal viewing, proofs of concept, or portfolio review. | **Forbidden for commercial marketing/ads.** | System warns user; recommends commercial replacement. |
| `ATTRIBUTION_REQUIRED` | Creative Commons (e.g., CC-BY 4.0) permitting commercial use provided credit is displayed. | **Eligible with Mandatory Credits.** | Social media caption generator automatically appends attribution block. |
| `RESTRICTED` | Content ID protected, platform-exclusive (e.g., TikTok commercial sound library only), or geographically bounded. | **Platform-Specific Only.** | Blocked on unapproved destinations (e.g., cannot post to YouTube if restricted to Instagram). |
| `UNKNOWN` | Source and license documentation are absent or ambiguous. | **Blocked from Publishing.** | System flags asset; recommends human review or replacement. |
| `NEEDS_REVIEW` | License claimed but contract terms or expiration date require verification. | **Pending Editorial Sign-off.** | Gatekeeper halts automated publish until verified. |

---

## 3. Mandatory License Audit Metadata

Every audio record in `data/audio_catalog.json` must record:

```json
{
  "license_status": "VERIFIED_COMMERCIAL_USE",
  "license_source": "Pyapiras Studio Internal Generation",
  "creator": "Pyapiras Games Audio Engine",
  "license_type": "Proprietary In-House Work-for-Hire",
  "commercial_use_allowed": true,
  "attribution_required": false,
  "modification_allowed": true,
  "platform_restrictions": [],
  "license_evidence_path": "docs/AUDIO_LICENSING_GUIDELINES.md",
  "verified_at": "2026-11-16T18:00:00"
}
```

---

## 4. Platform-Specific Commercial Music Restrictions

### 4.1 Instagram & Facebook Reels
- **Personal vs. Professional/Business Accounts:** Meta applies different audio libraries. Business accounts cannot use tracks from the general commercial music catalog without direct commercial sync licenses.
- **Audio Fingerprinting:** Meta's Content ID mute mechanism will automatically silence videos containing unapproved copyrighted music.
- **Studio Policy:** Use either in-house Pyapiras acoustic music, licensed royalty-free production libraries, or original gameplay sound effects.

### 4.2 YouTube Shorts & Longform Tutorials
- **Content ID Claim Risks:** Using unlicensed tracks triggers automated copyright claims, ad revenue redirection, or algorithmic reach suppression.
- **Shorts Sound Library Restrictions:** Tracks added via the YouTube mobile app editor are licensed for in-app shorts creation, but **cannot be burned into external MP4 files** uploaded via desktop or API.

---

## 5. Verification Checklist for New Audio Intake

Before advancing any imported audio file to `VERIFIED_COMMERCIAL_USE`:

- [ ] Is the license agreement or receipt filed in `data/licenses/`?
- [ ] Does the license explicitly grant **worldwide, perpetual, commercial synchronization rights**?
- [ ] Are there limits on impressions (e.g., limited to 500,000 views)?
- [ ] Does the license require on-screen or caption attribution?
- [ ] Is the track registered with YouTube Content ID or Audible Magic? If yes, is Pyapiras Games whitelisted?
- [ ] Has the file been inspected by `scripts/audio_analyzer.py` for acoustic quality and digital clipping?
