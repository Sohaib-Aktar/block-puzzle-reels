# 14 — Prioritized Remediation Backlog

**Studio:** Social Media Video Production Studio  
**Audit Date:** 2026-11-18  
**Status:** **PROPOSED ROADMAP ONLY — ZERO FIXES IMPLEMENTED (Awaiting User Approval)**

Priority Tiers:
- **P0 — Critical / Immediate:** Security vulnerabilities, state-gate bypasses, and cross-project brand leaks. Fix immediately.
- **P1 — High / Pre-Production:** Data portability, broken live masters, test isolation, and repo hygiene. Fix before normal production use.
- **P2 — Medium / Planned:** Stability, config consolidation, documentation, missing test coverage, and optional ASR.
- **P3 — Low / Debt & Optimization:** Refactoring, storage cleanup, and CI automation.

---

## P0 — Immediate Attention (4 Items | ~10 hours total)

| Finding ID | Problem | Proposed Change | Dependencies | Est. Effort | Regression Impact | Verification Requirements |
|---|---|---|---|---|---|---|
| **`AUD-001`** | PowerShell command injection & broken double-quote escaping in `scripts/audio_engine.py:generate_voiceover()`. | Replace inline `powershell -Command` f-string with parameterized `scripts/win_tts.ps1` invoked via `-File` and validate `int` bounds for `rate` (`-10..10`) and `volume` (`0..100`). | None | 2h | Low (Phase 1 Test B, Phase 3 Test 08) | Add unit test with single-quote filename & quoted narration text; run Phase 1 & Phase 3 suites. |
| **`AUD-002`** | `campaign_manager.py` omits `QC_APPROVED` from QC gate, ignores transition order (`current_idx`/`target_idx`), and lets `update_status()` set `PUBLISHED` without human approval. | Enforce QC gate on `QC_APPROVED`, validate allowed stage transitions, restrict `update_status()` from ungated `READY_TO_PUBLISH`/`PUBLISHED`, and clean up stale `QC_APPROVED` flags on unverified rows. | None | 3h | Medium (`run_test_e_lifecycle.py`, `campaign_manager.py` CLI) | Add negative tests proving `IDEA -> QC_APPROVED` (0 QC) and `update_status(..., 'PUBLISHED')` raise `PermissionError`; run Phase 1 & 2 suites. |
| **`AUD-003`** | Global `config/production/export_profiles.json` & `platform_adapter.py` hardcode `#BlockPuzzle` / `#PyapirasGames`, leaking game hashtags into `expand-ezisales` & future projects. | Remove project hashtags from global `export_profiles.json`; load project hashtags from per-project metadata (`projects/<project>/`) with empty default. | None | 2h | Low (Phase 4 delivery records) | Add Phase 4 test verifying `expand-ezisales` delivery record contains zero `#BlockPuzzle` / `#PyapirasGames` tags; run Phase 4 suite. |
| **`AUD-004`** | `scripts/drive_sync.py` allows unsanitized `content_id` path traversal inside hardcoded `G:\My Drive\Vids\generated` and syncs videos without verifying QC approval. | Enforce strict `content_id` slug regex + `os.path.commonpath` containment check, read Drive root from env/config, require `READY_TO_PUBLISH` QC approval (unless explicit `--allow-unapproved`), and add tests. | None | 3h | Low (standalone CLI) | Unit test traversal rejection (`../evil`), unapproved block, and approved sync into mock temp Drive root. |

---

## P1 — Fix Before Normal Production Use (6 Items | ~14 hours total)

