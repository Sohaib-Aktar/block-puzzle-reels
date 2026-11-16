# Day 04 Editing Plan: Offline Gameplay Proof (Airplane Mode)

**Project:** Block Puzzle Burst (`com.pyapiras.blockpuzzleburst`)  
**Campaign:** 30-Day Daily Instagram Reel Challenge  
**Content ID:** `BPB_DAY_04`  
**Content Topic:** Offline Gameplay Proof  
**Content Category:** Product Feature Demonstration / Trust Building  
**Target Duration:** Exactly 15.00 Seconds (450 frames @ 30.0 fps)  
**Aspect Ratio / Resolution:** 9:16 Vertical (1080 × 1920)  
**Primary Platform:** Instagram Reels (Cross-post: Facebook Reels, YouTube Shorts)  
**Studio Brand:** Pyapiras Games  

---

## 1. Marketing Strategy & Creative Direction

### 1.1 Objective & Value Proposition
- **Core Message:** **THE GAME WORKS WITHOUT INTERNET.**
- **Audience Problem:** Most modern mobile games require an active internet connection, drain cellular data, display constant video ads, or fail to load on trains, flights, or in weak network areas.
- **The Solution:** Block Puzzle Burst is built with an offline-first philosophy by a solo indie developer. Zero internet required. Zero loading spinners. Zero cellular data usage.
- **Hook Archetype:** Authenticity / Real-World Utility ("No WiFi? No problem.")
- **CTA:** "Play Anywhere. Stay Offline." (Direct link-in-bio callout).

### 1.2 Language & Brand Policy
- **STRICT Language Rule:** All on-screen video text is in **ENGLISH ONLY**.
- Bengali and Hindi translations are exclusively prepared for social media post copy, never burned into video pixels.
- Typography: Bold, high-contrast headings using Pyapiras Games studio brand standards (`#FFFFFF` text, `#FFD700` gold highlights, `#7B2FBE` royal purple glows).
- Safe Margins: Strict compliance with Instagram/TikTok safe areas (220px top margin, 280px bottom margin, 40px side margins).

---

## 2. Source Asset Inspection & Verification

| Asset Filename | Dimensions | Duration / FPS | Technical Notes | Editorial Role |
|---|---|---|---|---|
| `Raw_input_files/recording_3.mp4` | 720 × 1600 (9:20) | 30.25s / VFR (normalized to 30.0 fps CFR) | Clean Android 13 screen recording. Shows initial game board, quick settings pull-down, live touch on Aeroplane mode tile, status bar airplane icon activation, shade closure, and 17+ seconds of authentic 10x10 puzzle gameplay. | Primary video source for all 5 scenes. |
| `Raw_input_files/sample_airplane.jpg` | 1080 × 2400 | Still image | High-resolution capture at 09:27 showing quick settings shade with Aeroplane mode active green, Wi-Fi disconnected, mobile data disconnected, and airplane icon in status bar. | Reference benchmark & visual verification artifact. |

> [!NOTE]
> **Footage Authenticity:** Both assets represent 100% genuine Android device screen recordings from the developer's physical phone. Zero synthetic simulation or fabricated UI is used.

---

## 3. Shot-by-Shot Timeline & Source Mapping

| Scene | Composition Timecode | Frames (@30fps) | Duration | Visual Action | Source In–Out (CFR30) | On-Screen Overlay (EN Only) | Audio Treatment |
|---|---|---|---|---|---|---|---|
| **Scene 1** | `00:00.00 – 00:02.00` | 0 – 60 | 2.0s | Authentic Block Puzzle Burst board view at `09:26` with initial 3 tray pieces. | `00:00.0 – 00:02.0` (Frames 0 – 60) | **Hook Banner:** "No WiFi? No problem." / "100% Offline Gameplay" | Smooth ambient intro chime + original board audio |
| **Scene 2** | `00:02.00 – 00:04.00` | 60 – 120 | 2.0s | Phone quick settings drawer pulled down. Live finger touch on Aeroplane Mode tile; tile turns green, mobile data cuts off, airplane status icon appears at `09:27`. | `00:06.5 – 00:08.5` (Frames 195 – 255) | **Pill Badge:** "Airplane Mode: ON ✈️" | Authentic toggle click sound |
| **Scene 3** | `00:04.00 – 00:05.00` | 120 – 150 | 1.0s | Notification shade smoothly slides up, returning seamlessly to the Block Puzzle Burst board with airplane icon active in status bar. | `00:08.5 – 00:09.5` (Frames 255 – 285) | Smooth transition to gameplay | Ambient board audio |
| **Scene 4** | `00:05.00 – 00:13.00` | 150 – 390 | 8.0s | Genuine, fluid 10x10 board gameplay. Pieces dragged from tray and placed into the grid. Airplane icon remains active in top status bar throughout. | `00:09.5 – 00:17.5` (Frames 285 – 525) | **Feature Pill (05–08s):** "Zero Data • Zero Lag ⚡" | Authentic block placement clicks |
| **Scene 5** | `00:13.00 – 00:15.00` | 390 – 450 | 2.0s | Final board position with placed blocks under offline mode, transitioning into branded outro card. | `00:17.5 – 00:19.5` (Frames 525 – 585) | **Outro Card:** "Play Anywhere. Stay Offline." / "Trains • Flights • Zero Signal" / "Play Free Today 🧩" / Pyapiras Games | Closing chord + smooth fade to black |

---

## 4. Technical Rendering Specifications

- **Canvas Dimensions:** 1080 × 1920 pixels
- **Aspect Ratio:** 9:16 (Vertical)
- **Container / Codec:** MP4 / H.264 (High Profile, Level 4.0)
- **Audio Codec:** AAC-LC (Stereo, 48,000 Hz, 320 kbps)
- **Loudness Normalization:** Conforms to **EBU R128 (-14 LUFS standard)**
- **Total Duration:** 15.00 seconds (450 frames)
- **Renderer:** Remotion v4.0.543 Composition (`DayFourOfflineReel`) + FFmpeg loudness normalization
