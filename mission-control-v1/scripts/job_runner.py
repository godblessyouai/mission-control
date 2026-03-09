#!/usr/bin/env python3
"""Check for queued AI jobs and return them as actionable items.
Called by Mr Brain (heartbeat or direct) to pick up pending work."""

import sqlite3
import json
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "mission_control.db"


def get_queued_jobs(limit=10):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    jobs = conn.execute(
        """
        SELECT id, assigned_agent, job_type, company, request, owner, priority, status
        FROM ai_jobs
        WHERE status = 'Queued'
        ORDER BY
          CASE priority WHEN 'Critical' THEN 1 WHEN 'High' THEN 2 WHEN 'Medium' THEN 3 ELSE 4 END,
          id ASC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()
    conn.close()
    return [dict(j) for j in jobs]


def mark_in_progress(job_id):
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "UPDATE ai_jobs SET status='In Progress', updated_at=datetime('now') WHERE id=?",
        (job_id,),
    )
    conn.execute(
        "INSERT INTO ai_job_events(job_id, event_type, details, created_at) VALUES(?,?,?,datetime('now'))",
        (job_id, "updated", "status=In Progress (auto-picked by Mr Brain)", ),
    )
    conn.commit()
    conn.close()


def save_output(job_id, output_text, status="Done"):
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "UPDATE ai_jobs SET status=?, output=?, updated_at=datetime('now') WHERE id=?",
        (status, output_text, job_id),
    )
    conn.execute(
        "INSERT INTO ai_job_events(job_id, event_type, details, created_at) VALUES(?,?,?,datetime('now'))",
        (job_id, "updated", f"status={status}; output saved by Mr Brain", ),
    )
    conn.commit()
    conn.close()


if __name__ == "__main__":
    jobs = get_queued_jobs()
    if jobs:
        print(json.dumps(jobs, indent=2))
    else:
        print("No queued jobs.")
