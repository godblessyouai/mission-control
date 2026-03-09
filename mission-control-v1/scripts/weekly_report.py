#!/usr/bin/env python3
"""Weekly management report by company. Run via cron or Mr Brain."""

import sqlite3
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).parent.parent / "mission_control.db"


def generate_report() -> str:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    lines = [f"## 📊 Weekly Report — {datetime.now().strftime('%Y-%m-%d %H:%M')}"]

    for co in ["Mister Mobile", "Food Art", "Shared/Personal"]:
        lines.append(f"\n### {co}")

        tasks = conn.execute(
            "SELECT status, COUNT(*) as cnt FROM tasks WHERE company=? GROUP BY status", (co,)
        ).fetchall()
        if tasks:
            for t in tasks:
                lines.append(f"- Tasks {t['status']}: {t['cnt']}")
        else:
            lines.append("- No tasks")

        jobs = conn.execute(
            "SELECT status, COUNT(*) as cnt FROM ai_jobs WHERE company=? GROUP BY status", (co,)
        ).fetchall()
        if jobs:
            for j in jobs:
                lines.append(f"- AI Jobs {j['status']}: {j['cnt']}")

        overdue = conn.execute(
            """SELECT COUNT(*) as cnt FROM tasks
               WHERE company=? AND due_date != '' AND date(due_date) < date('now') AND status != 'Done'""",
            (co,),
        ).fetchone()
        if overdue["cnt"] > 0:
            lines.append(f"- ⚠️ Overdue: {overdue['cnt']}")

        escalations = conn.execute(
            "SELECT COUNT(*) as cnt FROM tasks WHERE company=? AND needs_decision=1 AND status != 'Done'",
            (co,),
        ).fetchone()
        if escalations["cnt"] > 0:
            lines.append(f"- 🚨 Escalations: {escalations['cnt']}")

    # Agent utilization
    lines.append("\n### Agent Utilization")
    agents = conn.execute(
        """SELECT assigned_agent, status, COUNT(*) as cnt
           FROM ai_jobs GROUP BY assigned_agent, status ORDER BY assigned_agent"""
    ).fetchall()
    if agents:
        for a in agents:
            lines.append(f"- {a['assigned_agent']} [{a['status']}]: {a['cnt']}")

    conn.close()
    return "\n".join(lines)


if __name__ == "__main__":
    print(generate_report())
