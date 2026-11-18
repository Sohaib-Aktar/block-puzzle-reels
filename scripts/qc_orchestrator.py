"""
qc_orchestrator.py — Phase 5 Automated Quality Control Orchestrator & Human Approval Gate
Coordinates:
  - Technical Video QC (reusing export_validator.py)
  - Audio QC (audio_qc.py)
  - Visual & Real Local OCR QC (visual_qc.py)
  - Content, Brand Isolation, Claims, Licensing & Creative Rubric QC (content_qc.py)
  - Shared-Artifact Multi-Platform Pack QC (analyzes each unique physical MP4 once, validates each platform independently)
  - Audited Human Approval / Override Gate (data/qc_approval_audit.jsonl — ZERO auto-publishing)
"""

import os
import sys
import json
import uuid
import hashlib
import argparse
import datetime
from typing import Dict, Any, List, Optional

WORKSPACE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(WORKSPACE_ROOT, "scripts"))

from media_engine import inspect_media
from export_validator import ExportValidator
from multi_platform_exporter import MultiPlatformExporter
from audio_qc import AudioQC
from visual_qc import VisualQC
from content_qc import ContentAndComplianceQC
from qc_report_builder import QCReportBuilder, QCStatus, compute_overall_status

QC_JOBS_DIR = os.path.join(WORKSPACE_ROOT, "data", "qc_jobs")
APPROVAL_AUDIT_LOG = os.path.join(WORKSPACE_ROOT, "data", "qc_approval_audit.jsonl")


def _sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


