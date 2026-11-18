# Studio Renaming & Identity Alignment Report

**Official Studio Title:** **Social Media Video Production Studio**  
**Target GitHub Slug:** `social-media-video-production-studio`  
**Target Local Folder Name:** `Social Media Video Production Studio`  
**Date:** 2026-11-18  
**Current Local Folder (Active IDE Session):** `C:\Users\Dell\Downloads\video gen` *(rename pending IDE close — see Section 6)*  
**Current GitHub Remote:** `https://github.com/Sohaib-Aktar/block-puzzle-reels.git` *(rename pending manual GitHub Settings action — see Section 6)*

---

## 1. Identity Transformation Summary

| Dimension | Previous Value | Target Official Value | Current Execution Status |
|---|---|---|---|
| **Official Studio Display Title** | `AI Social Media Content Studio` / `Pyapiras Games — AI Marketing & Creative Content Production Studio` | **Social Media Video Production Studio** | **COMPLETED** across active configs, metadata, README, scripts, project headers, and operational docs |
| **Package / Project Metadata Slug** | `block-puzzle-reels` (`package.json`) | `social-media-video-production-studio` (`package.json` & `pyproject.toml`) | **COMPLETED** |
| **Local Workspace Root Folder** | `C:\Users\Dell\Downloads\video gen` | `C:\Users\Dell\Downloads\Social Media Video Production Studio` | **PENDING MANUAL ACTION** (folder currently locked by active Antigravity IDE session & shell CWD) |
| **GitHub Repository Name / URL** | `https://github.com/Sohaib-Aktar/block-puzzle-reels` | `https://github.com/Sohaib-Aktar/social-media-video-production-studio` | **PENDING MANUAL ACTION** (`gh` CLI not installed; no GitHub admin API token available) |
| **Local Git Remote (`origin`)** | `https://github.com/Sohaib-Aktar/block-puzzle-reels.git` | `https://github.com/Sohaib-Aktar/social-media-video-production-studio.git` | **INTENTIONALLY PRESERVED** until GitHub remote rename completes so `git fetch`/`push` does not 404 |

---

## 2. Files Updated (21 Files)

| File | Category | Change Summary |
|---|---|---|
| `README.md` | Root Documentation | Updated H1 title to `Social Media Video Production Studio`, updated description, added `Expand eziSales` to active projects, documented target GitHub URL. |
| `package.json` | Node Metadata | Changed `"name"` from `block-puzzle-reels` to `social-media-video-production-studio` and updated `"description"`. |
| `pyproject.toml` | Python Metadata | Added `[project]` metadata block (`name = "social-media-video-production-studio"`, `version = "5.0.0"`, official description). |
| `config/studio_settings/global_defaults.json` | Global Config | Updated `"studio_name"` to `"Social Media Video Production Studio"`. |
| `config/production/defaults.json` | Pipeline Config | Updated `"engine_name"` to `"Social Media Video Production Studio Pipeline"`. |
| `MASTER_SOCIAL_VIDEO_STUDIO_PROMPT.md` | Studio Charter | Updated root workspace label from `video_gen/` to `Social Media Video Production Studio/`. |
| `scripts/media_engine.py` | Core Engine | Updated module docstring to `Social Media Video Production Studio`. |
| `scripts/media_intake.py` | CLI Tool | Updated CLI description to `Social Media Video Production Studio`. |
| `scripts/creative_qc.py` | Legacy QC | Updated brand observation text to `Social Media Video Production Studio`. |
| `scripts/README.md` | Scripts Index | Updated studio title to `Social Media Video Production Studio`. |
| `projects/block-puzzle-burst/PROJECT_PROFILE.md` | Active Project | Updated Studio header to `Social Media Video Production Studio` (preserved `Pyapiras Games` as Play Store developer/game brand). |
| `projects/expand-ezisales/PROJECT_PROFILE.md` | Active Project | Updated Studio header to `Social Media Video Production Studio`. |
| `projects/_template/PROJECT_PROFILE.template.md` | Project Template | Updated Studio header to `Social Media Video Production Studio`. |
| `docs/architecture.md` | Active Doc | Updated H1 title, workspace label, purpose, and target GitHub URL note. |
| `docs/AUDIO_ANALYSIS_GUIDE.md` | Active Guide | Updated Studio header & Workspace Root label. |
| `docs/MEDIA_ASSET_GUIDELINES.md` | Active Guide | Updated Studio header & Workspace Root label. |
| `docs/PRODUCTION_MANIFEST_GUIDE.md` | Active Guide | Updated Studio header to `Social Media Video Production Studio`. |
| `docs/PLATFORM_EXPORT_GUIDE.md` | Active Guide | Updated Studio header to `Social Media Video Production Studio`. |
| `docs/REFRAMING_AND_SAFE_ZONES.md` | Active Guide | Updated Studio header to `Social Media Video Production Studio`. |
| `docs/AUTOMATED_QC_OPERATIONS_GUIDE.md` | Active Guide | Updated Studio header to `Social Media Video Production Studio`. |
| `docs/HUMAN_APPROVAL_WORKFLOW.md` | Active Guide | Updated Studio header to `Social Media Video Production Studio`. |
| `docs/QC_RESULT_AND_SEVERITY_GUIDE.md` | Active Guide | Updated Studio header to `Social Media Video Production Studio`. |
| `docs/marketing_strategy_guide.md` | Active Guide | Updated subtitle to `Social Media Video Production Studio`. |

