# Audio Analysis & Acoustic Intelligence Guide

**Studio:** Pyapiras Games  
**Date:** 2026-11-16  
**Status:** Active Production Standard  
**Workspace Root:** `C:\Users\Dell\Downloads\video gen`

---

## 1. Overview

The Pyapiras Audio Intelligence System provides automated acoustic inspection, broadcast loudness measurement, rhythmic tempo estimation, and project-aware soundtrack recommendations for short-form video reels.

It ensures every video deliverable satisfies platform loudness standards (EBU R128 / -14 LUFS), features brand-appropriate pacing, avoids digital clipping, and maintains strict copyright compliance.

---

## 2. Acoustic Physics & Mathematical Formulations

Audio analysis operates on uncompressed 16-bit linear PCM audio samples ($s_t \in [-32768, 32767]$) at 44.1 kHz or 48.0 kHz.

### 2.1 Peak Amplitude (dBFS)
Measures the maximum instantaneous absolute amplitude relative to digital full scale (0 dBFS):
$$\text{Peak dBFS} = 20 \log_{10}\left(\frac{\max_{t} |s_t|}{32768}\right)$$
- Normalization Target: Peaks should remain below $-1.0\text{ dBFS}$ (True Peak $\le -1.5\text{ dBTP}$) to prevent inter-sample clipping during lossy AAC/MP3 re-encoding on Instagram and YouTube.

### 2.2 Root Mean Square (RMS dBFS)
Measures the effective continuous acoustic energy of the signal:
$$\text{RMS dBFS} = 20 \log_{10}\left(\sqrt{\frac{1}{N}\sum_{t=1}^{N} s_t^2} \Big/ 32768\right)$$
- High Energy Tracks (Upbeat gaming, fast reels): RMS $\ge -16.0\text{ dBFS}$.
- Moderate Energy Tracks (Corporate explainer, software demos): RMS between $-22.0$ and $-16.0\text{ dBFS}$.
- Low Energy / Ambient (Relaxing piano, background beds): RMS $\le -22.0\text{ dBFS}$.

### 2.3 Digital Clipping Detection
Digital clipping occurs when audio amplitudes saturate the integer limits of the bit depth, causing harsh square-wave distortion:
$$\text{Clipping} = \text{True if } \exists t \text{ such that } |s_t| \ge 32767$$
Any audio file with confirmed clipping is rejected by Quality Control.

### 2.4 Silence Ratio
The fraction of audio duration falling below the audibility noise floor ($-45.0\text{ dBFS}$):
$$\text{Silence Ratio} = \frac{N_{\text{silent frames}}}{N_{\text{total frames}}}, \quad \text{where frame is silent if } \text{RMS}_{\text{frame}} < -45.0\text{ dBFS}$$
- Instrumental Background Music: Typically $< 0.15$ (continuous energy).
- Spoken Voiceover Narration: Typically between $0.20$ and $0.45$ (natural conversational pauses between phrases).
- Disconnected / Broken Tracks: Silence ratio $> 0.60$ flags potential missing content.

---

## 3. Tempo & Rhythm Extraction (Vectorized BPM Autocorrelation)

### 3.1 Energy Envelope Extraction
1. Rectify signal: $x_t = |s_t|$.
2. Downsample to 100 Hz frame rate using a 10 ms sliding window average ($W = 441$ samples):
   $$e_m = \frac{1}{W} \sum_{k=0}^{W-1} x_{m \cdot W + k}$$
3. Compute onset difference: $\Delta e_m = \max(0, e_m - e_{m-1})$.

### 3.2 Normalized Autocorrelation
Calculates correlation across lag offsets $k$ corresponding to tempi between 60 BPM ($k = 100$) and 180 BPM ($k = 33$):
$$r(k) = \frac{\sum_{m} (e_m - \bar{e})(e_{m+k} - \bar{e})}{\sum_{m} (e_m - \bar{e})^2}$$

