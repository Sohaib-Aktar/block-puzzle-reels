# 02 — Complete Architecture Audit

**Studio:** Social Media Video Production Studio  
**Audit Date:** 2026-11-18

---

## 1. End-to-End Studio Workflow Diagram

```mermaid
flowchart TD
    S1["1. Marketing Strategy & Brief<br/>scripts/marketing_director.py"] --> S2["2. Project Knowledge<br/>projects/<project>/knowledge/"]
    S2 --> S3["3. Campaign Tracker<br/>scripts/campaign_manager.py -> data/campaign_tracker.sqlite"]
    R1["Raw_input_files/"] --> S4["4. Media Intake & Migration<br/>scripts/asset_migrator.py & media_intake.py"]
    S4 --> S5["5. Video/Image Analysis<br/>scripts/media_engine.py & footage_analyzer.py"]
    S4 --> S6["6. Audio DSP & Recommendation<br/>scripts/audio_analyzer.py & audio_recommender.py"]
    S5 --> C1[("data/media_catalog.json")]
    S6 --> C2[("data/audio_catalog.json")]
    C1 --> S7["7. Production Manifest & Timeline<br/>config/manifests/*.json -> scripts/timeline_builder.py"]
    C2 --> S7
    S7 --> S8["8-11. Production Render Job<br/>scripts/production_pipeline.py -> render_manager.py"]
    S8 --> S9["Overlay + Video + Audio Mix<br/>overlay_engine.py + video_processor.py + audio_mixer.py"]
    S9 --> S10["Master Validation<br/>scripts/render_validator.py"]
    S10 --> S11["12-14. Multi-Platform Shared Export<br/>scripts/multi_platform_exporter.py + reframing_engine.py"]
    S11 --> S12["Export Validation & Previews<br/>export_validator.py + export_preview_generator.py"]
    S12 --> S13["15-16. Automated QC System<br/>scripts/qc_orchestrator.py"]
    S13 --> Q1["audio_qc.py + visual_qc.py (win_ocr.ps1) + content_qc.py"]
    Q1 --> Q2["qc_report_builder.py -> qc_report.json / qc_summary.md"]
    Q2 --> S14["17. Mandatory Human Approval Gate<br/>qc_orchestrator.py approve -> data/qc_approval_audit.jsonl"]
    S14 --> S15["18. Manual Publishing Readiness<br/>Zero Auto-Publish (optional drive_sync.py)"]
```

---

## 2. Module Dependency Architecture

```mermaid
graph LR
    ME["media_engine.py<br/>(FFmpeg/ffprobe/inspect)"]
    TB["timeline_builder.py"] --> ME
    OE["overlay_engine.py"] --> ME
    VP["video_processor.py"] --> ME
    VP --> OE
    AE["audio_engine.py"] --> ME
    AM["audio_mixer.py"] --> ME
    AM --> AE
    RV["render_validator.py"] --> ME
    RM["render_manager.py"] --> TB
    RM --> VP
    RM --> AM
    RM --> RV
    RM --> PJ["production_job.py"]
    PP["production_pipeline.py"] --> RM
    PP --> PJ
    RE["reframing_engine.py"] --> ME
    EV["export_validator.py"] --> ME
    EP["export_preview_generator.py"] --> ME
    MPE["multi_platform_exporter.py"] --> RE
    MPE --> EV
    MPE --> EP
    AQC["audio_qc.py"] --> ME
    VQC["visual_qc.py"] --> ME
    VQC --> WOCR["win_ocr.ps1"]
    CQC["content_qc.py"] --> ME
    QCO["qc_orchestrator.py"] --> RV
    QCO --> EV
    QCO --> AQC
    QCO --> VQC
    QCO --> CQC
    QCO --> QRB["qc_report_builder.py"]
```

**Circular Dependency Check:** **0 circular imports detected** across all 39 modules in `scripts/`. The layered dependency graph is cleanly acyclic (DAG).

---

## 3. Component-by-Component Architecture Trace (18 Workflow Stages)

