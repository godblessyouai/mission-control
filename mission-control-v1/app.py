import json
from pathlib import Path
from datetime import datetime, timedelta

import streamlit as st
import pandas as pd

from db import init_db, quick_seed, fetch_df, add_task, update_task, add_comm, add_ai_job, update_ai_job

st.set_page_config(page_title="Mission Control", layout="wide")
init_db()
quick_seed()

st.title("🧭 Mission Control — Executive Assistant")
st.caption("Multi-company command center (v1 fast ship)")


def load_agent_routing():
    cfg_path = Path(__file__).parent / "agent-routing.json"
    if not cfg_path.exists():
        return {
            "orchestrator": "Mr Brain",
            "agents": [
                {"name": "Mr Engineering", "triggers": ["build", "api", "bug", "devops", "security"]},
                {"name": "Mr Design", "triggers": ["ui", "ux", "brand", "creative"]},
                {"name": "Mr Marketing", "triggers": ["campaign", "growth", "social", "content", "ads"]},
            ],
        }
    with open(cfg_path, "r", encoding="utf-8") as f:
        return json.load(f)


def suggest_agent(request_text: str, job_type: str, cfg: dict) -> str:
    txt = f"{job_type} {request_text}".lower().strip()
    best_name = cfg.get("routingPolicy", {}).get("default", cfg.get("orchestrator", "Mr Brain"))
    best_score = -1
    for agent in cfg.get("agents", []):
        score = sum(1 for t in agent.get("triggers", []) if t.lower() in txt)
        if score > best_score:
            best_score = score
            best_name = agent.get("name", best_name)
    return best_name


def build_agent_output(job: dict) -> str:
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    agent = job.get("assigned_agent", "Mr Brain")
    objective = job.get("request", "")
    owner = job.get("owner", "") or "TBD"

    if agent == "Mr Engineering":
        return f"""### Mr Engineering Draft ({now})
**Objective:** {objective}
**Approach:** Break into architecture, implementation, and validation checkpoints.
**Deliverables:** Code changes + technical checklist + deployment notes.
**Risks:** Integration unknowns, dependency drift, timeline risk.
**Validation:** Unit/integration checks + smoke test.
**Next Action:** Confirm repo/module target and start implementation.
"""

    if agent == "Mr Design":
        return f"""### Mr Design Draft ({now})
**Objective:** {objective}
**Context:** Company={job.get('company','')} | Owner={owner}
**Design Direction:** Prioritize clarity, consistency, and conversion-friendly UX.
**Deliverables:** Layout guidance, visual direction, UX notes.
**QA Criteria:** Brand consistency + usability + handoff readiness.
**Next Action:** Confirm audience and channel before final creative output.
"""

    if agent == "Mr Marketing":
        return f"""### Mr Marketing Draft ({now})
**Objective:** {objective}
**Audience/Offer:** Define ICP + core offer for this campaign.
**Strategy:** Hook → value → CTA with measurable funnel steps.
**Channel Plan:** Primary channel + support channel + cadence.
**KPI Targets:** Reach, CTR, leads/sales, conversion rate.
**7-Day Actions:** Launch test creatives, measure, iterate.
**Next Action:** Confirm budget and target segment.
"""

    return f"""### Mr Brain Draft ({now})
**Objective:** {objective}
**Owner Assignment:** {agent}
**Workplan:** Route, execute, review, and finalize.
**Risks/Dependencies:** Capacity, missing input, timing.
**Decision Needed:** Priority and deadline confirmation.
**Next Action:** Approve execution scope and begin run.
"""


routing_cfg = load_agent_routing()
agent_names = [a.get("name") for a in routing_cfg.get("agents", []) if a.get("name")]

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
    st.caption("Mr Brain routes jobs to Mr Engineering / Mr Design / Mr Marketing")

    jobs = fetch_df(
        """
        SELECT id, assigned_agent, job_type, company, request, owner, priority, status, output
        FROM ai_jobs
        ORDER BY id DESC
        """
    )
    st.dataframe(jobs, use_container_width=True, hide_index=True)

    with st.expander("⚙️ Run / Update AI job", expanded=True):
        active_jobs = fetch_df(
            """
            SELECT id, assigned_agent, status, request
            FROM ai_jobs
            ORDER BY id DESC
            LIMIT 200
            """
        )
        if active_jobs.empty:
            st.info("No AI jobs yet.")
        else:
            job_map = {
                f"#{row['id']} — {row['assigned_agent'] or 'Mr Brain'} [{row['status']}] {str(row['request'])[:70]}": int(row["id"])
                for _, row in active_jobs.iterrows()
            }
            selected_job_label = st.selectbox("Pick job", list(job_map.keys()))
            selected_job_id = job_map[selected_job_label]
            selected_row = fetch_df(
                """
                SELECT id, assigned_agent, job_type, company, request, owner, priority, status, output
                FROM ai_jobs
                WHERE id = ?
                """,
                [selected_job_id],
            ).iloc[0].to_dict()

            b1, b2, b3, b4 = st.columns(4)
            with b1:
                if st.button("▶️ Run now"):
                    update_ai_job(selected_job_id, {"status": "In Progress"})
                    st.success("Job set to In Progress")
                    st.rerun()
            with b2:
                if st.button("🧠 Generate draft output"):
                    draft = build_agent_output(selected_row)
                    update_ai_job(selected_job_id, {"status": "In Progress", "output": draft})
                    st.success("Draft output generated")
                    st.rerun()
            with b3:
                if st.button("✅ Mark done"):
                    update_ai_job(selected_job_id, {"status": "Done"})
                    st.success("Job marked Done")
                    st.rerun()
            with b4:
                if st.button("↩️ Re-queue"):
                    update_ai_job(selected_job_id, {"status": "Queued"})
                    st.success("Job moved back to Queued")
                    st.rerun()

            manual_output = st.text_area("Edit output", value=selected_row.get("output", ""), height=180, key=f"out_{selected_job_id}")
            if st.button("💾 Save output"):
                update_ai_job(selected_job_id, {"output": manual_output})
                st.success("Output saved")
                st.rerun()

    with st.expander("➕ Queue AI job"):
        j_type = st.selectbox("Type", ["assistant", "graphic", "video", "copy", "programmer"])
        j_company = st.selectbox("Company", companies[1:] if len(companies) > 1 else ["Shared/Personal"], key="jcompany")
        j_req = st.text_area("Request")
        j_owner = st.text_input("Owner", key="jowner")
        j_priority = st.selectbox("Priority", ["Low", "Medium", "High", "Critical"], key="jpriority")

        auto_route = st.checkbox("Auto-route with Mr Brain", value=True)
        recommended = suggest_agent(j_req, j_type, routing_cfg)
        st.caption(f"Suggested agent: **{recommended}**")

        selectable_agents = agent_names if agent_names else ["Mr Engineering", "Mr Design", "Mr Marketing"]
        selected_agent = st.selectbox(
            "Assigned agent",
            selectable_agents,
            index=(selectable_agents.index(recommended) if recommended in selectable_agents else 0),
            disabled=auto_route,
        )

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
                        "assigned_agent": recommended if auto_route else selected_agent,
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
