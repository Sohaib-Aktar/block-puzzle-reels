# Generated Outputs & Deliverables Hub

This directory contains all generated video assets, visual preview frames, planning documents, and technical architecture specifications produced by the **Remotion AI Block Puzzle Reels Generator**.

---

## 📁 Directory Structure

```text
generated_outputs/
├── README.md                           # This index file
├── videos/                             # Final rendered 1080x1920 30fps MP4 Reels
│   ├── Day_02_MyDayTwoReel.mp4         # Day 2: Continuous gameplay + slow-mo speed ramp + combo pulse
│   ├── Day_03_Puzzle_Challenge.mp4     # Day 3: 93.2% filled board + freeze + A/B/C interactive badges + solution reveal
│   └── BlockPuzzleBurst_Original.mp4   # Base gameplay render benchmark
├── previews/                           # High-res verification frames (PNG)
│   ├── contain_board_frame1780.png     # Full-board contain ratio inspection (no tray cropping)
│   ├── day2_hook_preview.png           # Day 2 hook banner ("Wait for the last piece")
│   ├── day2_combo_preview.png          # Day 2 slow-mo +400 combo pulse effect
│   ├── day2_outro_preview.png          # Day 2 outro brand card
│   ├── day3_badges_frame100.png        # Day 3 candidate badges (A, B, C) aligned over piece tray
│   ├── day3_reveal_frame370.png        # Day 3 gold winning badge B reveal + grid target box
│   ├── day3_badges_preview.png         # Alternative verification capture for badge placement
│   └── day3_reveal_preview.png         # Alternative verification capture for solution reveal
└── plans/                              # Production plans & architectural documents
    ├── Master_30_Day_Reels_Plan.md     # 30-day comprehensive content strategy & taxonomy
    ├── Project_Architecture.md         # Full Remotion technical architecture & dataflow diagrams
    ├── Prompt_Day_02.md                # Day 2 creative prompt & execution parameters
    └── Prompt_Day_03.md                # Day 3 creative prompt & 90%+ board fill parameters
```

---

## 🎬 Video Specifications

| Asset | Resolution | FPS | Duration | File Size | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `Day_02_MyDayTwoReel.mp4` | 1080×1920 (9:16) | 30 | 15s (450 frames) | 1.96 MB | Continuous playback (0:00–0:10 @ 1.0x) transitioning into 0.3x slow-mo combo burst (0:10–0:13) and sleek branded outro. |
| `Day_03_Puzzle_Challenge.mp4` | 1080×1920 (9:16) | 30 | 15s (450 frames) | 2.33 MB | Real gameplay frozen at Frame 1780 (93.2% full board). Badges A, B, C pop over tray; 5-dot countdown timer; winning move B revealed with gold glow & target grid box. |
| `BlockPuzzleBurst_Original.mp4` | 1080×1920 (9:16) | 30 | 15s (450 frames) | 2.64 MB | Baseline gameplay composition. |

---

## 🛠️ How to Re-render or Tweak

From the `my-video` folder:

```bash
# Day 2 Reel
cmd /c npx remotion render MyDayTwoReel "../generated_outputs/videos/Day_02_MyDayTwoReel.mp4"

# Day 3 Puzzle Challenge Reel
cmd /c npx remotion render MyDayThreeReel "../generated_outputs/videos/Day_03_Puzzle_Challenge.mp4"

# Scrub & Inspect in Studio
cmd /c npm run dev
```
