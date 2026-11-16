# Quality Control (QC) Report — [CONTENT_ID]

**Content ID:** [unique-content-id]  
**Project:** [project-slug]  
**Target Video File:** `outputs/[project]/[campaign]/[content-id]/final/[filename].mp4`  
**Evaluation Date:** [YYYY-MM-DD HH:MM]  
**Inspector:** [Manual / Automated QC Verifier]

---

## 1. Technical Stream Specifications
| Metric | Expected Preset Spec | Actual Measured Value | Status |
|---|---|---|---|
| **Resolution** | [1080×1920 / 1920×1080] | `[Width] × [Height]` | [PASS / FAIL] |
| **Aspect Ratio** | [9:16 / 16:9] | `[Aspect Ratio]` | [PASS / FAIL] |
| **Duration** | `[Min] – [Max] s` | `[Actual] s` | [PASS / FAIL] |
| **Frame Rate** | [30 / 60 fps] | `[Actual] fps` | [PASS / FAIL] |
| **Video Codec** | H.264 (avc1) High | `[Codec Name]` | [PASS / FAIL] |
| **Audio Stream** | AAC Stereo / 48kHz | `[Channels / Sample Rate]` | [PASS / FAIL] |
| **File Size** | `< 50 MB` | `[Actual] MB` | [PASS / FAIL] |
| **Moov Atom Placement** | `+faststart` (Streamable) | `[Yes / No]` | [PASS / FAIL] |

---

## 2. Brand & Content Compliance
| Check Item | Requirement | Verification Note | Status |
|---|---|---|---|
| **Project Identity** | Must match verified profile | Verified against `PROJECT_PROFILE.md` | [PASS / FAIL] |
| **Source Authenticity** | Real screen captures / gameplay only | No fabricated UI or fake statistics | [PASS / FAIL] |
| **On-Screen Language** | English-only default on-screen | No non-English burned in without approval | [PASS / FAIL] |
| **Safe Areas** | Inset 192px top/bottom, 54px left/right | Headlines & CTAs remain unobstructed | [PASS / FAIL] |
| **Privacy / Blur** | Zero PII or sensitive keys visible | Personal/financial details masked | [PASS / FAIL] |
| **Call to Action** | Exactly one clear, actionable CTA | Single clean ask at end | [PASS / FAIL] |

---

## 3. Playback & Visual Audit
- [ ] Decodability: File decodes cleanly from start to end without dropped frames
- [ ] Text legibility: High contrast against background at mobile screen size
- [ ] Audio-visual sync: Transitions align with audio cues
- [ ] Caption package: Accompanying `captions/` text file ready

---

## 4. Overall Disposition
- **QC Result:** [PASSED / RE-RENDER REQUIRED / REJECTED]
- **Approval Sign-off:** [PENDING APPROVAL / APPROVED FOR PUBLICATION]
