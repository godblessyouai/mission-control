import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

from db import init_db, quick_seed, fetch_df, add_task, update_task, add_comm, add_ai_job

st.set_page_config(page_title="Mission Control", layout="wide")
init_db()
quick_seed()

st.title("🧭 Mission Control — Executive Assistant")
st.caption("Multi-company command center (v1 fast ship)")

# ---------- Sidebar filters ----------
companies = ["All"] + fetch_df("SELECT name FROM companies ORDER BY name")["name"].tolist()
company_f = st.sidebar.selectbox("Company", companies)
owner_f = st.sidebar.text_input("Owner contains")
text_f = st.sidebar.text_input("Search title/project/notes")
urgency_f = st.sidebar.multiselect(
    "Urgency",
    ["Low", "Medium", "High", "Critical"],
    default=["Low", "Medium", "High", "Critical"],
)
status_f = st.sidebar.multiselect(
    "Task status",
    ["Open", "In Progress", "Blocked", "Done", "Snoozed"],
    default=["Open", "In Progress", "Blocked", "Done", "Snoozed"],
)
hide_done = st.sidebar.checkbox("Hide done tasks", value=True)

where = ["1=1"]
params = []
if company_f != "All":
    where.append("company = ?")
    params.append(company_f)
if owner_f.strip():
    where.append("owner LIKE ?")
    params.append(f"%{owner_f.strip()}%")
if text_f.strip():
    where.append("(title LIKE ? OR project LIKE ? OR notes LIKE ?)")
    like = f"%{text_f.strip()}%"
    params.extend([like, like, like])
if urgency_f:
    where.append("urgency IN ({})".format(",".join(["?"] * len(urgency_f))))
    params.extend(urgency_f)
if status_f:
    where.append("status IN ({})".format(",".join(["?"] * len(status_f))))
    params.extend(status_f)
if hide_done:
    where.append("status != 'Done'")

# ---------- KPI row ----------
kpi = fetch_df(
    f"""
    SELECT
      SUM(CASE WHEN status IN ('Open','In Progress','Blocked','Snoozed') THEN 1 ELSE 0 END) AS open_tasks,
      SUM(CASE WHEN needs_decision = 1 AND status != 'Done' THEN 1 ELSE 0 END) AS escalations,
      SUM(CASE WHEN due_date != '' AND due_date IS NOT NULL AND date(due_date) < date('now') AND status != 'Done' THEN 1 ELSE 0 END) AS overdue,
      SUM(CASE WHEN due_date != '' AND due_date IS NOT NULL AND date(due_date) = date('now') AND status != 'Done' THEN 1 ELSE 0 END) AS due_today
    FROM tasks
    WHERE {' AND '.join(where)}
    """,
    params,
)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Open tasks", int(kpi.iloc[0]["open_tasks"] or 0))
c2.metric("Escalations", int(kpi.iloc[0]["escalations"] or 0))
c3.metric("Overdue", int(kpi.iloc[0]["overdue"] or 0))
c4.metric("Due today", int(kpi.iloc[0]["due_today"] or 0))

focus = fetch_df(
    f"""
    SELECT id, title, company, owner, urgency, status, due_date
    FROM tasks
    WHERE {' AND '.join(where)}
    ORDER BY
      CASE urgency WHEN 'Critical' THEN 1 WHEN 'High' THEN 2 WHEN 'Medium' THEN 3 ELSE 4 END,
      COALESCE(NULLIF(due_date,''), '9999-12-31')
    LIMIT 5
    """,
    params,
)

with st.expander("🎯 Today focus (Top 5)", expanded=True):
    if focus.empty:
        st.info("No tasks in current filter.")
    else:
        st.dataframe(focus, use_container_width=True, hide_index=True)

# ---------- Tabs ----------
tab_tasks, tab_escalations, tab_comms, tab_ai, tab_auto = st.tabs(
    ["Tasks", "Escalations", "Communications", "AI Workers", "Automation"]
)

