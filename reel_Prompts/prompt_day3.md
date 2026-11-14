You are an expert Remotion developer. Build a 15-second vertical Reel (1080×1920, 30fps = 450 frames) for my mobile puzzle game "Block Puzzle Burst" (Day 3 Puzzle Challenge).

I have attached my recorded gameplay video (`gameplay.mp4`, placed in `public/gameplay.mp4`).

### How to Handle the Attached Video:
Instead of a static screenshot, use `<OffthreadVideo>` from `remotion` and `<Freeze>` so the video pauses while the viewer thinks, then plays the actual block placement and burst animation during the reveal:
1. Create a `CONFIG` object at the top of the file so I can easily adjust:
   - `pauseAtVideoFrame`: The exact frame in `gameplay.mp4` where the board and the 3 bottom pieces are clearly visible before a piece is dragged.
   - `badgePositions`: `{ A: { x, y }, B: { x, y }, C: { x, y } }` in pixels (default to the bottom tray area where the 3 candidate pieces sit: e.g., y = 1480, x = 220, 540, 860).
   - `solutionBox`: `{ x, y, width, height }` for the glowing highlight border on the 8x8 grid.
   - `correctAnswer`: `'A' | 'B' | 'C'` (default `'B'`).
   - `hookLanguage`: `'EN' | 'BN' | 'HI'` using these exact hooks:
     - EN: "Solve it in ONE move"
     - BN: "মাত্র এক চালে সমাধান করুন"
     - HI: "सिर्फ़ एक चाल में हल करो"

### Timeline (450 Frames @ 30fps):
- **0:00–0:01.5 (Frames 0–45):**
  - Fade in from `#0D0D0D` over 15 frames.
  - Play `gameplay.mp4` up to `pauseAtVideoFrame` (or hold on `pauseAtVideoFrame`).
  - Hook text centred at top (`top: 140px`): "Solve it in ONE move" in bold white, 64px, inside a dark pill background (`rgba(13, 13, 13, 0.88)`, border `2px solid #7B2FBE`, border-radius `999px`, padding `20px 44px`).
- **0:01.5–0:06.5 (Frames 45–195):**
  - Freeze `gameplay.mp4` at `pauseAtVideoFrame` full screen using `<Freeze frame={CONFIG.pauseAtVideoFrame}>`.
  - Keep the top hook pill visible.
  - Add three animated label badges (`A`, `B`, `C`) positioned above the three candidate pieces using `spring()` with a 15-frame stagger (Frame 45, 60, 75). Each badge: rounded rectangle (`borderRadius: 20px`), background `#7B2FBE`, white bold text (`48px`), subtle drop shadow.
- **0:06.5–0:11.5 (Frames 195–345):**
  - Keep the board frozen and badges visible.
  - Thinking pause: Add a pulsing clock icon and a 5-dot countdown bar at the bottom (`bottom: 160px`) where 1 dot turns `#FFD700` every 30 frames (1 second).
  - Overlay faint pulsing text (`opacity` oscillating between 0.65 and 1.0): "Where does the piece go?" at 36px bold white with a dark text shadow.
- **0:11.5–0:14.0 (Frames 345–420):**
  - Reveal the answer: Flash the correct badge (`B`) in `#FFD700` (with dark `#0D0D0D` text) and scale up to `1.5×` using `spring()`. Dim the incorrect badges (`A` and `C`) to `opacity: 0.35`.
  - Draw a glowing, pulsing highlight border (`4px solid #FFD700`, `boxShadow: '0 0 35px #FFD700'`) at `CONFIG.solutionBox` on the board grid.
  - Unfreeze `gameplay.mp4` from `pauseAtVideoFrame` so the viewer sees the actual piece placed and the burst combo animation play out!
- **0:14.0–0:15.0 (Frames 420–450):**
  - Smoothly fade to `#0D0D0D` background.
  - Centered call-to-action text: "Comment A, B or C below 👇" in bold white, 44px, with subtext "Did you spot it in time? 🧩" at 30px in `#FFD700`.

### Output Requirements:
- Provide the complete code for `src/MyDayThreeReel.tsx` and `src/Root.tsx` in TypeScript using `remotion`.
- Include terminal installation, preview, and MP4 export commands.
- Colour palette: dark background `#0D0D0D`, accent `#7B2FBE`, highlight `#FFD700`.