"""
test_phase5_automated_qc.py — Comprehensive Test Suite for Phase 5 Automated QC System
Verifies technical, audio, visual/OCR, content/brand/claims, documentary licensing,
shared-artifact pack QC, human approval/override gates, report comparison, and calibration evidence.
"""

import os
import sys
import json
import shutil
import tempfile
import unittest

WORKSPACE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(WORKSPACE_ROOT, "scripts"))

from qc_report_builder import compute_overall_status, QCStatus, QCReportBuilder
from audio_qc import AudioQC
from visual_qc import VisualQC
from content_qc import ContentAndComplianceQC
from qc_orchestrator import QCOrchestrator, QC_JOBS_DIR, APPROVAL_AUDIT_LOG


class TestPhase5AutomatedQC(unittest.TestCase):
    """Automated test suite for Phase 5 QC Automation."""

    @classmethod
    def setUpClass(cls):
        cls.orch = QCOrchestrator()
        cls.audio_qc = AudioQC()
        cls.visual_qc = VisualQC()
        cls.content_qc = ContentAndComplianceQC()
        cls.tmp_dir = tempfile.mkdtemp(prefix="p5_unit_")
        cls.temp_job_ids = []

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(cls.tmp_dir):
            shutil.rmtree(cls.tmp_dir, ignore_errors=True)
        for jid in cls.temp_job_ids:
            p = os.path.join(QC_JOBS_DIR, f"{jid}.json")
            if os.path.exists(p):
                try:
                    os.remove(p)
                except OSError:
                    pass

    def test_01_critical_failure_overrides_positive_checks(self):
        checks = [{"name": f"ok_{i}", "status": "PASS"} for i in range(20)]
        checks.append({"name": "critical_defect", "status": "FAIL"})
        self.assertEqual(compute_overall_status(checks), QCStatus.FAIL.value)

    def test_02_review_required_never_silently_passes(self):
        checks = [
            {"name": "c1", "status": "PASS"},
            {"name": "c2", "status": "PASS_WITH_WARNINGS"},
            {"name": "c3", "status": "REVIEW_REQUIRED"},
        ]
        self.assertEqual(compute_overall_status(checks), QCStatus.REVIEW_REQUIRED.value)

    def test_03_missing_input_returns_blocked(self):
        rep = self.orch.run_master_qc(
            video_path=os.path.join(self.tmp_dir, "nonexistent.mp4"),
            project_slug="block-puzzle-burst",
            platform_profile_id="instagram_reels",
            content_id="test_missing",
            qc_dir=os.path.join(self.tmp_dir, "qc_missing"),
        )
        self.temp_job_ids.append(rep["qc_job_id"])
        self.assertEqual(rep["overall_result"], QCStatus.BLOCKED.value)
        self.assertTrue(rep["blocks_progression"])

    def test_04_audio_qc_detects_silent_vs_mixed_audio(self):
        # Silent Day 04 Remotion artifact
        silent_vid = os.path.join(
            WORKSPACE_ROOT, "outputs", "block-puzzle-burst", "30-day-challenge",
            "day-04-shared-exports", "artifacts", "VERTICAL_1080_1920",
            "day-04-shared-exports_VERTICAL_1080_1920.mp4"
        )
        res_sil = self.audio_qc.run(silent_vid)
        sil_types = {i["type"] for i in res_sil["issues"]}
        self.assertIn("silent_audio_track", sil_types)
        self.assertIn("excessive_silence", sil_types)

        # Mixed Phase 3 Day 04 artifact (real BGM + VO + SFX)
        mixed_vid = os.path.join(
            WORKSPACE_ROOT, "outputs", "block-puzzle-burst", "30-day-challenge",
            "day-04-no-wifi-revision", "final", "Day_04_Final_Revised_Center_Text.mp4"
        )
        with open(os.path.join(WORKSPACE_ROOT, "config", "manifests", "manifest_bpb_day04_revision.json"), "r", encoding="utf-8") as f:
            m = json.load(f)
        res_mix = self.audio_qc.run(mixed_vid, manifest=m)
        mix_crit = [i for i in res_mix["issues"] if i["severity"] == "CRITICAL"]
        self.assertEqual(len(mix_crit), 0)
        # Must honestly flag ASR unavailable
        self.assertIn("asr_unavailable_manual_review", {i["type"] for i in res_mix["issues"]})

    def test_05_visual_qc_real_winrt_ocr_extraction(self):
        preview_png = os.path.join(
            WORKSPACE_ROOT, "outputs", "block-puzzle-burst", "30-day-challenge",
            "day-04-shared-exports", "previews", "VERTICAL_1080_1920_preview.png"
        )
        ocr = self.visual_qc.run_ocr(preview_png)
        self.assertTrue(ocr["available"])
        self.assertIn("no wifi", ocr["full_text"].lower())
        self.assertIn("offline gameplay", ocr["full_text"].lower())
        self.assertGreater(len(ocr["lines"]), 0)

    def test_06_content_qc_brand_isolation_catches_cross_project_leak(self):
        bad_manifest = {
            "project": "block-puzzle-burst",
            "timeline": [{"scene_id": "s1", "asset_id": "VID_0DD488E3", "duration": 2.0, "overlays": [{"title": "Expand eziSales Order Booking Play Free"}]}],
            "audio": {"music": {"asset_id": "AUDIO_753DE70D"}},
        }
        res = self.content_qc.run(project_slug="block-puzzle-burst", manifest=bad_manifest)
        self.assertIn("incorrect_project_branding", {i["type"] for i in res["issues"]})

    def test_07_content_qc_flags_unsupported_marketing_claims(self):
        claim_manifest = {
            "project": "block-puzzle-burst",
            "timeline": [{"scene_id": "s1", "asset_id": "VID_0DD488E3", "duration": 2.0, "overlays": [{"title": "500% growth guaranteed Play Free"}]}],
            "audio": {"music": {"asset_id": "AUDIO_753DE70D"}},
        }
        res = self.content_qc.run(project_slug="block-puzzle-burst", manifest=claim_manifest)
        self.assertIn("unsupported_marketing_claim", {i["type"] for i in res["issues"]})

    def test_08_documentary_licensing_enforcement(self):
        # 1. UNKNOWN audio -> FAIL
        m_unk = {"timeline": [{"asset_id": "VID_0DD488E3"}], "audio": {"music": {"asset_id": "AUDIO_UNKNOWN_XYZ"}}}
        r_unk = self.content_qc.check_assets_and_licensing(m_unk)
        self.assertIn("restricted_or_unknown_audio_license", {i["type"] for i in r_unk["issues"]})

        # 2. NEEDS_REVIEW user MP3 -> REVIEW_REQUIRED
        m_rev = {"timeline": [{"asset_id": "VID_0DD488E3"}], "audio": {"music": {"asset_id": "AUDIO_C9B3EDFF"}}}
        r_rev = self.content_qc.check_assets_and_licensing(m_rev)
        self.assertIn("unverified_audio_licensing", {i["type"] for i in r_rev["issues"]})

        # 3. Cleared STUDIO_ORIGINAL -> PASS
        m_ok = {"timeline": [{"asset_id": "VID_0DD488E3"}], "audio": {"music": {"asset_id": "AUDIO_753DE70D"}}}
        r_ok = self.content_qc.check_assets_and_licensing(m_ok)
        self.assertEqual(len(r_ok["issues"]), 0)

    def test_09_shared_artifact_pack_qc_deduplicates_physical_scans(self):
        qc_json = os.path.join(
            WORKSPACE_ROOT, "outputs", "block-puzzle-burst", "30-day-challenge",
            "day-04-shared-exports", "qc", "qc_report.json"
        )
        self.assertTrue(os.path.exists(qc_json))
        with open(qc_json, "r", encoding="utf-8") as f:
            rep = json.load(f)
        # Must analyze only 2 physical MP4s while validating all 4 platforms independently!
        self.assertEqual(rep["unique_physical_artifacts_analyzed"], 2)
        self.assertEqual(rep["platforms_validated_independently"], 4)
        self.assertIsNotNone(rep["platform_summaries"]["facebook_reels"]["physical_analysis_reused_from"])
        self.assertIsNotNone(rep["platform_summaries"]["youtube_shorts"]["physical_analysis_reused_from"])

    def test_10_pilot_b_ezisales_catches_placeholder_and_unverified_claim(self):
        qc_json = os.path.join(
            WORKSPACE_ROOT, "outputs", "expand-ezisales", "quick-start-tutorials",
            "ezisales-tut-01-multiplatform-exports", "qc", "qc_report.json"
        )
        self.assertTrue(os.path.exists(qc_json))
        with open(qc_json, "r", encoding="utf-8") as f:
            rep = json.load(f)
        self.assertEqual(rep["overall_result"], QCStatus.FAIL.value)
        itypes = {i["type"] for i in rep["issues"]}
        self.assertIn("placeholder_or_non_erp_footage", itypes)
        self.assertIn("unsupported_marketing_claim", itypes)
        self.assertIn("missing_cta", itypes)

    def test_11_human_approval_gate_and_override_audit(self):
        # Create a FAIL job (missing input -> BLOCKED) and a REVIEW_REQUIRED job
        rep_blk = self.orch.run_master_qc(
            video_path=os.path.join(self.tmp_dir, "missing_gate.mp4"),
            project_slug="block-puzzle-burst",
            content_id="gate_blk",
            qc_dir=os.path.join(self.tmp_dir, "qc_gate_blk"),
        )
        jid = rep_blk["qc_job_id"]
        self.temp_job_ids.append(jid)

        # Standard APPROVE must be blocked by gatekeeper
        with self.assertRaises(PermissionError):
            self.orch.record_human_decision(jid, reviewer="Studio Director", decision="APPROVE", reason="Trying to bypass")

        # OVERRIDE_APPROVE with too-short reason must be rejected
        with self.assertRaises(ValueError):
            self.orch.record_human_decision(jid, reviewer="Studio Director", decision="OVERRIDE_APPROVE", reason="ok")

        # OVERRIDE_APPROVE with proper written justification succeeds and NEVER auto-publishes
        entry = self.orch.record_human_decision(
            jid,
            reviewer="Studio Director",
            decision="OVERRIDE_APPROVE",
            reason="Authorized test override verified during Phase 5 gatekeeper unit test.",
        )
        self.assertEqual(entry["new_workflow_state"], "READY_TO_PUBLISH")
        self.assertFalse(entry["auto_published"])
        self.assertTrue(os.path.exists(APPROVAL_AUDIT_LOG))

    def test_12_compare_reports(self):
        ra = os.path.join(
            WORKSPACE_ROOT, "outputs", "block-puzzle-burst", "30-day-challenge",
            "day-04-shared-exports", "qc", "qc_report.json"
        )
        rb = os.path.join(
            WORKSPACE_ROOT, "outputs", "block-puzzle-burst", "30-day-challenge",
            "day-04-no-wifi-revision", "qc", "qc_report.json"
        )
        diff = self.orch.compare_reports(ra, rb)
        self.assertIn("silent_audio_track", diff["resolved_issue_types"])
        self.assertEqual(diff["report_a"]["overall_result"], "FAIL")
        self.assertEqual(diff["report_b"]["overall_result"], "REVIEW_REQUIRED")

    def test_13_calibration_and_held_out_metrics_verified(self):
        calib_path = os.path.join(WORKSPACE_ROOT, "data", "qc_calibration_results.json")
        self.assertTrue(os.path.exists(calib_path))
        with open(calib_path, "r", encoding="utf-8") as f:
            c = json.load(f)
        self.assertEqual(c["dataset_size"], 22)
        self.assertEqual(c["metrics_held_out_split"]["critical_false_pass_rate"], 0.0)
        self.assertEqual(c["metrics_held_out_split"]["recall"], 1.0)
        self.assertEqual(c["metrics_ocr_only"]["recall"], 1.0)
        self.assertEqual(c["metrics_real_studio_only"]["precision"], 1.0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
