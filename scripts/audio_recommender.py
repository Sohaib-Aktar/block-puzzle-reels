"""
audio_recommender.py — Intelligent Audio & Music Recommendation Engine
Recommends the best background music, narration, and sound effects based on:
  - Project identity & brand acoustic profile
  - Marketing objective & target audience
  - Desired mood & energy progression
  - Target video duration & scene timelines
  - Commercial licensing clearance status

Provides explainable, plain-English justifications and editing instructions.
"""

import os
import sys
import json
import argparse
from typing import Dict, Any, List, Optional, Tuple

WORKSPACE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(WORKSPACE_ROOT, "data")
AUDIO_CATALOG_PATH = os.path.join(DATA_DIR, "audio_catalog.json")

# Brand Acoustic Profiles
PROJECT_AUDIO_PROFILES = {
    "block-puzzle-burst": {
        "primary_moods": ["playful", "cheerful", "casual_gaming", "satisfying", "upbeat", "relaxing"],
        "preferred_energy": ["medium", "high"],
        "target_bpm_range": (105, 135),
        "instrumentation": ["light electronic", "rhodes piano", "bell chimes", "bouncy synth", "wood percussion"],
        "banned_moods": ["somber", "aggressive", "corporate_heavy"]
    },
    "expand-ezisales": {
        "primary_moods": ["corporate", "technology", "modern", "focused", "upbeat", "professional"],
        "preferred_energy": ["medium", "high"],
        "target_bpm_range": (110, 125),
        "instrumentation": ["clean electric guitar", "tech arpeggio", "steady electronic beat"],
        "banned_moods": ["silly", "chaotic", "melodramatic"]
    },
    "expand-hr": {
        "primary_moods": ["trustworthy", "corporate", "calm", "positive", "peaceful", "professional"],
        "preferred_energy": ["low", "medium"],
        "target_bpm_range": (85, 110),
        "instrumentation": ["warm acoustic piano", "gentle strings", "soft percussion"],
        "banned_moods": ["frantic", "suspenseful", "aggressive"]
    },
    "wms": {
        "primary_moods": ["modern", "technology", "focused", "operational", "energetic"],
        "preferred_energy": ["medium", "high"],
        "target_bpm_range": (115, 130),
        "instrumentation": ["forward-moving synth", "rhythmic tech drums", "clean pulses"],
        "banned_moods": ["whimsical", "sad"]
    },
    "pos": {
        "primary_moods": ["retail_friendly", "modern", "upbeat", "energetic", "cheerful"],
        "preferred_energy": ["medium", "high"],
        "target_bpm_range": (115, 128),
        "instrumentation": ["bright groove", "bouncy bass", "retail pop beat"],
        "banned_moods": ["dark", "sluggish"]
    }
}