class QCOrchestrator:
    """Master orchestrator for Phase 5 Automated QC and Human Approval Gates."""

    def __init__(self):
        self.exporter = MultiPlatformExporter()
        self.tech_validator = ExportValidator(safe_zones_config=self.exporter.safe_zones_cfg)
        self.audio_qc = AudioQC()
        self.visual_qc = VisualQC(safe_zones_config=self.exporter.safe_zones_cfg)
        self.content_qc = ContentAndComplianceQC()
        os.makedirs(QC_JOBS_DIR, exist_ok=True)

    @staticmethod
    def _extract_tech_checks_and_issues(tech_res: Dict[str, Any]) -> tuple:
        checks: List[Dict[str, Any]] = []
        issues: List[Dict[str, Any]] = []
        # Skip checks superseded with deeper analysis in audio_qc / visual_qc to avoid noisy duplication
        skip_names = {"no_unexpected_black_frames", "no_audio_clipping", "audio_video_sync", "safe_zone_compliance"}
        for c in tech_res.get("checks", []):
            if c["name"] in skip_names:
                continue
            st = c["status"]
            checks.append({
                "name": f"tech_{c['name']}",
                "category": "technical",
                "method": "deterministic",
                "status": st,
                "severity": "CRITICAL" if st == "FAIL" else "INFO",
                "expected": c.get("expected"),
                "actual": c.get("actual"),
            })
            if st == "FAIL":
                issues.append({
                    "issue_id": f"TECH_{c['id']:03d}",
                    "severity": "CRITICAL",
                    "type": c["name"],
                    "timestamp": "0.0s",
                    "expected": c.get("expected"),
                    "actual": c.get("actual"),
                    "confidence": 1.0,
                    "recommendation": f"Fix technical parameter '{c['name']}' and re-render.",
                })
        return checks, issues

    def _save_qc_job(self, qc_job_id: str, report: Dict[str, Any], qc_dir: str, file_refs: Dict[str, str]):
        workflow_state = (
            "BLOCKED_QC_FAILED"
            if report["overall_result"] in (QCStatus.FAIL.value, QCStatus.BLOCKED.value)
            else "AWAITING_HUMAN_APPROVAL"
        )
        job_record = {
            "qc_job_id": qc_job_id,
            "workflow_state": workflow_state,
            "overall_result": report["overall_result"],
            "content_id": report["content_id"],
            "project_id": report["project_id"],
            "platform_destination": report.get("platform_destination"),
            "qc_dir": os.path.abspath(qc_dir),
            "report_files": file_refs,
            "human_decision": None,
            "created_at": report["timestamp"],
            "updated_at": report["timestamp"],
        }
        with open(os.path.join(QC_JOBS_DIR, f"{qc_job_id}.json"), "w", encoding="utf-8") as f:
            json.dump(job_record, f, indent=2)
        return job_record

    def run_master_qc(
        self,
        video_path: str,
        project_slug: str,
        platform_profile_id: str = "instagram_reels",
        manifest_path: Optional[str] = None,
        manifest_data: Optional[Dict[str, Any]] = None,
        content_id: Optional[str] = None,
        qc_dir: Optional[str] = None,
        require_cta: bool = True,
        master_info: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Runs complete Phase 5 Automated QC on one rendered master or single platform video."""
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        cid = content_id or os.path.splitext(os.path.basename(video_path))[0]
        qc_job_id = f"QC_{project_slug.upper()}_{cid}_{ts}_{uuid.uuid4().hex[:6].upper()}"

        out_qc_dir = os.path.abspath(
            qc_dir or os.path.join(WORKSPACE_ROOT, "outputs", project_slug, "qc_runs", cid, "qc")
        )
        os.makedirs(out_qc_dir, exist_ok=True)

        # Load manifest if path given
        manifest = manifest_data
        abs_manifest = None
        if manifest_path:
            abs_manifest = os.path.abspath(manifest_path)
            if not os.path.exists(abs_manifest):
                rep = QCReportBuilder.build_report(
                    qc_job_id=qc_job_id,
                    content_id=cid,
                    project_id=project_slug,
                    master_video_hash=None,
                    export_artifact_hash=None,
                    production_manifest_ref=abs_manifest,
                    rendering_profile=None,
                    platform_destination=platform_profile_id,
                    checks=[],
                    issues=[{
                        "issue_id": "BLK_001",
                        "severity": "BLOCKED",
                        "type": "missing_manifest",
                        "timestamp": "0.0s",
                        "expected": "Valid production manifest JSON",
                        "actual": f"Manifest not found: {abs_manifest}",
                        "confidence": 1.0,
                        "recommendation": "Provide valid --manifest path.",
                    }],
                    blocked_reason=f"Manifest not found: {abs_manifest}",
                )
                refs = QCReportBuilder.write_reports(rep, out_qc_dir)
                self._save_qc_job(qc_job_id, rep, out_qc_dir, refs)
                return rep
            with open(abs_manifest, "r", encoding="utf-8") as f:
                manifest = json.load(f)

        # Resolve profile spec
        try:
            profile_spec = self.exporter.get_profile(platform_profile_id)
        except Exception as e:
            rep = QCReportBuilder.build_report(
                qc_job_id=qc_job_id,
                content_id=cid,
                project_id=project_slug,
                master_video_hash=None,
                export_artifact_hash=None,
                production_manifest_ref=abs_manifest,
                rendering_profile=None,
                platform_destination=platform_profile_id,
                checks=[],
                issues=[{
                    "issue_id": "BLK_002",
                    "severity": "BLOCKED",
                    "type": "invalid_platform_profile",
                    "timestamp": "0.0s",
                    "expected": "Configured platform destination profile",
                    "actual": str(e),
                    "confidence": 1.0,
                    "recommendation": "Use a valid profile from config/production/export_profiles.json.",
                }],
                blocked_reason=str(e),
            )
            refs = QCReportBuilder.write_reports(rep, out_qc_dir)
            self._save_qc_job(qc_job_id, rep, out_qc_dir, refs)
            return rep

        abs_video = os.path.abspath(video_path)
        if not os.path.exists(abs_video) or os.path.getsize(abs_video) == 0:
            rep = QCReportBuilder.build_report(
                qc_job_id=qc_job_id,
                content_id=cid,
                project_id=project_slug,
                master_video_hash=None,
                export_artifact_hash=None,
                production_manifest_ref=abs_manifest,
                rendering_profile=profile_spec.get("render_profile_id"),
                platform_destination=platform_profile_id,
                checks=[],
                issues=[{
                    "issue_id": "BLK_003",
                    "severity": "BLOCKED",
                    "type": "missing_or_empty_video",
                    "timestamp": "0.0s",
                    "expected": "Existing non-empty MP4 video",
                    "actual": f"File missing or empty: {abs_video}",
                    "confidence": 1.0,
                    "recommendation": "Render the target video before running QC.",
                }],
                blocked_reason=f"Target video missing or empty: {abs_video}",
            )
            refs = QCReportBuilder.write_reports(rep, out_qc_dir)
            self._save_qc_job(qc_job_id, rep, out_qc_dir, refs)
            return rep

        vid_sha = _sha256_file(abs_video)
        all_checks: List[Dict[str, Any]] = []
        all_issues: List[Dict[str, Any]] = []

        # 1. Technical Video QC (reuses ExportValidator)
        tech_res = self.tech_validator.validate_export(
            export_path=abs_video,
            profile_spec=profile_spec,
            master_info=master_info,
            manifest=manifest,
        )
        t_checks, t_issues = self._extract_tech_checks_and_issues(tech_res)
        all_checks.extend(t_checks)
        all_issues.extend(t_issues)

        # If unreadable container / cannot decode -> return FAIL cleanly without crashing downstream analyzers
        if not tech_res.get("media_info"):
            rep = QCReportBuilder.build_report(
                qc_job_id=qc_job_id,
                content_id=cid,
                project_id=project_slug,
                master_video_hash=vid_sha,
                export_artifact_hash=vid_sha,
                production_manifest_ref=abs_manifest,
                rendering_profile=profile_spec.get("render_profile_id"),
                platform_destination=platform_profile_id,
                checks=all_checks,
                issues=all_issues,
            )
            refs = QCReportBuilder.write_reports(rep, out_qc_dir)
            self._save_qc_job(qc_job_id, rep, out_qc_dir, refs)
            return rep

        # 2. Audio QC
        aud_res = self.audio_qc.run(
            video_path=abs_video,
            manifest=manifest,
            audio_required=bool(profile_spec.get("audio_required", True)),
            evidence_dir=os.path.join(out_qc_dir, "audio_evidence"),
        )
        all_checks.extend(aud_res["checks"])
        all_issues.extend(aud_res["issues"])

        # 3. Visual & Real Local OCR QC
        vis_res = self.visual_qc.run(
            video_path=abs_video,
            manifest=manifest,
            platform_profile_id=platform_profile_id,
            evidence_dir=os.path.join(out_qc_dir, "visual_evidence"),
            frame_dir=os.path.join(out_qc_dir, "frame_analysis"),
        )
        all_checks.extend(vis_res["checks"])
        all_issues.extend(vis_res["issues"])

        # 4. Content, Brand Isolation, Claims, Licensing & Creative Rubric QC
        cnt_res = self.content_qc.run(
            project_slug=project_slug,
            manifest=manifest,
            ocr_lines=vis_res.get("ocr_lines", []),
            visual_metrics=vis_res.get("metrics"),
            audio_metrics=aud_res.get("metrics"),
            platform_passed=tech_res.get("passed", False),
            require_cta=require_cta,
        )
        all_checks.extend(cnt_res["checks"])
        all_issues.extend(cnt_res["issues"])

        report = QCReportBuilder.build_report(
            qc_job_id=qc_job_id,
            content_id=cid,
            project_id=project_slug,
            master_video_hash=vid_sha,
            export_artifact_hash=vid_sha,
            production_manifest_ref=abs_manifest,
            rendering_profile=profile_spec.get("render_profile_id"),
            platform_destination=platform_profile_id,
            checks=all_checks,
            issues=all_issues,
            creative_rubric=cnt_res["creative_rubric"],
            audio_metrics=aud_res["metrics"],
            visual_metrics=vis_res["metrics"],
        )
        refs = QCReportBuilder.write_reports(report, out_qc_dir)
        report["report_files"] = refs
        self._save_qc_job(qc_job_id, report, out_qc_dir, refs)
        return report

    def run_export_pack_qc(self, export_dir: str, require_cta: bool = True) -> Dict[str, Any]:
        """
        Shared-artifact aware Phase 5 QC over a Phase 4 multi-platform export pack.
        Runs heavy physical Audio + Visual + OCR analysis ONCE per unique physical artifact_fingerprint,
        then executes INDEPENDENT platform-specific checks per destination (IG, FB, YT Shorts, YT Standard).
        """
        abs_dir = os.path.abspath(export_dir)
        summary_path = os.path.join(abs_dir, "reports", "export_summary.json")
        if not os.path.exists(summary_path):
            raise FileNotFoundError(f"Phase 4 export_summary.json not found in: {abs_dir}")

        with open(summary_path, "r", encoding="utf-8") as f:
            exp_summary = json.load(f)

        project_slug = exp_summary["project"]
        content_id = exp_summary["content_id"]
        master_sha = exp_summary.get("master_sha256")
        manifest_path = exp_summary.get("manifest_path")
        manifest = None
        if manifest_path and os.path.exists(manifest_path):
            with open(manifest_path, "r", encoding="utf-8") as f:
                manifest = json.load(f)

        master_info = None
        if exp_summary.get("master_path") and os.path.exists(exp_summary["master_path"]):
            master_info = inspect_media(exp_summary["master_path"])

        qc_dir = os.path.join(abs_dir, "qc")
        plat_res_dir = os.path.join(qc_dir, "platform_results")
        os.makedirs(plat_res_dir, exist_ok=True)

        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        pack_job_id = f"QC_PACK_{project_slug.upper()}_{content_id}_{ts}_{uuid.uuid4().hex[:6].upper()}"

        # Cache physical analysis per unique artifact_path / fingerprint so shared MP4s are NEVER scanned redundantly!
        physical_cache: Dict[str, Dict[str, Any]] = {}
        platform_reports: Dict[str, Dict[str, Any]] = {}
        all_pack_checks: List[Dict[str, Any]] = []
        all_pack_issues: List[Dict[str, Any]] = []

        for pid, r in exp_summary.get("results", {}).items():
            art_path = r.get("artifact_path") or r.get("output_path")
            fp = r.get("artifact_fingerprint") or r.get("fingerprint") or art_path
            rp_id = r.get("render_profile_id") or self.exporter.get_profile(pid).get("render_profile_id")
            profile_spec = self.exporter.get_profile(pid)

            if not art_path or not os.path.exists(art_path):
                p_rep = QCReportBuilder.build_report(
                    qc_job_id=f"{pack_job_id}_{pid}",
                    content_id=content_id,
                    project_id=project_slug,
                    master_video_hash=master_sha,
                    export_artifact_hash=None,
                    production_manifest_ref=manifest_path,
                    rendering_profile=rp_id,
                    platform_destination=pid,
                    checks=[],
                    issues=[{
                        "issue_id": f"BLK_{pid}",
                        "severity": "BLOCKED",
                        "type": "missing_platform_artifact",
                        "timestamp": "0.0s",
                        "expected": f"Valid exported MP4 for {pid}",
                        "actual": f"Artifact missing: {art_path}",
                        "confidence": 1.0,
                        "recommendation": "Re-run multi_platform_exporter.py.",
                    }],
                    blocked_reason=f"Missing exported artifact for {pid}",
                )
                platform_reports[pid] = p_rep
                continue

            # Run physical Audio + Visual + OCR analysis ONCE per unique physical artifact!
            if fp not in physical_cache:
                art_key = rp_id or fp[:8]
                aud_res = self.audio_qc.run(
                    video_path=art_path,
                    manifest=manifest,
                    audio_required=bool(profile_spec.get("audio_required", True)),
                    evidence_dir=os.path.join(qc_dir, "audio_evidence", art_key),
                )
                vis_res = self.visual_qc.run(
                    video_path=art_path,
                    manifest=manifest,
                    platform_profile_id=pid,
                    evidence_dir=os.path.join(qc_dir, "visual_evidence", art_key),
                    frame_dir=os.path.join(qc_dir, "frame_analysis", art_key),
                )
                physical_cache[fp] = {
                    "artifact_sha256": _sha256_file(art_path),
                    "audio": aud_res,
                    "visual": vis_res,
                    "analyzed_for_primary": pid,
                }

            cached = physical_cache[fp]
            reused_physical = (cached["analyzed_for_primary"] != pid)

            # Independent per-platform technical check (verifies THIS platform's duration limits, profile & safe zones!)
            tech_res = self.tech_validator.validate_export(
                export_path=art_path,
                profile_spec=profile_spec,
                master_info=master_info,
                manifest=manifest,
            )
            p_checks, p_issues = self._extract_tech_checks_and_issues(tech_res)

            # Re-evaluate platform-specific safe-zone bounds against cached OCR lines
            sz_spec = self.exporter.safe_zones_cfg.get("profiles", {}).get(pid)
            p_sz_unsafe = []
            if sz_spec:
                sb = sz_spec.get("safe_content_box")
                cw, ch = sz_spec["canvas"]["width"], sz_spec["canvas"]["height"]
                if sb and tech_res["media_info"]["width"] == cw and tech_res["media_info"]["height"] == ch:
                    for ov_chk in cached["visual"]["metrics"].get("expected_overlay_results", []):
                        mb = ov_chk.get("matched_box")
                        if mb:
                            bx, by, bw, bh = mb["x"], mb["y"], mb["width"], mb["height"]
                            if by < sb["y"] - 15 or (by + bh) > (sb["y"] + sb["height"] + 15):
                                p_sz_unsafe.append(mb)

            p_checks.append({
                "name": f"platform_safe_zone_{pid}",
                "category": "platform",
                "method": "ocr",
                "status": "FAIL" if p_sz_unsafe else "PASS",
                "severity": "CRITICAL" if p_sz_unsafe else "INFO",
                "actual": f"{len(p_sz_unsafe)} overlay(s) outside {pid} safe zone" if p_sz_unsafe else f"All matched overlays within {pid} provisional safe zone",
                "expected": f"Overlays inside {pid} safe content box",
            })

            # Combine physical audio + visual checks + independent content/licensing checks
            cnt_res = self.content_qc.run(
                project_slug=project_slug,
                manifest=manifest,
                ocr_lines=cached["visual"].get("ocr_lines", []),
                visual_metrics=cached["visual"].get("metrics"),
                audio_metrics=cached["audio"].get("metrics"),
                platform_passed=tech_res.get("passed", False),
                require_cta=require_cta,
            )

            combined_checks = p_checks + cached["audio"]["checks"] + cached["visual"]["checks"] + cnt_res["checks"]
            combined_issues = p_issues + cached["audio"]["issues"] + cached["visual"]["issues"] + cnt_res["issues"]

            p_rep = QCReportBuilder.build_report(
                qc_job_id=f"{pack_job_id}_{pid}",
                content_id=content_id,
                project_id=project_slug,
                master_video_hash=master_sha,
                export_artifact_hash=cached["artifact_sha256"],
                production_manifest_ref=manifest_path,
                rendering_profile=rp_id,
                platform_destination=pid,
                checks=combined_checks,
                issues=combined_issues,
                creative_rubric=cnt_res["creative_rubric"],
                audio_metrics=cached["audio"]["metrics"],
                visual_metrics=cached["visual"]["metrics"],
            )
            p_rep["physical_analysis_reused_from"] = cached["analyzed_for_primary"] if reused_physical else None

            with open(os.path.join(plat_res_dir, f"{pid}_qc.json"), "w", encoding="utf-8") as pf:
                json.dump(p_rep, pf, indent=2)

            platform_reports[pid] = p_rep
            all_pack_checks.append({
                "name": f"platform_qc_{pid}",
                "category": "platform",
                "method": "orchestrated",
                "status": p_rep["overall_result"],
                "severity": "CRITICAL" if p_rep["overall_result"] in ("FAIL", "BLOCKED") else ("REVIEW" if p_rep["overall_result"] == "REVIEW_REQUIRED" else "INFO"),
                "expected": f"Platform {pid} passes automated QC",
                "actual": f"{p_rep['overall_result']} (artifact={rp_id}, reused_scan={reused_physical})",
            })
            for iss in combined_issues:
                ic = dict(iss)
                ic["platform"] = pid
                all_pack_issues.append(ic)

        pack_report = QCReportBuilder.build_report(
            qc_job_id=pack_job_id,
            content_id=content_id,
            project_id=project_slug,
            master_video_hash=master_sha,
            export_artifact_hash=None,
            production_manifest_ref=manifest_path,
            rendering_profile=f"{len(physical_cache)} unique physical artifact(s)",
            platform_destination=", ".join(platform_reports.keys()),
            checks=all_pack_checks,
            issues=all_pack_issues,
            creative_rubric=next(iter(platform_reports.values())).get("creative_rubric", []) if platform_reports else [],
        )
        pack_report["unique_physical_artifacts_analyzed"] = len(physical_cache)
        pack_report["platforms_validated_independently"] = len(platform_reports)
        pack_report["platform_summaries"] = {
            pid: {
                "overall_result": pr["overall_result"],
                "render_profile": pr["rendering_profile"],
                "physical_analysis_reused_from": pr.get("physical_analysis_reused_from"),
                "report_path": os.path.join(plat_res_dir, f"{pid}_qc.json"),
            }
            for pid, pr in platform_reports.items()
        }

        refs = QCReportBuilder.write_reports(pack_report, qc_dir)
        pack_report["report_files"] = refs
        self._save_qc_job(pack_job_id, pack_report, qc_dir, refs)
        return pack_report

    def load_qc_job(self, qc_job_id: str) -> Dict[str, Any]:
        p = os.path.join(QC_JOBS_DIR, f"{qc_job_id}.json")
        if not os.path.exists(p):
            raise FileNotFoundError(f"QC job not found: {qc_job_id}")
        with open(p, "r", encoding="utf-8") as f:
            return json.load(f)

    def record_human_decision(
        self,
        qc_job_id: str,
        reviewer: str,
        decision: str,
        reason: str,
        accept_warnings: bool = False,
    ) -> Dict[str, Any]:
        """
        Records an audited human review decision (APPROVE, OVERRIDE_APPROVE, REJECT, REQUEST_RERENDER).
        Enforces strict gatekeeping: FAIL/BLOCKED cannot be approved without OVERRIDE_APPROVE + justification.
        NEVER triggers automated publishing!
        """
        valid_decisions = {"APPROVE", "OVERRIDE_APPROVE", "REJECT", "REQUEST_RERENDER"}
        dec = decision.upper()
        if dec not in valid_decisions:
            raise ValueError(f"Invalid decision '{decision}'. Must be one of: {sorted(valid_decisions)}")
        if not reviewer or not reviewer.strip():
            raise ValueError("Reviewer identity is required for audit trail.")

        job = self.load_qc_job(qc_job_id)
        overall = job["overall_result"]

        if dec == "APPROVE":
            if overall in (QCStatus.FAIL.value, QCStatus.BLOCKED.value):
                raise PermissionError(
                    f"GATEKEEPER BLOCK: QC job '{qc_job_id}' has result '{overall}'. "
                    "Cannot APPROVE a failed/blocked render; fix defects or use OVERRIDE_APPROVE with written justification."
                )
            if overall in (QCStatus.REVIEW_REQUIRED.value, QCStatus.PASS_WITH_WARNINGS.value) and not accept_warnings:
                raise PermissionError(
                    f"GATEKEEPER BLOCK: QC job '{qc_job_id}' has result '{overall}'. "
                    "Reviewer must explicitly confirm warnings/review items via accept_warnings=True."
                )
            new_state = "READY_TO_PUBLISH"
        elif dec == "OVERRIDE_APPROVE":
            if not reason or len(reason.strip()) < 10:
                raise ValueError("OVERRIDE_APPROVE requires a written justification of at least 10 characters.")
            new_state = "READY_TO_PUBLISH"
        elif dec == "REQUEST_RERENDER":
            new_state = "RERENDER_REQUESTED"
        else:
            new_state = "REJECTED"

        audit_entry = {
            "timestamp": datetime.datetime.now().isoformat(),
            "qc_job_id": qc_job_id,
            "content_id": job["content_id"],
            "project_id": job["project_id"],
            "previous_qc_result": overall,
            "reviewer": reviewer.strip(),
            "decision": dec,
            "accept_warnings": accept_warnings,
            "reason": reason.strip(),
            "new_workflow_state": new_state,
            "auto_published": False,  # Studio policy: NEVER auto-publish
        }

        with open(APPROVAL_AUDIT_LOG, "a", encoding="utf-8") as af:
            af.write(json.dumps(audit_entry) + "\n")

        job["workflow_state"] = new_state
        job["human_decision"] = audit_entry
        job["updated_at"] = audit_entry["timestamp"]
        with open(os.path.join(QC_JOBS_DIR, f"{qc_job_id}.json"), "w", encoding="utf-8") as jf:
            json.dump(job, jf, indent=2)

        return audit_entry

    @staticmethod
    def compare_reports(report_a_path: str, report_b_path: str) -> Dict[str, Any]:
        """Compares two qc_report.json files and reports resolved vs newly detected issues."""
        with open(os.path.abspath(report_a_path), "r", encoding="utf-8") as f:
            ra = json.load(f)
        with open(os.path.abspath(report_b_path), "r", encoding="utf-8") as f:
            rb = json.load(f)

        types_a = {i["type"] for i in ra.get("issues", [])}
        types_b = {i["type"] for i in rb.get("issues", [])}
        return {
            "report_a": {"qc_job_id": ra.get("qc_job_id"), "overall_result": ra.get("overall_result"), "issue_count": len(ra.get("issues", []))},
            "report_b": {"qc_job_id": rb.get("qc_job_id"), "overall_result": rb.get("overall_result"), "issue_count": len(rb.get("issues", []))},
            "resolved_issue_types": sorted(types_a - types_b),
            "new_issue_types": sorted(types_b - types_a),
            "persisting_issue_types": sorted(types_a & types_b),
        }


def main():
    parser = argparse.ArgumentParser(description="Pyapiras Games Phase 5 — Automated QC Orchestrator")
    sub = parser.add_subparsers(dest="action")

    p_m = sub.add_parser("run-master", help="Run automated QC on a single rendered video")
    p_m.add_argument("--input", required=True, help="Path to MP4 video")
    p_m.add_argument("--project", required=True, help="Project slug (e.g. block-puzzle-burst, expand-ezisales)")
    p_m.add_argument("--profile", default="instagram_reels", help="Target platform profile ID")
    p_m.add_argument("--manifest", default=None, help="Optional production manifest JSON")
    p_m.add_argument("--content-id", default=None, help="Content ID override")
    p_m.add_argument("--qc-dir", default=None, help="Explicit QC output directory")

    p_p = sub.add_parser("run-export-pack", help="Run shared-artifact automated QC across a Phase 4 export directory")
    p_p.add_argument("--export-dir", required=True, help="Path to Phase 4 export directory containing reports/export_summary.json")

    p_s = sub.add_parser("status", help="Inspect QC job status")
    p_s.add_argument("--qc-job-id", required=True)

    p_a = sub.add_parser("approve", help="Record audited human review decision (NEVER auto-publishes)")
    p_a.add_argument("--qc-job-id", required=True)
    p_a.add_argument("--reviewer", required=True)
    p_a.add_argument("--decision", required=True, choices=["APPROVE", "OVERRIDE_APPROVE", "REJECT", "REQUEST_RERENDER"])
    p_a.add_argument("--reason", required=True)
    p_a.add_argument("--accept-warnings", action="store_true")

    p_c = sub.add_parser("compare", help="Compare two qc_report.json files")
    p_c.add_argument("--report-a", required=True)
    p_c.add_argument("--report-b", required=True)

    args = parser.parse_args()
    orch = QCOrchestrator()

    if args.action == "run-master":
        rep = orch.run_master_qc(
            video_path=args.input,
            project_slug=args.project,
            platform_profile_id=args.profile,
            manifest_path=args.manifest,
            content_id=args.content_id,
            qc_dir=args.qc_dir,
        )
        print(f"\nQC Job ID     : {rep['qc_job_id']}")
        print(f"Overall Result: {rep['overall_result']} (blocks_progression={rep['blocks_progression']})")
        print(f"Checks        : {rep['summary_counts']}")
        print(f"Issues Found  : {len(rep['issues'])}")
        print(f"Summary Report: {rep['report_files']['qc_summary_md']}\n")
        sys.exit(0 if not rep["blocks_progression"] else 1)

    elif args.action == "run-export-pack":
        rep = orch.run_export_pack_qc(args.export_dir)
        print(f"\nPack QC Job ID: {rep['qc_job_id']}")
        print(f"Overall Result: {rep['overall_result']}")
        print(f"Physical Artifacts Analyzed: {rep['unique_physical_artifacts_analyzed']} (for {rep['platforms_validated_independently']} platforms)")
        for pid, ps in rep["platform_summaries"].items():
            reused = f"reused from {ps['physical_analysis_reused_from']}" if ps["physical_analysis_reused_from"] else "primary scan"
            print(f"  - {pid:<18}: {ps['overall_result']:<18} ({ps['render_profile']} | {reused})")
        print(f"Summary Report: {rep['report_files']['qc_summary_md']}\n")
        sys.exit(0 if not rep["blocks_progression"] else 1)

    elif args.action == "status":
        job = orch.load_qc_job(args.qc_job_id)
        print(json.dumps(job, indent=2))

    elif args.action == "approve":
        entry = orch.record_human_decision(
            qc_job_id=args.qc_job_id,
            reviewer=args.reviewer,
            decision=args.decision,
            reason=args.reason,
            accept_warnings=args.accept_warnings,
        )
        print(f"\nHuman Decision Recorded: {entry['decision']} -> {entry['new_workflow_state']} (auto_published=False)\n")

    elif args.action == "compare":
        diff = orch.compare_reports(args.report_a, args.report_b)
        print(json.dumps(diff, indent=2))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
