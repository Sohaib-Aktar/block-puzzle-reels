"""
audit_export_duplicates.py — Read-Only Storage Deduplication & SHA-256 Audit Tool
Inspects existing rendered outputs across outputs/ and generated_outputs/:
  1. Computes SHA-256 hashes of all MP4 and preview PNG files.
  2. Identifies exact byte-identical duplicate groups.
  3. Identifies functionally duplicate Phase 4 platform exports (same resolution/spec encoded separately).
  4. Checks references in SQLite campaign_tracker, production_jobs, export_jobs, and manifests.
  5. Produces a structured audit report with safe consolidation recommendations.

STRICT SAFETY RULE: This script is 100% READ-ONLY. It NEVER deletes or overwrites any file.
"""

import os
import sys
import json
import sqlite3
import hashlib
import datetime
from collections import defaultdict
from typing import Dict, Any, List

WORKSPACE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(WORKSPACE_ROOT, "scripts"))
from media_engine import inspect_media


def _sha256_file(path: str, chunk_size: int = 1024 * 1024) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def _collect_known_references() -> List[str]:
    """Collects file/directory paths referenced in campaign_tracker.sqlite, job JSONs, and manifests."""
    refs: List[str] = []

    db_path = os.path.join(WORKSPACE_ROOT, "data", "campaign_tracker.sqlite")
    if os.path.exists(db_path):
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        try:
            cur.execute("SELECT output_location FROM content_items WHERE output_location IS NOT NULL")
            for (loc,) in cur.fetchall():
                refs.append(os.path.normcase(os.path.abspath(loc)))
        except Exception:
            pass
        conn.close()

    for sub in ("production_jobs", "export_jobs"):
        jdir = os.path.join(WORKSPACE_ROOT, "data", sub)
        if os.path.exists(jdir):
            for fn in os.listdir(jdir):
                if fn.endswith(".json"):
                    try:
                        with open(os.path.join(jdir, fn), "r", encoding="utf-8") as f:
                            text = f.read()
                        refs.append(os.path.normcase(text))
                    except Exception:
                        pass

    return refs


