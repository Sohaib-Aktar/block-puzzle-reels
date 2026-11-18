# Phase 4 Operations Guide — Multi-Platform Export CLI
**Studio:** Pyapiras Games  
**Document:** `docs/PHASE_4_OPERATIONS_GUIDE.md`  
**CLI Entry Point:** `scripts/multi_platform_exporter.py`  
**Date:** 2026-11-18  

---

## 1. CLI Commands

### Show Help & Options
```powershell
python scripts/multi_platform_exporter.py --help
```

### List Configured Platform Profiles
```powershell
python scripts/multi_platform_exporter.py --list-profiles
```

### Export Selected Profiles
```powershell
python scripts/multi_platform_exporter.py `
  --input "outputs\block-puzzle-burst\30-day-challenge\day-04-offline-proof\final\Day_04_Final_Revised_Center_Text.mp4" `
  --manifest "config\manifests\manifest_bpb_day04_revision.json" `
  --profiles instagram_reels youtube_shorts
```

### Export All 4 Profiles (Recommended Full Adaptation Pack)
```powershell
python scripts/multi_platform_exporter.py `
  --input "outputs\block-puzzle-burst\30-day-challenge\day-04-offline-proof\final\Day_04_Final_Revised_Center_Text.mp4" `
  --manifest "config\manifests\manifest_bpb_day04_revision.json" `
  --project "block-puzzle-burst" `
  --campaign "30-day-challenge" `
  --content-id "day-04-multiplatform-exports" `
  --all-profiles
```

### Override Reframing Strategy or Manual Focal Point
```powershell
python scripts/multi_platform_exporter.py `
  --input "path\to\master.mp4" `
  --profiles youtube_standard `
  --reframe-strategy MANUAL_FOCAL_POINT `
  --focal-point 0.5,0.4
```

### Batch Export Multiple Masters
```powershell
python scripts/multi_platform_exporter.py --batch "path\to\batch_jobs.json" --max-workers 2
```

### Check Job Status & Retry Failed Exports
```powershell
python scripts/multi_platform_exporter.py --job-id "EXP_BLOCK-PUZZLE-BURST_..." --status
python scripts/multi_platform_exporter.py --job-id "EXP_BLOCK-PUZZLE-BURST_..." --retry-failed
```

---

## 2. Idempotency & Existing-Output Protection

- **Re-running an identical export:** Automatically detects matching SHA-256 fingerprint, re-verifies file integrity, and reuses the existing output (`REUSED_VALID`) without redundant re-encoding.
- **Protecting pre-existing files:** If a different file already exists at the target path and `--force` is not passed, the engine preserves the existing file untouched and writes a versioned file (`_v2.mp4`, `_v3.mp4`).
- **Explicit overwrite:** Pass `--force` only when intentionally replacing an existing output file.

---

## 3. Troubleshooting & Error Logs

Every export captures its complete FFmpeg command, exit code, elapsed time, stdout, and stderr inside:
- `outputs/<project>/<campaign>/<content_id>/reports/export_logs/<profile>_ffmpeg.log`
- `outputs/<project>/<campaign>/<content_id>/reports/platform_validation.json` (all 18 validation checks per profile)
- `data/export_jobs/<export_job_id>.json` (persistent job state for `--status` and `--retry-failed`)

If any single profile fails (e.g., disk full or interrupted render), temporary `.in_progress.mp4` files are cleaned up automatically without touching validated sibling profiles. Resolve the issue and run `--job-id <id> --retry-failed`.
