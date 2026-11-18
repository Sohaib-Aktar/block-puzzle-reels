# 04 — Bug and Defect Register

**Studio:** Social Media Video Production Studio  
**Machine-Readable Source:** `data/audit/audit_findings.json`  
**Audit Date:** 2026-11-18

This register distinguishes **confirmed bugs (`VERIFIED_BUG`)** from **potential bugs (`POTENTIAL_BUG`)**. All 15 mandatory fields are provided for each defect.

---

## 1. Confirmed Bugs (`VERIFIED_BUG` — 6 Findings)

### `AUD-002` — Campaign Lifecycle State Machine Gatekeeper Bypass
- **Severity:** `HIGH` | **Category:** `VERIFIED_BUG` | **Confidence:** `HIGH` | **Priority:** `P0`
- **Affected Files:** `scripts/campaign_manager.py`, `data/campaign_tracker.sqlite`
- **Affected Component:** `advance_state()` (L132–189), `update_status()` (L97–129)
- **Evidence:** L142 docstring promises `QC_APPROVED requires technical QC passed and creative QC score >= 72`, yet L163 checks only `if target_state in ["READY_TO_PUBLISH", "PUBLISHED"]:`. L159–160 compute `current_idx` and `target_idx` and never enforce ordering. Live SQLite confirms `multiplatform-pack-01` and `BPB_DAY_05` have `status='QC_APPROVED'` with `technical_qc_passed=0, creative_qc_score=0`. `update_status()` allows direct `status='PUBLISHED'` without sign-off.
- **Current Behavior:** Content can enter `QC_APPROVED` with zero QC and skip stages arbitrarily; `update_status()` can bypass Zero-Unauthorized-Publishing.
- **Expected Behavior:** `QC_APPROVED` enforces passing QC; stage transitions validate allowed edges; `update_status()` forbids direct `PUBLISHED`/`READY_TO_PUBLISH` transitions.
- **Impact:** Compromises lifecycle governance and contradicts studio publishing rules.
- **Reproduction:** Query `SELECT content_id, status, technical_qc_passed, creative_qc_score FROM content_items WHERE status='QC_APPROVED'` on `data/campaign_tracker.sqlite`.
- **Recommended Solution:** Add `QC_APPROVED` to gate checks, enforce valid transition graph, block ungated `PUBLISHED` updates in `update_status()`, and integrate Phase 5 QC approval state.
- **Risks of Fixing:** Medium; verify `scripts/run_test_e_lifecycle.py` and existing CLI calls.
- **Estimated Effort:** 3 hours.

### `AUD-003` — Cross-Project Brand Hashtag Leakage in Global Export Profiles
- **Severity:** `HIGH` | **Category:** `VERIFIED_BUG` | **Confidence:** `HIGH` | **Priority:** `P0`
- **Affected Files:** `config/production/export_profiles.json`, `scripts/multi_platform_exporter.py`, `scripts/platform_adapter.py`
- **Affected Component:** `export_profiles.json` (L16, 28, 40, 52), `MultiPlatformExporter.export_master()` (L759), `platform_adapter.py` (L46–119)
- **Evidence:** `export_profiles.json` globally sets `"default_hashtags": ["#BlockPuzzle", "#PyapirasGames", "#Reels"]` on `instagram_reels` and `#PyapirasGames` on all 4 profiles. `multi_platform_exporter.py:L759` copies `eff_spec.get("default_hashtags", [])` verbatim into every project's delivery record.
- **Current Behavior:** Non-game projects (e.g. `expand-ezisales` or any future client project) receive `#BlockPuzzle` and `#PyapirasGames` in staged platform delivery records.
- **Expected Behavior:** Global export profiles contain zero project-specific hashtags; hashtags are sourced solely from per-project configuration.
- **Impact:** Severe cross-project brand contamination risk if operators paste staged delivery hashtags.
- **Reproduction:** Run `multi_platform_exporter.py --project expand-ezisales` and inspect `deliveries/instagram_reels_delivery.json`.
- **Recommended Solution:** Remove `#BlockPuzzle` / `#PyapirasGames` from `export_profiles.json`; resolve project hashtags from `projects/<project>/` metadata.
- **Risks of Fixing:** Low.
- **Estimated Effort:** 2 hours.

