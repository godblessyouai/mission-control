from db import init_db, fetch_df
from datetime import datetime


def executive_summary():
    init_db()
    tasks = fetch_df(
        """
        SELECT company, title, owner, urgency, due_date, needs_decision
        FROM tasks
        WHERE status != 'Done'
        ORDER BY
          CASE urgency WHEN 'Critical' THEN 1 WHEN 'High' THEN 2 WHEN 'Medium' THEN 3 ELSE 4 END,
          COALESCE(due_date,'9999-12-31')
        """
    )

    comms = fetch_df(
        """
        SELECT source, company, subject, priority, escalated
        FROM comms
        WHERE status = 'Open'
        ORDER BY CASE priority WHEN 'Critical' THEN 1 WHEN 'High' THEN 2 WHEN 'Medium' THEN 3 ELSE 4 END
        """
    )

    lines = []
    lines.append(f"Mission Control Summary ({datetime.now().strftime('%Y-%m-%d %H:%M')})")
    lines.append("=" * 50)

    if len(tasks) == 0:
        lines.append("No open tasks.")
    else:
        lines.append(f"Open tasks: {len(tasks)}")
        dec = tasks[tasks['needs_decision'] == 1]
        lines.append(f"Needs decision: {len(dec)}")
        lines.append("Top priorities:")
        for _, r in tasks.head(10).iterrows():
            lines.append(
                f"- [{r['urgency']}] {r['company']}: {r['title']} (owner: {r['owner'] or 'Unassigned'}, due: {r['due_date'] or '-'})"
            )

    lines.append("")
    if len(comms) == 0:
        lines.append("No open comms items.")
    else:
        lines.append(f"Open comms items: {len(comms)}")
        lines.append("Items needing attention:")
        for _, r in comms.head(8).iterrows():
            esc = " ESCALATED" if int(r['escalated'] or 0) == 1 else ""
            lines.append(f"- [{r['priority']}] {r['source']} {r['company']}: {r['subject']}{esc}")

    return "\n".join(lines)


if __name__ == "__main__":
    print(executive_summary())
