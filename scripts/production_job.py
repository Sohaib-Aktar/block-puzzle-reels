"""
production_job.py — Production Job Lifecycle and Context Manager
Manages job states, working directories, intermediate files, and execution metadata.
"""

import os
import sys
import json
import time
import uuid
import datetime
from enum import Enum
from typing import Dict, Any, Optional

WORKSPACE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class JobStatus(str, Enum):
    CREATED = "CREATED"
    VALIDATING = "VALIDATING"
    VALIDATION_FAILED = "VALIDATION_FAILED"
    READY_TO_RENDER = "READY_TO_RENDER"
    RENDERING = "RENDERING"
    RENDER_FAILED = "RENDER_FAILED"
    RENDERED = "RENDERED"
    TECHNICAL_VALIDATION = "TECHNICAL_VALIDATION"
    TECHNICAL_FAILED = "TECHNICAL_FAILED"
    AWAITING_CREATIVE_QC = "AWAITING_CREATIVE_QC"
    AWAITING_HUMAN_APPROVAL = "AWAITING_HUMAN_APPROVAL"
    APPROVED = "APPROVED"
    CANCELLED = "CANCELLED"


class ProductionJob:
    """Represents an isolated, auditable video production job."""

    def __init__(
        self,
        manifest_data: Dict[str, Any],
        manifest_path: Optional[str] = None,
        job_id: Optional[str] = None,
        keep_intermediate: bool = False
    ):
        self.manifest = manifest_data
        self.manifest_path = manifest_path
        self.keep_intermediate = keep_intermediate

        self.project = manifest_data.get("project", "unknown-project")
        self.campaign = manifest_data.get("campaign", "default-campaign")
        self.content_id = manifest_data.get("content_id", "UNTITLED")
        self.output_profile = manifest_data.get("output_profile", "instagram_reel")

        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        short_id = uuid.uuid4().hex[:6].upper()
        self.job_id = job_id or f"JOB_{self.project.upper()}_{self.content_id}_{ts}_{short_id}"

        # Establish isolated directories
        self.base_output_dir = os.path.join(
            WORKSPACE_ROOT, "outputs", self.project, self.campaign, self.content_id
        )
        self.intermediate_dir = os.path.join(self.base_output_dir, "intermediate")
        self.final_dir = os.path.join(self.base_output_dir, "final")
        self.logs_dir = os.path.join(self.base_output_dir, "logs")
        self.report_dir = os.path.join(self.base_output_dir, "report")

        os.makedirs(self.intermediate_dir, exist_ok=True)
        os.makedirs(self.final_dir, exist_ok=True)
        os.makedirs(self.logs_dir, exist_ok=True)
        os.makedirs(self.report_dir, exist_ok=True)

        self.status = JobStatus.CREATED
        self.created_at = datetime.datetime.now().isoformat()
        self.updated_at = self.created_at
        self.error_message: Optional[str] = None
        self.execution_log: list = []
        self.output_file: Optional[str] = None
        self.metrics: Dict[str, Any] = {
            "render_seconds": 0.0,
            "intermediate_files_count": 0,
            "final_file_size_bytes": 0
        }

        # Save initial state in data/production_jobs
        self.jobs_store_dir = os.path.join(WORKSPACE_ROOT, "data", "production_jobs")
        os.makedirs(self.jobs_store_dir, exist_ok=True)
        self.save_state()

    def set_status(self, status: JobStatus, message: Optional[str] = None):
        """Transition state with timestamp and audit message."""
        self.status = status
        self.updated_at = datetime.datetime.now().isoformat()
        if message:
            self.execution_log.append({
                "timestamp": self.updated_at,
                "status": self.status.value,
                "message": message
            })
            if "FAILED" in status.value or "ERROR" in status.value:
                self.error_message = message
        self.save_state()

    def add_log(self, message: str):
        """Log a production event."""
        self.execution_log.append({
            "timestamp": datetime.datetime.now().isoformat(),
            "status": self.status.value,
            "message": message
        })
        self.save_state()

    def get_intermediate_path(self, filename: str) -> str:
        """Returns a path inside the isolated intermediate folder."""
        return os.path.join(self.intermediate_dir, filename)

    def get_final_path(self, filename: str) -> str:
        """Returns the canonical path for final deliverables."""
        return os.path.join(self.final_dir, filename)

    def cleanup_intermediate(self):
        """Safely clean temporary intermediate files unless keep_intermediate is set."""
        if self.keep_intermediate:
            self.add_log(f"Intermediate files preserved per policy at {self.intermediate_dir}")
            return

        cleaned_count = 0
        if os.path.exists(self.intermediate_dir):
            for item in os.listdir(self.intermediate_dir):
                item_path = os.path.join(self.intermediate_dir, item)
                try:
                    if os.path.isfile(item_path):
                        os.remove(item_path)
                        cleaned_count += 1
                    elif os.path.isdir(item_path):
                        import shutil
                        shutil.rmtree(item_path)
                        cleaned_count += 1
                except Exception as e:
                    self.add_log(f"Warning: could not clean intermediate item {item_path}: {e}")
        self.add_log(f"Cleaned up {cleaned_count} intermediate artifacts.")

    def to_dict(self) -> Dict[str, Any]:
        """Serialize job state."""
        return {
            "job_id": self.job_id,
            "status": self.status.value,
            "project": self.project,
            "campaign": self.campaign,
            "content_id": self.content_id,
            "output_profile": self.output_profile,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "output_file": self.output_file,
            "error_message": self.error_message,
            "metrics": self.metrics,
            "manifest_path": self.manifest_path,
            "manifest": self.manifest,
            "execution_log": self.execution_log
        }

    def save_state(self):
        """Persist state to disk."""
        store_path = os.path.join(self.jobs_store_dir, f"{self.job_id}.json")
        with open(store_path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load(cls, job_id: str) -> "ProductionJob":
        """Load an existing job by ID."""
        store_path = os.path.join(WORKSPACE_ROOT, "data", "production_jobs", f"{job_id}.json")
        if not os.path.exists(store_path):
            raise FileNotFoundError(f"Production job not found: {job_id}")
        with open(store_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        job = cls(
            manifest_data=data["manifest"],
            manifest_path=data.get("manifest_path"),
            job_id=data["job_id"]
        )
        job.status = JobStatus(data["status"])
        job.created_at = data["created_at"]
        job.updated_at = data["updated_at"]
        job.error_message = data.get("error_message")
        job.output_file = data.get("output_file")
        job.metrics = data.get("metrics", job.metrics)
        job.execution_log = data.get("execution_log", [])
        return job
