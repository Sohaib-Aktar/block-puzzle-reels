# 10 — Performance and Resource Audit

**Studio:** Social Media Video Production Studio  
**Machine-Readable Source:** `data/audit/workspace_inventory.json` & `data/audit/test_matrix.json`  
**Audit Date:** 2026-11-18

---

## 1. Disk & Storage Footprint Analysis (`AUD-016`)

- **Total Tracked Workspace (excluding `.git/` & `node_modules/`):** **681.31 MB** across **825 files**.
- **Exact Duplicate Storage Overhead:** **224.58 MB** (**33.0%**) across **66 duplicate SHA-256 groups**.
- **Primary Duplication Drivers:**
  1. `Raw_input_files/` copied verbatim into `source_assets/` AND duplicated again into `my-video/public/` (e.g., `recording_1.mp4` `28.98 MB × 4 = 115.92 MB`; `recording_3.mp4` `5.27 MB × 3 = 15.81 MB`).
  2. Duplicate filenames inside the same directory (e.g., `gameplay.mp4` identical to `recording_1.mp4` inside `source_assets/block-puzzle-burst/gameplay/`; `sigmamusicart-619322 (1).mp3` identical to `sigmamusicart-619322.mp3`).
  3. Legacy copies in `generated_outputs/` mirroring `outputs/` (e.g., `SolveItReel_Puzzle_Challenge.mp4` `5.07 MB × 2`).
- **Phase 4.1 Shared-Artifact Optimization (Verified Effective):** On `day-04-shared-exports`, Instagram Reels, Facebook Reels, and YouTube Shorts share **1** physical `1080×1920` MP4 artifact instead of 3 separate encodes, cutting vertical render time and storage by ~66% for compatible packs.

---

## 2. Execution Performance & Bottleneck Profile

| Operation | Measured Runtime | Primary Bottleneck | Scalability Notes |
|---|---:|---|---|
| Phase 5 `qc_orchestrator.py run-export-pack` (2 unique artifacts / 4 platforms) | ~18s | Sequential WinRT OCR (`~1.5s/frame × 5 frames × 2 artifacts`) | Shared-artifact scan cache already avoids re-scanning 2 of 4 platforms (`50%` speedup). |
| Phase 5 `qc_calibration.py` (22 cases: 19 synthetic renders + 22 full QC scans) | 67.93s | Sequential FFmpeg fixture generation + sequential PowerShell WinRT OCR invocations | Spawning a new `powershell.exe` process per OCR frame adds ~0.8–1.0s startup overhead per frame. |
| Phase 4 Multi-Platform Export Test Suite (24 tests) | 33.50s | Multiple synthetic H.264 re-encodes (`libx264 -preset fast`) | Reasonable for integration suite. |
| Phase 2 Audio & Media Suite (15 tests, 23 real MP3s) | 11.54s | Invokes Phase 1 `test_studio_suite.py` (~9.95s) inside `test_11` | Running Phase 1 standalone + inside Phase 2 duplicates ~10s of renders. |
| Phase 3 Pipeline & Phase 5 QC Unit Suites | 2.60s / 1.66s | Fast | Well-optimized. |

---

## 3. Resource & Subprocess Safety Risks
1. **Per-Frame PowerShell Startup Overhead (`scripts/visual_qc.py` -> `scripts/win_ocr.ps1`):** Invoking `powershell.exe` once per sampled frame (`5` spawns per video, `10` per dual-orientation export pack) incurs significant process startup overhead. Batching a list of image paths into a single `win_ocr.ps1` invocation would cut OCR runtime by ~60–70%.
2. **Unbounded Subprocess Runtime (`AUD-013`):** 25 `subprocess.run()` calls lack `timeout=`, risking indefinite CPU/memory lockups on corrupted media streams.
3. **Sequential FFmpeg Analysis Passes (`scripts/audio_qc.py` & `scripts/visual_qc.py`):** Runs separate FFmpeg passes for `ebur128`, `volumedetect`, `silencedetect`, `blackdetect`, `freezedetect`, and `scdet` (~6 separate decodes per unique artifact). Combining compatible audio/video filter chains in a single pass could halve decode CPU time for longer YouTube tutorials (`10–30 min`).
4. **No Streaming / Memory Bounds on `audio_analyzer.py`:** `analyze_acoustic_properties()` decodes audio waveforms into NumPy arrays in memory; fine for 15–180s tracks, but should cap waveform sampling window if analyzing multi-hour audio files.
