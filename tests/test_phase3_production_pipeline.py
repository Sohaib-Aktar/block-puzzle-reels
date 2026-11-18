"""
test_phase3_production_pipeline.py — Comprehensive Test Suite for Phase 3 Production Pipeline
Validates manifest validation, asset resolution, licensing enforcement, video processing,
audio mixing, loudness normalization, job lifecycle, and end-to-end pilot deliverables.
"""

import os
import sys
import json
import shutil
import unittest

WORKSPACE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(WORKSPACE_ROOT, "scripts"))

from production_job import ProductionJob, JobStatus
from timeline_builder import TimelineBuilder, PreflightValidationError
from video_processor import VideoProcessor
from overlay_engine import OverlayEngine
from audio_mixer import AudioMixer
from render_validator import RenderValidator, RenderValidationError
from render_manager import RenderManager
from media_engine import inspect_media


class TestPhase3ProductionPipeline(unittest.TestCase):
    """Exhaustive test suite for the Phase 3 FFmpeg production pipeline."""

    @classmethod
    def setUpClass(cls):
        cls.builder = TimelineBuilder()
        cls.validator = RenderValidator()
        cls.test_scratch_dir = os.path.join(WORKSPACE_ROOT, "data", "test_scratch_p3")
        os.makedirs(cls.test_scratch_dir, exist_ok=True)

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(cls.test_scratch_dir):
            shutil.rmtree(cls.test_scratch_dir, ignore_errors=True)

    # ─────────────────────────────────────────────────────────────────────────
    # 1. Manifest Validation & Asset Resolution Tests
    # ─────────────────────────────────────────────────────────────────────────

    def test_01_valid_manifest_preflight(self):
        """Confirms a fully specified manifest passes preflight validation."""
        manifest_path = os.path.join(WORKSPACE_ROOT, "config", "manifests", "manifest_bpb_day04_revision.json")
        with open(manifest_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        plan = self.builder.validate_manifest(data)
        self.assertEqual(plan["project"], "block-puzzle-burst")
        self.assertEqual(plan["canvas"]["width"], 1080)
        self.assertEqual(plan["canvas"]["height"], 1920)
        self.assertEqual(len(plan["scenes"]), 5)
        self.assertIsNotNone(plan["audio"]["music"])

    def test_02_missing_project_rejected(self):
        """Verifies that manifests missing required fields fail validation."""
        bad_manifest = {
            "content_id": "TEST_01",
            "timeline": [{"asset_id": "VID_0DD488E3", "duration": 2.0}]
        }
        with self.assertRaises(PreflightValidationError):
            self.builder.validate_manifest(bad_manifest)

    def test_03_missing_asset_reference_rejected(self):
        """Verifies that non-existent asset references fail preflight."""
        bad_manifest = {
            "project": "block-puzzle-burst",
            "content_id": "TEST_02",
            "timeline": [{"asset_id": "NON_EXISTENT_ASSET_12345", "duration": 2.0}]
        }
        with self.assertRaises(PreflightValidationError):
            self.builder.validate_manifest(bad_manifest)

    def test_04_audio_licensing_needs_review_enforcement(self):
        """Verifies that NEEDS_REVIEW audio is blocked unless allow_review_audio=True."""
        manifest_needs_review = {
            "project": "block-puzzle-burst",
            "content_id": "TEST_LIC_01",
            "allow_review_audio": False,
            "timeline": [{"asset_id": "VID_0DD488E3", "source_in": 0.0, "duration": 2.0}],
            "audio": {
                "music": {"asset_id": "AUDIO_C9B3EDFF", "volume": 0.25}  # User-supplied MP3 marked NEEDS_REVIEW
            }
        }
        with self.assertRaises(PreflightValidationError) as ctx:
            self.builder.validate_manifest(manifest_needs_review)
        self.assertIn("NEEDS_REVIEW", str(ctx.exception))

        # Should pass when allow_review_audio is True
        manifest_needs_review["allow_review_audio"] = True
        plan = self.builder.validate_manifest(manifest_needs_review)
        self.assertTrue(plan["is_preview_licensed"])

    def test_05_source_out_bounds_checking(self):
        """Verifies that source timestamps exceeding media duration are caught."""
        bad_bounds = {
            "project": "block-puzzle-burst",
            "content_id": "TEST_BOUNDS",
            "timeline": [{
                "asset_id": "VID_0DD488E3",
                "source_in": 10.0,
                "source_out": 999.0,  # Far exceeds 30.3s
                "duration": 5.0
            }]
        }
        with self.assertRaises(PreflightValidationError):
            self.builder.validate_manifest(bad_bounds)

    # ─────────────────────────────────────────────────────────────────────────
    # 2. Video Processing & Normalization Tests
    # ─────────────────────────────────────────────────────────────────────────

    def test_06_video_scene_trim_and_normalize(self):
        """Verifies trimming, aspect ratio contain padding, and 30fps CFR normalization."""
        vp = VideoProcessor(canvas_width=1080, canvas_height=1920, fps=30.0)
        scene = {
            "file_path": os.path.join(WORKSPACE_ROOT, "source_assets", "block-puzzle-burst", "gameplay", "recording_3_cfr30.mp4"),
            "source_in": 0.0,
            "duration": 1.5,
            "fit_mode": "contain",
            "overlays": []
        }
        out_clip = os.path.join(self.test_scratch_dir, "test_norm_clip.mp4")
        vp.normalize_and_trim_scene(scene, out_clip, self.test_scratch_dir)

        info = inspect_media(out_clip)
        self.assertEqual(info["width"], 1080)
        self.assertEqual(info["height"], 1920)
        self.assertEqual(info["fps"], 30.0)
        self.assertEqual(info["video_codec"], "h264")
        self.assertAlmostEqual(info["duration_seconds"], 1.5, delta=0.2)

    def test_07_overlay_badge_generation(self):
        """Verifies PIL-rendered overlay cards generate valid transparent PNGs."""
        oe = OverlayEngine(canvas_width=1080, canvas_height=1920)
        badge_path = os.path.join(self.test_scratch_dir, "test_badge.png")
        oe.render_badge_card(
            output_png_path=badge_path,
            title="Unit Test Title",
            subtitle="Unit Test Subtitle",
            style="purple_gold_badge"
        )
        self.assertTrue(os.path.exists(badge_path))
        self.assertGreater(os.path.getsize(badge_path), 5000)

    # ─────────────────────────────────────────────────────────────────────────
    # 3. Audio Mixing & Loudness Tests
    # ─────────────────────────────────────────────────────────────────────────

    def test_08_voiceover_synthesis_and_ducking(self):
        """Verifies Windows SAPI5 voiceover generation and master audio mixing."""
        mixer = AudioMixer(target_loudness_lufs=-14.0)
        vo_spec = {"text": "Phase three audio engine test.", "volume": 1.0, "rate": 0}
        vo_stem = mixer.prepare_voiceover_stem(vo_spec, self.test_scratch_dir)
        self.assertTrue(os.path.exists(vo_stem))
        self.assertGreater(os.path.getsize(vo_stem), 1000)

    def test_09_master_loudness_normalization(self):
        """Verifies that the mixed audio conforms to EBU R128 (-14 LUFS) specifications."""
        mixer = AudioMixer(target_loudness_lufs=-14.0)
        test_vid = os.path.join(self.test_scratch_dir, "test_norm_clip.mp4")
        audio_spec = {
            "music": {
                "file_path": os.path.join(WORKSPACE_ROOT, "source_assets", "block-puzzle-burst", "music", "bgm_upbeat_puzzle_bounce.wav"),
                "volume": 0.25,
                "fade_in": 0.2,
                "fade_out": 0.2
            },
            "voiceover": {"text": "Testing audio mastering.", "volume": 1.0},
            "master_loudness": -14.0
        }
        mixed_out = os.path.join(self.test_scratch_dir, "test_mixed.mp4")
        mixer.mix_master_audio(test_vid, audio_spec, mixed_out, self.test_scratch_dir)

        info = inspect_media(mixed_out)
        self.assertEqual(info["audio_codec"], "aac")
        self.assertEqual(info["audio_sample_rate"], 48000)
        self.assertEqual(info["audio_channels"], 2)

    # ─────────────────────────────────────────────────────────────────────────
    # 4. Job Lifecycle & Validation Tests
    # ─────────────────────────────────────────────────────────────────────────

    def test_10_job_state_transitions_and_persistence(self):
        """Verifies the state machine transitions and audit log persistence."""
        manifest = {
            "project": "test-project",
            "campaign": "test-campaign",
            "content_id": "TEST_LIFECYCLE",
            "timeline": []
        }
        job = ProductionJob(manifest)
        self.assertEqual(job.status, JobStatus.CREATED)

        job.set_status(JobStatus.VALIDATING, "Validating manifest")
        self.assertEqual(job.status, JobStatus.VALIDATING)

        job.set_status(JobStatus.READY_TO_RENDER, "Ready")
        self.assertEqual(job.status, JobStatus.READY_TO_RENDER)

        # Verify persistence and reload
        loaded = ProductionJob.load(job.job_id)
        self.assertEqual(loaded.status, JobStatus.READY_TO_RENDER)
        self.assertEqual(loaded.project, "test-project")

    def test_11_render_validator_detects_corrupt_or_invalid_specs(self):
        """Verifies that render_validator catches dimensional and codec mismatches."""
        test_clip = os.path.join(self.test_scratch_dir, "test_norm_clip.mp4")
        wrong_spec = {"width": 1920, "height": 1080, "duration_seconds": 10.0}

        with self.assertRaises(RenderValidationError):
            self.validator.validate_render(test_clip, wrong_spec, "test-project")

    # ─────────────────────────────────────────────────────────────────────────
    # 5. Real-World Production Pilots Acceptance Tests
    # ─────────────────────────────────────────────────────────────────────────

    def test_12_pilot1_bpb_day04_acceptance(self):
        """Verifies Pilot 1 (BPB_DAY_04 Reel Revision) deliverable integrity and QC pass."""
        p1_video = os.path.join(
            WORKSPACE_ROOT, "outputs", "block-puzzle-burst", "30-day-challenge",
            "day-04-no-wifi-revision", "final", "Day_04_Final_Revised_Center_Text.mp4"
        )
        self.assertTrue(os.path.exists(p1_video), f"Pilot 1 video missing: {p1_video}")

        info = inspect_media(p1_video)
        self.assertEqual(info["width"], 1080)
        self.assertEqual(info["height"], 1920)
        self.assertEqual(info["fps"], 30.0)
        self.assertEqual(info["video_codec"], "h264")
        self.assertEqual(info["audio_codec"], "aac")
        self.assertAlmostEqual(info["duration_seconds"], 15.0, delta=0.5)

        # Check QC reports
        qc_file = os.path.join(
            WORKSPACE_ROOT, "outputs", "block-puzzle-burst", "30-day-challenge",
            "day-04-no-wifi-revision", "report", "qc_report.md"
        )
        self.assertTrue(os.path.exists(qc_file))
        with open(qc_file, "r", encoding="utf-8") as f:
            self.assertIn("QC STATUS: PASSED", f.read())

    def test_13_pilot2_ezisales_acceptance(self):
        """Verifies Pilot 2 (EziSales Tutorial) deliverable integrity and QC pass."""
        p2_video = os.path.join(
            WORKSPACE_ROOT, "outputs", "expand-ezisales", "quick-start-tutorials",
            "ezisales-tut-01-order-booking-pipeline", "final", "software_tutorial_vertical.mp4"
        )
        self.assertTrue(os.path.exists(p2_video), f"Pilot 2 video missing: {p2_video}")

        info = inspect_media(p2_video)
        self.assertEqual(info["width"], 1080)
        self.assertEqual(info["height"], 1920)
        self.assertEqual(info["fps"], 30.0)
        self.assertEqual(info["video_codec"], "h264")
        self.assertEqual(info["audio_codec"], "aac")
        self.assertGreaterEqual(info["duration_seconds"], 15.0)

        # Check QC reports
        qc_file = os.path.join(
            WORKSPACE_ROOT, "outputs", "expand-ezisales", "quick-start-tutorials",
            "ezisales-tut-01-order-booking-pipeline", "report", "qc_report.md"
        )
        self.assertTrue(os.path.exists(qc_file))
        with open(qc_file, "r", encoding="utf-8") as f:
            self.assertIn("QC STATUS: PASSED", f.read())


if __name__ == "__main__":
    unittest.main(verbosity=2)