| Finding ID | Problem | Proposed Change | Dependencies | Est. Effort | Regression Impact | Verification Requirements |
|---|---|---|---|---|---|---|
| **`AUD-005`** | 12 JSON files in `data/` (291 paths) and 3 SQLite rows persist hardcoded `C:\Users\Dell\Downloads\video gen\...` paths, breaking historical links after folder rename. | Add `to_workspace_relative()` / `resolve_workspace_path()` helpers in shared utils, update job/DB writers to store relative POSIX paths, and run non-destructive migration on existing `data/` records. | Complete local folder rename (or run before rename so paths become portable immediately) | 4h | Medium (Phase 3–5 job & export readers) | Verify 0 `C:\Users\Dell` paths in `data/` JSONs & SQLite; run full Phase 1–5 regression suite. |
| **`AUD-006`** | Remotion Day 04 master renders 100% digital silence (`-70.0 LUFS`), causing all 4 Day 04 shared exports to `FAIL` Phase 5 QC. | Route approved audio into `my-video/src/DayFourOfflineReel.tsx` or re-export shared pack from verified Phase 3 mixed master (`day-04-no-wifi-revision.mp4`). | None | 1h | Low (versioned export pack) | Re-run `qc_orchestrator.py run-export-pack` and confirm `AUD_004`/`AUD_005` resolved (`~-14 LUFS`). |
| **`AUD-007`** | Pilot B (`expand-ezisales`) uses Android settings placeholder footage, unverified `"Under 30s"` claim, and lacks closing CTA. | Supply real Expand eziSales screen recordings in `source_assets/expand-ezisales/screen-recordings/`, verify/remove `"Under 30s"`, add approved CTA, and re-render. | Real ERP footage from user | 2h | Low | Re-run `qc_orchestrator.py run-export-pack` on Pilot B and confirm `CNT_001`, `CLM_001/002`, `CRV_001` cleared. |
| **`AUD-008`** | Phase 1 `test_studio_suite.py` and Phase 5 `test_11` mutate live `data/campaign_tracker.sqlite`, live `outputs/`, and live `data/qc_approval_audit.jsonl`. | Add env/parameter overrides for DB, outputs, `qc_jobs/`, and `qc_approval_audit.jsonl`; isolate all tests in `tempfile.TemporaryDirectory()`. | `AUD-002` | 4h | Medium (test harnesses) | Run full suite twice; verify `git status` shows zero mutations in `data/` or `outputs/`. |
| **`AUD-009`** | `scripts/video_processor.py` misplaces `-t` before `extra_inputs`, assumes `len(extra_inputs)//2` for audio index, and parses filter strings via `.split()`. | Remove misplaced input `-t`, track explicit `next_input_idx`, and pass structured overlay specs from `OverlayEngine`. | None | 2h | Low (Phase 3 renderer) | Add unit test with multi-flag overlay input (`-loop 1`) and run Phase 3 suite (`13/13` PASS). |
| **`AUD-015`** | `.gitignore` omits `.env`, `*.key`, `*.pem`, `credentials.json`, `token.json`; no `requirements.txt` or `[project.dependencies]` exists. | Add defensive secret + SQLite WAL patterns to `.gitignore`; add pinned/bounded Python deps to `requirements.txt` and `pyproject.toml`. | None | 1h | None | Verify `git check-ignore .env credentials.json` and dry-run `pip install --dry-run -r requirements.txt`. |

---

## P2 — Planned Improvements (7 Items | ~4–5 days total)

