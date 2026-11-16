# Remotion Renderer

For animated motion graphics: spring animations, React component overlays, countdown timers, badge transitions.

## Project location
`my-video/` — this is the actual Node.js project. Always run Remotion commands from inside it or use the `--prefix` flag.

## Compositions
| ID | File | Description |
|---|---|---|
| `FrameFinder` | `src/FrameFinder.tsx` | Frame inspection tool (dev only) |
| `MyDayTwoReel` | `src/MyDayTwoReel.tsx` | Day 2 satisfying clear reel |
| `MyDayThreeReel` | `src/MyDayThreeReel.tsx` | Day 3 puzzle challenge reel |
| `SolveItReel` | `src/SolveItReel.tsx` | Full 5-scene viral challenge reel |

## Commands
Run from workspace root:

```bash
# Open Remotion Studio (preview in browser)
npm run dev

# Render a specific composition
npm --prefix my-video exec remotion -- render src/index.ts SolveItReel outputs/block-puzzle-burst/30-day-challenge/solve-it-reel/final/instagram_reel.mp4

# Render Day 2
npm --prefix my-video exec remotion -- render src/index.ts MyDayTwoReel outputs/block-puzzle-burst/30-day-challenge/day-02-satisfying-clear/final/instagram_reel.mp4

# Render Day 3
npm --prefix my-video exec remotion -- render src/index.ts MyDayThreeReel outputs/block-puzzle-burst/30-day-challenge/day-03-puzzle-challenge/final/instagram_reel.mp4
```

## Component library
Located at `my-video/src/components/`:
- `CandidateBadge` — A/B/C puzzle piece label badge
- `ComboPulse` — Animated combo multiplier display
- `CountdownBar` — Dot-based countdown bar
- `HookBanner` — Animated headline banner
- `OutroCard` — Game promo outro card
- `SolutionBox` — Solution reveal box

## Design tokens
`my-video/src/theme/tokens.ts` — colours, fonts, spring presets, canvas specs (1080×1920 @ 30fps)

## Important notes
- Remotion version: 4.0.543 — do not upgrade without reason
- Root `package.json` has orchestration scripts only. No `node_modules` at root.
- All actual Remotion packages are in `my-video/node_modules/`