with tab_tasks:
    st.subheader("Task + Follow-up Control")
    tasks = fetch_df(
        f"""
        SELECT id, title, company, project, owner, urgency, status, due_date, snooze_until, needs_decision, notes
        FROM tasks
        WHERE {' AND '.join(where)}
        ORDER BY
          CASE urgency WHEN 'Critical' THEN 1 WHEN 'High' THEN 2 WHEN 'Medium' THEN 3 ELSE 4 END,
          COALESCE(NULLIF(due_date,''), '9999-12-31')
        """,
        params,
    )
    st.dataframe(tasks, use_container_width=True, hide_index=True)

    with st.expander("➕ Add Task"):
        col1, col2 = st.columns(2)
        with col1:
            t_title = st.text_input("Title")
            t_company = st.selectbox("Company", companies[1:] if len(companies) > 1 else ["Shared/Personal"])
            t_project = st.text_input("Project")
            t_owner = st.text_input("Owner")
        with col2:
            t_urgency = st.selectbox("Urgency", ["Low", "Medium", "High", "Critical"], index=1)
            t_status = st.selectbox("Status", ["Open", "In Progress", "Blocked", "Done", "Snoozed"], index=0)
            t_due = st.date_input("Due date", value=None)
            t_decision = st.checkbox("Needs my decision")
        t_notes = st.text_area("Notes")
        if st.button("Save task"):
            if not t_title.strip():
                st.warning("Title is required")
            else:
                add_task(
                    {
                        "title": t_title.strip(),
                        "company": t_company,
                        "project": t_project.strip(),
                        "owner": t_owner.strip(),
                        "urgency": t_urgency,
                        "status": t_status,
                        "due_date": t_due.isoformat() if t_due else "",
                        "snooze_until": "",
                        "needs_decision": 1 if t_decision else 0,
                        "notes": t_notes.strip(),
                    }
                )
                st.success("Task added")
                st.rerun()

    with st.expander("⚡ Quick Actions"):
        quick_tasks = fetch_df(
            """
            SELECT id, title, status
            FROM tasks
            WHERE status != 'Done'
            ORDER BY id DESC
            LIMIT 100
            """
        )
        if quick_tasks.empty:
            st.info("No active tasks available.")
        else:
            task_map = {
                f"#{row['id']} — {row['title']} ({row['status']})": int(row["id"])
                for _, row in quick_tasks.iterrows()
            }
            selected_label = st.selectbox("Pick task", list(task_map.keys()))
            task_id = task_map[selected_label]

            a1, a2, a3, a4 = st.columns(4)
            with a1:
                if st.button("Mark Done"):
                    update_task(task_id, {"status": "Done"})
                    st.success("Updated")
                    st.rerun()
            with a2:
                if st.button("Snooze +1 day"):
                    update_task(
                        task_id,
                        {
                            "status": "Snoozed",
                            "snooze_until": (datetime.now() + timedelta(days=1)).date().isoformat(),
                        },
                    )
                    st.success("Updated")
                    st.rerun()
            with a3:
                new_owner = st.text_input("Reassign owner")
                if st.button("Reassign") and new_owner.strip():
                    update_task(task_id, {"owner": new_owner.strip()})
                    st.success("Updated")
                    st.rerun()
            with a4:
                new_due = st.date_input("New deadline", key="newdue")
                if st.button("Set deadline"):
                    update_task(task_id, {"due_date": new_due.isoformat()})
                    st.success("Updated")
                    st.rerun()

with tab_escalations:
    st.subheader("Escalations needing decision")
    esc = fetch_df(
        """
        SELECT id, title, company, project, owner, urgency, due_date, notes
        FROM tasks
        WHERE needs_decision = 1 AND status != 'Done'
        ORDER BY
          CASE urgency WHEN 'Critical' THEN 1 WHEN 'High' THEN 2 WHEN 'Medium' THEN 3 ELSE 4 END,
          COALESCE(NULLIF(due_date,''), '9999-12-31')
        """
    )
    st.dataframe(esc, use_container_width=True, hide_index=True)

with tab_comms:
    st.subheader("Comms triage")
    comms = fetch_df(
        """
        SELECT id, source, company, subject, owner, priority, action_required, escalated, status, notes
        FROM comms
        ORDER BY id DESC
        """
    )
    st.dataframe(comms, use_container_width=True, hide_index=True)

    with st.expander("➕ Add communication item"):
        source = st.selectbox("Source", ["Email", "Slack", "Telegram", "Customer", "Staff"], key="csource")
        company = st.selectbox("Company", companies[1:] if len(companies) > 1 else ["Shared/Personal"], key="ccompany")
        subject = st.text_input("Subject", key="csubject")
        owner = st.text_input("Owner", key="cowner")
        priority = st.selectbox("Priority", ["Low", "Medium", "High", "Critical"], key="cpriority")
        action = st.checkbox("Action required", value=True, key="caction")
        escalated = st.checkbox("Escalated", value=False, key="cesc")
        notes = st.text_area("Notes", key="cnotes")
        if st.button("Save comm item"):
            if subject.strip():
                add_comm(
                    {
                        "source": source,
                        "company": company,
                        "subject": subject.strip(),
                        "owner": owner.strip(),
                        "priority": priority,
                        "action_required": 1 if action else 0,
                        "escalated": 1 if escalated else 0,
                        "status": "Open",
                        "notes": notes.strip(),
                    }
                )
                st.success("Comms item added")
                st.rerun()

with tab_ai:
    st.subheader("AI worker modules")
    st.caption("Assistant / Graphic / Video / Copy / Programmer job queue")
    jobs = fetch_df(
        """
        SELECT id, job_type, company, request, owner, priority, status, output
        FROM ai_jobs
        ORDER BY id DESC
        """
    )
    st.dataframe(jobs, use_container_width=True, hide_index=True)

    with st.expander("➕ Queue AI job"):
        j_type = st.selectbox("Type", ["assistant", "graphic", "video", "copy", "programmer"])
        j_company = st.selectbox("Company", companies[1:] if len(companies) > 1 else ["Shared/Personal"], key="jcompany")
        j_req = st.text_area("Request")
        j_owner = st.text_input("Owner", key="jowner")
        j_priority = st.selectbox("Priority", ["Low", "Medium", "High", "Critical"], key="jpriority")
        if st.button("Add AI job"):
            if j_req.strip():
                add_ai_job(
                    {
                        "job_type": j_type,
                        "company": j_company,
                        "request": j_req.strip(),
                        "owner": j_owner.strip(),
                        "priority": j_priority,
                        "status": "Queued",
                        "output": "",
                    }
                )
                st.success("AI job queued")
                st.rerun()

with tab_auto:
    st.subheader("Automation Center (v1)")
    st.markdown(
        """
- ✅ Daily 9am executive summary (script ready)
- ✅ End-of-day summary (script ready)
- ✅ Weekly management report by company (script ready)
- ✅ SLA/overdue alert rules (query-ready)

Use the bundled script `summary.py` + cron/launchd to send summaries.
        """
    )
