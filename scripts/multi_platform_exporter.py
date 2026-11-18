"""
multi_platform_exporter.py — Phase 4 Multi-Platform Export & Adaptation Engine
(Post-Phase-4 Shared Rendering Profile & Storage Deduplication Architecture)

Clean 4-layer separation:
  1. Platform destination profile  (config/production/export_profiles.json)
  2. Physical rendering profile    (config/production/render_profiles.json)
  3. Generated video artifact      (artifacts/<render_profile_id>/<content_id>_<render_profile_id>.mp4)
  4. Platform validation & delivery record (platform_exports/<platform_id>/delivery_record.json)

Generates each unique physical MP4 artifact ONCE per unique full fingerprint
(master SHA-256 + manifest hash + render profile hash + source assets + overlay/audio/reframe config),
while running independent 18-point platform validation and maintaining separate platform delivery records.
"""

import os
import sys
import json
import time
import uuid
import shutil
import hashlib
import argparse
import datetime
import subprocess
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, Any, List, Optional, Tuple

WORKSPACE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(WORKSPACE_ROOT, "scripts"))

from media_engine import get_ffmpeg_cmd, inspect_media
from reframing_engine import ReframingEngine, ReframeStrategy
from export_validator import ExportValidator
from export_preview_generator import ExportPreviewGenerator

RENDER_PROFILES_PATH = os.path.join(WORKSPACE_ROOT, "config", "production", "render_profiles.json")
EXPORT_PROFILES_PATH = os.path.join(WORKSPACE_ROOT, "config", "production", "export_profiles.json")
SAFE_ZONES_PATH = os.path.join(WORKSPACE_ROOT, "config", "production", "safe_zones.json")
EXPORT_JOBS_DIR = os.path.join(WORKSPACE_ROOT, "data", "export_jobs")


