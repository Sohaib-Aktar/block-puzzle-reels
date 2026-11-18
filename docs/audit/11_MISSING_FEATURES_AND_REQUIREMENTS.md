# 11 — Missing Features and Requirements Audit

**Studio:** Social Media Video Production Studio  
**Audit Date:** 2026-11-18

---

## 1. Confirmed Capability Gaps & Missing Requirements

| Gap ID / Ref | Capability | Current State | Impact | Priority |
|---|---|---|---|---|
| `AUD-011` | **Offline Voiceover ASR (Speech-to-Text)** | Not installed; `audio_qc.py` honestly outputs `AUD_007 (REVIEW_REQUIRED, confidence=0.0)` | Every video with voiceover requires manual human listen-through for transcript alignment. | P2 |
| `AUD-011` | **Subjective Creative AI Scoring (Dims 2 & 3)** | Not configured; `content_qc.py` flags Story Clarity & Audience Relevance as `REVIEW_REQUIRED` | Human creative director review remains required (aligned with studio policy, though optional multimodal assist is unavailable). | P3 |
| `AUD-002` | **Unified Campaign <-> QC Approval Synchronization** | Phase 5 `qc_orchestrator.py approve` writes `data/qc_approval_audit.jsonl` & `data/qc_jobs/*.json`, but does **not** update `data/campaign_tracker.sqlite` | Campaign dashboard (`campaign_manager.py`) can show stale `QC_APPROVED` / `RENDERED` status out of sync with actual Phase 5 QC decisions. | P0 / P1 |
| `AUD-003` | **Per-Project Platform Hashtag & Copy Configuration** | Global `export_profiles.json` hardcodes `#BlockPuzzle` / `#PyapirasGames`; no project-level hashtag config loader exists | Blocks clean multi-project caption/hashtag staging for `expand-ezisales` and future projects. | P0 |
| `AUD-007` | **Authentic Expand eziSales Screen Recordings** | `source_assets/expand-ezisales/screen-recordings/` is empty | Pilot B (`ezisales-tut-01`) cannot pass QC until genuine ERP screen recordings are supplied. | P1 |
| `AUD-015` | **Reproducible Python Environment Manifest (`requirements.txt`)** | Missing (`pyproject.toml` lacks `[project.dependencies]`) | Fresh workstation or CI setup cannot run `pip install -r requirements.txt`. | P1 |
| `AUD-017` | **Documentary License Proof Repository (`data/licenses/`)** | Documented in `docs/AUDIO_LICENSING_GUIDELINES.md:L81` but directory does not exist | All 23 user-supplied MP3s remain stuck in `NEEDS_REVIEW` without a structured proof folder. | P2 |
| `AUD-022` | **CI/CD Automation (`.github/workflows/`)** | Absent | No automated regression test execution on Git push or PR. | P3 |
| `AUD-004` | **QC-Gated, Configurable Delivery Sync (`drive_sync.py`)** | Hardcoded `G:\My Drive\Vids\generated`, no QC approval check | Cannot safely sync approved packages across different operator workstations without editing source code. | P0 |

---

## 2. Explicit Scope Confirmations (Intentionally Absent by Policy)
- **Automatic Social Media Publishing:** **Deliberately NOT implemented** (hard policy: zero auto-publishing; mandatory human approval enforced via `auto_published: false`).
- **Replacement Project Scaffolding:** **Deliberately NOT created** per explicit user instructions after removing Expand HR, POS, and WMS.