| Finding ID | Problem | Proposed Change | Dependencies | Est. Effort | Regression Impact | Verification Requirements |
|---|---|---|---|---|---|---|
| **`AUD-010`** | `renderers/ffmpeg/trim_and_scale.bat:L39` fallback stretches non-9:16 video (`scale=1080:1920` without pad). | Align L39 `-vf` filtergraph with L36 (`force_original_aspect_ratio=decrease,pad=...`). | None | 15m | None | Run batch script on 16:9 sample clip and verify `SAR=1:1` and letterboxed 1080×1920 output. |
| **`AUD-011`** | Offline ASR unavailable (`AUD_007` always `REVIEW_REQUIRED`). | Add optional pluggable `faster-whisper` backend in `audio_qc.py` with automatic fallback to `AUD_007` when absent. | `AUD-015` | 1d | Low (additive plugin) | Run calibration benchmark with known mismatched VO audio and measure ASR recall/precision. |
| **`AUD-012`** | 4 overlapping profile configs with singular/plural slug mismatch & legacy Phase 1 scripts alongside Phase 4/5 engines. | Create canonical profile loader with alias normalization (`instagram_reel -> instagram_reels`), move per-project config into `projects/<project>/project_config.json`, mark legacy Phase 1 helpers as shims. | `AUD-003` | 1.5d | Medium (Phase 1–5 config lookups) | Run full Phase 1–5 regression suites + test adding a mock 3rd project via config only. |
| **`AUD-013`** | 25 `subprocess.run()` calls across 15 scripts lack `timeout=`. | Route FFmpeg/ffprobe/PowerShell calls through shared `run_subprocess_safe(cmd, timeout=...)` in `studio_utils.py`. | `AUD-019` (extract helper) | 3h | Low | Unit test `TimeoutExpired` handling + full Phase 1–5 regression. |
| **`AUD-014`** | Direct non-atomic JSON writes & SQLite missing WAL / `busy_timeout`. | Implement `atomic_write_json()` (`.tmp` + `os.replace`) and add `PRAGMA journal_mode=WAL; PRAGMA busy_timeout=5000` in `campaign_manager.py`. | `AUD-015` (`.gitignore` WAL) | 3h | Low | Unit test atomic write preservation on simulated failure + concurrent SQLite write test. |
| **`AUD-017`** | `docs/architecture.md` reports Phases 3–4 as Not Started; 6 broken file references (`data/licenses/`, 5 split Phase 3 test names); incomplete `README.md` setup. | Update `docs/architecture.md`, expand `README.md` setup/CLI guide, create `data/licenses/README.md`, update `scripts/README.md`. | `AUD-015` | 1.5h | None | Re-run automated broken-link scanner and verify `0` broken references. |
| **`AUD-018`** | 11 standalone/supporting scripts lack direct unit tests. | Add isolated unit test suites for `drive_sync.py`, `marketing_director.py`, `content_workflow.py`, `audio_mixer.py` edge cases, `render_manager.py` failure paths, and `win_ocr.ps1` errors. | `AUD-004`, `AUD-008` | 1d | None | Run full `unittest discover` and verify all new + existing tests pass. |

---

## P3 — Optimization & Technical Debt (5 Items | ~3 days total)

| Finding ID | Problem | Proposed Change | Dependencies | Est. Effort | Regression Impact | Verification Requirements |
|---|---|---|---|---|---|---|
| **`AUD-016`** | 224.58 MB (33%) exact binary duplication across 66 SHA-256 groups + per-frame PowerShell OCR spawn overhead. | Clean intra-folder duplicate copies (after user approval) and batch image paths into single `win_ocr.ps1` invocation. | User approval for any binary removal | 4h | Medium (catalog & Remotion paths) | Verify `media_catalog.json`, `audio_catalog.json`, Remotion render, and Phase 5 OCR tests pass. |
| **`AUD-019`** | Duplicate SHA-256 (6×) & `get_ffprobe_cmd` (2×) helpers + 5 monolithic 300–479L functions. | Extract `scripts/studio_utils.py` and decompose `export_master()`, `visual_qc.run()`, `export_validator.validate_export()`, `content_qc.run()`, `audio_qc.run()`. | `AUD-008` | 2d | Medium | Full Phase 1–5 regression + `qc_calibration.py` (`22/22` identical metrics). |
| **`AUD-020`** | 9 silent `except Exception: pass` blocks across 5 scripts. | Narrow exception classes and add structured warning logging. | None | 2h | Low | Run Phase 2 & Phase 4 suites. |
| **`AUD-021`** | Empty `data/footage_catalog.json` & orphan `data/check_video0/`, `outputs/test-project/`. | Remove/archive orphan artifacts after explicit approval. | User confirmation | 30m | Low | Verify `footage_analyzer.py` and all 5 suites pass cleanly. |
| **`AUD-022`** | No `.github/workflows/` CI & pending manual GitHub/folder renames. | Complete manual renames in `STUDIO_RENAMING_REPORT.md` and add Windows GitHub Actions CI running fast unit tests on push/PR. | Manual GitHub rename | 2h | None | Trigger CI workflow on push and verify green check. |
