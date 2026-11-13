# Project: 30-Day AI Block Puzzle Reels Generator

Build a local AI-assisted gameplay video editing tool.

### Objective
I have a block puzzle mobile game and need to publish one Instagram Reel daily for 30 consecutive days.

I will provide:
- Original gameplay recordings.
- A creative editing prompt.
- Optional reference Reels for editing inspiration.

### Editing requirements
1. Preserve the actual gameplay footage.
2. Automatically identify interesting gameplay segments.
3. Generate different creative hooks for each Reel.
4. Add animated captions and text overlays.
5. Add zoom-in, slow-motion and speed-up effects where appropriate.
6. Add transitions and sound effects.
7. Add background music from royalty-free or user-provided audio.
8. Keep the original game visuals, blocks and scores unchanged.
9. Generate vertical 1080x1920 videos.
10. Export MP4 ready for Instagram Reels.

### Automation
- Generate 30 unique Reel concepts.
- Avoid repeating the same opening hook.
- Use different gameplay timestamps.
- Maintain a consistent visual identity.
- Save each output as Day_01.mp4 through Day_30.mp4.
- Allow individual editing and regeneration.

### Technology
- Python for workflow automation.
- FFmpeg for video processing.
- Gemini API for creative planning and gameplay analysis, with configurable API usage.
- A simple local web interface for uploading footage, entering prompts and previewing output.

### Important
Do not use AI-generated replacement gameplay.
Do not require paid video-generation APIs for ordinary cuts, captions, transitions or effects.
Use local processing wherever possible.

First build a working prototype that generates one complete Reel from an uploaded gameplay video. Test the output before implementing batch generation for all 30 days.