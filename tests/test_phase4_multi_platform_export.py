"""
test_phase4_multi_platform_export.py — Comprehensive Phase 4 Multi-Platform Export Test Suite
Covers all 19 Phase 4 functional, reframing, safe-zone, validation, idempotency, retry,
and error-handling tests plus Pilot A and Pilot B acceptance verification.
(Phase 1, Phase 2, and Phase 3 regression suites are executed separately and verified.)
"""

import os
import sys
import json
import time
import shutil
import unittest
import tempfile

WORKSPACE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(WORKSPACE_ROOT, "scripts"))

from media_engine import get_ffmpeg_cmd, inspect_media
from reframing_engine import ReframingEngine, ReframeStrategy
from export_validator import ExportValidator
from export_preview_generator import ExportPreviewGenerator
from multi_platform_exporter import MultiPlatformExporter, EXPORT_JOBS_DIR


class TestPhase4MultiPlatformExport(unittest.TestCase):
    """Automated unit, integration, and acceptance tests for Phase 4."""

    @classmethod
    def setUpClass(cls):
        cls.exporter = MultiPlatformExporter()
        cls.reframer = ReframingEngine()
        cls.validator = ExportValidator()
        cls.previewer = ExportPreviewGenerator()

        cls.tmp_root = tempfile.mkdtemp(prefix="p4_test_")
        cls.fixture_clip = os.path.join(cls.tmp_root, "fixture_vertical_2s.mp4")

        # Create a fast 2-second authentic trimmed fixture from real Day 04 master for unit/integration tests
        real_master = os.path.join(
            WORKSPACE_ROOT, "outputs", "block-puzzle-burst", "30-day-challenge",
            "day-04-offline-proof", "final", "Day_04_Final_Revised_Center_Text.mp4"
        )
        import subprocess
        cmd = get_ffmpeg_cmd() + [
            "-y", "-v", "error",
            "-ss", "0", "-t", "2.0",
            "-i", real_master,
            "-c:v", "libx264", "-crf", "23", "-preset", "ultrafast",
            "-c:a", "aac", "-b:a", "128k", "-ar", "48000", "-ac", "2",
            cls.fixture_clip
        ]
        subprocess.run(cmd, check=True)
        cls.created_job_ids = []

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(cls.tmp_root):
            shutil.rmtree(cls.tmp_root, ignore_errors=True)
        # Clean up test job JSON files created during synthetic tests
        for jid in cls.created_job_ids:
            jpath = os.path.join(EXPORT_JOBS_DIR, f"{jid}.json")
            if os.path.exists(jpath):
                try:
                    os.remove(jpath)
                except OSError:
                    pass

    # 1. Platform profile loading
    def test_01_platform_profile_loading(self):
        profiles = {p["profile_id"]: p for p in self.exporter.list_profiles()}
        for required in ("instagram_reels", "youtube_shorts", "facebook_reels", "youtube_standard"):
            self.assertIn(required, profiles)
        self.assertEqual(profiles["instagram_reels"]["width"], 1080)
        self.assertEqual(profiles["instagram_reels"]["height"], 1920)
        self.assertEqual(profiles["youtube_standard"]["width"], 1920)
        self.assertEqual(profiles["youtube_standard"]["height"], 1080)

    # 2. Invalid profile handling
    def test_02_invalid_profile_handling(self):
        with self.assertRaises(ValueError):
            self.exporter.get_profile("nonexistent_platform_999")
        with self.assertRaises(ValueError):
            self.exporter.export_master(
                master_path=self.fixture_clip,
                profile_ids=["nonexistent_platform_999"],
                output_root=os.path.join(self.tmp_root, "bad_prof"),
            )

    # 3. Master input validation
    def test_03_master_input_validation(self):
        info = self.exporter.validate_master_input(self.fixture_clip)
        self.assertEqual(info["width"], 1080)
        self.assertEqual(info["height"], 1920)
        with self.assertRaises(FileNotFoundError):
            self.exporter.validate_master_input(os.path.join(self.tmp_root, "missing_video.mp4"))

    # 4. Manifest compatibility
    def test_04_manifest_compatibility(self):
        manifest_path = os.path.join(WORKSPACE_ROOT, "config", "manifests", "manifest_bpb_day04_revision.json")
        out_root = os.path.join(self.tmp_root, "manifest_compat")
        summary = self.exporter.export_master(
            master_path=self.fixture_clip,
            profile_ids=["instagram_reels"],
            manifest_path=manifest_path,
            output_root=out_root,
            generate_previews=False,
        )
        self.created_job_ids.append(summary["export_job_id"])
        self.assertEqual(summary["project"], "block-puzzle-burst")
        self.assertEqual(summary["campaign"], "30-day-challenge")
        self.assertTrue(os.path.exists(os.path.join(out_root, "master", "production_manifest.json")))

    # 5. 9:16 export
    def test_05_vertical_9x16_export(self):
        out_root = os.path.join(self.tmp_root, "exp_9x16")
        summary = self.exporter.export_master(
            master_path=self.fixture_clip,
            profile_ids=["instagram_reels"],
            project_slug="block-puzzle-burst",
            content_id="test_9x16",
            output_root=out_root,
            generate_previews=True,
        )
        self.created_job_ids.append(summary["export_job_id"])
        self.assertEqual(summary["status"], "COMPLETED_VALIDATED")
        res = summary["results"]["instagram_reels"]
        self.assertEqual(res["validation"]["media_info"]["width"], 1080)
        self.assertEqual(res["validation"]["media_info"]["height"], 1920)

    # 6. 16:9 export
    def test_06_horizontal_16x9_export(self):
        out_root = os.path.join(self.tmp_root, "exp_16x9")
        summary = self.exporter.export_master(
            master_path=self.fixture_clip,
            profile_ids=["youtube_standard"],
            project_slug="block-puzzle-burst",
            content_id="test_16x9",
            output_root=out_root,
            generate_previews=True,
        )
        self.created_job_ids.append(summary["export_job_id"])
        self.assertEqual(summary["status"], "COMPLETED_VALIDATED")
        res = summary["results"]["youtube_standard"]
        self.assertEqual(res["reframe_plan"]["strategy"], ReframeStrategy.BLURRED_BACKGROUND.value)
        self.assertEqual(res["validation"]["media_info"]["width"], 1920)
        self.assertEqual(res["validation"]["media_info"]["height"], 1080)
        self.assertEqual(res["reframe_plan"]["crop_loss_percent"], 0.0)

    # 7. Smart reframing
    def test_07_smart_reframing(self):
        plan = self.reframer.build_filter_plan(
            video_path=self.fixture_clip,
            src_width=1080,
            src_height=1920,
            target_width=1920,
            target_height=1080,
            target_fps=30.0,
            project_slug="block-puzzle-burst",
            strategy="SMART_CROP",
        )
        self.assertEqual(plan["strategy"], "SMART_CROP")
        self.assertIsNotNone(plan["content_analysis"])
        # Aggressive 9:16 -> 16:9 crop must automatically flag for manual review
        self.assertTrue(plan["requires_manual_review"])
        self.assertGreater(plan["crop_loss_percent"], 15.0)

    # 8. Manual focal-point configuration
    def test_08_manual_focal_point_configuration(self):
        out_root = os.path.join(self.tmp_root, "exp_focal")
        summary = self.exporter.export_master(
            master_path=self.fixture_clip,
            profile_ids=["youtube_standard"],
            project_slug="block-puzzle-burst",
            content_id="test_focal",
            output_root=out_root,
            reframe_strategy="MANUAL_FOCAL_POINT",
            focal_point=(0.5, 0.35),
            generate_previews=False,
        )
        self.created_job_ids.append(summary["export_job_id"])
        res = summary["results"]["youtube_standard"]
        self.assertEqual(res["status"], "VALIDATED")
        self.assertEqual(res["reframe_plan"]["focal_point"], [0.5, 0.35])
        self.assertTrue(res["requires_manual_review"])

    # 9. Safe-zone configuration & preview generation
    def test_09_safe_zone_configuration_and_preview(self):
        sz_profiles = self.exporter.safe_zones_cfg.get("profiles", {})
        for pid in ("instagram_reels", "youtube_shorts", "facebook_reels", "youtube_standard"):
            self.assertIn(pid, sz_profiles)
            self.assertEqual(sz_profiles[pid]["status"], "PROVISIONAL")
            self.assertIn("safe_content_box", sz_profiles[pid])
            self.assertIn("ui_occlusion_zones", sz_profiles[pid])

        frame_png = os.path.join(self.tmp_root, "sz_frame.png")
        sz_png = os.path.join(self.tmp_root, "sz_overlay.png")
        self.previewer.extract_frame(self.fixture_clip, frame_png, timestamp_sec=0.5)
        self.previewer.generate_safe_zone_overlay(frame_png, "instagram_reels", sz_png)
        self.assertTrue(os.path.exists(sz_png))
        self.assertGreater(os.path.getsize(sz_png), 10000)

    # 10. Text & logo preservation (non-destructive 0% crop loss)
    def test_10_text_and_logo_preservation(self):
        # Gameplay 9:16 -> 16:9 uses BLURRED_BACKGROUND (0% crop loss)
        p_game = self.reframer.build_filter_plan(
            self.fixture_clip, 1080, 1920, 1920, 1080, 30.0, project_slug="block-puzzle-burst"
        )
        self.assertEqual(p_game["crop_loss_percent"], 0.0)
        # ERP 9:16 -> 16:9 uses FIT_WITH_BACKGROUND (0% crop loss)
        p_erp = self.reframer.build_filter_plan(
            self.fixture_clip, 1080, 1920, 1920, 1080, 30.0, project_slug="expand-ezisales"
        )
        self.assertEqual(p_erp["strategy"], "FIT_WITH_BACKGROUND")
        self.assertEqual(p_erp["crop_loss_percent"], 0.0)

    # 11. Audio preservation and synchronization
    def test_11_audio_preservation_and_sync(self):
        out_root = os.path.join(self.tmp_root, "exp_audio")
        summary = self.exporter.export_master(
            master_path=self.fixture_clip,
            profile_ids=["youtube_shorts"],
            content_id="test_audio",
            output_root=out_root,
            generate_previews=False,
        )
        self.created_job_ids.append(summary["export_job_id"])
        val = summary["results"]["youtube_shorts"]["validation"]
        self.assertTrue(val["passed"])
        check_map = {c["name"]: c["status"] for c in val["checks"]}
        self.assertEqual(check_map["audio_stream_present"], "PASS")
        self.assertEqual(check_map["audio_sample_rate_and_channels"], "PASS")
        self.assertEqual(check_map["audio_video_sync"], "PASS")
        self.assertEqual(check_map["no_audio_clipping"], "PASS")

    # 12. Output naming and directory structure
    def test_12_output_naming_and_directory_structure(self):
        out_root = os.path.join(self.tmp_root, "exp_struct")
        summary = self.exporter.export_master(
            master_path=self.fixture_clip,
            profile_ids=["facebook_reels", "youtube_standard"],
            content_id="struct_cid",
            output_root=out_root,
            generate_previews=True,
        )
        self.created_job_ids.append(summary["export_job_id"])
        self.assertTrue(os.path.exists(os.path.join(out_root, "master", "master_reference.json")))
        self.assertTrue(os.path.exists(os.path.join(out_root, "artifacts", "VERTICAL_1080_1920", "struct_cid_VERTICAL_1080_1920.mp4")))
        self.assertTrue(os.path.exists(os.path.join(out_root, "artifacts", "HORIZONTAL_1920_1080", "struct_cid_HORIZONTAL_1920_1080.mp4")))
        self.assertTrue(os.path.exists(os.path.join(out_root, "platform_exports", "facebook_reels", "delivery_record.json")))
        self.assertTrue(os.path.exists(os.path.join(out_root, "platform_exports", "youtube_standard", "delivery_record.json")))
        self.assertTrue(os.path.exists(os.path.join(out_root, "previews", "multi_platform_contact_sheet.png")))
        self.assertTrue(os.path.exists(os.path.join(out_root, "previews", "reframing_comparison_9x16_vs_16x9.png")))
        self.assertTrue(os.path.exists(os.path.join(out_root, "reports", "export_summary.json")))
        self.assertTrue(os.path.exists(os.path.join(out_root, "reports", "platform_validation.json")))
        self.assertTrue(os.path.exists(os.path.join(out_root, "reports", "technical_comparison.json")))

    # 13 & 15. Duplicate export detection & Idempotency
    def test_13_duplicate_detection_and_idempotency(self):
        out_root = os.path.join(self.tmp_root, "exp_idem")
        s1 = self.exporter.export_master(
            master_path=self.fixture_clip,
            profile_ids=["instagram_reels"],
            content_id="idem_cid",
            output_root=out_root,
            generate_previews=False,
        )
        self.created_job_ids.append(s1["export_job_id"])
        out_file = s1["results"]["instagram_reels"]["output_path"]
        mtime_1 = os.path.getmtime(out_file)

        # Second identical call must reuse existing validated export without re-encoding
        s2 = self.exporter.export_master(
            master_path=self.fixture_clip,
            profile_ids=["instagram_reels"],
            content_id="idem_cid",
            output_root=out_root,
            generate_previews=False,
        )
        self.created_job_ids.append(s2["export_job_id"])
        self.assertEqual(s2["results"]["instagram_reels"]["status"], "REUSED_VALID")
        self.assertEqual(os.path.getmtime(out_file), mtime_1)

    # 14. Retry after export failure
    def test_14_retry_after_export_failure(self):
        out_root = os.path.join(self.tmp_root, "exp_retry")
        s1 = self.exporter.export_master(
            master_path=self.fixture_clip,
            profile_ids=["instagram_reels"],
            content_id="retry_cid",
            output_root=out_root,
            generate_previews=False,
        )
        jid = s1["export_job_id"]
        self.created_job_ids.append(jid)
        ig_path = s1["results"]["instagram_reels"]["output_path"]
        ig_mtime = os.path.getmtime(ig_path)

        # Simulate a second profile (16:9 youtube_standard) failing in the persisted job record
        job_file = os.path.join(EXPORT_JOBS_DIR, f"{jid}.json")
        with open(job_file, "r", encoding="utf-8") as f:
            jdata = json.load(f)
        jdata["status"] = "PARTIAL_FAILURE"
        jdata["failed_profiles"] = ["youtube_standard"]
        jdata["results"]["youtube_standard"] = {"profile_id": "youtube_standard", "status": "FAILED", "output_path": None, "error": "Simulated failure"}
        with open(job_file, "w", encoding="utf-8") as f:
            json.dump(jdata, f, indent=2)

        # Retry only failed profile
        retried = self.exporter.retry_failed(jid)
        self.assertEqual(retried["status"], "COMPLETED_VALIDATED")
        self.assertEqual(retried["results"]["youtube_standard"]["status"], "VALIDATED")
        # Already completed instagram_reels physical artifact must remain untouched
        self.assertEqual(os.path.getmtime(ig_path), ig_mtime)

    # 16. Existing output protection
    def test_16_existing_output_protection(self):
        out_root = os.path.join(self.tmp_root, "exp_protect")
        art_dir = os.path.join(out_root, "artifacts", "VERTICAL_1080_1920")
        os.makedirs(art_dir, exist_ok=True)
        existing_file = os.path.join(art_dir, "protect_cid_VERTICAL_1080_1920.mp4")
        with open(existing_file, "wb") as f:
            f.write(b"PRE_EXISTING_PROTECTED_BYTES")

        # Without --force, must NEVER overwrite existing file; must create _v2.mp4
        summary = self.exporter.export_master(
            master_path=self.fixture_clip,
            profile_ids=["instagram_reels"],
            content_id="protect_cid",
            output_root=out_root,
            force=False,
            generate_previews=False,
        )
        self.created_job_ids.append(summary["export_job_id"])
        with open(existing_file, "rb") as f:
            self.assertEqual(f.read(), b"PRE_EXISTING_PROTECTED_BYTES")
        new_out = summary["results"]["instagram_reels"]["output_path"]
        self.assertTrue(new_out.endswith("_v2.mp4"))
        self.assertTrue(os.path.exists(new_out))

    # 17 & 18. FFprobe and full decode validation
    def test_17_ffprobe_and_full_decode_validation(self):
        val = self.validator.validate_export(
            export_path=self.fixture_clip,
            profile_spec=self.exporter.get_profile("instagram_reels"),
        )
        check_map = {c["name"]: c["status"] for c in val["checks"]}
        self.assertEqual(check_map["ffprobe_readable"], "PASS")
        self.assertEqual(check_map["full_video_decode"], "PASS")
        self.assertEqual(len(val["checks"]), 18)

    # 19. Corrupt input handling
    def test_19_corrupt_input_handling(self):
        corrupt_path = os.path.join(self.tmp_root, "corrupt_video.mp4")
        with open(corrupt_path, "wb") as f:
            f.write(b"NOT_A_VALID_MP4_HEADER_CORRUPT_PAYLOAD_1234567890")

        with self.assertRaises(ValueError):
            self.exporter.validate_master_input(corrupt_path)

        val = self.validator.validate_export(
            export_path=corrupt_path,
            profile_spec=self.exporter.get_profile("instagram_reels"),
        )
        self.assertFalse(val["passed"])

    # 20. Real-world Pilot A (Block Puzzle Burst Day 04) 4-profile verification
    def test_20_pilot_a_bpb_day04_all_four_profiles(self):
        pilot_root = os.path.join(
            WORKSPACE_ROOT, "outputs", "block-puzzle-burst", "30-day-challenge", "day-04-multiplatform-exports"
        )
        summary_path = os.path.join(pilot_root, "reports", "export_summary.json")
        self.assertTrue(os.path.exists(summary_path), "Pilot A export_summary.json missing")
        with open(summary_path, "r", encoding="utf-8") as f:
            summary = json.load(f)
        self.assertEqual(summary["status"], "COMPLETED_VALIDATED")
        for pid in ("instagram_reels", "youtube_shorts", "facebook_reels", "youtube_standard"):
            r = summary["results"][pid]
            self.assertIn(r["status"], ("VALIDATED", "REUSED_VALID"))
            self.assertEqual(r["validation"]["passed_count"], 18)
            self.assertTrue(os.path.exists(r["output_path"]))

    # 21. Real-world Pilot B (Expand EziSales) 4-profile verification
    def test_21_pilot_b_ezisales_all_four_profiles(self):
        pilot_root = os.path.join(
            WORKSPACE_ROOT, "outputs", "expand-ezisales", "quick-start-tutorials", "ezisales-tut-01-multiplatform-exports"
        )
        summary_path = os.path.join(pilot_root, "reports", "export_summary.json")
        self.assertTrue(os.path.exists(summary_path), "Pilot B export_summary.json missing")
        with open(summary_path, "r", encoding="utf-8") as f:
            summary = json.load(f)
        self.assertEqual(summary["status"], "COMPLETED_VALIDATED")
        for pid in ("instagram_reels", "youtube_shorts", "facebook_reels", "youtube_standard"):
            r = summary["results"][pid]
            self.assertIn(r["status"], ("VALIDATED", "REUSED_VALID"))
            self.assertEqual(r["validation"]["passed_count"], 18)
            self.assertTrue(os.path.exists(r["output_path"]))

    # 22. Instagram & Facebook share one physical MP4 with independent platform records & validation
    def test_22_shared_artifact_instagram_facebook_and_independent_validation(self):
        out_root = os.path.join(self.tmp_root, "exp_ig_fb_shared")
        summary = self.exporter.export_master(
            master_path=self.fixture_clip,
            profile_ids=["instagram_reels", "facebook_reels"],
            project_slug="block-puzzle-burst",
            content_id="shared_ig_fb",
            output_root=out_root,
            generate_previews=True,
        )
        self.created_job_ids.append(summary["export_job_id"])
        self.assertEqual(summary["status"], "COMPLETED_VALIDATED")

        ig = summary["results"]["instagram_reels"]
        fb = summary["results"]["facebook_reels"]

        # Must reference the exact same physical MP4 file
        self.assertEqual(ig["artifact_path"], fb["artifact_path"])
        self.assertEqual(ig["artifact_fingerprint"], fb["artifact_fingerprint"])
        self.assertTrue(ig["shared_artifact"])
        self.assertTrue(fb["shared_artifact"])
        self.assertEqual(summary["storage_summary"]["unique_physical_artifacts"], 1)
        self.assertGreater(summary["storage_summary"]["bytes_saved"], 0)

        # Independent delivery records and safe-zone previews must exist for each platform
        self.assertNotEqual(ig["delivery_record_path"], fb["delivery_record_path"])
        self.assertTrue(os.path.exists(ig["delivery_record_path"]))
        self.assertTrue(os.path.exists(fb["delivery_record_path"]))
        with open(ig["delivery_record_path"], "r", encoding="utf-8") as f:
            ig_rec = json.load(f)
        with open(fb["delivery_record_path"], "r", encoding="utf-8") as f:
            fb_rec = json.load(f)
        self.assertEqual(ig_rec["safe_zone_validation"]["safe_zone_profile"], "instagram_reels")
        self.assertEqual(fb_rec["safe_zone_validation"]["safe_zone_profile"], "facebook_reels")
        self.assertNotEqual(
            ig_rec["safe_zone_validation"]["safe_zone_preview_path"],
            fb_rec["safe_zone_validation"]["safe_zone_preview_path"],
        )
        self.assertEqual(ig["validation"]["passed_count"], 18)
        self.assertEqual(fb["validation"]["passed_count"], 18)

    # 23. YouTube Shorts reuses shared vertical when compatible, and renders separately when render profile differs
    def test_23_youtube_shorts_reuse_and_divergence(self):
        # Case A: Compatible (all 3 map to VERTICAL_1080_1920) -> 1 unique physical MP4
        out_compat = os.path.join(self.tmp_root, "exp_yts_compat")
        s_compat = self.exporter.export_master(
            master_path=self.fixture_clip,
            profile_ids=["instagram_reels", "facebook_reels", "youtube_shorts"],
            content_id="yts_compat",
            output_root=out_compat,
            generate_previews=False,
        )
        self.created_job_ids.append(s_compat["export_job_id"])
        self.assertEqual(s_compat["storage_summary"]["unique_physical_artifacts"], 1)
        self.assertEqual(
            s_compat["results"]["instagram_reels"]["artifact_path"],
            s_compat["results"]["youtube_shorts"]["artifact_path"],
        )

        # Case B: Divergent render profile override for YouTube Shorts (VERTICAL_1080_1920_HQ)
        # Same 1080x1920 resolution, different CRF/bitrate -> MUST produce separate physical MP4!
        out_div = os.path.join(self.tmp_root, "exp_yts_div")
        s_div = self.exporter.export_master(
            master_path=self.fixture_clip,
            profile_ids=["instagram_reels", "youtube_shorts"],
            content_id="yts_div",
            output_root=out_div,
            profile_render_overrides={"youtube_shorts": "VERTICAL_1080_1920_HQ"},
            generate_previews=False,
        )
        self.created_job_ids.append(s_div["export_job_id"])
        self.assertEqual(s_div["storage_summary"]["unique_physical_artifacts"], 2)
        self.assertNotEqual(
            s_div["results"]["instagram_reels"]["artifact_fingerprint"],
            s_div["results"]["youtube_shorts"]["artifact_fingerprint"],
        )
        self.assertNotEqual(
            s_div["results"]["instagram_reels"]["artifact_path"],
            s_div["results"]["youtube_shorts"]["artifact_path"],
        )

    # 24. All 4 platforms -> exactly 2 physical MP4s (shared 9:16 + separate 16:9) & real Pilot A shared check
    def test_24_separate_16x9_and_real_shared_pilot_savings(self):
        shared_root = os.path.join(
            WORKSPACE_ROOT, "outputs", "block-puzzle-burst", "30-day-challenge", "day-04-shared-exports"
        )
        summary_path = os.path.join(shared_root, "reports", "export_summary.json")
        self.assertTrue(os.path.exists(summary_path))
        with open(summary_path, "r", encoding="utf-8") as f:
            summary = json.load(f)
        self.assertEqual(summary["status"], "COMPLETED_VALIDATED")
        ss = summary["storage_summary"]
        self.assertEqual(ss["total_platform_destinations"], 4)
        self.assertEqual(ss["unique_physical_artifacts"], 2)
        self.assertGreater(ss["bytes_saved"], 3_000_000)
        self.assertGreater(ss["percent_saved"], 45.0)
        self.assertNotEqual(
            summary["results"]["instagram_reels"]["artifact_path"],
            summary["results"]["youtube_standard"]["artifact_path"],
        )

    # 25. Fingerprint detects manifest overlay/audio differences even with identical resolution
    def test_25_fingerprint_sensitivity_to_overlays_and_audio(self):
        from multi_platform_exporter import _compute_artifact_fingerprint
        rp = self.exporter.get_render_profile("VERTICAL_1080_1920")
        reframe = {"strategy": "FIT_WITH_BACKGROUND", "focal_point": [0.5, 0.5], "background_color": "0x070B14"}

        m1 = {"timeline": [{"scene_id": "s1", "asset_id": "VID_1", "overlays": [{"title": "Hook A"}]}], "audio": {"music": {"asset_id": "AUD_1"}}}
        m2 = {"timeline": [{"scene_id": "s1", "asset_id": "VID_1", "overlays": [{"title": "Hook B"}]}], "audio": {"music": {"asset_id": "AUD_1"}}}

        fp1 = _compute_artifact_fingerprint("abc123", rp, reframe, "mh1", m1)
        fp2 = _compute_artifact_fingerprint("abc123", rp, reframe, "mh2", m2)
        self.assertNotEqual(fp1["artifact_fingerprint"], fp2["artifact_fingerprint"])

    # 26. Read-only duplicate storage audit runs cleanly without deleting files
    def test_26_read_only_duplicate_storage_audit(self):
        from audit_export_duplicates import run_duplicate_audit
        rep = run_duplicate_audit()
        self.assertIn("byte_identical_mp4_groups", rep)
        self.assertIn("safe_consolidation_recommendations", rep)
        for rec in rep["safe_consolidation_recommendations"]:
            self.assertEqual(rec["action"], "DO_NOT_DELETE_WITHOUT_APPROVAL")
            self.assertTrue(os.path.exists(os.path.join(WORKSPACE_ROOT, rec["candidate_for_removal"])))


if __name__ == "__main__":
    unittest.main(verbosity=2)
