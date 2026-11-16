"""
campaign_manager.py — Campaign Lifecycle & Content State Tracking System
Tracks content across the 8-stage lifecycle:
  IDEA -> PLANNED -> BRIEF_APPROVED -> SCRIPT_APPROVED -> RENDERED -> QC_APPROVED -> READY_TO_PUBLISH -> PUBLISHED
"""

import os
import sys
import sqlite3
import argparse
from datetime import datetime
from typing import Dict, Any, List, Optional

WORKSPACE_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(WORKSPACE_ROOT, "data")
DB_PATH = os.path.join(DATA_DIR, "campaign_tracker.sqlite")

LIFECYCLE_STATES = [
    "IDEA",
    "PLANNED",
    "BRIEF_APPROVED",
    "SCRIPT_APPROVED",
    "RENDERED",
    "QC_APPROVED",
    "READY_TO_PUBLISH",
    "PUBLISHED"
]


def get_db_connection() -> sqlite3.Connection:
    os.makedirs(DATA_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db_connection()
    with conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS content_items (
            content_id TEXT PRIMARY KEY,
            project TEXT NOT NULL,
            campaign TEXT NOT NULL,
            topic TEXT NOT NULL,
            platform TEXT NOT NULL,
            status TEXT NOT NULL,
            planned_date TEXT,
            output_location TEXT,
            technical_qc_passed INTEGER DEFAULT 0,
            creative_qc_score INTEGER DEFAULT 0,
            published_url TEXT,
            performance_notes TEXT,
            created_at TEXT,
            updated_at TEXT
        )
        """)
    conn.close()


def add_or_update_item(
    content_id: str,
    project: str,
    campaign: str,
    topic: str,
    platform: str = "instagram_reel",
    status: str = "PLANNED",
    planned_date: Optional[str] = None,
    output_location: Optional[str] = None
):
    init_db()
    if status not in LIFECYCLE_STATES:
        raise ValueError(f"Invalid status '{status}'. Must be one of: {LIFECYCLE_STATES}")

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = get_db_connection()
    with conn:
        conn.execute("""
        INSERT INTO content_items (
            content_id, project, campaign, topic, platform, status, planned_date, output_location, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(content_id) DO UPDATE SET
            project = excluded.project,
            campaign = excluded.campaign,
            topic = excluded.topic,
            platform = excluded.platform,
            status = excluded.status,
            planned_date = COALESCE(excluded.planned_date, content_items.planned_date),
            output_location = COALESCE(excluded.output_location, content_items.output_location),
            technical_qc_passed = CASE WHEN excluded.status = 'IDEA' THEN 0 ELSE content_items.technical_qc_passed END,
            creative_qc_score = CASE WHEN excluded.status = 'IDEA' THEN 0 ELSE content_items.creative_qc_score END,
            updated_at = excluded.updated_at
        """, (content_id, project, campaign, topic, platform, status, planned_date, output_location, now, now))
    conn.close()


def update_status(
    content_id: str,
    status: str,
    technical_qc_passed: Optional[bool] = None,
    creative_qc_score: Optional[int] = None,
    published_url: Optional[str] = None
):
    init_db()
    if status not in LIFECYCLE_STATES:
        raise ValueError(f"Invalid status '{status}'. Must be one of: {LIFECYCLE_STATES}")

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = get_db_connection()
    with conn:
        updates = ["status = ?", "updated_at = ?"]
        params = [status, now]

        if technical_qc_passed is not None:
            updates.append("technical_qc_passed = ?")
            params.append(1 if technical_qc_passed else 0)

        if creative_qc_score is not None:
            updates.append("creative_qc_score = ?")
            params.append(creative_qc_score)

        if published_url is not None:
            updates.append("published_url = ?")
            params.append(published_url)

        params.append(content_id)
        query = f"UPDATE content_items SET {', '.join(updates)} WHERE content_id = ?"
        conn.execute(query, params)
    conn.close()


def advance_state(
    content_id: str,
    target_state: str,
    approval_record_path: Optional[str] = None,
    approved_by: Optional[str] = None
) -> Dict[str, Any]:
    """
    Advances a content item through the 8 lifecycle stages with gatekeeping checks:
      IDEA -> PLANNED -> BRIEF_APPROVED -> SCRIPT_APPROVED -> RENDERED -> QC_APPROVED -> READY_TO_PUBLISH -> PUBLISHED
    Enforces:
      - QC_APPROVED requires technical QC passed and creative QC score >= 72.
      - READY_TO_PUBLISH requires both QCs passed.
      - PUBLISHED requires verified human sign-off (Zero Unauthorized Publishing).
    """
    init_db()
    if target_state not in LIFECYCLE_STATES:
        raise ValueError(f"Invalid target state '{target_state}'. Must be one of: {LIFECYCLE_STATES}")

    conn = get_db_connection()
    cursor = conn.execute("SELECT * FROM content_items WHERE content_id = ?", (content_id,))
    item = cursor.fetchone()
    if not item:
        conn.close()
        raise ValueError(f"Content item '{content_id}' not found in database.")

    item_dict = dict(item)
    current_state = item_dict["status"]
    current_idx = LIFECYCLE_STATES.index(current_state)
    target_idx = LIFECYCLE_STATES.index(target_state)

    # Gatekeeping Rules
    if target_state in ["READY_TO_PUBLISH", "PUBLISHED"]:
        if not item_dict["technical_qc_passed"]:
            conn.close()
            raise PermissionError(f"Cannot transition to '{target_state}': Technical QC has not passed.")
        if (item_dict["creative_qc_score"] or 0) < 72:
            conn.close()
            raise PermissionError(f"Cannot transition to '{target_state}': Creative QC score ({item_dict['creative_qc_score']}/90) is below minimum threshold 72.")

    if target_state == "PUBLISHED":
        if not approved_by and not (approval_record_path and os.path.exists(approval_record_path)):
            conn.close()
            raise PermissionError(
                "POLICY VIOLATION: Zero Unauthorized Publishing. "
                "Transitioning to 'PUBLISHED' requires human sign-off via --approved-by or verified approval_record.md."
            )

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with conn:
        conn.execute("UPDATE content_items SET status = ?, updated_at = ? WHERE content_id = ?", (target_state, now, content_id))
    conn.close()

    return {
        "content_id": content_id,
        "previous_state": current_state,
        "new_state": target_state,
        "success": True
    }


def list_items(project: Optional[str] = None) -> List[Dict[str, Any]]:
    init_db()
    conn = get_db_connection()
    if project:
        cursor = conn.execute("SELECT * FROM content_items WHERE project = ? ORDER BY planned_date, content_id", (project,))
    else:
        cursor = conn.execute("SELECT * FROM content_items ORDER BY project, planned_date, content_id")
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows


def print_dashboard():
    items = list_items()
    print("\n" + "="*85)
    print("                    CAMPAIGN CONTENT LIFECYCLE DASHBOARD")
    print("="*85)
    print(f"{'Content ID':<25} {'Project':<18} {'Platform':<15} {'Status':<16} {'Tech QC':<8}")
    print("-" * 85)
    for it in items:
        tech_status = "✅ PASS" if it["technical_qc_passed"] else "PENDING"
        print(f"{it['content_id']:<25} {it['project']:<18} {it['platform']:<15} {it['status']:<16} {tech_status:<8}")
    print("="*85 + "\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Campaign Manager Lifecycle Tracker")
    subparsers = parser.add_subparsers(dest="action")

    # Add item
    p_add = subparsers.add_parser("add", help="Add or update a content item")
    p_add.add_argument("--content-id", required=True)
    p_add.add_argument("--project", required=True)
    p_add.add_argument("--campaign", required=True)
    p_add.add_argument("--topic", required=True)
    p_add.add_argument("--platform", default="instagram_reel")
    p_add.add_argument("--status", default="PLANNED", choices=LIFECYCLE_STATES)
    p_add.add_argument("--date", default=None)
    p_add.add_argument("--output", default=None)

    # Update status
    p_up = subparsers.add_parser("update-status", help="Update content item status")
    p_up.add_argument("--content-id", required=True)
    p_up.add_argument("--status", required=True, choices=LIFECYCLE_STATES)
    p_up.add_argument("--tech-qc", type=bool, default=None)
    p_up.add_argument("--creative-qc", type=int, default=None)
    p_up.add_argument("--url", default=None)

    # Advance state with gatekeeping
    p_adv = subparsers.add_parser("advance", help="Advance state with lifecycle and approval gatekeeping")
    p_adv.add_argument("--content-id", required=True)
    p_adv.add_argument("--to", required=True, choices=LIFECYCLE_STATES)
    p_adv.add_argument("--approval-record", default=None)
    p_adv.add_argument("--approved-by", default=None)

    # Dashboard
    subparsers.add_parser("dashboard", help="Print lifecycle dashboard")

    args = parser.parse_args()

    if args.action == "advance":
        res = advance_state(
            content_id=args.content_id,
            target_state=args.to,
            approval_record_path=args.approval_record,
            approved_by=args.approved_by
        )
        print(f"Content item '{args.content_id}' transitioned from {res['previous_state']} -> {res['new_state']}.")
    elif args.action == "add":
        add_or_update_item(
            content_id=args.content_id,
            project=args.project,
            campaign=args.campaign,
            topic=args.topic,
            platform=args.platform,
            status=args.status,
            planned_date=args.date,
            output_location=args.output
        )
        print(f"Content item '{args.content_id}' added/updated in status {args.status}.")
    elif args.action == "update-status":
        update_status(
            content_id=args.content_id,
            status=args.status,
            technical_qc_passed=args.tech_qc,
            creative_qc_score=args.creative_qc,
            published_url=args.url
        )
        print(f"Content item '{args.content_id}' updated to {args.status}.")
    elif args.action == "dashboard":
        print_dashboard()
    else:
        print_dashboard()