### `AUD-006` — Remotion Day 04 Master Produces 100% Digital Silence Audio Track
- **Severity:** `HIGH` | **Category:** `VERIFIED_BUG` | **Confidence:** `HIGH` | **Priority:** `P1`
- **Affected Files:** `my-video/src/DayFourOfflineReel.tsx`, `outputs/block-puzzle-burst/30-day-challenge/day-04-shared-exports/qc/qc_report.json`
- **Affected Component:** Remotion `DayFourOfflineReel` audio stem routing
- **Evidence:** Phase 5 Audio QC measured `integrated_lufs = -70.0 LUFS` and `silence_ratio = 100.0%` across all `15.02s` (`AUD_004`, `AUD_005`).
- **Current Behavior:** Remotion exports an AAC stream header containing 100% silence, blocking all 4 shared Day 04 exports (`FAIL`).
- **Expected Behavior:** Audible mixed soundtrack around `-14 LUFS` (matching the verified Phase 3 `day-04-no-wifi-revision` mix at `-14.8 LUFS`).
- **Impact:** All 4 Day 04 shared-artifact exports fail QC and cannot be published.
- **Reproduction:** Run `qc_orchestrator.py run-export-pack` on `outputs/block-puzzle-burst/30-day-challenge/day-04-shared-exports`.
- **Recommended Solution:** Route approved audio into `DayFourOfflineReel.tsx` or re-export shared pack from the verified Phase 3 mixed master.
- **Risks of Fixing:** Low.
- **Estimated Effort:** 1 hour.

### `AUD-007` — Pilot B (`expand-ezisales`) Uses Non-ERP Placeholder Footage & Unverified Claim
- **Severity:** `HIGH` | **Category:** `VERIFIED_BUG` | **Confidence:** `HIGH` | **Priority:** `P1`
- **Affected Files:** `config/manifests/manifest_ezisales_tut01_pilot.json`, `source_assets/expand-ezisales/screen-recordings/`, `outputs/expand-ezisales/quick-start-tutorials/ezisales-tut-01-multiplatform-exports/qc/qc_report.json`
- **Affected Component:** Expand eziSales Pilot B manifest & source asset pool
- **Evidence:** Phase 5 QC caught `CNT_001` (OCR read Android settings `['mobile data', 'aeroplane', 'bluetooth', 'torch', 'bedtime']` while `screen-recordings/` is empty), `CLM_001/002` (unsubstantiated `"Under 30s"` claim), and `CRV_001` (missing closing CTA).
- **Current Behavior:** Pilot B tutorial renders phone quick-settings footage with an unverified timing claim and no CTA.
- **Expected Behavior:** Authentic Expand eziSales screen recordings, verified copy matching `projects/expand-ezisales/knowledge/verified_features.md`, and closing CTA.
- **Impact:** Pilot B is blocked from publication.
- **Reproduction:** Read `outputs/expand-ezisales/quick-start-tutorials/ezisales-tut-01-multiplatform-exports/qc/qc_summary.md`.
- **Recommended Solution:** Record real Expand eziSales app footage, verify or remove `"Under 30s"`, add CTA overlay, and re-render.
- **Risks of Fixing:** None.
- **Estimated Effort:** 2 hours.

### `AUD-009` — FFmpeg `-t` Option Placement & Fragile Overlay Filtergraph Parsing
- **Severity:** `MEDIUM` | **Category:** `VERIFIED_BUG` | **Confidence:** `HIGH` | **Priority:** `P1`
- **Affected Files:** `scripts/video_processor.py`
- **Affected Component:** `VideoProcessor.normalize_and_trim_scene()` (L70–111)
- **Evidence:** L95 puts `-t str(duration)` immediately after `-i abs_in` and before `extra_inputs`, applying `-t` as an input option to the first overlay PNG (masked only by repeating `-t` at L132). L107 calculates `audio_input_idx = 1 + (len(extra_inputs) // 2)`, assuming strictly 2 tokens per input. L76–78 parse filter strings via `.split("[ov")[1].split("]overlay=")[1]`.
- **Current Behavior:** Succeeds only for static 2-token PNG overlay inputs; silently breaks stream indexing if `-loop 1` or multi-flag overlay inputs are introduced.
- **Expected Behavior:** Clean input/output `-t` placement, explicit integer input counter, and structured overlay metadata passed from `OverlayEngine`.
- **Impact:** Latent pipeline failure when extending overlay features.
- **Reproduction:** Append `"-loop", "1"` to an overlay input in `overlay_engine.py` and invoke `normalize_and_trim_scene()`.
- **Recommended Solution:** Remove misplaced `-t` at L95, track `input_idx` explicitly, and pass structured overlay dicts instead of string-splitting filtergraphs.
- **Risks of Fixing:** Low; verified by Phase 3 tests.
- **Estimated Effort:** 2 hours.

