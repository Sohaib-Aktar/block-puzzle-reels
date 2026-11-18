# 05 — Security Audit

**Studio:** Social Media Video Production Studio  
**Audit Date:** 2026-11-18  
**Policy:** Zero secrets exposed; zero credentials modified, rotated, or extracted.

---

## 1. Security Posture Summary

| Check Area | Result | Details |
|---|---|---|
| Hardcoded API Keys / Tokens / Passwords | **PASS (0 found)** | Regex & manual scan across all 825 tracked files found zero hardcoded API keys (`AIza...`, `sk-...`, `ghp_...`, `AKIA...`) or plaintext passwords. |
| Git-Tracked Credential Files | **PASS (0 found)** | No `.env`, `.pem`, `.key`, `credentials.json`, or `token.json` tracked in workspace. |
| `shell=True` / `os.system` / `eval` / `exec` / `pickle` | **PASS (0 found)** | Zero occurrences across all 43 Python files. |
| SQL Injection (`campaign_manager.py`) | **PASS** | All SQLite queries bind user values via `?` placeholders. |
| **PowerShell Command Injection (`audio_engine.py`)** | **FAIL (`AUD-001`, HIGH)** | Unescaped `abs_out`, `rate`, and `volume` interpolated directly into `powershell -Command`. |
| **Local Path Traversal (`drive_sync.py`)** | **FAIL (`AUD-004`, HIGH)** | Unsanitized `content_id` joined directly onto `G:\My Drive\Vids\generated` without containment check or QC approval gate. |
| **`.gitignore` Secret Hygeine & Dependency Pinning** | **WARNING (`AUD-015`, MEDIUM)** | `.gitignore` lacks `.env`, `*.key`, `*.pem`, `credentials.json`, `token.json`; Python deps unpinned (no `requirements.txt`). |
| Zero Auto-Publishing Enforcement | **PASS (with Phase 1 gap)** | Phase 5 `qc_orchestrator.py` strictly enforces `auto_published: false`. Phase 1 `campaign_manager.py:update_status()` gap documented under `AUD-002`. |

---

## 2. Detailed Security Findings (3 Findings)

### `AUD-001` — PowerShell Command Injection & Improper Quote Escaping in Offline TTS
- **Severity:** `HIGH` | **Category:** `SECURITY_RISK` | **Confidence:** `HIGH` | **Priority:** `P0`
- **Affected Files:** `scripts/audio_engine.py`
- **Affected Component:** `generate_voiceover()` (L20–53)
- **Evidence:** L35–45 builds an inline PowerShell script via Python f-string and passes it to `powershell -NoProfile -Command`:
  - `abs_out` (`L41`) is not quote-escaped (`'$abs_out'`).
  - `rate` (`L39`) and `volume` (`L40`) are interpolated without `int()` validation/clamping.
  - `safe_text` escapes `"` as `` `" `` inside a single-quoted PowerShell string, which does not unescape backticks and corrupts spoken output.
- **Current Behavior:** Specially crafted filenames containing `'` or non-integer `rate`/`volume` break out of PowerShell string context and execute arbitrary PowerShell commands.
- **Expected Behavior:** Invoke a dedicated `.ps1` file with a typed `param([string]$Text, [string]$OutPath, [int]$Rate, [int]$Volume)` via `subprocess.run(["powershell", "-NoProfile", "-File", ...])` (matching the safe pattern already used in `scripts/win_ocr.ps1`).
- **Impact:** Local command execution vulnerability if filenames, manifests, or voiceover fields come from untrusted or external sources.
- **Reproduction:** Pass an `output_wav_path` containing a single quote `'` to `generate_voiceover()`.
- **Recommended Solution:** Refactor TTS synthesis into `scripts/win_tts.ps1` invoked via `-File` with argument array and strict `int` bounds (`-10 <= rate <= 10`, `0 <= volume <= 100`).
- **Risks of Fixing:** Low.
- **Estimated Effort:** 2 hours.

