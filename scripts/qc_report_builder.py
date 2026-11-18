"""
qc_report_builder.py — Unified Phase 5 QC Result Model & Report Generator
Statuses: PASS | PASS_WITH_WARNINGS | REVIEW_REQUIRED | FAIL | BLOCKED
Critical failures ALWAYS override aggregate scores. REVIEW_REQUIRED NEVER silently becomes PASS.
"""

import os
import json
import datetime
from enum import Enum
from typing import Dict, Any, List, Optional


class QCStatus(str, Enum):
    PASS = "PASS"
    PASS_WITH_WARNINGS = "PASS_WITH_WARNINGS"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    FAIL = "FAIL"
    BLOCKED = "BLOCKED"


def compute_overall_status(checks: List[Dict[str, Any]], blocked: bool = False) -> str:
    """Computes strict gatekeeping QC status from individual checks."""
    if blocked:
        return QCStatus.BLOCKED.value
    statuses = [c.get("status", "PASS") for c in checks]
    if any(s == QCStatus.BLOCKED.value for s in statuses):
        return QCStatus.BLOCKED.value
    if any(s == QCStatus.FAIL.value for s in statuses):
        return QCStatus.FAIL.value
    if any(s == QCStatus.REVIEW_REQUIRED.value for s in statuses):
        return QCStatus.REVIEW_REQUIRED.value
    if any(s == QCStatus.PASS_WITH_WARNINGS.value for s in statuses):
        return QCStatus.PASS_WITH_WARNINGS.value
    return QCStatus.PASS.value


