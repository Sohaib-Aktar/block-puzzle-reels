# Verified Features — Block Puzzle Burst

**Project:** Block Puzzle Burst (`com.pyapiras.blockpuzzleburst`)  
**Developer Studio:** Pyapiras Games  
**Verification Level:** GROUND TRUTH (Directly verified via screen recordings and Play Store listing)

---

## 1. Core Mechanics
- **Grid Size:** 10×10 block puzzle grid.
- **Piece Tray:** Three pieces available at any time; once all three are placed, a fresh trio is served.
- **Row & Column Clearing:** Completing any full horizontal row (10 blocks) or vertical column (10 blocks) causes it to clear.
- **Multi-Line & Cross Clears:** A single piece placement can clear both rows and columns simultaneously.
- **Combo Multipliers:** Chaining consecutive clears awards exponential combo multipliers (2X, 4X, 6X, 8X+).
- **Game Over Condition:** Occurs only when none of the three current tray pieces can fit on the remaining open board tiles.
- **No Pressure Timer:** The player has infinite time to think about every move. No rush, no forced countdown timer during normal gameplay.

---

## 2. Technical & Offline Capabilities
- **100% Offline Playability:** Works fully in Airplane Mode without WiFi or mobile data.
- **Instant Resume:** Game state persists across app closures; no loss of active board progress.
- **Lightweight Package:** Fast download, minimal storage consumption, smooth 60fps rendering on low-end and high-end Android devices.

---

## 3. Social & Sharing
- **Score Card Generation:** Built-in WhatsApp and social sharing card featuring the player's final high score and a scannable QR code.
- **Free with Ads:** Completely free to download and play; monetized unobtrusively via ad placements.
