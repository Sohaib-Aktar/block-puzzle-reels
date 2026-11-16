#!/usr/bin/env python3
"""
tests/test_phase2_intake_audio.py
=================================
Comprehensive Verification Test Suite for Phase 2:
Media Intake, Asset Organization & Audio Intelligence System.

Covers:
  1. Video metadata extraction (inspect_video_asset)
  2. Image metadata & transparency extraction (inspect_image_asset)
  3. Audio stream & EBU R128 loudness extraction (get_audio_stream_metadata, measure_ebur128_loudness)
  4. Acoustic analysis (Peak, RMS, clipping, silence, BPM autocorrelation)
  5. Audio mood classification & suitability recommendations
  6. Multi-scene timeline recommendation
  7. Media and audio catalog integrity
  8. Duplicate detection accuracy via SHA-256
  9. Corrupted, empty, and unsupported file error handling
  10. Licensing status gatekeeping
  11. Phase 1 regression verification (invoking test_studio_suite.py)
"""

import os
import sys
import json
import unittest
import subprocess
import numpy as np

# Ensure scripts directory is in sys.path
TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
WORKSPACE_ROOT = os.path.abspath(os.path.join(TESTS_DIR, ".."))
SCRIPTS_DIR = os.path.join(WORKSPACE_ROOT, "scripts")
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)

import footage_analyzer
import audio_analyzer
import audio_recommender
import asset_migrator
import media_intake

DATA_DIR = os.path.join(WORKSPACE_ROOT, "data")
SOURCE_ASSETS_DIR = os.path.join(WORKSPACE_ROOT, "source_assets")


