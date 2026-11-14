# Block Puzzle Reels Generator 🎮🎬

An automated, prompt-driven Instagram Reels video generation pipeline built with **Remotion (React + TypeScript)**. Generates high-converting, deterministic 1080×1920 mobile videos from actual block puzzle gameplay recordings without any third-party paid AI video generation APIs.

---

## 🗂️ Project Organization

The repository is structured into dedicated workspaces for raw media inputs, generated video deliverables, creative prompts, and the Remotion rendering engine:

```text
block-puzzle-reels/
├── Raw_files/                     # Source assets & gameplay recordings
│   ├── recording_1.mp4            # Real gameplay capture (720x1600, 60fps)
│   ├── redording_2.mp4            # Secondary gameplay recording
│   ├── sample_1.jpg               # UI & board sample reference
│   └── sample_2.jpg               # Board state reference
│
├── Output_files/                  # Fast-access rendered MP4 videos
│   ├── MyDayTwoReel.mp4           # Day 2: Continuous variable-speed Reel
│   ├── day3-puzzle-challenge.mp4  # Day 3: 90%+ filled board freeze puzzle Reel
│   └── BlockPuzzleBurst.mp4       # Baseline composition export
│
├── generated_outputs/             # Complete deliverables hub (Videos + Previews + Plans)
│   ├── README.md                  # Detailed catalog of all generated assets
│   ├── videos/                    # Master copies of rendered Reels
│   ├── previews/                  # PNG verification snapshots across critical frames
│   └── plans/                     # Architecture & 30-Day strategic blueprints
│       ├── Master_30_Day_Reels_Plan.md
│       ├── Project_Architecture.md
│       ├── Prompt_Day_02.md
│       └── Prompt_Day_03.md
│
├── reel_Prompts/                  # Daily creative prompts & specifications
│   ├── prompt_day2.md             # Specification for Day 2 speed ramp reel
│   └── Prompt_day3.md             # Specification for Day 3 puzzle challenge reel
│
├── my-video/                      # Remotion React composition project
│   ├── src/
│   │   ├── Root.tsx               # Remotion composition registry
│   │   ├── MyDayTwoReel.tsx       # Day 2 composition component
│   │   ├── MyDayThreeReel.tsx     # Day 3 composition component
│   │   └── FrameFinder.tsx        # Frame scrubbing and coordinate calibration utility
│   ├── public/
│   │   └── gameplay.mp4           # Active gameplay video linked to compositions
│   └── package.json               # Remotion dependencies (Remotion v4.0.543)
│
└── .agents/skills/                # Remotion Agent Skills for automated composition
    ├── remotion-best-practices
    ├── remotion-markup
    ├── remotion-render
    └── remotion-studio
```

---

## ⚡ Quick Start

### 1. Prerequisites
- Node.js (v18+)
- FFmpeg (bundled automatically via Remotion)

### 2. Install Dependencies
```bash
cd my-video
npm install
```

### 3. Launch Remotion Studio (Visual Preview)
To visually inspect animations, verify coordinates, or scrub frames:
```bash
npm run dev
```
Open [http://localhost:3000](http://localhost:3000) in your browser.

### 4. Render Videos
To render directly via CLI:
```bash
# Day 2: Continuous Gameplay + Slow-Mo Combo
npx remotion render MyDayTwoReel ../Output_files/MyDayTwoReel.mp4

# Day 3: Puzzle Challenge (93% Board Fill)
npx remotion render MyDayThreeReel ../Output_files/day3-puzzle-challenge.mp4
```

---

## 📐 Architecture & Key Innovations

1. **Aspect Ratio Preservation (`objectFit: contain`):**
   Mobile gameplay captured at `720×1600` (9:20 ratio) is scaled to `864×1920` inside the `1080×1920` canvas with `#0D0D0D` letterboxing. This guarantees that 100% of the game board, top scores, and bottom candidate piece tray remain completely visible without being cropped.
2. **Accurate 93% Board Fill:**
   Day 3 freezes at Frame 1780 where the board is 93.2% full, presenting a genuine high-stakes tactical puzzle.
3. **Deterministic Spring Physics:**
   Built using Remotion's frame-driven `spring()` and `interpolate()` functions, ensuring smooth, reproducible animations in headless Chromium without frame jitter.

For full architectural details, see [`generated_outputs/plans/Project_Architecture.md`](generated_outputs/plans/Project_Architecture.md).
