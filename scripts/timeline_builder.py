"""
timeline_builder.py — Manifest Validation, Asset Resolution & Timeline Normalization
Resolves Phase 2 Catalog Asset IDs (VID_*, AUDIO_*) to physical files, verifies licensing,
and produces a validated, preflight-checked timeline execution plan.
"""

import os
import sys
import json
from typing import Dict, Any, List, Optional, Tuple

WORKSPACE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(WORKSPACE_ROOT, "scripts"))
from media_engine import inspect_media

MEDIA_CATALOG_PATH = os.path.join(WORKSPACE_ROOT, "data", "media_catalog.json")
AUDIO_CATALOG_PATH = os.path.join(WORKSPACE_ROOT, "data", "audio_catalog.json")
REAL_AUDIO_PATH = os.path.join(WORKSPACE_ROOT, "data", "real_audio_inspection.json")
PROFILES_PATH = os.path.join(WORKSPACE_ROOT, "config", "production", "video_profiles.json")
DEFAULTS_PATH = os.path.join(WORKSPACE_ROOT, "config", "production", "defaults.json")


class PreflightValidationError(Exception):
    """Raised when manifest validation fails during preflight checks."""
    pass


class TimelineBuilder:
    """Validates manifests and resolves catalog assets into an actionable production plan."""

    def __init__(self):
        self.media_catalog = self._load_json(MEDIA_CATALOG_PATH, {}).get("assets", {})
        self.audio_catalog = self._load_json(AUDIO_CATALOG_PATH, {}).get("assets", {})
        self.real_audio_inspection = {
            item["asset_id"]: item for item in self._load_json(REAL_AUDIO_PATH, [])
        }
        self.video_profiles = self._load_json(PROFILES_PATH, {})
        self.defaults = self._load_json(DEFAULTS_PATH, {})

    @staticmethod
    def _load_json(path: str, default_val: Any) -> Any:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        return default_val

    def resolve_media_asset(self, asset_ref: str, project_slug: Optional[str] = None) -> Dict[str, Any]:
        """Resolves an asset ID (e.g. VID_2B4C0018) or relative file path to full metadata."""
        # 1. Direct Catalog ID match
        if asset_ref in self.media_catalog:
            asset = self.media_catalog[asset_ref]
            loc = asset.get("file_location", "")
            abs_path = os.path.join(WORKSPACE_ROOT, loc)
            if not os.path.exists(abs_path):
                raise FileNotFoundError(f"Catalog asset {asset_ref} references missing file: {abs_path}")
            return {
                "asset_id": asset_ref,
                "file_path": abs_path,
                "project": asset.get("project"),
                "duration": asset.get("duration_seconds", 0.0),
                "width": asset.get("width", 0),
                "height": asset.get("height", 0),
                "fps": asset.get("fps", 30.0)
            }

        # 2. Search by original filename or partial ID in catalog
        for aid, data in self.media_catalog.items():
            if asset_ref in (data.get("original_filename"), aid, data.get("file_location")):
                abs_path = os.path.join(WORKSPACE_ROOT, data["file_location"])
                if os.path.exists(abs_path):
                    return {
                        "asset_id": aid,
                        "file_path": abs_path,
                        "project": data.get("project"),
                        "duration": data.get("duration_seconds", 0.0),
                        "width": data.get("width", 0),
                        "height": data.get("height", 0),
                        "fps": data.get("fps", 30.0)
                    }

        # 3. Direct disk path fallback
        direct_candidates = [
            asset_ref,
            os.path.join(WORKSPACE_ROOT, asset_ref),
            os.path.join(WORKSPACE_ROOT, "source_assets", project_slug or "", "gameplay", asset_ref),
            os.path.join(WORKSPACE_ROOT, "Raw_input_files", asset_ref),
            os.path.join(WORKSPACE_ROOT, "my-video", "public", asset_ref)
        ]
        for c in direct_candidates:
            if c and os.path.exists(c) and os.path.isfile(c):
                info = inspect_media(c)
                return {
                    "asset_id": f"FILE_{os.path.basename(c)}",
                    "file_path": os.path.abspath(c),
                    "project": project_slug,
                    "duration": info["duration_seconds"],
                    "width": info["width"],
                    "height": info["height"],
                    "fps": info["fps"]
                }

        raise PreflightValidationError(
            f"Unable to resolve media asset reference: '{asset_ref}'. Not found in catalog or workspace."
        )

    def resolve_audio_asset(
        self,
        asset_ref: str,
        allow_review_audio: bool = False
    ) -> Dict[str, Any]:
        """Resolves audio by Asset ID, verifies file presence and enforces licensing rules."""
        audio_entry = None
        asset_id = asset_ref

        # Check in audio_catalog
        if asset_ref in self.audio_catalog:
            audio_entry = self.audio_catalog[asset_ref]
        else:
            # Match by filename
            for aid, data in self.audio_catalog.items():
                if asset_ref in (data.get("filename"), aid, data.get("path")):
                    audio_entry = data
                    asset_id = aid
                    break

        # Check real audio inspection for licensing metadata
        insp = self.real_audio_inspection.get(asset_id, {})
        provenance = insp.get("provenance", {})

        # Resolve path
        rel_path = audio_entry.get("path") if audio_entry else None
        abs_path = None
        if rel_path:
            abs_path = os.path.join(WORKSPACE_ROOT, rel_path)
            if not os.path.exists(abs_path):
                # Try direct path
                alt = os.path.join(WORKSPACE_ROOT, "Raw_input_files", "audio", os.path.basename(rel_path))
                if os.path.exists(alt):
                    abs_path = alt

        if not abs_path or not os.path.exists(abs_path):
            # Direct file search
            direct_candidates = [
                asset_ref,
                os.path.join(WORKSPACE_ROOT, asset_ref),
                os.path.join(WORKSPACE_ROOT, "source_assets", "shared", "music", os.path.basename(asset_ref)),
                os.path.join(WORKSPACE_ROOT, "Raw_input_files", "audio", os.path.basename(asset_ref)),
                os.path.join(WORKSPACE_ROOT, "my-video", "public", os.path.basename(asset_ref))
            ]
            for c in direct_candidates:
                if c and os.path.exists(c) and os.path.isfile(c):
                    abs_path = os.path.abspath(c)
                    break

        if not abs_path or not os.path.exists(abs_path):
            raise PreflightValidationError(f"Audio asset '{asset_ref}' could not be located on disk.")

        # Determine licensing status
        lic_status = provenance.get("license_status")
        if not lic_status:
            # Check filename indicators
            fn = os.path.basename(abs_path).lower()
            if "no-copyright" in fn or "no_copyright" in fn:
                lic_status = "NEEDS_REVIEW"
            elif fn.startswith("bgm_") or fn.startswith("sfx_") or fn.startswith("vo_"):
                lic_status = "STUDIO_ORIGINAL"
            else:
                lic_status = "UNKNOWN"

        # Enforce licensing policy
        lic_policy = self.defaults.get("licensing", {})
        commercial_allowed = lic_policy.get("commercial_publishing_allowed_statuses", ["VERIFIED_COMMERCIAL_USE", "STUDIO_ORIGINAL"])
        preview_allowed = lic_policy.get("preview_only_statuses", ["NEEDS_REVIEW"])
        blocked = lic_policy.get("blocked_statuses", ["RESTRICTED", "UNKNOWN"])

        if lic_status in blocked:
            raise PreflightValidationError(
                f"Audio asset '{asset_ref}' is BLOCKED by licensing policy. Status: {lic_status}. Commercial usage prohibited."
            )

        warning_issued = False
        if lic_status in preview_allowed:
            if not allow_review_audio:
                raise PreflightValidationError(
                    f"Audio asset '{asset_ref}' has license status '{lic_status}' (not cleared for commercial publishing). "
                    f"To use for internal testing/preview, set 'allow_review_audio': true in the manifest."
                )
            warning_issued = True

        return {
            "asset_id": asset_id,
            "file_path": abs_path,
            "filename": os.path.basename(abs_path),
            "license_status": lic_status,
            "is_preview_only": lic_status in preview_allowed,
            "licensing_warning": warning_issued
        }

    def validate_manifest(self, manifest: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes complete preflight verification.
        Returns a normalized timeline execution plan.
        """
        errors: List[str] = []
        warnings: List[str] = []

        # 1. Essential Fields
        project = manifest.get("project")
        if not project:
            errors.append("Manifest missing required field: 'project'")

        content_id = manifest.get("content_id")
        if not content_id:
            errors.append("Manifest missing required field: 'content_id'")

        # 2. Output Profile
        output_profile = manifest.get("output_profile", "instagram_reel")
        profile_spec = self.video_profiles.get(output_profile)
        if not profile_spec:
            # Fallback to defaults
            profile_spec = {
                "width": 1080,
                "height": 1920,
                "fps": 30.0,
                "min_duration": 3.0,
                "max_duration": 90.0,
                "safe_areas": {"top_px": 220, "bottom_px": 280, "left_px": 60, "right_px": 120}
            }
            warnings.append(f"Output profile '{output_profile}' not in video_profiles.json; using vertical 1080x1920 default.")

        # 3. Canvas Specification
        canvas = manifest.get("canvas", {})
        canvas_width = canvas.get("width", profile_spec.get("width", 1080))
        canvas_height = canvas.get("height", profile_spec.get("height", 1920))
        canvas_fps = float(canvas.get("fps", profile_spec.get("fps", 30.0)))
        expected_duration = float(canvas.get("duration_seconds", 0.0))

        # 4. Scenes & Timeline Validation
        scenes = manifest.get("timeline") or manifest.get("scenes") or []
        if not scenes:
            errors.append("Manifest timeline contains no scenes or shots.")

        resolved_scenes = []
        calculated_duration = 0.0
        allow_review_audio = manifest.get("allow_review_audio", False)

        for idx, scene in enumerate(scenes):
            scene_id = scene.get("scene_id", f"scene_{idx+1:02d}")
            asset_ref = scene.get("asset_id") or scene.get("source_file")
            if not asset_ref:
                errors.append(f"Scene '{scene_id}' has no asset reference ('asset_id' or 'source_file').")
                continue

            try:
                media_meta = self.resolve_media_asset(asset_ref, project)
            except Exception as e:
                errors.append(f"Scene '{scene_id}': {e}")
                continue

            source_in = float(scene.get("source_in", 0.0))
            scene_dur = float(scene.get("duration", 0.0))
            source_out = float(scene.get("source_out", source_in + scene_dur))

            if scene_dur <= 0:
                scene_dur = source_out - source_in
            if scene_dur <= 0:
                errors.append(f"Scene '{scene_id}': duration must be greater than zero.")

            # Bounds checking
            if source_in < 0:
                errors.append(f"Scene '{scene_id}': source_in ({source_in}) cannot be negative.")
            if source_out > media_meta["duration"] + 0.1:
                errors.append(
                    f"Scene '{scene_id}': source_out ({source_out:.2f}s) exceeds media duration ({media_meta['duration']:.2f}s)."
                )

            # Fit mode
            fit_mode = scene.get("fit_mode", "contain")
            if fit_mode not in ("contain", "cover", "stretch"):
                fit_mode = "contain"

            # Overlays in scene
            overlays = scene.get("overlays", [])
            for ov in overlays:
                ov_text = ov.get("text") or ov.get("title")
                if not ov_text and ov.get("type") != "image":
                    errors.append(f"Scene '{scene_id}' overlay missing text/title content.")

            resolved_scenes.append({
                "scene_id": scene_id,
                "asset_id": media_meta["asset_id"],
                "file_path": media_meta["file_path"],
                "source_in": source_in,
                "source_out": source_out,
                "duration": scene_dur,
                "fit_mode": fit_mode,
                "overlays": overlays,
                "timeline_start": calculated_duration,
                "timeline_end": calculated_duration + scene_dur
            })
            calculated_duration += scene_dur

        # Total duration consistency check
        if expected_duration > 0 and abs(expected_duration - calculated_duration) > 0.2:
            warnings.append(
                f"Canvas expected duration ({expected_duration:.2f}s) differs from sum of scenes ({calculated_duration:.2f}s). "
                f"Timeline total will be {calculated_duration:.2f}s."
            )
        total_duration = calculated_duration if calculated_duration > 0 else expected_duration

        # 5. Audio Track Validation
        audio_spec = manifest.get("audio", {})
        resolved_audio: Dict[str, Any] = {
            "music": None,
            "voiceover": None,
            "sound_effects": [],
            "master_loudness": audio_spec.get("master_loudness_target", -14.0)
        }

        # Music
        music_cfg = audio_spec.get("music") or audio_spec.get("bgm")
        if music_cfg:
            music_ref = music_cfg.get("asset_id") or music_cfg.get("file_path") or audio_spec.get("music_asset_id")
            if music_ref:
                try:
                    music_resolved = self.resolve_audio_asset(music_ref, allow_review_audio)
                    resolved_audio["music"] = {
                        **music_resolved,
                        "volume": float(music_cfg.get("volume", 0.25)),
                        "start_time": float(music_cfg.get("start_time", 0.0)),
                        "fade_in": float(music_cfg.get("fade_in", 0.5)),
                        "fade_out": float(music_cfg.get("fade_out", 0.8))
                    }
                    if music_resolved.get("licensing_warning"):
                        warnings.append(
                            f"Music '{music_resolved['filename']}' is marked NEEDS_REVIEW. Permitted for internal preview only."
                        )
                except Exception as e:
                    errors.append(f"Audio Music error: {e}")

        # Voiceover
        vo_cfg = audio_spec.get("voiceover") or audio_spec.get("vo")
        if vo_cfg:
            vo_text = vo_cfg.get("text") or audio_spec.get("voiceover_text")
            vo_ref = vo_cfg.get("asset_id") or vo_cfg.get("file_path")
            resolved_audio["voiceover"] = {
                "text": vo_text,
                "asset_id": vo_ref,
                "volume": float(vo_cfg.get("volume", 1.0)),
                "ducking": bool(vo_cfg.get("ducking", True)),
                "duck_level_db": float(vo_cfg.get("duck_level_db", -18.0)),
                "rate": int(vo_cfg.get("rate", 0))
            }

        # Sound effects
        sfx_list = audio_spec.get("sound_effects", [])
        for sfx in sfx_list:
            sfx_ref = sfx.get("asset_id") or sfx.get("file_path")
            if sfx_ref:
                try:
                    sfx_resolved = self.resolve_audio_asset(sfx_ref, allow_review_audio=True)
                    resolved_audio["sound_effects"].append({
                        **sfx_resolved,
                        "timeline_start": float(sfx.get("timeline_start", 0.0)),
                        "volume": float(sfx.get("volume", 0.8))
                    })
                except Exception as e:
                    warnings.append(f"Warning: SFX '{sfx_ref}' skipped: {e}")

        # Final Evaluation
        if errors:
            raise PreflightValidationError(
                f"Manifest preflight validation failed with {len(errors)} error(s):\n" +
                "\n".join(f"  • {err}" for err in errors)
            )

        return {
            "project": project,
            "campaign": manifest.get("campaign", "default"),
            "content_id": content_id,
            "output_profile": output_profile,
            "renderer": manifest.get("renderer", "ffmpeg"),
            "canvas": {
                "width": canvas_width,
                "height": canvas_height,
                "fps": canvas_fps,
                "duration_seconds": total_duration
            },
            "scenes": resolved_scenes,
            "audio": resolved_audio,
            "warnings": warnings,
            "is_preview_licensed": any(
                resolved_audio["music"].get("is_preview_only") for _ in [1] if resolved_audio["music"]
            )
        }
