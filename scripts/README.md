# Scripts

Utility scripts for the Social Media Video Production Studio.

## Available scripts

### `inspect_footage.py`
Inspect any video file using the FFprobe bundled inside Remotion.  
Reports: duration, dimensions, fps, codec, audio track.

```
python scripts/inspect_footage.py Raw_input_files/recording_1.mp4
```

Requires: `my-video/node_modules` installed. Run `cd my-video && npm install` first if needed.

## Planned scripts
- `trim_and_overlay.py` — FFmpeg-based trim + text overlay wrapper
- `batch_qc.py` — scan `outputs/` folder and verify all required files exist
- `export_platform.py` — re-encode approved finals for Facebook/YouTube Shorts