class QCReportBuilder:
    """Builds machine-readable (JSON) and human-readable (Markdown) Phase 5 QC reports."""

    @staticmethod
    def build_report(
        qc_job_id: str,
        content_id: str,
        project_id: str,
        master_video_hash: Optional[str],
        export_artifact_hash: Optional[str],
        production_manifest_ref: Optional[str],
        rendering_profile: Optional[str],
        platform_destination: Optional[str],
        checks: List[Dict[str, Any]],
        issues: List[Dict[str, Any]],
        creative_rubric: Optional[List[Dict[str, Any]]] = None,
        audio_metrics: Optional[Dict[str, Any]] = None,
        visual_metrics: Optional[Dict[str, Any]] = None,
        tool_versions: Optional[Dict[str, str]] = None,
        blocked_reason: Optional[str] = None,
    ) -> Dict[str, Any]:
        overall = compute_overall_status(checks, blocked=bool(blocked_reason))

        warnings = [
            f"[{c['name']}] {c.get('actual', '')}"
            for c in checks
            if c.get("status") in (QCStatus.PASS_WITH_WARNINGS.value, QCStatus.REVIEW_REQUIRED.value)
        ]
        failure_explanations = [
            f"[{c['name']}] Expected: {c.get('expected', '')} | Actual: {c.get('actual', '')}"
            for c in checks
            if c.get("status") in (QCStatus.FAIL.value, QCStatus.BLOCKED.value)
        ]
        if blocked_reason:
            failure_explanations.insert(0, f"[BLOCKED] {blocked_reason}")

        # Calculate automated rubric subtotal separately from subjective review items
        scored_dims = [d for d in (creative_rubric or []) if d.get("score") is not None]
        auto_score = sum(d["score"] for d in scored_dims)
        auto_max = sum(d["max"] for d in scored_dims)

        return {
            "qc_job_id": qc_job_id,
            "content_id": content_id,
            "project_id": project_id,
            "master_video_hash": master_video_hash,
            "export_artifact_hash": export_artifact_hash,
            "production_manifest_ref": production_manifest_ref,
            "rendering_profile": rendering_profile,
            "platform_destination": platform_destination,
            "tool_versions": tool_versions or {
                "qc_engine": "5.0.0",
                "ffmpeg": "9.0.2-static",
                "ocr_engine": "Windows.Media.Ocr.OcrEngine (en-US)",
                "asr_engine": "NOT_INSTALLED (PENDING)",
                "subjective_ai_judge": "NOT_CONFIGURED (HUMAN_REQUIRED)",
            },
            "overall_result": overall,
            "blocks_progression": overall in (QCStatus.FAIL.value, QCStatus.BLOCKED.value),
            "requires_human_approval": True,  # Mandatory per studio policy — NEVER auto-publishes
            "summary_counts": {
                "total_checks": len(checks),
                "pass": sum(1 for c in checks if c.get("status") == "PASS"),
                "pass_with_warnings": sum(1 for c in checks if c.get("status") == "PASS_WITH_WARNINGS"),
                "review_required": sum(1 for c in checks if c.get("status") == "REVIEW_REQUIRED"),
                "fail": sum(1 for c in checks if c.get("status") == "FAIL"),
                "blocked": sum(1 for c in checks if c.get("status") == "BLOCKED"),
            },
            "automated_creative_score": {
                "score": auto_score,
                "max_automated": auto_max,
                "subjective_dimensions_pending_human": sum(
                    1 for d in (creative_rubric or []) if d.get("subjective_review_required")
                ),
                "note": "Critical technical/brand/licensing failures always override any positive score.",
            },
            "checks": checks,
            "issues": issues,
            "creative_rubric": creative_rubric or [],
            "warnings": warnings,
            "failure_explanations": failure_explanations,
            "audio_metrics": audio_metrics or {},
            "visual_metrics": visual_metrics or {},
            "timestamp": datetime.datetime.now().isoformat(),
        }

    @staticmethod
    def write_reports(report: Dict[str, Any], qc_dir: str) -> Dict[str, str]:
        """Writes qc_report.json, issue_timeline.json, and qc_summary.md to `qc_dir`."""
        os.makedirs(qc_dir, exist_ok=True)
        json_path = os.path.join(qc_dir, "qc_report.json")
        timeline_path = os.path.join(qc_dir, "issue_timeline.json")
        md_path = os.path.join(qc_dir, "qc_summary.md")

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)

        with open(timeline_path, "w", encoding="utf-8") as f:
            json.dump({
                "qc_job_id": report["qc_job_id"],
                "content_id": report["content_id"],
                "overall_result": report["overall_result"],
                "issue_count": len(report["issues"]),
                "issues": report["issues"],
            }, f, indent=2)

        # Human-readable Markdown summary
        sc = report["summary_counts"]
        lines = [
            f"# Automated QC Summary — {report['content_id']}",
            "",
            f"**QC Job ID:** `{report['qc_job_id']}`  ",
            f"**Project:** `{report['project_id']}`  ",
            f"**Platform Destination:** `{report.get('platform_destination') or 'master'}`  ",
            f"**Rendering Profile:** `{report.get('rendering_profile') or 'N/A'}`  ",
            f"**Overall QC Result:** **`{report['overall_result']}`**  ",
            f"**Blocks Progression:** `{report['blocks_progression']}`  ",
            f"**Timestamp:** `{report['timestamp']}`  ",
            "",
            "## 1. Check Breakdown",
            f"- Total Checks: **{sc['total_checks']}** | PASS: **{sc['pass']}** | PASS_WITH_WARNINGS: **{sc['pass_with_warnings']}** | REVIEW_REQUIRED: **{sc['review_required']}** | FAIL: **{sc['fail']}** | BLOCKED: **{sc['blocked']}**",
            "",
            "| Category | Check | Method | Status | Actual Result |",
            "|---|---|---|---|---|",
        ]
        for c in report["checks"]:
            lines.append(
                f"| {c.get('category', '')} | `{c['name']}` | {c.get('method', '')} | **{c['status']}** | {str(c.get('actual', '')).replace('|', '/')} |"
            )

        if report["issues"]:
            lines.extend(["", "## 2. Detected Issues & Evidence", ""])
            for iss in report["issues"]:
                lines.append(
                    f"- **[{iss['severity']}] `{iss['issue_id']}` ({iss['type']})** @ `{iss.get('timestamp', 'N/A')}`: "
                    f"{iss['actual']} — *Recommendation:* {iss.get('recommendation', '')}"
                )
        else:
            lines.extend(["", "## 2. Detected Issues & Evidence", "", "Zero automated defects detected."])

        if report.get("creative_rubric"):
            lines.extend([
                "",
                "## 3. Evidence-Based Creative Rubric (9 Dimensions)",
                "",
                "| Dimension | Method | Auto Status | Score | Evidence |",
                "|---|---|---|---|---|",
            ])
            for d in report["creative_rubric"]:
                sc_str = f"{d['score']}/{d['max']}" if d.get("score") is not None else "Human Review"
                lines.append(
                    f"| {d['dimension']} | {d['method']} | **{d['automated_status']}** | {sc_str} | {d['evidence']} |"
                )

        lines.extend([
            "",
            "## 4. Mandatory Human Approval Policy",
            "- Automated QC never auto-publishes any video.",
            "- Record final human approval, rejection, or justified override via `python scripts/qc_orchestrator.py approve ...`.",
        ])

        with open(md_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")

        return {
            "qc_report_json": json_path,
            "issue_timeline_json": timeline_path,
            "qc_summary_md": md_path,
        }
