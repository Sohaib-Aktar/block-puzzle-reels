# 03 — Code Quality Audit

**Studio:** Social Media Video Production Studio  
**Scope:** Full AST and manual code audit of all 39 Python modules in `scripts/`, 4 test suites in `tests/`, `scripts/win_ocr.ps1`, and `renderers/ffmpeg/trim_and_scale.bat`.

---

## 1. Codebase Metrics Summary

- **Total Python Files Audited:** `43` (`39` in `scripts/`, `4` in `tests/`)
- **Syntax Errors:** `0`
- **Circular Dependencies:** `0`
- **Built-in `open()` Missing `encoding="utf-8"`:** `0` *(initial AST scan flagged PIL `Image.open()` calls; manually verified all built-in text `open()` calls specify UTF-8)*
- **Hardcoded `C:\Users\Dell\Downloads\video gen` inside `.py` source:** `0` *(all Python scripts derive `WORKSPACE_ROOT` dynamically — hardcoded paths occur only in persisted JSON/SQLite outputs and `drive_sync.py`'s `G:\My Drive\Vids\generated`)*
- **Bare `except:` Clauses:** `0`
- **Silent `except Exception: pass` Clauses:** `9` across 5 files (`AUD-020`)
- **`subprocess.run()` Calls Missing `timeout=`:** `25` across 15 scripts (`AUD-013`)

---

## 2. Complexity & Maintainability Hotspots (`AUD-019`)

| File | Total Lines | Longest Function | Function Length | Maintainability Assessment |
|---|---:|---|---:|---|
| `scripts/multi_platform_exporter.py` | 1,140 | `export_master()` | **479 lines** | Monolithic orchestration combining planning, fingerprinting, FFmpeg execution, validation, previewing, and delivery record serialization. |
| `scripts/visual_qc.py` | 688 | `run()` | **447 lines** | Combines FFmpeg detection, checkpoint sampling, PIL analysis, WinRT OCR invocation, safe-zone math, and evidence rendering in one method. |
| `scripts/export_validator.py` | 400 | `validate_export()` | **365 lines** | Sequential 14-check procedural block; clean candidate for decomposed check registry. |
| `scripts/content_qc.py` | 633 | `run()` | **348 lines** | Mixes knowledge loading, brand leak scanning, ERP footage heuristics, claim regexes, licensing, and creative rubric construction. |
| `scripts/audio_qc.py` | 413 | `run()` | **301 lines** | Combines FFprobe inspection, `ebur128`, `volumedetect`, `silencedetect`, tail fade, and check assembly. |
| `scripts/qc_orchestrator.py` | 697 | `run_export_pack_qc()` | **209 lines** | Moderately complex pack/artifact deduplication loop. |
| `scripts/reframing_engine.py` | 450 | `build_filter_plan()` | **208 lines** | Branch-heavy strategy switch; well-structured return schema. |
| `scripts/audio_recommender.py` | 332 | `recommend_audio()` | **200 lines** | Filtering, scoring, licensing gate, and scene plan combined. |

---

## 3. Code Duplication Findings (`AUD-019`)

1. **SHA-256 File Hashing Duplicated 6 Times:**
   - `calculate_sha256()` in `scripts/asset_migrator.py:L44` & `scripts/footage_analyzer.py:L32`
   - `_sha256_file()` in `scripts/audit_export_duplicates.py:L27`, `scripts/content_qc.py:L46`, `scripts/multi_platform_exporter.py:L43`, `scripts/qc_orchestrator.py:L36`
2. **FFprobe Binary Resolution Duplicated Twice:**
   - `get_ffprobe_cmd()` in `scripts/inspect_footage.py:L24` & `scripts/media_engine.py:L53`
3. **Subprocess FFmpeg Execution Boilerplate:** Repeated directly via `subprocess.run(...)` without shared timeout/error wrapper across 15 modules.

---

## 4. Specific Code Quality Defects Verified

1. **Unused Computed Variables (`scripts/campaign_manager.py:L159-160`):** `current_idx` and `target_idx` are calculated inside `advance_state()` and never referenced (`AUD-002`).
2. **Fragile FFmpeg Filtergraph Parsing (`scripts/video_processor.py:L74-80,95,107`):** Splits filter strings with `.split("[ov")[1].split("]overlay=")[1]`, misplaces `-t` before `extra_inputs`, and computes `audio_input_idx` via `len(extra_inputs) // 2` (`AUD-009`).
3. **Silent Exception Swallowing (`AUD-020`):**
   - `scripts/audio_analyzer.py`: lines `112`, `533`, `549`
   - `scripts/audit_export_duplicates.py`: lines `50`, `63`
   - `scripts/media_engine.py`: line `39`
   - `scripts/media_intake.py`: line `318`
   - `scripts/multi_platform_exporter.py`: lines `260`, `279`
4. **Non-Atomic State Serialization (`AUD-014`):** All JSON catalog/job writes open destination paths directly in `"w"` mode rather than writing to a sibling `.tmp` file and atomically replacing with `os.replace()`.
5. **Hardcoded Machine-Specific Drive Path (`scripts/drive_sync.py:L14,25`):** Hardcodes `G:\My Drive\Vids\generated` instead of reading `STUDIO_GDRIVE_ROOT` environment variable / studio config (`AUD-004`).
6. **Batch Script Fallback Bug (`renderers/ffmpeg/trim_and_scale.bat:L39`):** Drops `force_original_aspect_ratio=decrease,pad=...` in the Remotion FFmpeg fallback branch (`AUD-010`).

---

## 5. Positive Code Quality Practices Observed
- Consistent UTF-8 file encoding across all Python text I/O.
- Consistent list-form `subprocess.run([...])` without `shell=True` across all 39 Python scripts (zero shell injection via `shell=True`).
- Parameterized SQL (`?` placeholders) used for all user values in `scripts/campaign_manager.py`.
- Clean separation of Windows WinRT OCR into a parameterized standalone `.ps1` file (`scripts/win_ocr.ps1`) with `try/finally` stream disposal.
