You are a Remotion developer. Build a 15-second vertical Reel (1080×1920, 30fps = 450 frames) for a mobile puzzle game called Block Puzzle Burst.

I will upload my gameplay screen recording. Use it as the main video layer.

Timeline:
- 0:00–0:01.5 (frames 0–45): Fade in. Show the hook text centred at the top in bold white with a dark semi-transparent pill background: "Wait for the last piece" (English version). Font: Inter or Poppins, size 64px.
- 0:01.5–0:10 (frames 45–300): Play the gameplay video at full screen, cropped to 1080×1920. No text overlay during this segment.
- 0:10–0:13 (frames 300–390): Slow the video to 0.3× speed (Remotion's <OffthreadVideo> with playbackRate). Add a glowing pulse animation on the combo score number using spring() — scale from 1 to 1.4 and back, colour #FFD700.
- 0:13–0:15 (frames 390–450): Fade to black. Show the game name "Block Puzzle Burst" in white centred, size 48px. Below it, smaller text (32px): "How big is your best combo? 🔥"

Sound: no background music (I will add it in CapCut). Keep the video's original audio.

Output: a single Remotion composition file (MyDayTwoReel.tsx) using @remotion/core, with a Root.tsx export. Include install instructions for remotion and @remotion/core. Use TypeScript.

Colour palette: dark background #0D0D0D, accent #7B2FBE (purple), highlight #FFD700 (gold). Match the game's dark-neon look.