def load_catalog() -> Dict[str, Any]:
    """Loads data/audio_catalog.json."""
    if not os.path.exists(AUDIO_CATALOG_PATH):
        raise FileNotFoundError(f"Audio catalog not found at {AUDIO_CATALOG_PATH}. Run 'python scripts/audio_analyzer.py --scan-dir source_assets' first.")
    with open(AUDIO_CATALOG_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def calculate_mood_score(desired_moods: List[str], asset_moods: List[str]) -> Tuple[float, List[str]]:
    """Calculates mood overlap between desired query and asset tags."""
    if not desired_moods:
        return 1.0, []

    matched = []
    d_set = [m.lower().strip() for m in desired_moods]
    a_set = [m.lower().strip() for m in asset_moods]

    for d in d_set:
        for a in a_set:
            if d in a or a in d:
                matched.append(d)
                break

    score = len(matched) / max(len(d_set), 1)
    return min(1.0, score), list(set(matched))


def calculate_duration_score(target_dur: float, asset_dur: float) -> Tuple[float, str]:
    """
    Evaluates duration fit:
      - Asset >= target: Can be trimmed with fade out (Score 0.85 - 1.0)
      - Asset == target: Perfect fit (Score 1.0)
      - Asset < target: Requires looping or additional track (Score penalty)
    """
    diff = asset_dur - target_dur
    if abs(diff) <= 1.0:
        return 1.0, "Exact duration match (seamless fit without editing)."
    elif diff > 0:
        # Asset is longer than target -> trim needed
        score = max(0.70, 1.0 - (diff / 60.0) * 0.15)
        return round(score, 2), f"Asset ({asset_dur:.1f}s) is longer than target ({target_dur:.1f}s). Trim to {target_dur:.1f}s with a 0.5s audio fade-out."
    else:
        # Asset is shorter than target -> looping needed
        shortage = target_dur - asset_dur
        score = max(0.40, 1.0 - (shortage / target_dur) * 0.6)
        return round(score, 2), f"Asset ({asset_dur:.1f}s) is shorter than target ({target_dur:.1f}s). Requires looping or pairing with a secondary track."


def recommend_audio(
    project: str,
    content_category: str = "lifestyle_reel",
    objective: str = "general_marketing",
    desired_mood: str = "playful",
    target_duration: float = 15.0,
    scenes: Optional[List[Dict[str, Any]]] = None,
    allow_unverified_licenses: bool = False
) -> Dict[str, Any]:
    """
    Recommends and ranks the best audio assets based on multi-dimensional scoring.
    """
    catalog = load_catalog()
    assets = list(catalog.get("assets", {}).values())

    profile = PROJECT_AUDIO_PROFILES.get(project, PROJECT_AUDIO_PROFILES["block-puzzle-burst"])
    query_moods = [m.strip().lower() for m in desired_mood.replace(",", " ").replace(";", " ").split() if m.strip()]

    ranked_recommendations = []

    for item in assets:
        # Only evaluate music for background music queries (exclude raw voiceovers unless requested)
        is_vo = item.get("sound_classification") == "voiceover_speech"
        is_sfx = item.get("sound_classification") == "sound_effect"

        if "voiceover" in content_category.lower() and not is_vo:
            continue
        if "sound_effect" in content_category.lower() and not is_sfx:
            continue
        if "voiceover" not in content_category.lower() and "sound_effect" not in content_category.lower() and (is_vo or is_sfx):
            continue

        item_path = item.get("path", "")
        item_moods = item.get("mood", [])
        item_energy = item.get("energy_level", "medium")
        item_bpm = item.get("bpm")
        item_dur = item.get("duration_seconds", 0.0)
        lic_status = item.get("license_status", "UNKNOWN")

        # 1. Project Affinity Score (0–30 pts)
        proj_score = 0
        if project in item.get("recommended_projects", []):
            proj_score += 25
        elif any(pm in item_moods for pm in profile["primary_moods"]):
            proj_score += 15

        if any(bm in item_moods for bm in profile.get("banned_moods", [])):
            proj_score -= 20

        # 2. Mood & Emotional Tone Score (0–35 pts)
        mood_ratio, matched_tags = calculate_mood_score(query_moods, item_moods)
        mood_score = mood_ratio * 35.0

        # 3. Energy & BPM Compatibility (0–15 pts)
        energy_score = 10
        if item_energy in profile.get("preferred_energy", []):
            energy_score += 5
        if item_bpm:
            bpm_min, bpm_max = profile["target_bpm_range"]
            if bpm_min <= item_bpm <= bpm_max:
                energy_score += 5

        # 4. Duration Suitability (0–20 pts)
        dur_ratio, dur_explanation = calculate_duration_score(target_duration, item_dur)
        duration_score = dur_ratio * 20.0

        # 5. Licensing Gatekeeping & Compliance Check
        lic_warning = None
        if lic_status == "VERIFIED_COMMERCIAL_USE":
            lic_cleared = True
        elif lic_status in ["UNKNOWN", "NEEDS_REVIEW", "RESTRICTED"]:
            lic_cleared = False
            lic_warning = f"⚠️ Licensing Status: {lic_status}. Requires human clearance before commercial publishing."
        else:
            lic_cleared = False
            lic_warning = f"⚠️ Commercial Use Prohibited: {lic_status}."

        # If unverified licenses are disallowed, skip non-cleared tracks
        if not allow_unverified_licenses and not lic_cleared:
            continue

        total_score = round(max(0.0, min(100.0, proj_score + mood_score + energy_score + duration_score)), 1)

        # Build Explainable Reasoning
        reasons = []
        if proj_score >= 20:
            reasons.append(f"Direct match for '{project}' brand identity.")
        if matched_tags:
            reasons.append(f"Acoustic mood matches desired tags: {', '.join(matched_tags)}.")
        if item_bpm:
            reasons.append(f"Rhythmic tempo is {item_bpm:.1f} BPM ({item_energy} energy).")
        reasons.append(dur_explanation)

        ranked_recommendations.append({
            "asset_id": item["asset_id"],
            "filename": item["filename"],
            "path": item_path,
            "match_score": total_score,
            "sound_classification": item.get("sound_classification"),
            "bpm": item_bpm,
            "energy_level": item_energy,
            "mood_tags": item_moods,
            "duration_seconds": item_dur,
            "license_status": lic_status,
            "commercial_cleared": lic_cleared,
            "matched_moods": matched_tags,
            "explanation": " ".join(reasons),
            "warnings": [lic_warning] if lic_warning else []
        })

    # Sort descending by match score
    ranked_recommendations.sort(key=lambda x: x["match_score"], reverse=True)

    # Multi-Scene Timeline Analysis
    scene_plan = []
    if scenes:
        for idx, sc in enumerate(scenes, 1):
            s_dur = sc.get("end_sec", 0.0) - sc.get("start_sec", 0.0)
            s_mood = sc.get("mood", desired_mood)
            scene_plan.append({
                "scene_name": sc.get("name", f"Scene {idx}"),
                "start_sec": sc.get("start_sec", 0.0),
                "end_sec": sc.get("end_sec", s_dur),
                "time_window": f"{sc.get('start_sec', 0.0):.1f}s - {sc.get('end_sec', s_dur):.1f}s",
                "scene_mood": s_mood,
                "pacing": sc.get("pacing", "upbeat"),
                "audio_action": f"Apply track segment supporting '{s_mood}'. Transition at {sc.get('end_sec', s_dur):.1f}s."
            })
    else:
        # Default 3-act marketing structure (Hook, Core, CTA)
        hook_end = min(3.0, target_duration * 0.2)
        body_end = max(hook_end, target_duration - min(3.0, target_duration * 0.2))
        scene_plan = [
            {
                "scene_name": "Hook Scene",
                "start_sec": 0.0,
                "end_sec": hook_end,
                "time_window": f"0.0s - {hook_end:.1f}s",
                "scene_mood": "attention_grabbing",
                "pacing": "high",
                "audio_action": "High-impact intro rhythm or sound effect accent."
            },
            {
                "scene_name": "Core Gameplay / Demo",
                "start_sec": hook_end,
                "end_sec": body_end,
                "time_window": f"{hook_end:.1f}s - {body_end:.1f}s",
                "scene_mood": desired_mood,
                "pacing": "steady",
                "audio_action": "Sustained rhythmic bed ducked -18dB under voiceover."
            },
            {
                "scene_name": "CTA Outro",
                "start_sec": body_end,
                "end_sec": target_duration,
                "time_window": f"{body_end:.1f}s - {target_duration:.1f}s",
                "scene_mood": "conclusive",
                "pacing": "resolving",
                "audio_action": "Musical crescendo with logo chime accent."
            }
        ]

    return {
        "query": {
            "project": project,
            "category": content_category,
            "objective": objective,
            "desired_mood": desired_mood,
            "target_duration": target_duration
        },
        "total_evaluated": len(assets),
        "top_recommendations": ranked_recommendations[:5],
        "multi_scene_plan": scene_plan
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Intelligent Audio Recommendation Engine")
    parser.add_argument("--project", default="block-puzzle-burst", help="Project slug")
    parser.add_argument("--category", default="lifestyle_reel", help="Content category")
    parser.add_argument("--objective", default="lifestyle_marketing", help="Video marketing objective")
    parser.add_argument("--mood", default="playful upbeat", help="Desired emotional mood tags")
    parser.add_argument("--duration", type=float, default=22.0, help="Target video duration in seconds")
    parser.add_argument("--json", action="store_true", help="Output raw JSON")
    args = parser.parse_args()

    recs = recommend_audio(
        project=args.project,
        content_category=args.category,
        objective=args.objective,
        desired_mood=args.mood,
        target_duration=args.duration
    )

    if args.json:
        print(json.dumps(recs, indent=2))
    else:
        print("\n" + "=" * 75)
        print(f"AUDIO RECOMMENDATION REPORT — {args.project.upper()}")
        print(f"Category: {args.category} | Objective: {args.objective} | Duration: {args.duration}s")
        print("=" * 75 + "\n")

        top = recs.get("top_recommendations", [])
        if not top:
            print("No matching audio assets found in catalog.")
        for idx, r in enumerate(top, 1):
            print(f"#{idx} [{r['match_score']}/100] {r['filename']} ({r['duration_seconds']}s)")
            print(f"    Moods   : {', '.join(r['mood_tags'])} | Energy: {r['energy_level']} | BPM: {r['bpm']}")
            print(f"    License : {r['license_status']} ({'✅ Cleared' if r['commercial_cleared'] else '⚠️ Review Needed'})")
            print(f"    Guidance: {r['explanation']}")
            if r["warnings"]:
                for w in r["warnings"]:
                    print(f"    {w}")
            print()
