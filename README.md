# Block Puzzle Reels Generator 🎮🎬

An automated, prompt-driven Instagram Reels video generation pipeline built with **Remotion (React + TypeScript)**. Generates high-converting, deterministic 1080×1920 mobile videos from actual block puzzle gameplay recordings without any third-party paid AI video generation APIs.

---

## 🗂️ Project Organization

The repository is cleanly partitioned into dedicated architectural domains:

```text
block-puzzle-reels/
├── package.json                   # Root orchestrator scripts (dev, build, render:day2, render:day3)
├── README.md                      # Developer onboarding & architectural documentation
├── .gitignore                     # Ignores dependencies, builds, OS artifacts, and temp frames
│
├── Raw_files/                     # Source assets & gameplay recordings
│   ├── recording_1.mp4            # Primary gameplay capture (720x1600 @ 60fps)
│   ├── recording_2.mp4            # Secondary gameplay recording
│   ├── sample_1.jpg               # UI & board sample reference
│   └── sample_2.jpg               # Board state reference
│
├── generated_outputs/             # Deliverables Hub (Videos + Previews + Plans)
│   ├── README.md                  # Detailed catalog of all generated assets
│   ├── videos/                    # Rendered 1080x1920 MP4 Reels
│   │   ├── Day_02_MyDayTwoReel.mp4
│   │   ├── Day_03_Puzzle_Challenge.mp4
│   │   └── BlockPuzzleBurst_Original.mp4
│   ├── previews/                  # PNG verification snapshots across critical frames
│   └── plans/                     # Architecture & 30-Day strategic blueprints
│       ├── Master_30_Day_Reels_Plan.md
│       ├── Project_Architecture.md
│       ├── Prompt_Day_02.md
│       └── Prompt_Day_03.md
│
├── reel_Prompts/                  # Daily creative prompts & specifications
│   ├── prompt_day2.md             # Specification for Day 2 speed ramp reel
│   └── prompt_day3.md             # Specification for Day 3 puzzle challenge reel
│
├── my-video/                      # Remotion React composition engine
│   ├── package.json               # Remotion engine dependencies (Remotion v4.0.543, React 19)
│   ├── public/
│   │   └── gameplay.mp4           # Active gameplay video linked to compositions
│   └── src/
│       ├── Root.tsx               # Remotion composition registry
│       ├── MyDayTwoReel.tsx       # Day 2: Continuous variable-speed composition
│       ├── MyDayThreeReel.tsx     # Day 3: Interactive freeze puzzle composition
│       ├── FrameFinder.tsx        # Frame scrubbing and coordinate calibration utility
│       ├── theme/
│       │   └── tokens.ts          # Central design tokens (palette, typography, spring presets)
│       └── components/            # Reusable, modular overlay components
│           ├── CandidateBadge.tsx # A, B, C option badges with spring entrance & gold reveal
│           ├── ComboPulse.tsx     # High-energy combo score celebration banner
│           ├── CountdownBar.tsx   # 5-dot animated countdown indicator
│           ├── HookBanner.tsx     # Top hook banner with glowing gradient
│           ├── OutroCard.tsx      # Branded end card with call-to-action
│           └── SolutionBox.tsx    # Target grid solution highlight box
│
└── .agents/skills/                # Remotion Agent Skills for AI-driven automation
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
# Install once from the root:
npm --prefix my-video install
```

### 3. Launch Remotion Studio (Visual Preview)
To visually inspect animations, verify coordinates, or scrub frames in real time:
```bash
npm run dev
```
Open [http://localhost:3000](http://localhost:3000) in your browser.

### 4. Render Videos Directly via Root CLI
You can render individual reels or all reels directly from the repository root:
```bash
# Render Day 2: Continuous Gameplay + Slow-Mo Combo
npm run render:day2

# Render Day 3: Puzzle Challenge (93% Board Fill)
npm run render:day3

# Render all compositions in batch
npm run render:all
```
All rendered MP4 outputs are placed directly into [`generated_outputs/videos/`](generated_outputs/videos/).

---

## 📐 Architecture & Key Innovations

1. **Aspect Ratio Preservation (`objectFit: contain`):**
   Mobile gameplay captured at `720×1600` (9:20 ratio) is scaled to `864×1920` inside the `1080×1920` canvas with `#0D0D0D` letterboxing. This guarantees that 100% of the game board, top scores, and bottom candidate piece tray remain completely visible without being cropped.
2. **Accurate 93% Board Fill:**
   Day 3 freezes at Frame 1780 where the board is 93.2% full, presenting a genuine high-stakes tactical puzzle.
3. **Deterministic Spring Physics & Shared Tokens:**
   Built using Remotion's frame-driven `spring()` and `interpolate()` functions with centralized theme tokens in [`src/theme/tokens.ts`](my-video/src/theme/tokens.ts) and modular components in [`src/components/`](my-video/src/components/), eliminating UI code duplication.

For full architectural details, see [`generated_outputs/plans/Project_Architecture.md`](generated_outputs/plans/Project_Architecture.md).
