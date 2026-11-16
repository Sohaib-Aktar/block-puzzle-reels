# Solve-It Reel Brief — Full 5-Scene Challenge

**Content ID:** solve-it-reel  
**Campaign:** 30-day-challenge  
**Project:** Block Puzzle Burst  
**Platform:** Instagram Reel  
**Status:** RENDERED — `outputs/block-puzzle-burst/30-day-challenge/solve-it-reel/final/instagram_reel.mp4`  
**Remotion composition:** `SolveItReel`  
**Source file:** `generated_outputs/videos/SolveItReel_Puzzle_Challenge.mp4`

> [!WARNING]
> The original render (`SolveItReel_Puzzle_Challenge.mp4`) contains Bengali and Hindi on-screen text in Scene 1 (HookScene) and Scene 4 (InteractionScene). This violates the English-only rule from MASTER_SOCIAL_VIDEO_STUDIO_PROMPT §4. A compliance re-render is required. See `my-video/src/SolveItReel.tsx`.

## Concept
Viral 5-scene brain-challenge format. 20 seconds. The most polished reel in the series. No answer revealed — answer coming in Part 2. Designed for maximum comments (A/B/C) and shares.

## Technical specs
- Duration: 20 seconds (600 frames @ 30fps)
- Aspect ratio: 9:16 (1080×1920)
- Renderer: Remotion (SolveItReel composition)
- Source: `my-video/public/gameplay2.mp4` (recording_2.mp4 copy)

## Scenes
| Scene | Frames | Duration | Content |
|---|---|---|---|
| 1 — Hook | 0–90 | 0–3s | "Solve it in ONE MOVE!" over live gameplay |
| 2 — Challenge | 90–210 | 3–7s | Frozen board, A/B/C badges, "Which piece would you place first?" |
| 3 — Countdown | 210–360 | 7–12s | 5-second countdown circle, "Think carefully!" |
| 4 — CTA | 360–480 | 12–16s | Big A/B/C cards, "Which one would you choose? Comment A, B or C!" |
| 5 — Promo | 480–600 | 16–20s | "Block Puzzle Burst", "PLAY NOW 🎮", "Link in Bio!" |

## Compliance fix needed
In `SolveItReel.tsx`:
- Remove Bengali `মাত্র এক চালে সমাধান করুন!` from HookScene (lines ~152)
- Remove Hindi `सिर्फ़ एक चाल में हल करो!` from HookScene (lines ~164)
- Remove Bengali `আপনার উত্তর কী? A, B নাকি C? কমেন্ট করুন!` from InteractionScene (lines ~733)
- Remove Hindi `आपका जवाब क्या है? A, B या C? कमेंट करें!` from InteractionScene (lines ~742)
- Keep English CTA: "Which one would you choose? Comment A, B or C!"

## Captions

### English (primary)
Which piece goes first, and where? 🤔  
Comment A, B or C.  
Think carefully! The answer will be revealed in the next Reel.  
Want to play? Check the link in bio! 🎮  
#BlockPuzzle #PuzzleChallenge #BrainGame #BrainTeaser #MobileGaming  
Link in bio ⬇️

### Bengali
কোন ব্লকটি আগে বসবে এবং কোথায়? 🤔  
A, B নাকি C? কমেন্ট করুন।  
ভালো করে ভাবুন! উত্তর আসবে পরের রিলে।  
খেলতে চান? Bio-তে লিংক দেখুন! 🎮  
লিংক বায়োতে ⬇️

### Hindi
कौन सा ब्लॉक पहले और कहाँ रखना चाहिए? 🤔  
A, B या C कमेंट करें।  
ध्यान से सोचें! जवाब अगली Reel में मिलेगा।  
खेलना चाहते हैं? Bio में लिंक देखें! 🎮  
लिंक बायो में ⬇️

## CTA
"Comment A, B or C" — drives comment engagement. No answer revealed.