def _sha256_file(path: str, chunk_size: int = 1024 * 1024) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def _sha256_dict(data: Any) -> str:
    raw = json.dumps(data, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _extract_manifest_fingerprint_components(manifest: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Extracts source asset/version info plus overlay and audio config from a manifest."""
    if not manifest:
        return {
            "source_assets": [],
            "overlays": [],
            "audio": None,
            "manifest_version": None,
        }
    scenes = manifest.get("timeline") or manifest.get("scenes") or []
    source_assets = [
        {
            "scene_id": s.get("scene_id"),
            "asset_id": s.get("asset_id"),
            "source_file": s.get("source_file"),
            "source_in": s.get("source_in"),
            "source_out": s.get("source_out"),
            "duration": s.get("duration"),
        }
        for s in scenes
    ]
    overlays = [
        {"scene_id": s.get("scene_id"), "overlays": s.get("overlays", [])}
        for s in scenes
        if s.get("overlays")
    ]
    return {
        "source_assets": source_assets,
        "overlays": overlays,
        "audio": manifest.get("audio"),
        "manifest_version": manifest.get("version") or manifest.get("schema_version"),
    }


def _compute_artifact_fingerprint(
    master_sha256: str,
    render_profile_spec: Dict[str, Any],
    reframe_plan: Dict[str, Any],
    manifest_sha256: Optional[str] = None,
    manifest: Optional[Dict[str, Any]] = None,
    master_info: Optional[Dict[str, Any]] = None,
    custom_layout: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Computes a reliable physical artifact fingerprint from:
      1. Master video SHA-256
      2. Production manifest hash
      3. Physical rendering profile configuration hash
      4. Source asset / version information
      5. Relevant overlay, audio, and reframing configuration
    Never assumes matching resolution alone means two exports are identical.
    """
    render_profile_hash = _sha256_dict(render_profile_spec)[:16]
    manifest_components = _extract_manifest_fingerprint_components(manifest)
    overlay_audio_hash = _sha256_dict({
        "overlays": manifest_components["overlays"],
        "audio": manifest_components["audio"],
        "reframe_strategy": reframe_plan.get("strategy"),
        "focal_point": reframe_plan.get("focal_point"),
        "custom_layout": custom_layout,
        "background_color": reframe_plan.get("background_color"),
    })[:16]
    source_asset_hash = _sha256_dict({
        "manifest_sources": manifest_components["source_assets"],
        "manifest_version": manifest_components["manifest_version"],
        "master_dims": [master_info.get("width"), master_info.get("height")] if master_info else None,
        "master_fps": master_info.get("fps") if master_info else None,
    })[:16]

    combined_payload = {
        "master_sha256": master_sha256,
        "manifest_sha256": manifest_sha256,
        "render_profile_hash": render_profile_hash,
        "source_asset_hash": source_asset_hash,
        "overlay_audio_reframe_hash": overlay_audio_hash,
    }
    artifact_fingerprint = _sha256_dict(combined_payload)[:20]

    return {
        "artifact_fingerprint": artifact_fingerprint,
        "components": combined_payload,
    }


class MultiPlatformExporter:
    """Orchestrator for deduplicated, shared-artifact, independently validated multi-platform exports."""

    def __init__(
        self,
        profiles_path: str = EXPORT_PROFILES_PATH,
        render_profiles_path: str = RENDER_PROFILES_PATH,
        safe_zones_path: str = SAFE_ZONES_PATH,
    ):
        self.profiles_path = profiles_path
        self.render_profiles_path = render_profiles_path
        self.safe_zones_path = safe_zones_path

        with open(self.render_profiles_path, "r", encoding="utf-8") as f:
            self.render_profiles_cfg = json.load(f)
        self.render_profiles: Dict[str, Dict[str, Any]] = self.render_profiles_cfg.get("render_profiles", {})

        with open(self.profiles_path, "r", encoding="utf-8") as f:
            self.profiles_cfg = json.load(f)
        self.platform_destinations: Dict[str, Dict[str, Any]] = self.profiles_cfg.get("profiles", {})
        self.project_bg_colors: Dict[str, str] = self.profiles_cfg.get("project_background_colors", {})

        # Backwards-compatible resolved profile view (merges physical render profile + destination metadata)
        self.profiles: Dict[str, Dict[str, Any]] = {}
        for pid, dest in self.platform_destinations.items():
            self.profiles[pid] = self._resolve_effective_profile(pid, dest)

        with open(self.safe_zones_path, "r", encoding="utf-8") as f:
            self.safe_zones_cfg = json.load(f)

        self.reframing_engine = ReframingEngine(project_bg_colors=self.project_bg_colors)
        self.validator = ExportValidator(safe_zones_config=self.safe_zones_cfg)
        self.preview_gen = ExportPreviewGenerator(safe_zones_config=self.safe_zones_cfg)

        os.makedirs(EXPORT_JOBS_DIR, exist_ok=True)

    def _resolve_effective_profile(
        self,
        profile_id: str,
        dest_spec: Dict[str, Any],
        render_profile_override: Optional[str] = None,
    ) -> Dict[str, Any]:
        rp_id = render_profile_override or dest_spec.get("render_profile_id")
        if rp_id:
            if rp_id not in self.render_profiles:
                raise ValueError(f"Platform profile '{profile_id}' references unknown render profile '{rp_id}'.")
            merged = dict(self.render_profiles[rp_id])
            merged.update(dest_spec)
            merged["render_profile_id"] = rp_id
            return merged
        return dict(dest_spec)

    def list_profiles(self) -> List[Dict[str, Any]]:
        """Returns resolved platform destination profiles."""
        return list(self.profiles.values())

    def list_render_profiles(self) -> List[Dict[str, Any]]:
        """Returns physical rendering profiles."""
        return list(self.render_profiles.values())

    def get_render_profile(self, render_profile_id: str) -> Dict[str, Any]:
        if render_profile_id not in self.render_profiles:
            avail = ", ".join(sorted(self.render_profiles.keys()))
            raise ValueError(f"Unknown render profile '{render_profile_id}'. Available: {avail}")
        return self.render_profiles[render_profile_id]

    def get_profile(self, profile_id: str, render_profile_override: Optional[str] = None) -> Dict[str, Any]:
        """Retrieves an effective platform profile by ID (optionally overriding its physical render profile)."""
        if profile_id not in self.platform_destinations:
            available = ", ".join(sorted(self.platform_destinations.keys()))
            raise ValueError(f"Unknown export profile '{profile_id}'. Available profiles: {available}")
        if render_profile_override:
            return self._resolve_effective_profile(profile_id, self.platform_destinations[profile_id], render_profile_override)
        return self.profiles[profile_id]

    def validate_master_input(self, master_path: str) -> Dict[str, Any]:
        """Confirms master video exists, is readable by FFprobe, and contains a valid video stream."""
        abs_master = os.path.abspath(master_path)
        if not os.path.exists(abs_master) or not os.path.isfile(abs_master):
            raise FileNotFoundError(f"Master video not found: {abs_master}")
        if os.path.getsize(abs_master) == 0:
            raise ValueError(f"Master video is empty (0 bytes): {abs_master}")

        try:
            info = inspect_media(abs_master)
        except Exception as e:
            raise ValueError(f"Master video failed FFprobe inspection (possibly corrupt): {e}")

        if not info.get("video_codec") or info.get("width", 0) <= 0 or info.get("height", 0) <= 0:
            raise ValueError(f"Master video lacks valid video stream: {abs_master}")
        if info.get("duration_seconds", 0.0) <= 0.1:
            raise ValueError(f"Master video has invalid duration ({info.get('duration_seconds')}s): {abs_master}")

        return info

    def _resolve_artifact_filepath(
        self,
        artifact_dir: str,
        base_stem: str,
        artifact_fingerprint: str,
        force: bool,
    ) -> Tuple[str, str, str]:
        """
        Determines physical artifact output path respecting idempotency and existing-output protection.
        Returns: (target_mp4_path, action ['REUSE', 'WRITE', 'VERSIONED'], meta_path)
        """
        os.makedirs(artifact_dir, exist_ok=True)
        primary_mp4 = os.path.join(artifact_dir, f"{base_stem}.mp4")
        primary_meta = os.path.join(artifact_dir, f"{base_stem}.artifact_meta.json")

        if os.path.exists(primary_mp4):
            if os.path.exists(primary_meta) and not force:
                try:
                    with open(primary_meta, "r", encoding="utf-8") as f:
                        meta = json.load(f)
                    if meta.get("artifact_fingerprint") == artifact_fingerprint and meta.get("artifact_valid"):
                        return primary_mp4, "REUSE", primary_meta
                except Exception:
                    pass

            if force:
                return primary_mp4, "WRITE", primary_meta

            # Protect existing non-matching file: never overwrite without --force
            ver = 2
            while True:
                cand_mp4 = os.path.join(artifact_dir, f"{base_stem}_v{ver}.mp4")
                cand_meta = os.path.join(artifact_dir, f"{base_stem}_v{ver}.artifact_meta.json")
                if not os.path.exists(cand_mp4):
                    return cand_mp4, "VERSIONED", cand_meta
                if os.path.exists(cand_meta):
                    try:
                        with open(cand_meta, "r", encoding="utf-8") as f:
                            cmeta = json.load(f)
                        if cmeta.get("artifact_fingerprint") == artifact_fingerprint and cmeta.get("artifact_valid"):
                            return cand_mp4, "REUSE", cand_meta
                    except Exception:
                        pass
                ver += 1

        return primary_mp4, "WRITE", primary_meta

    def _render_physical_artifact(
        self,
        master_path: str,
        master_info: Dict[str, Any],
        master_sha256: str,
        render_profile_spec: Dict[str, Any],
        reframe_plan: Dict[str, Any],
        fp_info: Dict[str, Any],
        export_root: str,
        project_slug: str,
        content_id: str,
        force: bool = False,
    ) -> Dict[str, Any]:
        """
        Renders (or idempotently reuses) ONE physical MP4 artifact for a unique artifact_fingerprint.
        """
        t0 = time.time()
        rp_id = render_profile_spec["render_profile_id"]
        fingerprint = fp_info["artifact_fingerprint"]

        artifact_dir = os.path.join(export_root, "artifacts", rp_id)
        logs_dir = os.path.join(export_root, "reports", "export_logs")
        os.makedirs(artifact_dir, exist_ok=True)
        os.makedirs(logs_dir, exist_ok=True)

        base_stem = f"{content_id}_{rp_id}"
        target_mp4, action, meta_path = self._resolve_artifact_filepath(
            artifact_dir=artifact_dir,
            base_stem=base_stem,
            artifact_fingerprint=fingerprint,
            force=force,
        )
        log_path = os.path.join(logs_dir, f"{rp_id}_ffmpeg.log")

        # Idempotent reuse verification: verify file still exists & opens cleanly via FFprobe
        if action == "REUSE":
            try:
                chk_info = inspect_media(target_mp4)
                if chk_info.get("width") == render_profile_spec["width"] and chk_info.get("height") == render_profile_spec["height"]:
                    return {
                        "render_profile_id": rp_id,
                        "artifact_fingerprint": fingerprint,
                        "fingerprint_components": fp_info["components"],
                        "artifact_path": target_mp4,
                        "artifact_sha256": _sha256_file(target_mp4),
                        "artifact_size_bytes": os.path.getsize(target_mp4),
                        "status": "REUSED_VALID",
                        "action": "REUSE",
                        "reframe_plan": reframe_plan,
                        "elapsed_seconds": round(time.time() - t0, 2),
                        "log_path": log_path if os.path.exists(log_path) else None,
                        "error": None,
                    }
            except Exception:
                action = "WRITE"

        ffmpeg_bin = get_ffmpeg_cmd()
        has_audio = bool(master_info.get("audio_codec"))
        audio_req = bool(render_profile_spec.get("audio_required", True))

        temp_mp4 = target_mp4 + ".in_progress.mp4"
        cmd = list(ffmpeg_bin) + ["-y", "-i", os.path.abspath(master_path)]

        if not has_audio and audio_req:
            cmd.extend([
                "-f", "lavfi", "-i",
                f"anullsrc=channel_layout=stereo:sample_rate={render_profile_spec['audio_sample_rate']}"
            ])

        if reframe_plan["uses_filter_complex"]:
            cmd.extend(["-filter_complex", reframe_plan["filter_complex"]])
            cmd.extend(["-map", reframe_plan["video_map"]])
        else:
            cmd.extend(["-vf", reframe_plan["vf"]])
            cmd.extend(["-map", "0:v:0"])

        if has_audio:
            cmd.extend(["-map", "0:a:0"])
        elif audio_req:
            cmd.extend(["-map", "1:a:0", "-shortest"])

        cmd.extend([
            "-c:v", render_profile_spec.get("video_codec", "libx264"),
            "-profile:v", render_profile_spec.get("video_profile", "high"),
            "-level:v", str(render_profile_spec.get("video_level", "4.1")),
            "-crf", str(render_profile_spec.get("crf", 21)),
            "-preset", render_profile_spec.get("preset", "fast"),
            "-maxrate", f"{render_profile_spec.get('max_video_bitrate_kbps', 5500)}k",
            "-bufsize", f"{render_profile_spec.get('bufsize_kbps', 11000)}k",
            "-pix_fmt", render_profile_spec.get("pixel_format", "yuv420p"),
        ])

        if has_audio or audio_req:
            cmd.extend([
                "-c:a", render_profile_spec.get("audio_codec", "aac"),
                "-b:a", render_profile_spec.get("audio_bitrate", "160k"),
                "-ar", str(render_profile_spec.get("audio_sample_rate", 48000)),
                "-ac", str(render_profile_spec.get("audio_channels", 2)),
            ])

        cmd.extend(["-movflags", render_profile_spec.get("movflags", "+faststart"), temp_mp4])

        res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
        elapsed = round(time.time() - t0, 2)

        with open(log_path, "w", encoding="utf-8") as lf:
            lf.write(f"Render Profile: {rp_id}\n")
            lf.write(f"Artifact Fingerprint: {fingerprint}\n")
            lf.write(f"Timestamp: {datetime.datetime.now().isoformat()}\n")
            lf.write(f"Command: {' '.join(cmd)}\n")
            lf.write(f"Exit Code: {res.returncode}\n")
            lf.write(f"Elapsed: {elapsed}s\n")
            lf.write("\n--- STDOUT ---\n")
            lf.write(res.stdout or "")
            lf.write("\n--- STDERR ---\n")
            lf.write(res.stderr or "")

        if res.returncode != 0 or not os.path.exists(temp_mp4):
            if os.path.exists(temp_mp4):
                try:
                    os.remove(temp_mp4)
                except OSError:
                    pass
            return {
                "render_profile_id": rp_id,
                "artifact_fingerprint": fingerprint,
                "fingerprint_components": fp_info["components"],
                "artifact_path": None,
                "artifact_sha256": None,
                "artifact_size_bytes": 0,
                "status": "FAILED",
                "action": action,
                "reframe_plan": reframe_plan,
                "elapsed_seconds": elapsed,
                "log_path": log_path,
                "error": f"FFmpeg exited with code {res.returncode}. See log: {log_path}",
            }

        os.replace(temp_mp4, target_mp4)
        art_sha = _sha256_file(target_mp4)
        art_size = os.path.getsize(target_mp4)

        meta_record = {
            "render_profile_id": rp_id,
            "content_id": content_id,
            "project": project_slug,
            "artifact_fingerprint": fingerprint,
            "fingerprint_components": fp_info["components"],
            "artifact_path": target_mp4,
            "artifact_sha256": art_sha,
            "artifact_size_bytes": art_size,
            "master_path": os.path.abspath(master_path),
            "master_sha256": master_sha256,
            "reframe_strategy": reframe_plan["strategy"],
            "artifact_valid": True,
            "generated_at": datetime.datetime.now().isoformat(),
        }
        with open(meta_path, "w", encoding="utf-8") as mf:
            json.dump(meta_record, mf, indent=2)

        return {
            "render_profile_id": rp_id,
            "artifact_fingerprint": fingerprint,
            "fingerprint_components": fp_info["components"],
            "artifact_path": target_mp4,
            "artifact_sha256": art_sha,
            "artifact_size_bytes": art_size,
            "status": "RENDERED",
            "action": action,
            "reframe_plan": reframe_plan,
            "elapsed_seconds": elapsed,
            "log_path": log_path,
            "error": None,
        }

    def export_master(
        self,
        master_path: str,
        profile_ids: List[str],
        manifest_path: Optional[str] = None,
        project_slug: Optional[str] = None,
        campaign_slug: Optional[str] = None,
        content_id: Optional[str] = None,
        output_root: Optional[str] = None,
        reframe_strategy: Optional[str] = None,
        focal_point: Optional[Tuple[float, float]] = None,
        custom_layout: Optional[Dict[str, Any]] = None,
        profile_render_overrides: Optional[Dict[str, str]] = None,
        max_workers: int = 1,
        force: bool = False,
        job_id: Optional[str] = None,
        existing_results: Optional[Dict[str, Dict[str, Any]]] = None,
        generate_previews: bool = True,
    ) -> Dict[str, Any]:
        """
        Exports an approved master video to one or more platform destinations using
        deduplicated physical rendering profiles and independent platform validation & delivery records.
        """
        job_start = time.time()
        overrides = profile_render_overrides or {}

        # 1. Validate requested destination profiles upfront
        if not profile_ids:
            raise ValueError("At least one target profile must be specified.")
        effective_profiles: Dict[str, Dict[str, Any]] = {}
        for pid in profile_ids:
            effective_profiles[pid] = self.get_profile(pid, render_profile_override=overrides.get(pid))

        # 2. Validate master video
        abs_master = os.path.abspath(master_path)
        master_info = self.validate_master_input(abs_master)
        master_sha = _sha256_file(abs_master)

        # 3. Load optional manifest
        manifest = None
        manifest_sha = None
        abs_manifest = None
        if manifest_path:
            abs_manifest = os.path.abspath(manifest_path)
            if not os.path.exists(abs_manifest):
                raise FileNotFoundError(f"Manifest not found: {abs_manifest}")
            with open(abs_manifest, "r", encoding="utf-8") as f:
                manifest = json.load(f)
            manifest_sha = _sha256_file(abs_manifest)

        proj = project_slug or (manifest.get("project") if manifest else None) or "general"
        camp = campaign_slug or (manifest.get("campaign") if manifest else None) or "multi-platform"
        cid = content_id or (manifest.get("content_id") if manifest else None) or os.path.splitext(os.path.basename(abs_master))[0]

        export_root = os.path.abspath(
            output_root or os.path.join(WORKSPACE_ROOT, "outputs", proj, camp, cid)
        )
        master_dir = os.path.join(export_root, "master")
        previews_dir = os.path.join(export_root, "previews")
        reports_dir = os.path.join(export_root, "reports")
        os.makedirs(master_dir, exist_ok=True)
        os.makedirs(previews_dir, exist_ok=True)
        os.makedirs(reports_dir, exist_ok=True)

        # Record non-destructive master reference
        with open(os.path.join(master_dir, "master_reference.json"), "w", encoding="utf-8") as f:
            json.dump({
                "source_master_path": abs_master,
                "sha256": master_sha,
                "width": master_info["width"],
                "height": master_info["height"],
                "fps": master_info["fps"],
                "duration_seconds": master_info["duration_seconds"],
                "video_codec": master_info["video_codec"],
                "audio_codec": master_info["audio_codec"],
                "recorded_at": datetime.datetime.now().isoformat(),
            }, f, indent=2)

        if manifest and abs_manifest:
            dst_manifest = os.path.join(master_dir, "production_manifest.json")
            if os.path.abspath(dst_manifest) != abs_manifest:
                shutil.copy2(abs_manifest, dst_manifest)

        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        export_job_id = job_id or f"EXP_{proj.upper()}_{cid}_{ts}_{uuid.uuid4().hex[:6].upper()}"

        # 4. Plan physical artifacts & deduplicate by full artifact_fingerprint
        sample_sec = min(1.0, max(0.0, master_info["duration_seconds"] * 0.15))
        destination_plans: Dict[str, Dict[str, Any]] = {}
        unique_artifact_tasks: Dict[str, Dict[str, Any]] = {}  # fingerprint -> render task
        fingerprint_to_platforms: Dict[str, List[str]] = {}

        for pid in profile_ids:
            eff_spec = effective_profiles[pid]
            rp_id = eff_spec["render_profile_id"]
            rp_spec = self.get_render_profile(rp_id)

            reframe_plan = self.reframing_engine.build_filter_plan(
                video_path=abs_master,
                src_width=master_info["width"],
                src_height=master_info["height"],
                target_width=rp_spec["width"],
                target_height=rp_spec["height"],
                target_fps=rp_spec["fps"],
                project_slug=proj,
                strategy=reframe_strategy,
                focal_point=focal_point,
                custom_layout=custom_layout,
                sample_sec=sample_sec,
            )

            fp_info = _compute_artifact_fingerprint(
                master_sha256=master_sha,
                render_profile_spec=rp_spec,
                reframe_plan=reframe_plan,
                manifest_sha256=manifest_sha,
                manifest=manifest,
                master_info=master_info,
                custom_layout=custom_layout,
            )
            fp = fp_info["artifact_fingerprint"]

            destination_plans[pid] = {
                "profile_id": pid,
                "effective_spec": eff_spec,
                "render_profile_id": rp_id,
                "render_profile_spec": rp_spec,
                "reframe_plan": reframe_plan,
                "fp_info": fp_info,
                "artifact_fingerprint": fp,
            }

            fingerprint_to_platforms.setdefault(fp, []).append(pid)
            if fp not in unique_artifact_tasks:
                unique_artifact_tasks[fp] = {
                    "render_profile_spec": rp_spec,
                    "reframe_plan": reframe_plan,
                    "fp_info": fp_info,
                }

        # 5. Render each UNIQUE physical artifact once (bounded concurrency <= 2)
        safe_workers = max(1, min(2, int(max_workers)))
        rendered_artifacts: Dict[str, Dict[str, Any]] = {}

        if safe_workers == 1 or len(unique_artifact_tasks) == 1:
            for fp, task in unique_artifact_tasks.items():
                rendered_artifacts[fp] = self._render_physical_artifact(
                    master_path=abs_master,
                    master_info=master_info,
                    master_sha256=master_sha,
                    render_profile_spec=task["render_profile_spec"],
                    reframe_plan=task["reframe_plan"],
                    fp_info=task["fp_info"],
                    export_root=export_root,
                    project_slug=proj,
                    content_id=cid,
                    force=force,
                )
        else:
            with ThreadPoolExecutor(max_workers=safe_workers) as pool:
                fmap = {
                    pool.submit(
                        self._render_physical_artifact,
                        abs_master,
                        master_info,
                        master_sha,
                        task["render_profile_spec"],
                        task["reframe_plan"],
                        task["fp_info"],
                        export_root,
                        proj,
                        cid,
                        force,
                    ): fp
                    for fp, task in unique_artifact_tasks.items()
                }
                for fut in as_completed(fmap):
                    fp = fmap[fut]
                    try:
                        rendered_artifacts[fp] = fut.result()
                    except Exception as e:
                        rendered_artifacts[fp] = {
                            "artifact_fingerprint": fp,
                            "status": "FAILED",
                            "artifact_path": None,
                            "error": str(e),
                        }

        # 6. Independent Platform Validation & Delivery Records (never merged!)
        results: Dict[str, Dict[str, Any]] = dict(existing_results or {})
        artifact_base_previews: Dict[str, str] = {}
        preview_artifacts: Dict[str, Any] = {}

        sample_t = min(1.0, max(0.0, master_info["duration_seconds"] * 0.12))
        if generate_previews:
            master_preview_png = os.path.join(previews_dir, "master_preview.png")
            self.preview_gen.extract_frame(abs_master, master_preview_png, timestamp_sec=sample_t)
            preview_artifacts["master_preview"] = master_preview_png

            # Extract ONE shared base preview frame per unique rendered artifact (zero duplicate preview PNGs!)
            for fp, art in rendered_artifacts.items():
                ap = art.get("artifact_path")
                if ap and os.path.exists(ap):
                    rp_id = art["render_profile_id"]
                    base_prev = os.path.join(previews_dir, f"{rp_id}_preview.png")
                    if not os.path.exists(base_prev) or force:
                        self.preview_gen.extract_frame(ap, base_prev, timestamp_sec=sample_t)
                    artifact_base_previews[fp] = base_prev
                    preview_artifacts[f"{rp_id}_preview"] = base_prev

        for pid in profile_ids:
            dplan = destination_plans[pid]
            fp = dplan["artifact_fingerprint"]
            art = rendered_artifacts[fp]
            eff_spec = dplan["effective_spec"]
            rp_id = dplan["render_profile_id"]
            reframe_plan = dplan["reframe_plan"]
            siblings = fingerprint_to_platforms.get(fp, [pid])
            is_shared = len(siblings) > 1

            platform_dir = os.path.join(export_root, "platform_exports", pid)
            os.makedirs(platform_dir, exist_ok=True)
            delivery_record_path = os.path.join(platform_dir, "delivery_record.json")

            if art["status"] == "FAILED" or not art.get("artifact_path"):
                results[pid] = {
                    "profile_id": pid,
                    "render_profile_id": rp_id,
                    "status": "FAILED",
                    "action": art.get("action"),
                    "output_path": None,
                    "artifact_path": None,
                    "artifact_fingerprint": fp,
                    "shared_artifact": is_shared,
                    "shared_with_platforms": [s for s in siblings if s != pid],
                    "delivery_record_path": delivery_record_path,
                    "reframe_plan": reframe_plan,
                    "validation": None,
                    "elapsed_seconds": art.get("elapsed_seconds", 0.0),
                    "log_path": art.get("log_path"),
                    "requires_manual_review": True,
                    "error": art.get("error"),
                }
                continue

            # Run INDEPENDENT 18-point technical validation for THIS platform destination
            val = self.validator.validate_export(
                export_path=art["artifact_path"],
                profile_spec=eff_spec,
                master_info=master_info,
                reframe_plan=reframe_plan,
                manifest=manifest,
            )

            # Generate platform-specific safe-zone overlay from shared base preview
            sz_png = None
            if generate_previews and fp in artifact_base_previews:
                sz_png = os.path.join(previews_dir, f"{pid}_safe_zone.png")
                self.preview_gen.generate_safe_zone_overlay(artifact_base_previews[fp], pid, sz_png)
                preview_artifacts[f"{pid}_safe_zone"] = sz_png

            if art["status"] == "REUSED_VALID" and val["passed"]:
                dest_status = "REUSED_VALID"
            elif val["passed"]:
                dest_status = "VALIDATED"
            else:
                dest_status = "FAILED"

            sz_check = next((c for c in val["checks"] if c["name"] == "safe_zone_compliance"), {})

            delivery_record = {
                "platform_id": pid,
                "platform_name": eff_spec.get("display_name", pid),
                "platform": eff_spec.get("platform"),
                "project": proj,
                "campaign": camp,
                "content_id": cid,
                "render_profile_id": rp_id,
                "artifact_fingerprint": fp,
                "fingerprint_components": dplan["fp_info"]["components"],
                "artifact_path": art["artifact_path"],
                "artifact_sha256": art.get("artifact_sha256"),
                "artifact_size_bytes": art.get("artifact_size_bytes"),
                "shared_artifact": is_shared,
                "shared_with_platforms": [s for s in siblings if s != pid],
                "validation": {
                    "passed": val["passed"],
                    "score": f"{val['passed_count']}/{val['total_checks']}",
                    "warnings": val.get("warnings", []),
                    "validation_report_ref": os.path.join(reports_dir, "platform_validation.json"),
                },
                "safe_zone_validation": {
                    "safe_zone_profile": eff_spec.get("safe_zone_profile", pid),
                    "status": sz_check.get("status", "PASS"),
                    "details": sz_check.get("actual"),
                    "safe_zone_preview_path": sz_png,
                },
                "caption_and_hashtags": {
                    "caption": None,
                    "hashtags": eff_spec.get("default_hashtags", []),
                    "status": "AWAITING_PLATFORM_COPY_REVIEW",
                },
                "delivery_status": "STAGED_FOR_HUMAN_REVIEW" if val["passed"] else "BLOCKED_VALIDATION_FAILED",
                "publishing_reference": None,
                "platform_notes": eff_spec.get("spec_notes", ""),
                "requires_manual_review": reframe_plan.get("requires_manual_review", False) or (not val["passed"]),
                "updated_at": datetime.datetime.now().isoformat(),
            }
            with open(delivery_record_path, "w", encoding="utf-8") as df:
                json.dump(delivery_record, df, indent=2)

            results[pid] = {
                "profile_id": pid,
                "render_profile_id": rp_id,
                "status": dest_status,
                "action": art["action"],
                "output_path": art["artifact_path"],
                "artifact_path": art["artifact_path"],
                "artifact_fingerprint": fp,
                "shared_artifact": is_shared,
                "shared_with_platforms": [s for s in siblings if s != pid],
                "delivery_record_path": delivery_record_path,
                "reframe_plan": reframe_plan,
                "validation": val,
                "elapsed_seconds": art["elapsed_seconds"],
                "log_path": art.get("log_path"),
                "requires_manual_review": reframe_plan.get("requires_manual_review", False) or (not val["passed"]),
                "error": None if val["passed"] else f"Platform validation failed ({val['passed_count']}/{val['total_checks']} passed).",
            }

        # 7. Contact Sheet & Reframing Comparison (reusing deduplicated base previews)
        if generate_previews:
            contact_items = [{
                "label": "Approved Master",
                "preview_png": preview_artifacts["master_preview"],
                "specs_line": f"{master_info['width']}x{master_info['height']} | {master_info['fps']}fps | {master_info['duration_seconds']:.2f}s",
                "status": "MASTER",
            }]
            for pid, res in results.items():
                fp = res.get("artifact_fingerprint")
                base_prev = artifact_base_previews.get(fp)
                if base_prev and os.path.exists(base_prev):
                    mi = (res.get("validation") or {}).get("media_info") or {}
                    shared_tag = " [SHARED]" if res.get("shared_artifact") else ""
                    contact_items.append({
                        "label": self.profiles[pid]["display_name"].split(" (")[0] + shared_tag,
                        "preview_png": base_prev,
                        "specs_line": f"{mi.get('width', '?')}x{mi.get('height', '?')} | {res.get('render_profile_id', '')} | {mi.get('bitrate_kbps', '?')}kbps",
                        "status": res["status"],
                    })

            if "youtube_standard" in results and results["youtube_standard"].get("artifact_fingerprint") in artifact_base_previews:
                yt_res = results["youtube_standard"]
                yt_prev = artifact_base_previews[yt_res["artifact_fingerprint"]]
                reframe_cmp_png = os.path.join(previews_dir, "reframing_comparison_9x16_vs_16x9.png")
                self.preview_gen.generate_reframing_comparison(
                    master_preview_png=preview_artifacts["master_preview"],
                    adapted_preview_png=yt_prev,
                    output_png=reframe_cmp_png,
                    master_label=f"Master ({master_info['width']}x{master_info['height']})",
                    adapted_label=f"YouTube Standard (1920x1080 | {yt_res['reframe_plan']['strategy']})",
                    strategy_note=yt_res["reframe_plan"]["reason"],
                )
                preview_artifacts["reframing_comparison"] = reframe_cmp_png

            if len(contact_items) > 1:
                cs_png = os.path.join(previews_dir, "multi_platform_contact_sheet.png")
                self.preview_gen.generate_contact_sheet(
                    items=contact_items,
                    output_png=cs_png,
                    title=f"Multi-Platform Shared-Artifact Comparison — {proj} / {cid}",
                )
                preview_artifacts["contact_sheet"] = cs_png

        # 8. Storage Optimization Metrics & Structured Reports
        unique_artifact_paths: Dict[str, int] = {}
        unshared_equivalent_bytes = 0
        for pid, r in results.items():
            ap = r.get("artifact_path")
            if ap and os.path.exists(ap):
                sz = os.path.getsize(ap)
                unique_artifact_paths[ap] = sz
                unshared_equivalent_bytes += sz

        actual_video_bytes = sum(unique_artifact_paths.values())
        bytes_saved = max(0, unshared_equivalent_bytes - actual_video_bytes)
        pct_saved = round((bytes_saved / unshared_equivalent_bytes) * 100.0, 2) if unshared_equivalent_bytes > 0 else 0.0

        storage_summary = {
            "total_platform_destinations": len(results),
            "unique_physical_artifacts": len(unique_artifact_paths),
            "deduplicated_destination_references": max(0, len(results) - len(unique_artifact_paths)),
            "actual_video_storage_bytes": actual_video_bytes,
            "unshared_equivalent_bytes": unshared_equivalent_bytes,
            "bytes_saved": bytes_saved,
            "percent_saved": pct_saved,
        }

        all_ok = all(r["status"] in ("VALIDATED", "REUSED_VALID") for r in results.values())
        failed_profiles = [pid for pid, r in results.items() if r["status"] not in ("VALIDATED", "REUSED_VALID")]
        overall_status = "COMPLETED_VALIDATED" if all_ok else ("PARTIAL_FAILURE" if len(failed_profiles) < len(results) else "FAILED")

        tech_comparison = {
            "master": {
                "path": abs_master,
                "width": master_info["width"],
                "height": master_info["height"],
                "fps": master_info["fps"],
                "duration_seconds": master_info["duration_seconds"],
                "video_codec": master_info["video_codec"],
                "audio_codec": master_info["audio_codec"],
                "file_size_bytes": master_info["file_size_bytes"],
            },
            "storage_summary": storage_summary,
            "exports": {},
        }
        platform_validation = {}
        for pid, r in results.items():
            val = r.get("validation")
            platform_validation[pid] = val
            mi = val.get("media_info") if val else {}
            tech_comparison["exports"][pid] = {
                "status": r["status"],
                "render_profile_id": r.get("render_profile_id"),
                "artifact_fingerprint": r.get("artifact_fingerprint"),
                "shared_artifact": r.get("shared_artifact", False),
                "output_path": r.get("output_path"),
                "delivery_record_path": r.get("delivery_record_path"),
                "reframe_strategy": (r.get("reframe_plan") or {}).get("strategy"),
                "requires_manual_review": r.get("requires_manual_review", False),
                "width": mi.get("width"),
                "height": mi.get("height"),
                "fps": mi.get("fps"),
                "duration_seconds": mi.get("duration_seconds"),
                "video_codec": mi.get("video_codec"),
                "audio_codec": mi.get("audio_codec"),
                "audio_sample_rate": mi.get("audio_sample_rate"),
                "audio_channels": mi.get("audio_channels"),
                "bitrate_kbps": mi.get("bitrate_kbps"),
                "file_size_bytes": val.get("file_size_bytes") if val else 0,
                "validation_passed": val.get("passed") if val else False,
                "validation_score": f"{val.get('passed_count', 0)}/{val.get('total_checks', 18)}" if val else "0/18",
            }

        summary = {
            "export_job_id": export_job_id,
            "status": overall_status,
            "project": proj,
            "campaign": camp,
            "content_id": cid,
            "master_path": abs_master,
            "master_sha256": master_sha,
            "manifest_path": abs_manifest,
            "export_root": export_root,
            "requested_profiles": list(results.keys()),
            "failed_profiles": failed_profiles,
            "reframe_strategy_override": reframe_strategy,
            "focal_point_override": list(focal_point) if focal_point else None,
            "profile_render_overrides": overrides,
            "storage_summary": storage_summary,
            "artifacts": rendered_artifacts,
            "total_elapsed_seconds": round(time.time() - job_start, 2),
            "created_at": datetime.datetime.now().isoformat(),
            "previews": preview_artifacts,
            "results": results,
        }

        with open(os.path.join(reports_dir, "export_summary.json"), "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)
        with open(os.path.join(reports_dir, "platform_validation.json"), "w", encoding="utf-8") as f:
            json.dump(platform_validation, f, indent=2)
        with open(os.path.join(reports_dir, "technical_comparison.json"), "w", encoding="utf-8") as f:
            json.dump(tech_comparison, f, indent=2)

        job_store_path = os.path.join(EXPORT_JOBS_DIR, f"{export_job_id}.json")
        with open(job_store_path, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)

        return summary

    def load_job(self, export_job_id: str) -> Dict[str, Any]:
        path = os.path.join(EXPORT_JOBS_DIR, f"{export_job_id}.json")
        if not os.path.exists(path):
            raise FileNotFoundError(f"Export job not found: {export_job_id}")
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def retry_failed(self, export_job_id: str, force: bool = True) -> Dict[str, Any]:
        """Retries ONLY failed platform destinations in an existing job without touching validated ones."""
        job = self.load_job(export_job_id)
        failed = job.get("failed_profiles", [])
        if not failed:
            return job

        focal = tuple(job["focal_point_override"]) if job.get("focal_point_override") else None
        return self.export_master(
            master_path=job["master_path"],
            profile_ids=failed,
            manifest_path=job.get("manifest_path"),
            project_slug=job["project"],
            campaign_slug=job["campaign"],
            content_id=job["content_id"],
            output_root=job["export_root"],
            reframe_strategy=job.get("reframe_strategy_override"),
            focal_point=focal,
            profile_render_overrides=job.get("profile_render_overrides"),
            force=force,
            job_id=export_job_id,
            existing_results=job.get("results", {}),
        )

    def run_batch(self, batch_config_path: str, max_workers: int = 1) -> List[Dict[str, Any]]:
        with open(os.path.abspath(batch_config_path), "r", encoding="utf-8") as f:
            batch = json.load(f)

        items = batch.get("jobs", batch if isinstance(batch, list) else [])
        summaries = []
        for item in items:
            profiles = item.get("profiles") or list(self.profiles.keys())
            focal = tuple(item["focal_point"]) if item.get("focal_point") else None
            res = self.export_master(
                master_path=item["input"],
                profile_ids=profiles,
                manifest_path=item.get("manifest"),
                project_slug=item.get("project"),
                campaign_slug=item.get("campaign"),
                content_id=item.get("content_id"),
                output_root=item.get("output_root"),
                reframe_strategy=item.get("reframe_strategy"),
                focal_point=focal,
                profile_render_overrides=item.get("profile_render_overrides"),
                max_workers=max_workers,
                force=bool(item.get("force", False)),
            )
            summaries.append(res)
        return summaries


def _parse_focal_point(val: Optional[str]) -> Optional[Tuple[float, float]]:
    if not val:
        return None
    parts = [p.strip() for p in val.split(",")]
    if len(parts) != 2:
        raise ValueError("--focal-point must be formatted as 'x,y' (normalized 0.0..1.0), e.g. '0.5,0.4'")
    return (float(parts[0]), float(parts[1]))


def main():
    parser = argparse.ArgumentParser(
        description="Pyapiras Games Phase 4 — Shared-Artifact Multi-Platform Export Engine"
    )
    parser.add_argument("--list-profiles", action="store_true", help="List platform destination profiles and mapped physical render profiles")
    parser.add_argument("--input", help="Path to approved master MP4 video")
    parser.add_argument("--manifest", help="Optional path to source production manifest JSON")
    parser.add_argument("--project", help="Project slug override")
    parser.add_argument("--campaign", help="Campaign slug override")
    parser.add_argument("--content-id", help="Content ID override")
    parser.add_argument("--output-root", help="Explicit output directory root")
    parser.add_argument("--profiles", nargs="+", help="Target destination profile IDs")
    parser.add_argument("--all-profiles", action="store_true", help="Export to all configured platform destinations")
    parser.add_argument(
        "--reframe-strategy",
        choices=[s.value for s in ReframeStrategy],
        default=None,
        help="Optional reframing strategy override",
    )
    parser.add_argument("--focal-point", default=None, help="Manual focal point 'x,y' in [0.0, 1.0]")
    parser.add_argument("--max-workers", type=int, default=1, help="Parallel FFmpeg workers (1 or 2 max)")
    parser.add_argument("--force", action="store_true", help="Explicitly overwrite existing artifacts")
    parser.add_argument("--batch", help="Path to batch export JSON config")
    parser.add_argument("--job-id", help="Existing export job ID for status or retry")
    parser.add_argument("--status", action="store_true", help="Display status of --job-id")
    parser.add_argument("--retry-failed", action="store_true", help="Retry failed platform exports in --job-id")

    args = parser.parse_args()
    exporter = MultiPlatformExporter()

    if args.list_profiles:
        print("\nPhysical Rendering Profiles (config/production/render_profiles.json):")
        print("-" * 92)
        print(f"{'RENDER PROFILE ID':<24} | {'RESOLUTION':<12} | {'RATIO':<6} | {'FPS':<5} | {'CRF':<4} | {'DEFAULT REFRAME'}")
        print("-" * 92)
        for rp in exporter.list_render_profiles():
            print(
                f"{rp['render_profile_id']:<24} | {rp['width']}x{rp['height']:<7} | {rp['aspect_ratio']:<6} | "
                f"{rp['fps']:<5} | {rp['crf']:<4} | {rp['default_reframe_strategy']}"
            )
        print("\nPlatform Destination Profiles (config/production/export_profiles.json):")
        print("-" * 92)
        print(f"{'PLATFORM PROFILE':<20} | {'RENDER PROFILE':<24} | {'SAFE ZONE':<18} | {'MAX DUR'}")
        print("-" * 92)
        for p in exporter.list_profiles():
            print(
                f"{p['profile_id']:<20} | {p['render_profile_id']:<24} | "
                f"{p['safe_zone_profile']:<18} | {p['duration_max_seconds']:.0f}s"
            )
        print("")
        return

    if args.job_id and args.status:
        job = exporter.load_job(args.job_id)
        print(f"\nExport Job: {job['export_job_id']}")
        print(f"Status    : {job['status']}")
        print(f"Master    : {job['master_path']}")
        print(f"Output Dir: {job['export_root']}")
        ss = job.get("storage_summary", {})
        if ss:
            print(
                f"Storage   : {ss.get('unique_physical_artifacts')} unique MP4(s) serving "
                f"{ss.get('total_platform_destinations')} platform(s) "
                f"(saved {ss.get('bytes_saved', 0)/1024/1024:.2f} MB / {ss.get('percent_saved', 0)}%)"
            )
        for pid, r in job.get("results", {}).items():
            val = r.get("validation") or {}
            checks = f"{val.get('passed_count', 0)}/{val.get('total_checks', 18)}" if val else "N/A"
            shared = "SHARED" if r.get("shared_artifact") else "UNIQUE"
            print(f"  - {pid:<18}: {r['status']:<12} | {shared:<6} | checks={checks} | {r.get('artifact_path')}")
        print("")
        return

    if args.job_id and args.retry_failed:
        res = exporter.retry_failed(args.job_id)
        print(f"\nRetry Completed for {res['export_job_id']} -> Status: {res['status']}")
        sys.exit(0 if res["status"] == "COMPLETED_VALIDATED" else 1)

    if args.batch:
        summaries = exporter.run_batch(args.batch, max_workers=args.max_workers)
        ok_cnt = sum(1 for s in summaries if s["status"] == "COMPLETED_VALIDATED")
        print(f"\nBatch Export Complete: {ok_cnt}/{len(summaries)} jobs validated cleanly.")
        sys.exit(0 if ok_cnt == len(summaries) else 1)

    if not args.input:
        parser.print_help()
        sys.exit(1)

    target_profiles = list(exporter.profiles.keys()) if args.all_profiles else (args.profiles or [])
    if not target_profiles:
        print("Error: Specify --profiles <id ...> or --all-profiles.")
        sys.exit(1)

    focal = _parse_focal_point(args.focal_point)
    summary = exporter.export_master(
        master_path=args.input,
        profile_ids=target_profiles,
        manifest_path=args.manifest,
        project_slug=args.project,
        campaign_slug=args.campaign,
        content_id=args.content_id,
        output_root=args.output_root,
        reframe_strategy=args.reframe_strategy,
        focal_point=focal,
        max_workers=args.max_workers,
        force=args.force,
    )

    ss = summary["storage_summary"]
    print(f"\n==================================================================")
    print(f"  SHARED-ARTIFACT EXPORT SUMMARY: {summary['export_job_id']}")
    print(f"==================================================================")
    print(f"Status     : {summary['status']}")
    print(f"Output Dir : {summary['export_root']}")
    print(f"Total Time : {summary['total_elapsed_seconds']}s")
    print(
        f"Storage    : {ss['unique_physical_artifacts']} unique MP4(s) for {ss['total_platform_destinations']} platforms "
        f"| actual={ss['actual_video_storage_bytes']/1024/1024:.2f} MB vs unshared={ss['unshared_equivalent_bytes']/1024/1024:.2f} MB "
        f"(saved {ss['bytes_saved']/1024/1024:.2f} MB / {ss['percent_saved']}%)"
    )
    for pid, r in summary["results"].items():
        val = r.get("validation") or {}
        score = f"{val.get('passed_count', 0)}/{val.get('total_checks', 18)}" if val else "FAIL"
        shared = "SHARED" if r.get("shared_artifact") else "UNIQUE"
        print(f"  [{pid:<16}] {r['status']:<12} | {r.get('render_profile_id', ''):<20} | {shared:<6} | checks={score}")
    if summary.get("previews", {}).get("contact_sheet"):
        print(f"Contact Sheet: {summary['previews']['contact_sheet']}")
    print(f"==================================================================\n")

    sys.exit(0 if summary["status"] == "COMPLETED_VALIDATED" else 1)


if __name__ == "__main__":
    main()
