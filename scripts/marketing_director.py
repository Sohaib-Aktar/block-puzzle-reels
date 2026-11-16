"""
marketing_director.py — AI Marketing Director & Creative Production Engine
Translates project knowledge and verified footage into high-retention social media campaigns.
"""

import os
import sys
import json
import argparse
from typing import Dict, Any, List

WORKSPACE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(WORKSPACE_ROOT, "scripts"))
from footage_analyzer import recommend_footage

HOOK_ARCHETYPES = {
    "challenge": {
        "pattern": "Can you solve it in ONE move? 🤔",
        "description": "Engages cognitive curiosity and compels comments",
        "best_for": ["puzzle_challenge", "gamification"]
    },
    "frustration": {
        "pattern": "Still tracking orders on paper notebooks? ❌",
        "description": "Highlights common manual operational friction",
        "best_for": ["software_tutorial", "pain_point"]
    },
    "speed": {
        "pattern": "Watch an entire store order booked in 15 seconds. ⚡",
        "description": "Demonstrates rapid software capability",
        "best_for": ["feature_demo", "productivity"]
    },
    "authenticity": {
        "pattern": "Solo indie dev, zero WiFi required. ✈️",
        "description": "Builds trust through authentic founder journey",
        "best_for": ["dev_log", "offline_proof"]
    },
    "insight": {
        "pattern": "Why clearing lines too early ruins your score! 💡",
        "description": "Counter-intuitive educational gameplay tip",
        "best_for": ["tips_and_tricks", "educational"]
    }
}


def load_project_knowledge(project_slug: str) -> Dict[str, Any]:
    """Load project profile and verified knowledge base."""
    proj_dir = os.path.join(WORKSPACE_ROOT, "projects", project_slug)
    k_dir = os.path.join(proj_dir, "knowledge")

    prof_file = os.path.join(proj_dir, "PROJECT_PROFILE.md")
    verified_file = os.path.join(k_dir, "verified_features.md")
    claims_file = os.path.join(k_dir, "marketing_claims.md")

    return {
        "project_slug": project_slug,
        "profile_exists": os.path.exists(prof_file),
        "verified_features_exists": os.path.exists(verified_file),
        "claims_exists": os.path.exists(claims_file)
    }