| Stage | Primary Component(s) | Inputs | Outputs | State / DB Interaction | Failure & Recovery Behavior |
|---|---|---|---|---|---|
| 1. Strategy & Brief | `marketing_director.py` | Project slug, topic | `brief.md`, `script.md`, `manifest.json` | Registers item in SQLite via `campaign_manager.py` | Fails fast if project profile missing. |
| 2. Knowledge Repo | `projects/<project>/knowledge/` | Markdown ground-truth docs | Parsed corpus in `content_qc.py` | Read-only | Missing knowledge triggers `FAIL` in Phase 5 QC. |
| 3. Campaign Mgmt | `campaign_manager.py` | CLI / API calls | `data/campaign_tracker.sqlite` | SQLite `content_items` table | **Weakness (`AUD-002`):** `QC_APPROVED` gate & sequential transitions unenforced; `update_status()` bypasses publishing gate. |
| 4. Media Intake | `asset_migrator.py`, `media_intake.py` | `Raw_input_files/`, `source_assets/` | Copied assets, `migration_log.json`, `media_catalog.json` | Non-destructive copy + SHA-256 dedup | Safe against overwrite; non-atomic JSON writes (`AUD-014`). |
| 5. Video/Image Analysis | `media_engine.py`, `footage_analyzer.py` | Video/image paths | Codec, fps, dimensions, transparency, SHA-256 | Writes `media_catalog.json` | Handles corrupt files cleanly; missing subprocess timeouts (`AUD-013`). |
| 6. Audio Analysis & Rec | `audio_analyzer.py`, `audio_recommender.py` | Audio stems / MP3s | Loudness, BPM, energy, mood, license status | Writes `audio_catalog.json` | Commercial license gate enforces `VERIFIED_COMMERCIAL_USE` unless preview flag set. |
| 7. Manifest & Timeline | `timeline_builder.py` | `config/manifests/*.json` | Resolved scene timeline & audio plan | Reads `media_catalog.json` & `audio_catalog.json` | Fails preflight on missing asset, invalid trim bounds, or unlicensed audio. |
| 8–11. Production Render | `production_pipeline.py`, `render_manager.py`, `production_job.py`, `overlay_engine.py`, `video_processor.py`, `audio_mixer.py`, `audio_engine.py` | Resolved timeline | Master MP4, logs, `data/production_jobs/*.json` | Persists `ProductionJob` state (`PENDING`->`COMPLETED`/`FAILED`) | Preserves job failure log; **Bugs:** TTS PowerShell injection (`AUD-001`), FFmpeg `-t` placement (`AUD-009`), absolute path persistence (`AUD-005`). |
| 12–14. Multi-Platform Export & Shared Dedup | `multi_platform_exporter.py`, `reframing_engine.py`, `export_preview_generator.py`, `audit_export_duplicates.py` | Master MP4 + `export_profiles.json` + `render_profiles.json` | Physical artifacts (`artifacts/`), delivery records (`deliveries/`), previews, `data/export_jobs/*.json` | Content-addressed fingerprint caching; idempotent reuse | **Bug (`AUD-003`):** `#BlockPuzzle`/`#PyapirasGames` default hashtags leak from global profile into non-game delivery records. |
| 15. Technical Validation | `render_validator.py`, `export_validator.py` | Master or platform MP4 | 14-check technical validation JSON | Stateless | Full FFmpeg decode (`-f null -`) detects stream corruption. |
| 16. Automated QC | `qc_orchestrator.py`, `audio_qc.py`, `visual_qc.py`, `content_qc.py`, `qc_report_builder.py`, `win_ocr.ps1` | Master or export pack | `qc_report.json`, `issue_timeline.json`, `qc_summary.md`, `visual_evidence/`, `audio_evidence/`, `data/qc_jobs/*.json` | Shared-artifact scan caching by `artifact_fingerprint` | Critical-failure override blocks progression (`FAIL`/`BLOCKED`); offline ASR & subjective editorial honestly return `REVIEW_REQUIRED`. |
| 17. Human Approval | `qc_orchestrator.py approve` | `--job-id`, `--decision`, `--reviewer` | `data/qc_approval_audit.jsonl`, updated `data/qc_jobs/*.json` | Append-only audit trail (`auto_published: false`) | Rejects `APPROVE` on `FAIL`/`BLOCKED`; requires written override justification. **Gap:** Decoupled from `campaign_tracker.sqlite` (`AUD-002`). |
| 18. Delivery Readiness | Manual upload / `drive_sync.py` | Approved outputs | Optional copy to Google Drive local mount | None | **Risk (`AUD-004`):** `drive_sync.py` does not check QC approval and lacks path traversal validation. |

---

## 4. Key Architectural Strengths & Structural Fault Lines

### Strengths
- Zero circular dependencies across 39 Python modules.
- Clean separation of platform destination profile vs. physical rendering profile vs. physical artifact (Phase 4.1).
- Evidence-first Phase 5 QC architecture with real DSP + local WinRT OCR and honest capability boundaries (zero fake ASR or fake subjective PASS).
- Strict zero-auto-publishing enforcement in both Phase 1 (`campaign_manager.py` via `advance_state`) and Phase 5 (`qc_orchestrator.py`).

### Structural Fault Lines
1. **Two Disconnected State Stores:** Phase 1 `data/campaign_tracker.sqlite` and Phase 3–5 JSON stores (`data/production_jobs/`, `data/export_jobs/`, `data/qc_jobs/`, `data/qc_approval_audit.jsonl`) do not synchronize state transitions. Approving a QC job in Phase 5 does not update `campaign_tracker.sqlite`, and `campaign_manager.py` still checks legacy `creative_qc_score >= 72`.
2. **Legacy + Modern Coexistence (`AUD-012`):** Four config files define overlapping video/platform specs with inconsistent singular/plural IDs (`instagram_reel` vs `instagram_reels`).
3. **Host-Specific Absolute Path Persistence (`AUD-005`):** Job JSONs and SQLite store absolute Windows paths, impeding portability and root folder renaming.