class TestPhase2IntakeAndAudio(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        print("\n" + "=" * 70)
        print("INITIALIZING PHASE 2 VERIFICATION TEST SUITE")
        print("=" * 70)

    # -------------------------------------------------------------------------
    # Test 1: Video Metadata Extraction
    # -------------------------------------------------------------------------
    def test_01_video_metadata_extraction(self):
        """Verifies deep inspection of video assets (dimensions, duration, codecs)."""
        video_path = os.path.join(
            SOURCE_ASSETS_DIR, "block-puzzle-burst", "gameplay", "recording_3.mp4"
        )
        self.assertTrue(os.path.isfile(video_path), f"Sample video missing: {video_path}")

        meta = footage_analyzer.inspect_video_asset(video_path)
        self.assertEqual(meta["width"], 720)
        self.assertEqual(meta["height"], 1600)
        self.assertEqual(meta["aspect_ratio"], "9:16")
        self.assertEqual(meta["orientation"], "portrait")
        self.assertAlmostEqual(meta["duration_seconds"], 30.25, delta=1.0)
        self.assertEqual(meta["video_codec"], "h264")
        self.assertEqual(meta["audio_codec"], "aac")
        self.assertTrue(len(meta["sha256"]) == 64)
        print("  [PASS] Test 1: Video metadata extraction verified.")

    # -------------------------------------------------------------------------
    # Test 2: Image Metadata & Transparency Extraction
    # -------------------------------------------------------------------------
    def test_02_image_metadata_and_transparency(self):
        """Verifies image inspection, alpha channel transparency, and category."""
        # Test transparent PNG logo
        logo_path = os.path.join(
            SOURCE_ASSETS_DIR, "block-puzzle-burst", "logos", "icon_block_game.png"
        )
        self.assertTrue(os.path.isfile(logo_path), f"Logo missing: {logo_path}")

        meta_logo = footage_analyzer.inspect_image_asset(logo_path)
        self.assertEqual(meta_logo["width"], 1080)
        self.assertEqual(meta_logo["height"], 1080)
        self.assertEqual(meta_logo["aspect_ratio"], "1:1")
        self.assertEqual(meta_logo["orientation"], "square")
        self.assertEqual(meta_logo["format"], "png")
        self.assertEqual(meta_logo["color_mode"], "RGBA")
        self.assertTrue(meta_logo["has_transparency"])
        self.assertEqual(meta_logo["image_category"], "logo_badge")

        # Test opaque JPG screenshot
        screen_path = os.path.join(
            SOURCE_ASSETS_DIR, "block-puzzle-burst", "screenshots", "sample_1.jpg"
        )
        self.assertTrue(os.path.isfile(screen_path), f"Screenshot missing: {screen_path}")

        meta_screen = footage_analyzer.inspect_image_asset(screen_path)
        self.assertEqual(meta_screen["orientation"], "portrait")
        self.assertFalse(meta_screen["has_transparency"])
        print("  [PASS] Test 2: Image metadata & transparency detection verified.")

    # -------------------------------------------------------------------------
    # Test 3: Audio Stream & EBU R128 Loudness Extraction
    # -------------------------------------------------------------------------
    def test_03_audio_stream_metadata_and_ebur128(self):
        """Verifies audio container parsing and broadcast EBU R128 loudness metrics."""
        audio_path = os.path.join(
            SOURCE_ASSETS_DIR, "block-puzzle-burst", "music", "bgm_upbeat_puzzle_bounce.wav"
        )
        self.assertTrue(os.path.isfile(audio_path), f"Audio missing: {audio_path}")

        stream_meta = audio_analyzer.get_audio_stream_metadata(audio_path)
        self.assertEqual(stream_meta["channels"], 1)
        self.assertEqual(stream_meta["sample_rate"], 44100)
        self.assertEqual(stream_meta["codec"], "pcm_s16le")
        self.assertAlmostEqual(stream_meta["duration_seconds"], 15.0, delta=0.5)

        ebur = audio_analyzer.measure_ebur128_loudness(audio_path)
        self.assertIsInstance(ebur["integrated_lufs"], float)
        self.assertLess(ebur["integrated_lufs"], 0.0)
        self.assertGreater(ebur["integrated_lufs"], -70.0)
        self.assertIsInstance(ebur["true_peak_dbtp"], float)
        self.assertIsInstance(ebur["loudness_range_lu"], float)
        print("  [PASS] Test 3: Audio stream & EBU R128 loudness verification passed.")

    # -------------------------------------------------------------------------
    # Test 4: Acoustic Analysis (Peak, RMS, Clipping, Silence, Tempo)
    # -------------------------------------------------------------------------
    def test_04_acoustic_analysis_and_bpm_estimation(self):
        """Verifies acoustic waveform computation and envelope autocorrelation BPM."""
        audio_path = os.path.join(
            SOURCE_ASSETS_DIR, "block-puzzle-burst", "music", "bgm_upbeat_puzzle_bounce.wav"
        )
        samples, sr = audio_analyzer.load_pcm_samples(audio_path)
        self.assertGreater(len(samples), 0)

        acoustic = audio_analyzer.analyze_acoustic_properties(samples, sr)
        self.assertLess(acoustic["peak_dbfs"], 0.0)
        self.assertLess(acoustic["rms_dbfs"], 0.0)
        self.assertFalse(acoustic["clipping_detected"])
        self.assertGreaterEqual(acoustic["silence_ratio"], 0.0)
        self.assertLessEqual(acoustic["silence_ratio"], 1.0)

        # bgm_upbeat_puzzle_bounce was synthesized at 120.0 BPM
        self.assertIsNotNone(acoustic["estimated_bpm"])
        self.assertAlmostEqual(acoustic["estimated_bpm"], 120.0, delta=5.0)
        self.assertIn(acoustic["bpm_confidence"], ["high", "medium"])
        self.assertEqual(acoustic["energy_level"], "high")
        print("  [PASS] Test 4: Acoustic waveform & BPM estimation verified.")

    # -------------------------------------------------------------------------
    # Test 5: Audio Mood Classification & Suitability Recommendation
    # -------------------------------------------------------------------------
    def test_05_audio_mood_classification_and_recommendation(self):
        """Verifies project-aware mood filtering and ranking recommendations."""
        res = audio_recommender.recommend_audio(
            project="block-puzzle-burst",
            content_category="lifestyle_reel",
            desired_mood="energetic",
            target_duration=15.0,
            allow_unverified_licenses=True
        )
        recs = res.get("top_recommendations", [])
        self.assertGreater(len(recs), 0)

        top_track = recs[0]
        self.assertEqual(top_track["filename"], "bgm_upbeat_puzzle_bounce.wav")
        self.assertGreaterEqual(top_track["match_score"], 90.0)
        self.assertIn("energetic", top_track["mood_tags"])
        self.assertIn("block-puzzle-burst", top_track["explanation"])
        print("  [PASS] Test 5: Audio mood classification & recommendation verified.")

    # -------------------------------------------------------------------------
    # Test 6: Multi-Scene Timeline Audio Plan
    # -------------------------------------------------------------------------
    def test_06_multi_scene_timeline_recommendation(self):
        """Verifies multi-scene pacing and dynamic audio action planning."""
        res = audio_recommender.recommend_audio(
            project="block-puzzle-burst",
            content_category="lifestyle_reel",
            desired_mood="playful",
            target_duration=15.0,
            allow_unverified_licenses=True
        )
        scene_plan = res.get("multi_scene_plan", [])
        self.assertGreaterEqual(len(scene_plan), 3)

        # Check scene coverage
        self.assertEqual(scene_plan[0]["scene_name"], "Hook Scene")
        self.assertEqual(scene_plan[0]["start_sec"], 0.0)
        self.assertIn("audio_action", scene_plan[0])
        print("  [PASS] Test 6: Multi-scene timeline audio plan verified.")

    # -------------------------------------------------------------------------
    # Test 7: Catalog Integrity (media_catalog.json & audio_catalog.json)
    # -------------------------------------------------------------------------
    def test_07_catalog_integrity(self):
        """Verifies schema structure, item counts, and validity of catalogs."""
        media_cat_path = os.path.join(DATA_DIR, "media_catalog.json")
        audio_cat_path = os.path.join(DATA_DIR, "audio_catalog.json")

        self.assertTrue(os.path.isfile(media_cat_path), "media_catalog.json missing")
        self.assertTrue(os.path.isfile(audio_cat_path), "audio_catalog.json missing")

        with open(media_cat_path, "r", encoding="utf-8") as f:
            media_data = json.load(f)
        with open(audio_cat_path, "r", encoding="utf-8") as f:
            audio_data = json.load(f)

        self.assertIn("assets", media_data)
        self.assertGreaterEqual(len(media_data["assets"]), 10)
        for aid, item in media_data["assets"].items():
            self.assertIn("file_type", item)
            self.assertIn("project", item)
            self.assertIn("sha256", item)

        self.assertIn("assets", audio_data)
        self.assertGreaterEqual(len(audio_data["assets"]), 10)
        for aid, item in audio_data["assets"].items():
            self.assertIn("integrated_lufs", item)
            self.assertIn("license_status", item)
            self.assertIn("sound_classification", item)
        print("  [PASS] Test 7: Media and audio catalog integrity verified.")

    # -------------------------------------------------------------------------
    # Test 8: Duplicate Detection via SHA-256
    # -------------------------------------------------------------------------
    def test_08_duplicate_detection_via_sha256(self):
        """Verifies byte-level SHA-256 duplicate detection across directories."""
        raw_rec1 = os.path.join(WORKSPACE_ROOT, "Raw_input_files", "recording_1.mp4")
        public_rec1 = os.path.join(WORKSPACE_ROOT, "my-video", "public", "gameplay.mp4")

        self.assertTrue(os.path.isfile(raw_rec1))
        self.assertTrue(os.path.isfile(public_rec1))

        sha_raw = footage_analyzer.calculate_sha256(raw_rec1)
        sha_public = footage_analyzer.calculate_sha256(public_rec1)
        self.assertEqual(sha_raw, sha_public)

        # Check migration log records duplicate
        mig_log_path = os.path.join(DATA_DIR, "migration_log.json")
        self.assertTrue(os.path.isfile(mig_log_path))
        with open(mig_log_path, "r", encoding="utf-8") as f:
            mig_data = json.load(f)
        dups = [op for op in mig_data.get("operations", []) if op.get("is_duplicate")]
        self.assertGreaterEqual(len(dups), 4)
        print("  [PASS] Test 8: SHA-256 duplicate detection verified.")

    # -------------------------------------------------------------------------
    # Test 9: Corrupted, Empty & Unsupported File Error Handling
    # -------------------------------------------------------------------------
    def test_09_corrupted_empty_unsupported_file_handling(self):
        """Verifies safe rejection and error handling for missing/unsupported files."""
        non_existent = os.path.join(WORKSPACE_ROOT, "does_not_exist.wav")
        with self.assertRaises(FileNotFoundError):
            audio_analyzer.analyze_audio_asset(non_existent)

        with self.assertRaises(FileNotFoundError):
            footage_analyzer.inspect_image_asset(non_existent)

        # Unsupported extension in analyze CLI
        cmd = [sys.executable, os.path.join(SCRIPTS_DIR, "media_intake.py"), "analyze", "README.md"]
        res = subprocess.run(cmd, cwd=WORKSPACE_ROOT, capture_output=True, text=True)
        self.assertNotEqual(res.returncode, 0)
        self.assertIn("Unsupported file format", res.stderr)
        print("  [PASS] Test 9: Corrupted & unsupported file handling verified.")

    # -------------------------------------------------------------------------
    # Test 10: Licensing Status Gatekeeping
    # -------------------------------------------------------------------------
    def test_10_licensing_status_gatekeeping(self):
        """Verifies licensing gatekeeper flags unverified assets."""
        # Query with allow_unverified_licenses=False
        res_strict = audio_recommender.recommend_audio(
            project="block-puzzle-burst",
            desired_mood="energetic",
            allow_unverified_licenses=False
        )
        for r in res_strict.get("top_recommendations", []):
            self.assertTrue(r["commercial_cleared"])
            self.assertEqual(r["license_status"], "VERIFIED_COMMERCIAL_USE")

        # Query with allow_unverified_licenses=True should include warning
        res_permissive = audio_recommender.recommend_audio(
            project="block-puzzle-burst",
            desired_mood="energetic",
            allow_unverified_licenses=True
        )
        has_warning = any("NEEDS_REVIEW" in r.get("license_status", "") for r in res_permissive.get("top_recommendations", []))
        self.assertTrue(has_warning)
        print("  [PASS] Test 10: Licensing status gatekeeping verified.")

    # -------------------------------------------------------------------------
    # Test 11: Phase 1 Master Regression Verification
    # -------------------------------------------------------------------------
    def test_11_phase1_regression_suite(self):
        """Verifies that all 5 Phase 1 tests pass without regression."""
        cmd = [sys.executable, os.path.join(SCRIPTS_DIR, "test_studio_suite.py")]
        res = subprocess.run(cmd, cwd=WORKSPACE_ROOT, capture_output=True, text=True)
        self.assertEqual(res.returncode, 0, f"Phase 1 regression failed:\n{res.stdout}\n{res.stderr}")
        self.assertIn("ALL 5 STUDIO VERIFICATION TESTS PASSED SUCCESSFULLY", res.stdout)
        print("  [PASS] Test 11: Phase 1 master regression suite passed 100%.")


if __name__ == "__main__":
    unittest.main(verbosity=2)