def strategize_content_piece(
    project_slug: str,
    campaign_slug: str,
    content_id: str,
    objective: str,
    platform_preset: str = "instagram_reel",
    hook_archetype: str = "challenge",
    target_duration: float = 15.0
) -> Dict[str, Any]:
    """
    Develops a complete creative package (brief, script, timeline, manifest, captions).
    """
    # 1. Footage Recommendation
    footages = recommend_footage(objective, target_duration)
    recommended_shot = footages[0] if footages else {
        "source_file": "Raw_input_files/recording_1.mp4",
        "recommended_start": 0.0,
        "recommended_duration": target_duration
    }

    # 2. Hook and Narrative Strategy
    hook_data = HOOK_ARCHETYPES.get(hook_archetype, HOOK_ARCHETYPES["challenge"])
    hook_text = hook_data["pattern"]

    # 3. Dynamic Narrative Construction by Project
    if project_slug == "block-puzzle-burst":
        title = "Block Puzzle Burst — Brain Challenge"
        on_screen_hook = hook_text
        vo_script = "Solve it in one move! Which piece goes first: A, B or C? Think carefully and drop your comment below."
        cta_text = "Comment A, B or C! 👇"
        caption = "Which piece goes first, and where? 🤔 Comment A, B or C. Think carefully! Play Block Puzzle Burst free offline. Link in bio! 🎮\n\n#BlockPuzzle #BrainTeaser #PyapirasGames #PuzzleGame"
    elif project_slug == "expand-ezisales":
        title = "Expand eziSales — Rapid Order Booking"
        on_screen_hook = "Book orders in under 30s ⚡"
        vo_script = "Stop taking retail orders on paper. With Expand eziSales, select your retailer, add SKUs with active schemes, and sync directly with your backend ERP in seconds."
        cta_text = "Schedule a Free Demo 🔗"
        caption = "Ditch paper order pads. Boost secondary field sales order booking speed with Expand eziSales SFA. Connect with our team via link in bio! 🚀\n\n#FieldSales #SFA #B2BSaaS #DistributionERP"
    elif project_slug == "expand-hr":
        title = "Expand HR — Automated Payroll Walkthrough"
        on_screen_hook = "Payroll in One Click 💼"
        vo_script = "Calculate monthly payroll, tax deductions, and statutory compliances in just one click with Expand HR."
        cta_text = "Simplify HR Today 🔗"
        caption = "Save 5 days every month on payroll calculations. Compliant, accurate, and automated with Expand HR. Link in bio! 📊\n\n#HRMS #PayrollAutomation #CloudHR"
    else:
        title = f"{project_slug} Spotlight"
        on_screen_hook = hook_text
        vo_script = f"Discover how {project_slug} streamlines your daily operations."
        cta_text = "Learn More 🔗"
        caption = f"Streamline your operations with {project_slug}. Link in bio!\n\n#{project_slug} #Productivity"

    # 4. Editing Manifest Generation
    manifest = {
        "content_id": content_id,
        "project": project_slug,
        "campaign": campaign_slug,
        "platform": platform_preset.split("_")[0],
        "format": "reel" if "reel" in platform_preset else "short",
        "renderer": "ffmpeg",
        "canvas": {
            "width": 1080 if "vertical" in platform_preset or "reel" in platform_preset or "short" in platform_preset else 1920,
            "height": 1920 if "vertical" in platform_preset or "reel" in platform_preset or "short" in platform_preset else 1080,
            "fps": 30,
            "duration_seconds": target_duration
        },
        "timeline": [
            {
                "shot_id": "shot-01-main",
                "source_file": recommended_shot["source_file"],
                "source_start": recommended_shot["recommended_start"],
                "duration": target_duration,
                "text_overlays": [
                    {"text": on_screen_hook, "position_y": 140}
                ]
            }
        ],
        "audio": {
            "voiceover_text": vo_script,
            "bgm_volume": 0.25,
            "vo_volume": 1.0
        }
    }

    script_md = f"""# Script — {title}
**Hook Archetype:** {hook_archetype} ({hook_data['description']})

## Timeline Breakdown
- **00:00 - 00:03 (Hook):** On-screen headline: "{on_screen_hook}"
- **00:03 - 00:12 (Body):** Feature demonstration / gameplay highlight
- **00:12 - 00:15 (CTA):** Outro prompt: "{cta_text}"

## Voiceover Script
"{vo_script}"
"""

    return {
        "content_id": content_id,
        "title": title,
        "objective": objective,
        "hook_archetype": hook_archetype,
        "hook_text": on_screen_hook,
        "cta_text": cta_text,
        "manifest": manifest,
        "script": script_md,
        "captions": {"instagram": caption, "youtube": caption, "facebook": caption}
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AI Marketing Director")
    parser.add_argument("--project", required=True, help="Project slug")
    parser.add_argument("--campaign", default="growth-campaign", help="Campaign slug")
    parser.add_argument("--content-id", required=True, help="Unique content ID")
    parser.add_argument("--objective", required=True, choices=["satisfying_clear", "puzzle_challenge", "offline_proof", "software_tutorial", "score_challenge"], help="Marketing objective")
    parser.add_argument("--hook", default="challenge", choices=["challenge", "frustration", "speed", "authenticity", "insight"], help="Hook archetype")
    parser.add_argument("--preset", default="instagram_reel", help="Platform preset")

    args = parser.parse_args()
    plan = strategize_content_piece(
        project_slug=args.project,
        campaign_slug=args.campaign,
        content_id=args.content_id,
        objective=args.objective,
        platform_preset=args.preset,
        hook_archetype=args.hook
    )

    print(f"\nAI Marketing Director Plan for {plan['content_id']}:")
    print(f"  Title     : {plan['title']}")
    print(f"  Hook      : {plan['hook_text']}")
    print(f"  Archetype : {plan['hook_archetype']}")
    print(f"  CTA       : {plan['cta_text']}\n")
    print("Editing Manifest generated.")
