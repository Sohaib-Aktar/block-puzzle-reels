# Phase 3 Operations & CLI Guide
**Pyapiras Games Video Production Pipeline**  
**Document:** `docs/PHASE_3_OPERATIONS_GUIDE.md`  
**Date:** 2026-11-17  
**Version:** 3.0.0  

---

## 1. Quick Start Commands

The production pipeline is operated via `scripts/production_pipeline.py`.

### A. Preflight Manifest Validation
Before starting a render, validate that all referenced video clips and audio tracks exist, timestamps are valid, and licensing rules are satisfied:

```powershell
python scripts/production_pipeline.py validate --manifest "config\manifests\manifest_bpb_day04_revision.json"
```

If using unverified sample tracks (`NEEDS_REVIEW`) for internal testing, pass `--allow-review-audio`:
```powershell
python scripts/production_pipeline.py validate --manifest "config\manifests\sample_manifest.json" --allow-review-audio
```

---

### B. Rendering a Production Video
Execute the full production pipeline (scene normalization, overlay rendering, audio mixing with voiceover and ducking, loudness mastering, and post-render validation):

```powershell
python scripts/production_pipeline.py render --manifest "config\manifests\manifest_bpb_day04_revision.json"
```

#### Optional Flags:
- `--output-filename <name.mp4>`: Custom filename in the final folder (defaults to `<content_id>_Final.mp4`).
- `--keep-intermediate`: Retain intermediate scratch clips in `outputs/.../intermediate/` for visual debugging.
- `--allow-review-audio`: Allow preview-only soundtracks for internal test renders.

---

### C. Checking Job Status
Inspect the status and full audit log of any running or completed job:

```powershell
python scripts/production_pipeline.py status --job-id "JOB_BLOCK-PUZZLE-BURST_day-04-no-wifi-revision_20261117_161105_514927"
```

---

### D. Listing Recent Production Jobs
Display recent jobs and their lifecycle states:

```powershell
python scripts/production_pipeline.py list-jobs
```

---

## 2. Directory Layout & Deliverables

Every production render creates an isolated, structured workspace:

```text
outputs/<project>/<campaign>/<content_id>/
├── intermediate/             # Temporary clips & stems (cleaned automatically)
├── final/                    # Broadcast-ready verified MP4 deliverable
│   └── <content_id>_Final.mp4
├── logs/                     # Detailed FFmpeg execution logs
│   ├── ffmpeg_render.log
│   └── render_error.log      # (Only present if job failed)
└── report/                   # Post-render Quality Control reports
    ├── technical_validation_report.md
    ├── qc_report.md          # 7/7 automated checks
    └── creative_qc_report.md # 80/90 creative score
```

---

## 3. Troubleshooting & Failure Recovery

| Issue | Cause | Resolution |
|---|---|---|
| `PreflightValidationError: Audio asset is BLOCKED` | Music track has `RESTRICTED` or `UNKNOWN` licensing status. | Select a verified commercial track (`data/audio_catalog.json`) or studio original. |
| `PreflightValidationError: source_out exceeds media duration` | The scene timestamp requests footage beyond the video's actual length. | Adjust `source_in` / `duration` to fit within media bounds. |
| `QC Check Failed: Duration Constraints` | Rendered length is shorter or longer than the platform preset min/max. | Adjust scene durations in the manifest to match preset rules. |
| `Command failed with exit code 4294967294` | Relative file path not resolved from the execution working directory. | Use absolute paths or canonical Asset IDs (`VID_*`, `AUDIO_*`). |
