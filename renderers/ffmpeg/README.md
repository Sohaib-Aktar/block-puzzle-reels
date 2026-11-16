# FFmpeg Renderer

For ordinary video editing: trimming, scaling, text overlays, platform re-encoding.

## When to use FFmpeg vs Remotion

| Task | Use |
|---|---|
| Trim a clip | FFmpeg |
| Scale to platform size | FFmpeg |
| Burn static text overlay | FFmpeg |
| Re-encode for Facebook/YT Shorts | FFmpeg |
| Animated motion graphics | Remotion |
| Spring-animated badges, countdowns | Remotion |
| Video with React component overlays | Remotion |

## Available scripts

### `trim_and_scale.bat`
Trim a source video and scale it to 1080×1920 (Instagram Reel).

```bat
renderers\ffmpeg\trim_and_scale.bat Raw_input_files\recording_1.mp4 00:01:30 00:00:15 output.mp4
```

## FFmpeg availability
Bundled inside Remotion at `my-video/node_modules/`.  
If not on system PATH, run via:
```
npm --prefix my-video exec remotion -- ffmpeg -version
```
Or install system FFmpeg: https://ffmpeg.org/download.html