### 3.3 BPM Confidence Rubric
The peak autocorrelation value $r_{\max} = \max_{k} r(k)$ determines tempo and confidence:
- **High Confidence:** $r_{\max} \ge 0.18$ with prominent peak sharpness ($> 1.25\times$ background mean). Found in steady-beat electronic, pop, and rhythmic gaming soundtracks.
- **Medium Confidence:** $0.08 \le r_{\max} < 0.18$. Found in acoustic guitar, moderate corporate beds, or complex syncopated percussion.
- **Low Confidence / Ambiguous:** $r_{\max} < 0.08$. Typical of free-form classical piano, ambient drones, and spoken dialogue.

---

## 4. Broadcast Loudness Standards (EBU R128)

Social media platforms apply algorithmic loudness penalties to audio that exceeds standard broadcast thresholds:

| Metric | Target Specification | Enforcement |
|---|---|---|
| **Integrated Loudness ($I$)** | $-14.0\text{ LUFS} \pm 1.0\text{ LU}$ | Normalized via FFmpeg `loudnorm`. |
| **Maximum True Peak ($TP$)** | $\le -1.5\text{ dBTP}$ | Prevents DAC clipping on mobile devices. |
| **Loudness Range ($LRA$)** | $\le 11.0\text{ LU}$ | Controls dynamic range for noisy mobile environments. |

### Normalization Filter:
```powershell
npx remotion ffmpeg -i input.wav -af "loudnorm=I=-14:LRA=11:TP=-1.5" -c:a pcm_s16le output_norm.wav
```

---

## 5. Emotional Mood Taxonomy & Project Rubric

### 5.1 Project Profiles

| Project Slug | Brand Personality | Preferred BPM | Primary Mood Tags | Banned / Unsuitable Tones |
|---|---|---|---|---|
| `block-puzzle-burst` | Vibrant, satisfying, casual mobile gaming | 110–135 BPM | `energetic`, `playful`, `cheerful`, `casual_gaming`, `satisfying`, `relaxing` | `somber`, `dramatic`, `aggressive`, `melancholy` |
| `expand-ezisales` | Professional, efficient, modern B2B SaaS | 100–125 BPM | `modern`, `corporate`, `tech`, `confident`, `efficient` | `cartoonish`, `chaotic`, `somber` |
| `expand-hr` | Trustworthy, calm, enterprise HR & payroll | 90–115 BPM | `calm`, `corporate`, `trustworthy`, `professional`, `clean` | `frantic`, `heavy_bass`, `aggressive` |
| `wms` | Organized, swift, logistics and supply chain | 115–130 BPM | `operational`, `focused`, `dynamic`, `structured` | `whimsical`, `sleepy` |
| `pos` | Upbeat, active, retail storefront groove | 115–130 BPM | `retail`, `groove`, `upbeat`, `friendly` | `mournful`, `dark` |

---

## 6. Multi-Scene Timeline & Audio Pacing

When planning a reel, audio is structured into a dynamic 3-act progression:

```
[0.0s ─────── 3.0s]          [3.0s ──────────────────────── 12.0s]          [12.0s ────── 15.0s]
     ACT 1: HOOK                     ACT 2: CORE GAMEPLAY / DEMO                   ACT 3: CTA
Attention-grabbing intro       Sustained rhythmic bed (Ducked -18dB)         Musical crescendo & UI pop
```

- **Hook (0–3s):** Full volume BGM ($0\text{ dB}$ relative) or impactful sound effect accent to stop scrolling.
- **Core Demo (3–12s):** BGM ducked by $-18.0\text{ dB}$ to ensure complete dialogue intelligibility over voiceover.
- **CTA Outro (12–15s):** BGM returns to $-6.0\text{ dB}$ for decisive final resolve, punctuated by transparent logo chime or pop SFX.

---

## 7. Copyright & Commercial Clearance Protocol

Every audio asset cataloged in `data/audio_catalog.json` carries a verified `license_status`:

1. `VERIFIED_COMMERCIAL_USE`: Studio-generated synthesis, internally produced sound effects, or fully licensed royalty-free assets with documentation. Allowed for immediate production rendering.
2. `NEEDS_REVIEW`: External source audio without verified documentation. Filtered out of automated rendering pipelines unless explicitly overridden with `--allow-unverified-licenses`.
3. `RESTRICTED`: Third-party copyrighted content or non-commercial CC licenses. **Blocked from all commercial outputs.**
4. `UNKNOWN`: Unchecked files. Must be audited before use.