---

## 3. References Intentionally Retained

1. **`Pyapiras Games` inside `Block Puzzle Burst` assets/profiles/hashtags:** `Pyapiras Games` is the actual Play Store publisher and brand name of the retained game project **Block Puzzle Burst** (`com.pyapiras.blockpuzzleburst`, `#PyapirasGames`), NOT an obsolete studio alias. Preserved untouched.
2. **Historical Phase Reports & Prior Job Logs (`docs/PHASE_*.md`, `data/production_jobs/*.json`, `data/export_jobs/*.json`, `data/qc_jobs/*.json`, `data/migration_log.json`):** Preserved as factual historical artifacts recording the paths/titles active when those runs occurred. *(Note: Stored absolute Windows paths inside `data/` job JSONs and `data/campaign_tracker.sqlite` are logged as a HIGH audit finding in `docs/audit/04_BUG_AND_DEFECT_REGISTER.md` so they are migrated to workspace-relative paths cleanly before or during remediation.)*
3. **Remotion Sub-Project (`my-video/`):** Folder and `my-video/package.json` name (`my-video`) were intentionally NOT renamed so existing `npm --prefix my-video ...` scripts and Remotion build references remain unbroken.

---

## 4. Git & GitHub Verification Evidence

Executed on `2026-11-18`:
```text
git remote -v:
  origin  https://github.com/Sohaib-Aktar/block-puzzle-reels.git (fetch)
  origin  https://github.com/Sohaib-Aktar/block-puzzle-reels.git (push)

git branch -a:
  * main
  remotes/origin/HEAD -> origin/main
  remotes/origin/main

git tag: (none)
.github/ workflows: (none)

git log -1 --oneline:
  48d4717 Remove HR, POS, and WMS projects

git ls-remote origin HEAD:
  2dc800d2d835e638c0f1166e6f9520423c8346ee  HEAD  (remote reachable)
```
- GitHub CLI (`gh`): **Not installed** in local environment.
- Git history: **Untouched** (no history rewrite, no force push, no replacement repo created).

---

## 5. Impact Analysis of Local Folder Rename (`video gen` -> `Social Media Video Production Studio`)

- **Dynamic Python Scripts (`scripts/*.py`, `tests/*.py`):** Compute `WORKSPACE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))` dynamically -> **will continue working automatically** after folder rename.
- **Stored Absolute Paths (Important Caveat Audited in Part 3):** Existing records in `data/campaign_tracker.sqlite` (`output_location`), `data/production_jobs/*.json`, `data/export_jobs/*.json`, `data/qc_jobs/*.json`, and `data/migration_log.json` contain hardcoded `C:\Users\Dell\Downloads\video gen\...` paths from earlier runs. All newly executed runs after renaming will resolve paths dynamically, while historical records should be migrated to relative paths in the remediation backlog (Finding `AUD-001`).

---

## 6. Pending Manual Actions (Exact Instructions)

### Action A — Rename GitHub Repository & Update Local Remote
1. Open `https://github.com/Sohaib-Aktar/block-puzzle-reels/settings` in your browser.
2. Under **General -> Repository name**, change `block-puzzle-reels` to:
   ```text
   social-media-video-production-studio
   ```
   and click **Rename** *(preserves all commits, branches, issues, PRs, releases, collaborators, secrets, and redirects automatically)*.
3. In the repository **About** sidebar, set the description to `Social Media Video Production Studio`.
4. Run in PowerShell inside the local repository:
   ```powershell
   git remote set-url origin https://github.com/Sohaib-Aktar/social-media-video-production-studio.git
   git remote -v
   git fetch origin
   ```

### Action B — Rename Local Workspace Folder (After Closing Antigravity IDE)
Because Antigravity IDE and its Python language server currently hold open directory handles inside `C:\Users\Dell\Downloads\video gen`, renaming while open can fail with a Windows sharing violation or disconnect the live workspace session.
1. Close Antigravity IDE (and any terminals open inside `video gen`).
2. Run in a separate PowerShell window opened in `C:\Users\Dell\Downloads`:
   ```powershell
   Rename-Item -Path "C:\Users\Dell\Downloads\video gen" -NewName "Social Media Video Production Studio"
   ```
3. Re-open `C:\Users\Dell\Downloads\Social Media Video Production Studio` in Antigravity IDE and run `python tests/test_phase5_automated_qc.py` to confirm everything operates cleanly from the new folder path.
