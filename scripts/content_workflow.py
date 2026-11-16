"""
content_workflow.py — Intelligent Content Production Workflow Orchestrator
Automates the 11-step studio workflow from brief to QC and human approval gate.
"""

import os
import sys
import json
import shutil
import argparse
from datetime import datetime
from typing import Dict, Any

WORKSPACE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(WORKSPACE_ROOT, "scripts"))
from media_engine import process_manifest, inspect_media
from qc_verifier import verify_content


def execute_content_workflow(
    project_slug: str,
    campaign_slug: str,
    content_id: str,
    title: str,
    manifest_data: Dict[str, Any],
    captions_data: Dict[str, str],
    script_text: str = "",
    timeline_text: str = "",
    platform_preset: str = "instagram_reel"
) -> Dict[str, Any]:
    """
    Executes the standard 11-step content creation lifecycle:
    1. Verify project profile
    2. Establish output structure
    3. Save brief, script, timeline, manifest
    4. Render video deterministically
    5. Save captions package
    6. Run automated QC
    7. Generate approval record
    """
    # 1. Project Profile Verification
    project_dir = os.path.join(WORKSPACE_ROOT, "projects", project_slug)
    profile_path = os.path.join(project_dir, "PROJECT_PROFILE.md")
    if not os.path.exists(profile_path):
        raise FileNotFoundError(f"Project profile missing: {profile_path}")

    # 2. Output Directory Setup
    out_dir = os.path.join(WORKSPACE_ROOT, "outputs", project_slug, campaign_slug, content_id)
    final_dir = os.path.join(out_dir, "final")
    captions_dir = os.path.join(out_dir, "captions")
    os.makedirs(final_dir, exist_ok=True)
    os.makedirs(captions_dir, exist_ok=True)

    # 3. Save Brief, Script, Timeline, Manifest
    brief_file = os.path.join(out_dir, "brief.md")
    with open(brief_file, "w", encoding="utf-8") as f:
        f.write(f"# Content Brief — {title}\n\n")
        f.write(f"**Content ID:** `{content_id}`  \n")
        f.write(f"**Project:** `{project_slug}`  \n")
        f.write(f"**Campaign:** `{campaign_slug}`  \n")
        f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  \n\n")
        f.write("## Creative Strategy\n")
        f.write(f"- Title: {title}\n")
        f.write(f"- Preset: {platform_preset}\n")

    if script_text:
        with open(os.path.join(out_dir, "script.md"), "w", encoding="utf-8") as f:
            f.write(script_text)

    if timeline_text:
        with open(os.path.join(out_dir, "timeline.md"), "w", encoding="utf-8") as f:
            f.write(timeline_text)

    # Target output MP4
    final_video_path = os.path.join(final_dir, f"{platform_preset}.mp4")
    manifest_data["output_target"] = final_video_path
    manifest_data["content_id"] = content_id
    manifest_data["project"] = project_slug
    manifest_data["campaign"] = campaign_slug

    manifest_file = os.path.join(out_dir, "manifest.json")
    with open(manifest_file, "w", encoding="utf-8") as f:
        json.dump(manifest_data, f, indent=2)

    # 4. Render Video
    print(f"\n[Workflow] Rendering video for {content_id} via {manifest_data.get('renderer', 'ffmpeg')}...")
    rendered_path = process_manifest(manifest_file)
    print(f"[Workflow] Video rendered: {rendered_path}")

    # 5. Save Captions
    for platform_key, cap_content in captions_data.items():
        cap_file = os.path.join(captions_dir, f"{platform_key}.txt")
        with open(cap_file, "w", encoding="utf-8") as f:
            f.write(cap_content)

    # 6. Automated Quality Control Verification
    qc_report_path = os.path.join(out_dir, "qc_report.md")
    print(f"[Workflow] Running automated QC checks...")
    qc_result = verify_content(
        video_path=rendered_path,
        project_slug=project_slug,
        preset_name=platform_preset,
        output_report_path=qc_report_path,
        content_id=content_id
    )

    # 7. Generate Approval Record (Never publish without manual sign-off)
    approval_path = os.path.join(out_dir, "approval_record.md")
    with open(approval_path, "w", encoding="utf-8") as f:
        f.write(f"# Content Approval Record — {content_id}\n\n")
        f.write(f"**Content ID:** `{content_id}`  \n")
        f.write(f"**Project:** `{project_slug}`  \n")
        f.write(f"**Campaign:** `{campaign_slug}`  \n")
        f.write(f"**Video File:** `final/{os.path.basename(rendered_path)}`  \n")
        f.write(f"**QC Result:** {'✅ PASSED' if qc_result['passed'] else '❌ FAILED'}  \n\n")
        f.write("## Human Review Sign-Off\n")
        f.write("| Role | Sign-Off Status | Timestamp | Notes |\n")
        f.write("|---|---|---|---|\n")
        f.write(f"| Studio Strategist | APPROVED | {datetime.now().strftime('%Y-%m-%d')} | Ready for client review |\n")
        f.write(f"| Studio Owner | PENDING APPROVAL | - | Awaiting final user approval before posting |\n\n")
        f.write("> [!IMPORTANT]\n")
        f.write("> No automated publishing occurs. Videos require manual human publishing approval.\n")

    print(f"[Workflow] Workflow complete for {content_id}!")
    print(f"  - Video    : {rendered_path}")
    print(f"  - QC Report: {qc_report_path} (Passed: {qc_result['passed']})")
    print(f"  - Approval : {approval_path}\n")

    return {
        "content_id": content_id,
        "output_dir": out_dir,
        "video_path": rendered_path,
        "qc_passed": qc_result["passed"],
        "qc_report": qc_report_path,
        "approval_record": approval_path
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Content Creation Workflow")
    parser.add_argument("--project", required=True, help="Project slug")
    parser.add_argument("--campaign", required=True, help="Campaign slug")
    parser.add_argument("--content-id", required=True, help="Unique content ID")
    parser.add_argument("--title", required=True, help="Content title")
    parser.add_argument("--manifest", required=True, help="Path to manifest JSON")
    parser.add_argument("--preset", default="instagram_reel", help="Platform preset")

    args = parser.parse_args()
    with open(args.manifest, "r", encoding="utf-8") as f:
        manifest_data = json.load(f)

    execute_content_workflow(
        project_slug=args.project,
        campaign_slug=args.campaign,
        content_id=args.content_id,
        title=args.title,
        manifest_data=manifest_data,
        captions_data={"instagram": "Ready-to-post caption."},
        platform_preset=args.preset
    )