### `AUD-010` — Aspect-Ratio Distortion in Fallback Branch of `trim_and_scale.bat`
- **Severity:** `MEDIUM` | **Category:** `VERIFIED_BUG` | **Confidence:** `HIGH` | **Priority:** `P2`
- **Affected Files:** `renderers/ffmpeg/trim_and_scale.bat`
- **Affected Component:** Remotion FFmpeg fallback branch (L39)
- **Evidence:** L36 uses `scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2:color=black`, while L39 runs bare `scale=1080:1920`.
- **Current Behavior:** Stretches any non-9:16 input video whenever system `ffmpeg` is not on `PATH` (which is true on this machine).
- **Expected Behavior:** Preserve aspect ratio with padding identically in both branches.
- **Impact:** Visually distorted outputs if operators invoke the legacy batch utility.
- **Reproduction:** Execute `renderers\ffmpeg\trim_and_scale.bat` on a 16:9 clip on a system without global `ffmpeg` on `PATH`.
- **Recommended Solution:** Copy the exact L36 `-vf` filter string to L39.
- **Risks of Fixing:** Negligible.
- **Estimated Effort:** 15 minutes.

---

## 2. Potential Bugs (`POTENTIAL_BUG` — 2 Findings)

### `AUD-013` — Unbounded Subprocess Calls Without Timeout Across 15 Scripts
- **Severity:** `MEDIUM` | **Category:** `POTENTIAL_BUG` | **Confidence:** `HIGH` | **Priority:** `P2`
- **Affected Files:** 15 scripts in `scripts/` (25 `subprocess.run()` calls without `timeout=`).
- **Affected Component:** FFmpeg, ffprobe, PowerShell, and sub-script execution wrappers.
- **Evidence:** AST audit confirmed 25 `subprocess.run()` calls omit `timeout=`, including `media_engine.py:L71`, `audio_qc.py:L43`, `visual_qc.py:L81`, `multi_platform_exporter.py:L387`, `qc_orchestrator.py:L258,268,279,386,443`.
- **Current Behavior:** Stalled FFmpeg or PowerShell child processes can hang indefinitely.
- **Expected Behavior:** Explicit bounded timeouts (e.g., 30s probe/OCR, 300–600s render) with `TimeoutExpired` handling.
- **Impact:** Hung automation jobs and orphaned background processes.
- **Reproduction:** Inspect `subprocess.run` calls in `scripts/media_engine.py:L71` and `scripts/audio_qc.py:L43`.
- **Recommended Solution:** Route all subprocess invocations through a single shared helper with default timeouts.
- **Risks of Fixing:** Low (choose generous timeouts for long 16:9 renders).
- **Estimated Effort:** 3 hours.

### `AUD-020` — Silent Exception Swallowing (`except Exception: pass`) Across 5 Scripts
- **Severity:** `LOW` | **Category:** `POTENTIAL_BUG` | **Confidence:** `HIGH` | **Priority:** `P3`
- **Affected Files:** `scripts/audio_analyzer.py` (L112, 533, 549), `scripts/audit_export_duplicates.py` (L50, 63), `scripts/media_engine.py` (L39), `scripts/media_intake.py` (L318), `scripts/multi_platform_exporter.py` (L260, 279).
- **Affected Component:** Error-handling blocks in metadata/JSON/media helpers.
- **Evidence:** AST scan verified 9 exact `except Exception: pass` blocks.
- **Current Behavior:** Unexpected errors are silently discarded without logging.
- **Expected Behavior:** Catch narrow exception types and log structured warnings.
- **Impact:** Obscures root causes during debugging of corrupt files or unexpected runtime failures.
- **Reproduction:** Inspect cited line numbers.
- **Recommended Solution:** Replace with targeted exceptions (`OSError`, `json.JSONDecodeError`, `ValueError`) and structured warning logs.
- **Risks of Fixing:** Low.
- **Estimated Effort:** 2 hours.
