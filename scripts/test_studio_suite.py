"""
test_studio_suite.py — Studio Master Verification Suite
Runs the 4 active end-to-end verification tests:
  - Test A: Block Puzzle Day 4 Offline Proof Reel (Image-video concat, dual QC)
  - Test B: EziSales Feature Tutorial (Offline VO synthesis, -14 LUFS loudness norm, QC)
  - Test D: Multi-Platform Creative Adaptations (IG, FB, YT Shorts, YT Tutorial)
  - Test E: End-to-End Lifecycle & Approval Gatekeeping (Zero Unauthorized Publishing)
"""

import os
import sys
import subprocess

WORKSPACE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def run_subtest(name: str, script_path: str):
    print("\n" + "=" * 70)
    print(f"RUNNING: {name}")
    print("=" * 70)
    res = subprocess.run([sys.executable, script_path], cwd=WORKSPACE_ROOT)
    if res.returncode != 0:
        print(f"❌ FAILED: {name}")
        sys.exit(res.returncode)
    print(f"✅ PASSED: {name}")


if __name__ == "__main__":
    scripts_dir = os.path.join(WORKSPACE_ROOT, "scripts")
    run_subtest("Test A — Block Puzzle Day 4 Reel", os.path.join(scripts_dir, "run_test_a_day4.py"))
    run_subtest("Test B — EziSales Tutorial with VO", os.path.join(scripts_dir, "run_test_b_ezisales.py"))
    run_subtest("Test D — Multiplatform Creative Adaptations", os.path.join(scripts_dir, "platform_adapter.py"))
    run_subtest("Test E — Approval Workflow & Gatekeeping", os.path.join(scripts_dir, "run_test_e_lifecycle.py"))

    print("\n" + "*" * 70)
    print("🎉 ALL 4 STUDIO VERIFICATION TESTS PASSED SUCCESSFULLY!")
    print("*" * 70 + "\n")
