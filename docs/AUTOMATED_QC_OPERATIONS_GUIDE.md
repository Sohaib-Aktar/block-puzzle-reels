# Automated QC Operations Guide

**Studio:** Pyapiras Games — AI Marketing & Creative Content Production Studio  
**CLI Entry Point:** `scripts/qc_orchestrator.py`  
**Calibration Harness:** `scripts/qc_calibration.py`

---

## 1. Quick Command Reference

### 1.1 Run Automated QC on a Single Master Render
```powershell
python scripts/qc_orchestrator.py run-master `
  --video "outputs/block-puzzle-burst/30-day-challenge/day-04-no-wifi-revision/final/day-04-no-wifi-revision.mp4" `
  --project "block-puzzle-burst" `
  --platform "instagram_reels" `
  --manifest "config/manifests/day_04_no_wifi_revision.json" `
  --output-dir "outputs/block-puzzle-burst/30-day-challenge/day-04-no-wifi-revision/qc"
```

**Outputs created in `--output-dir`:**
- `qc_report.json` — Complete machine-readable QC record, check matrix, creative rubric, and issue list.
- `issue_timeline.json` — Chronological time-stamped defects and review flags (`start_s`, `end_s`, `severity`, `evidence`).
- `qc_summary.md` — Human-readable QC summary table and review checklist.
- `visual_evidence/` — Sampled PNG frames and annotated safe-zone/OCR bounding-box overlays.
- `audio_evidence/` — FFmpeg `ebur128`, `volumedetect`, and `silencedetect` measurements (`audio_metrics.json`).
- Job state snapshot in `data/qc_jobs/<qc_job_id>.json`.

---

### 1.2 Run Automated QC on a Multi-Platform / Shared-Artifact Export Pack
```powershell
python scripts/qc_orchestrator.py run-export-pack `
  --export-dir "outputs/block-puzzle-burst/30-day-challenge/day-04-shared-exports" `
  --project "block-puzzle-burst" `
  --manifest "config/manifests/day_04_no_wifi_revision.json"
```

**Shared-Artifact Deduplication Behavior:**
- Reads `export_manifest.json` (supporting both Phase 4 shared-artifact packs and legacy per-platform packs).
- Computes/reads each physical video's `artifact_fingerprint` (or SHA-256).
- Runs heavy physical analysis (full FFmpeg decode, EBU R128 loudness, silence, black/freeze detection, multi-frame WinRT OCR) **once per unique physical artifact**.
- Runs independent platform-specific technical profile checks, safe-zone OCR placement checks, and destination QC reports under `qc/platform_results/<platform>.json`.

---

### 1.3 Inspect QC Job Status
```powershell
python scripts/qc_orchestrator.py status --job-id "QC_BLOCK-PUZZLE-BURST_day-04-no-wifi-revision_20261118_114728_1BCB60"
```

List latest QC jobs:
```powershell
Get-ChildItem data/qc_jobs/*.json | Sort-Object LastWriteTime -Descending | Select-Object -First 10 Name, LastWriteTime
```

---

### 1.4 Record Mandatory Human Approval, Rejection, or Override
Automated QC **never** publishes videos. A human reviewer must record the final decision:

**Approve a `PASS`, `PASS_WITH_WARNINGS`, or `REVIEW_REQUIRED` run:**
```powershell
python scripts/qc_orchestrator.py approve `
  --job-id "<QC_JOB_ID>" `
  --decision "APPROVE" `
  --reviewer "Creative Director" `
  --notes "Listened to audio mix, confirmed voiceover clarity and safe zones."
```

**Reject a video for revision:**
```powershell
python scripts/qc_orchestrator.py approve `
  --job-id "<QC_JOB_ID>" `
  --decision "REJECT" `
  --reviewer "Creative Director" `
  --notes "Audio track silent on Remotion master; re-route audio stem."
```

**Override a `FAIL` (requires explicit `--override-reason` of >= 10 characters):**
```powershell
python scripts/qc_orchestrator.py approve `
  --job-id "<QC_JOB_ID>" `
  --decision "OVERRIDE_APPROVE" `
  --reviewer "Studio Lead" `
  --override-reason "Intentional silent teaser variant approved for muted-autoplay internal preview only."
```

All decisions are appended immutably to `data/qc_approval_audit.jsonl` with `"auto_published": false`.

---

### 1.5 Compare Two QC Runs (Before vs. After Revision)
```powershell
python scripts/qc_orchestrator.py compare `
  --before "outputs/.../v1/qc/qc_report.json" `
  --after "outputs/.../v2/qc/qc_report.json"
```
Reports overall status transition, resolved issues, newly introduced issues, and persistent issues.

---

### 1.6 Run Calibration & Held-Out Validation Benchmark
```powershell
python scripts/qc_calibration.py
```
Executes all 22 labeled cases (9 calibration + 13 held-out) across deterministic, OCR, and real studio tracks and writes `data/qc_calibration_results.json`.

---

## 2. Troubleshooting & Operational Notes

- **WinRT OCR (`scripts/win_ocr.ps1`):** Uses Windows built-in `Windows.Media.Ocr.OcrEngine` (`en-US`). Requires no internet connection or paid API key. Average runtime is ~1.2–1.8 seconds per sampled frame.
- **Audio Analysis:** Uses the bundled `imageio-ffmpeg` static binary (FFmpeg `9.0.2`). If FFmpeg is missing from `PATH`, `scripts/video_processor.py` automatically resolves the bundled binary.
- **ASR Pending (`AUD_007`):** Because no offline Whisper/SAPI ASR engine is installed, every video with audio produces `AUD_007 (REVIEW_REQUIRED)`. Reviewers must manually listen to confirm voiceover pronunciation and script fidelity before approving.
- **Project Knowledge Isolation:** Always pass the exact `--project` slug (`block-puzzle-burst`, `expand-ezisales`). Running a video under the wrong project slug triggers `CRITICAL` brand isolation failures (`BRD_001`).