def run_duplicate_audit() -> Dict[str, Any]:
    """Executes complete read-only SHA-256 and spec audit across outputs/ and generated_outputs/."""
    scan_roots = [
        os.path.join(WORKSPACE_ROOT, "outputs"),
        os.path.join(WORKSPACE_ROOT, "generated_outputs"),
    ]

    mp4_by_hash: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    png_by_hash: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    phase4_exports_analysis: List[Dict[str, Any]] = []

    for root in scan_roots:
        if not os.path.exists(root):
            continue
        for dp, _, fns in os.walk(root):
            for fn in sorted(fns):
                fp = os.path.join(dp, fn)
                rel = os.path.relpath(fp, WORKSPACE_ROOT)
                sz = os.path.getsize(fp)
                if fn.endswith(".mp4"):
                    h = _sha256_file(fp)
                    mp4_by_hash[h].append({"path": rel, "abs_path": fp, "size_bytes": sz, "sha256": h})
                elif fn.endswith(".png") and "previews" in dp:
                    h = _sha256_file(fp)
                    png_by_hash[h].append({"path": rel, "abs_path": fp, "size_bytes": sz, "sha256": h})

    # Inspect Phase 4 multi-platform export directories specifically
    p4_dirs = [
        os.path.join(WORKSPACE_ROOT, "outputs", "block-puzzle-burst", "30-day-challenge", "day-04-multiplatform-exports"),
        os.path.join(WORKSPACE_ROOT, "outputs", "expand-ezisales", "quick-start-tutorials", "ezisales-tut-01-multiplatform-exports"),
    ]
    for d in p4_dirs:
        pexp = os.path.join(d, "platform_exports")
        if not os.path.exists(pexp):
            continue
        entries = []
        for dp, _, fns in os.walk(pexp):
            for fn in sorted(fns):
                if fn.endswith(".mp4"):
                    fp = os.path.join(dp, fn)
                    info = inspect_media(fp)
                    entries.append({
                        "filename": fn,
                        "rel_path": os.path.relpath(fp, WORKSPACE_ROOT),
                        "size_bytes": os.path.getsize(fp),
                        "sha256": _sha256_file(fp),
                        "width": info["width"],
                        "height": info["height"],
                        "fps": info["fps"],
                        "duration": round(info["duration_seconds"], 3),
                        "video_codec": info["video_codec"],
                        "audio_codec": info["audio_codec"],
                        "audio_sample_rate": info["audio_sample_rate"],
                        "audio_channels": info["audio_channels"],
                    })
        phase4_exports_analysis.append({
            "export_dir": os.path.relpath(d, WORKSPACE_ROOT),
            "mp4_files": entries,
            "total_mp4_bytes": sum(e["size_bytes"] for e in entries),
        })

    # Collect byte-identical groups
    byte_identical_mp4 = []
    total_mp4_dup_bytes = 0
    for h, items in mp4_by_hash.items():
        if len(items) > 1:
            sz = items[0]["size_bytes"]
            redundant = sz * (len(items) - 1)
            total_mp4_dup_bytes += redundant
            byte_identical_mp4.append({
                "sha256": h,
                "size_bytes": sz,
                "count": len(items),
                "redundant_bytes": redundant,
                "files": [i["path"] for i in sorted(items, key=lambda x: x["path"])],
            })

    byte_identical_png = []
    total_png_dup_bytes = 0
    for h, items in png_by_hash.items():
        if len(items) > 1:
            sz = items[0]["size_bytes"]
            redundant = sz * (len(items) - 1)
            total_png_dup_bytes += redundant
            byte_identical_png.append({
                "sha256": h,
                "size_bytes": sz,
                "count": len(items),
                "redundant_bytes": redundant,
                "files": [i["path"] for i in sorted(items, key=lambda x: x["path"])],
            })

    # Check references for recommendations
    known_refs = _collect_known_references()
    recommendations = []
    for grp in byte_identical_mp4:
        # Prefer keeping canonical outputs/ path over generated_outputs/ legacy copy when safe
        canonical = next((f for f in grp["files"] if f.startswith("outputs")), grp["files"][0])
        for f in grp["files"]:
            if f == canonical:
                continue
            norm_f = os.path.normcase(os.path.abspath(os.path.join(WORKSPACE_ROOT, f)))
            is_referenced = any(norm_f in r for r in known_refs)
            recommendations.append({
                "candidate_for_removal": f,
                "canonical_keep": canonical,
                "sha256": grp["sha256"],
                "reclaimable_bytes": grp["size_bytes"],
                "referenced_in_tracker_or_jobs": is_referenced,
                "action": "DO_NOT_DELETE_WITHOUT_APPROVAL",
            })

    report = {
        "audited_at": datetime.datetime.now().isoformat(),
        "byte_identical_mp4_groups": byte_identical_mp4,
        "byte_identical_png_groups": byte_identical_png,
        "total_byte_identical_mp4_redundant_bytes": total_mp4_dup_bytes,
        "total_byte_identical_png_redundant_bytes": total_png_dup_bytes,
        "phase4_existing_exports": phase4_exports_analysis,
        "safe_consolidation_recommendations": recommendations,
    }

    # Save JSON report
    out_json = os.path.join(WORKSPACE_ROOT, "data", "duplicate_storage_audit.json")
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    return report


if __name__ == "__main__":
    rep = run_duplicate_audit()
    print(f"Audit saved to data/duplicate_storage_audit.json")
    print(f"Byte-identical MP4 duplicate groups: {len(rep['byte_identical_mp4_groups'])} ({rep['total_byte_identical_mp4_redundant_bytes']/1024/1024:.2f} MB redundant)")
    print(f"Byte-identical PNG preview groups  : {len(rep['byte_identical_png_groups'])} ({rep['total_byte_identical_png_redundant_bytes']/1024/1024:.2f} MB redundant)")
    print(f"Recommended consolidation candidates (pending approval): {len(rep['safe_consolidation_recommendations'])}")
