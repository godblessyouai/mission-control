#!/usr/bin/env python3
"""Daily KPI Pulse — generates executive summary from Mission Control DB.
Run via cron or Mr Brain heartbeat. Output to stdout (pipe to Telegram via openclaw)."""

import sqlite3
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).parent.parent / "mission_control.db"


def generate_pulse() -> str:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    # Tasks
    tasks = conn.execute("""
        SELECT
          COUNT(*) as total,
          SUM(CASE WHEN status IN ('Open','In Progress','Blocked','Snoozed') THEN 1 ELSE 0 END) as open_tasks,
          SUM(CASE WHEN needs_decision = 1 AND status != 'Done' THEN 1 ELSE 0 END) as escalations,
          SUM(CASE WHEN due_date != '' AND date(due_date) < date('now') AND status != 'Done' THEN 1 ELSE 0 END) as overdue,
          SUM(CASE WHEN due_date != '' AND date(due_date) = date('now') AND status != 'Done' THEN 1 ELSE 0 END) as due_today
        FROM tasks
    """).fetchone()

    # AI Jobs
    jobs = conn.execute("""
        SELECT
          COUNT(*) as total,
          SUM(CASE WHEN status = 'Queued' THEN 1 ELSE 0 END) as queued,
          SUM(CASE WHEN status = 'In Progress' THEN 1 ELSE 0 END) as in_progress,
          SUM(CASE WHEN status = 'Done' THEN 1 ELSE 0 END) as done
        FROM ai_jobs
    """).fetchone()

    # Agent distribution
    agents = conn.execute("""
        SELECT assigned_agent, COUNT(*) as cnt
        FROM ai_jobs
        WHERE status IN ('Queued', 'In Progress')
        GROUP BY assigned_agent
        ORDER BY cnt DESC
    """).fetchall()

    conn.close()

    today = datetime.now().strftime("%Y-%m-%d %H:%M")
    status_emoji = "⚠️" if (tasks["overdue"] or 0) > 0 or (tasks["escalations"] or 0) > 0 else "✅"

    lines = [
        f"📈 **KPI Pulse — {today}**",
        "",
        f"**Tasks:** {tasks['open_tasks'] or 0} open · {tasks['overdue'] or 0} overdue · {tasks['due_today'] or 0} due today",
        f"**Escalations:** {tasks['escalations'] or 0} pending decision",
        f"**AI Jobs:** {jobs['in_progress'] or 0} running · {jobs['queued'] or 0} queued · {jobs['done'] or 0} completed",
        "",
    ]

    if agents:
        lines.append("**Agent workload:**")
        for a in agents:
            lines.append(f"  · {a['assigned_agent']}: {a['cnt']} active")
        lines.append("")

    lines.append(f"**Status:** {status_emoji} {'Attention needed' if status_emoji == '⚠️' else 'On track'}")
    return "\n".join(lines)


if __name__ == "__main__":
    print(generate_pulse())