### `AUD-004` — Unsanitized Path Traversal & Missing QC Gate in Google Drive Sync
- **Severity:** `HIGH` | **Category:** `SECURITY_RISK` | **Confidence:** `HIGH` | **Priority:** `P0`
- **Affected Files:** `scripts/drive_sync.py`
- **Affected Component:** `sync_to_drive()` (L14, L55–67)
- **Evidence:** L14 hardcodes `GDRIVE_ROOT = r"G:\My Drive\Vids\generated"`. L55 computes `dest_folder = os.path.join(GDRIVE_ROOT, content_id)` without sanitizing `content_id` (`..`, drive letters, backslashes) or checking `os.path.commonpath([GDRIVE_ROOT, abs_dest]) == GDRIVE_ROOT`. Furthermore, L58–67 copies files without checking `qc_report.json` or human approval.
- **Current Behavior:** Arbitrary directory write inside `G:\` via traversal `--content-id` values; unapproved/failed renders can be synced directly to the user's phone.
- **Expected Behavior:** Strict slug regex (`^[A-Za-z0-9_-]+$`), resolved `commonpath` containment check, configurable Drive root via env var, and mandatory QC `READY_TO_PUBLISH` check before sync.
- **Impact:** Overwriting arbitrary files in Google Drive and accidental mobile distribution of QC-failed videos.
- **Reproduction:** Inspect `scripts/drive_sync.py:L55` (`os.path.join(GDRIVE_ROOT, content_id)`).
- **Recommended Solution:** Enforce slug validation + `os.path.commonpath` check + Phase 5 approval check + unit tests.
- **Risks of Fixing:** Low.
- **Estimated Effort:** 3 hours.

### `AUD-015` — Missing Secret-File Protections in `.gitignore` & Unpinned Python Dependencies
- **Severity:** `MEDIUM` | **Category:** `SECURITY_RISK` | **Confidence:** `HIGH` | **Priority:** `P1`
- **Affected Files:** `.gitignore`, `pyproject.toml`
- **Affected Component:** Repository ignore rules & dependency supply-chain reproducibility
- **Evidence:** `.gitignore` ignores only `node_modules/`, build dirs, `*.log`, `__pycache__/`, `*.pyc`, `*.tmp`, `.vscode/`. No ignore rules exist for `.env`, `.env.*`, `*.pem`, `*.key`, `credentials.json`, `token.json`, or SQLite WAL files. No `requirements.txt` exists for `pillow==13.0.0`, `numpy==2.4.2`, `imageio-ffmpeg==0.8.1`.
- **Current Behavior:** Future local credentials could be accidentally staged via `git add .`; Python package versions are unpinned.
- **Expected Behavior:** Defensive `.gitignore` secret patterns + pinned/bounded Python dependencies in `pyproject.toml` and `requirements.txt`.
- **Impact:** Supply-chain drift and accidental credential exposure risk in future phases.
- **Reproduction:** Inspect `.gitignore` and confirm absence of `requirements.txt`.
- **Recommended Solution:** Add defensive secret/SQLite-WAL ignore rules to `.gitignore` and create `requirements.txt` + `[project.dependencies]` in `pyproject.toml`.
- **Risks of Fixing:** None.
- **Estimated Effort:** 1 hour.

---

## 3. Dependency Vulnerability Note
- **Python (`3.14.0`):** Uses current major releases (`Pillow 13.0.0`, `NumPy 2.4.2`, `imageio-ffmpeg 0.8.1` bundling FFmpeg `9.0.2`). No local `pip-audit` tool is installed to query CVE feeds offline; adding `pip-audit` and `npm audit` to a future CI workflow is recommended.
- **Node (`v24.14.1` / `my-video/`):** Uses Remotion `4.0.543`, React `19.3.1`, TypeScript `5.9.3`, ESLint `10.12.0` (`private: true`, local renderer only, no public web server exposed).
