import json
from pathlib import Path
from datetime import datetime, timedelta

import streamlit as st
import pandas as pd

from db import init_db, quick_seed, fetch_df, add_task, update_task, add_comm, add_ai_job, update_ai_job

st.set_page_config(page_title="Mission Control", layout="wide", page_icon="🧭")
init_db()
quick_seed()

# ---------- Agent team ----------
AGENTS = {
    "Mr Brain": {"emoji": "🧠", "role": "Orchestrator", "color": "#6C5CE7", "skills": 4},
    "Mr Engineering": {"emoji": "💻", "role": "Engineering Lead", "color": "#0984E3", "skills": 10},
    "Mr Design": {"emoji": "🎨", "role": "Design Lead", "color": "#E17055", "skills": 9},
    "Mr Marketing": {"emoji": "📢", "role": "Marketing Lead", "color": "#00B894", "skills": 8},
}

st.title("🧭 Mission Control — Executive Assistant")
st.caption("Multi-company command center · Powered by Mr Brain + 3 specialist agents")

# ---------- Agent avatar row ----------
agent_cols = st.columns(4)
for col, (name, info) in zip(agent_cols, AGENTS.items()):
    with col:
        active_count = 0
        try:
            active_df = fetch_df(
                "SELECT COUNT(*) as cnt FROM ai_jobs WHERE assigned_agent = ? AND status IN ('Queued','In Progress')",
                [name],
            )
            active_count = int(active_df.iloc[0]["cnt"] or 0)
        except Exception:
            pass
        status_dot = "🟢" if active_count > 0 else "⚪"
        st.markdown(
            f"""
            <div style="text-align:center; padding:12px; border-radius:12px; background:{info['color']}15; border:2px solid {info['color']}40;">
                <div style="font-size:48px;">{info['emoji']}</div>
                <div style="font-weight:700; font-size:16px; margin-top:4px;">{name}</div>
                <div style="font-size:12px; color:#888;">{info['role']}</div>
                <div style="font-size:12px; margin-top:4px;">{status_dot} {active_count} active · {info['skills']} skills</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

st.divider()


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


def route_decision(request_text: str, job_type: str, cfg: dict) -> dict:
    txt = f"{job_type} {request_text}".lower().strip()
    default_agent = cfg.get("routingPolicy", {}).get("default", cfg.get("orchestrator", "Mr Brain"))

    scores = {}
    reasons = {}
    for agent in cfg.get("agents", []):
        name = agent.get("name", "")
        triggers = [t.lower() for t in agent.get("triggers", [])]
        matched = [t for t in triggers if t in txt]
        score = len(matched)
        # weighted hints by job type
        if job_type in ["programmer", "assistant"] and name == "Mr Engineering":
            score += 1
        if job_type in ["graphic", "video"] and name == "Mr Design":
            score += 1
        if job_type in ["copy"] and name == "Mr Marketing":
            score += 1

        scores[name] = score
        reasons[name] = matched

    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    primary = ranked[0][0] if ranked else default_agent
    secondary = ranked[1][0] if len(ranked) > 1 and ranked[1][1] > 0 else ""
    confidence = ranked[0][1] - (ranked[1][1] if len(ranked) > 1 else 0)

    reason_text = "matched: " + ", ".join(reasons.get(primary, [])) if reasons.get(primary) else "fallback routing by job type"
    return {
        "primary": primary,
        "secondary": secondary,
        "confidence": confidence,
        "reason": reason_text,
    }


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
**Owner Assignment:** {agent}{(' | Reviewer: ' + job.get('reviewer_agent')) if job.get('reviewer_agent') else ''}
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
tab_team, tab_tasks, tab_escalations, tab_comms, tab_ai, tab_auto = st.tabs(
    ["🤖 Team", "Tasks", "Escalations", "Communications", "AI Workers", "Automation"]
)

with tab_team:
    st.subheader("Agent Team Overview")

    for name, info in AGENTS.items():
        with st.expander(f"{info['emoji']} {name} — {info['role']}", expanded=(name == "Mr Brain")):
            team_jobs = fetch_df(
                """
                SELECT status, COUNT(*) as cnt
                FROM ai_jobs
                WHERE assigned_agent = ?
                GROUP BY status
                """,
                [name],
            )
            if team_jobs.empty:
                st.caption("No jobs assigned yet.")
            else:
                m1, m2, m3 = st.columns(3)
                queued = int(team_jobs[team_jobs["status"] == "Queued"]["cnt"].sum()) if "Queued" in team_jobs["status"].values else 0
                in_prog = int(team_jobs[team_jobs["status"] == "In Progress"]["cnt"].sum()) if "In Progress" in team_jobs["status"].values else 0
                done = int(team_jobs[team_jobs["status"] == "Done"]["cnt"].sum()) if "Done" in team_jobs["status"].values else 0
                m1.metric("Queued", queued)
                m2.metric("In Progress", in_prog)
                m3.metric("Done", done)

            recent = fetch_df(
                """
                SELECT id, request, status, updated_at
                FROM ai_jobs
                WHERE assigned_agent = ?
                ORDER BY updated_at DESC
                LIMIT 5
                """,
                [name],
            )
            if not recent.empty:
                st.caption("Recent jobs")
                st.dataframe(recent, use_container_width=True, hide_index=True)


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
        SELECT id, assigned_agent, reviewer_agent, job_type, company, request, owner, priority, status, route_reason, output
        FROM ai_jobs
        ORDER BY id DESC
        """
    )

    view_agents = ["All"] + sorted([a for a in jobs["assigned_agent"].dropna().unique().tolist() if a]) if not jobs.empty else ["All"]
    view_statuses = ["All", "Queued", "In Progress", "Done", "Blocked"]
    vf1, vf2 = st.columns(2)
    with vf1:
        agent_view = st.selectbox("Filter by assigned agent", view_agents, key="ai_filter_agent")
    with vf2:
        status_view = st.selectbox("Filter by status", view_statuses, key="ai_filter_status")

    filtered_jobs = jobs.copy()
    if agent_view != "All":
        filtered_jobs = filtered_jobs[filtered_jobs["assigned_agent"] == agent_view]
    if status_view != "All":
        filtered_jobs = filtered_jobs[filtered_jobs["status"] == status_view]

    st.dataframe(filtered_jobs, use_container_width=True, hide_index=True)

    with st.expander("🧩 Batch actions"):
        batch_source = filtered_jobs if not filtered_jobs.empty else jobs
        if batch_source.empty:
            st.info("No jobs available for batch actions.")
        else:
            batch_map = {
                f"#{row['id']} — {row['assigned_agent'] or 'Mr Brain'} [{row['status']}] {str(row['request'])[:70]}": int(row["id"])
                for _, row in batch_source.head(200).iterrows()
            }
            picked_labels = st.multiselect("Pick jobs", list(batch_map.keys()), key="batch_pick_jobs")
            picked_ids = [batch_map[x] for x in picked_labels]
            if picked_ids:
                b1, b2, b3, b4 = st.columns(4)
                with b1:
                    if st.button("Set In Progress", key="batch_inprogress"):
                        for jid in picked_ids:
                            update_ai_job(jid, {"status": "In Progress"})
                        st.success(f"Updated {len(picked_ids)} jobs")
                        st.rerun()
                with b2:
                    if st.button("Mark Done", key="batch_done"):
                        for jid in picked_ids:
                            update_ai_job(jid, {"status": "Done"})
                        st.success(f"Updated {len(picked_ids)} jobs")
                        st.rerun()
                with b3:
                    if st.button("Re-queue", key="batch_queue"):
                        for jid in picked_ids:
                            update_ai_job(jid, {"status": "Queued"})
                        st.success(f"Updated {len(picked_ids)} jobs")
                        st.rerun()
                with b4:
                    if st.button("Escalate to Mr Brain", key="batch_escalate"):
                        for jid in picked_ids:
                            update_ai_job(jid, {"assigned_agent": "Mr Brain", "priority": "Critical", "status": "In Progress", "route_reason": "escalated manually"})
                        st.success(f"Escalated {len(picked_ids)} jobs to Mr Brain")
                        st.rerun()

    with st.expander("⚙️ Run / Update AI job", expanded=True):
        active_jobs = fetch_df(
            """
            SELECT id, assigned_agent, reviewer_agent, status, request
            FROM ai_jobs
            ORDER BY id DESC
            LIMIT 200
            """
        )
        if active_jobs.empty:
            st.info("No AI jobs yet.")
        else:
            job_map = {
                f"#{row['id']} — {row['assigned_agent'] or 'Mr Brain'}{' + ' + row['reviewer_agent'] if row['reviewer_agent'] else ''} [{row['status']}] {str(row['request'])[:70]}": int(row["id"])
                for _, row in active_jobs.iterrows()
            }
            selected_job_label = st.selectbox("Pick job", list(job_map.keys()))
            selected_job_id = job_map[selected_job_label]
            selected_row = fetch_df(
                """
                SELECT id, assigned_agent, reviewer_agent, route_reason, job_type, company, request, owner, priority, status, output
                FROM ai_jobs
                WHERE id = ?
                """,
                [selected_job_id],
            ).iloc[0].to_dict()

            if selected_row.get("route_reason"):
                st.caption(f"Routing note: {selected_row.get('route_reason')}")

            r1, r2, r3, r4 = st.columns(4)
            with r1:
                if st.button("Assign Mr Engineering", key=f"assign_eng_{selected_job_id}"):
                    update_ai_job(selected_job_id, {"assigned_agent": "Mr Engineering", "route_reason": "manual reassignment"})
                    st.success("Assigned to Mr Engineering")
                    st.rerun()
            with r2:
                if st.button("Assign Mr Design", key=f"assign_des_{selected_job_id}"):
                    update_ai_job(selected_job_id, {"assigned_agent": "Mr Design", "route_reason": "manual reassignment"})
                    st.success("Assigned to Mr Design")
                    st.rerun()
            with r3:
                if st.button("Assign Mr Marketing", key=f"assign_mkt_{selected_job_id}"):
                    update_ai_job(selected_job_id, {"assigned_agent": "Mr Marketing", "route_reason": "manual reassignment"})
                    st.success("Assigned to Mr Marketing")
                    st.rerun()
            with r4:
                if st.button("Escalate to Mr Brain", key=f"assign_brain_{selected_job_id}"):
                    update_ai_job(selected_job_id, {"assigned_agent": "Mr Brain", "priority": "Critical", "status": "In Progress", "route_reason": "manual escalation"})
                    st.success("Escalated to Mr Brain")
                    st.rerun()

            b1, b2, b3, b4, b5 = st.columns(5)
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
            with b5:
                if st.button("📄 Clone job"):
                    add_ai_job(
                        {
                            "job_type": selected_row.get("job_type", "assistant"),
                            "company": selected_row.get("company", "Shared/Personal"),
                            "request": selected_row.get("request", ""),
                            "owner": selected_row.get("owner", ""),
                            "priority": selected_row.get("priority", "Medium"),
                            "status": "Queued",
                            "output": "",
                            "assigned_agent": selected_row.get("assigned_agent", "Mr Brain"),
                            "reviewer_agent": selected_row.get("reviewer_agent", ""),
                            "route_reason": f"cloned from #{selected_job_id}",
                        }
                    )
                    st.success("Cloned as a new queued job")
                    st.rerun()

            manual_output = st.text_area("Edit output", value=selected_row.get("output", ""), height=180, key=f"out_{selected_job_id}")
            if st.button("💾 Save output"):
                update_ai_job(selected_job_id, {"output": manual_output})
                st.success("Output saved")
                st.rerun()

            events = fetch_df(
                """
                SELECT created_at, event_type, details
                FROM ai_job_events
                WHERE job_id = ?
                ORDER BY id DESC
                LIMIT 30
                """,
                [selected_job_id],
            )
            st.caption("Execution history")
            st.dataframe(events, use_container_width=True, hide_index=True)

    with st.expander("📚 Completed jobs (latest 20)"):
        completed = fetch_df(
            """
            SELECT id, assigned_agent, reviewer_agent, company, owner, priority, updated_at, request, output
            FROM ai_jobs
            WHERE status = 'Done'
            ORDER BY updated_at DESC
            LIMIT 20
            """
        )
        st.dataframe(completed, use_container_width=True, hide_index=True)

    with st.expander("➕ Queue AI job"):
        j_type = st.selectbox("Type", ["assistant", "graphic", "video", "copy", "programmer"])
        j_company = st.selectbox("Company", companies[1:] if len(companies) > 1 else ["Shared/Personal"], key="jcompany")
        j_req = st.text_area("Request")
        j_owner = st.text_input("Owner", key="jowner")
        j_priority = st.selectbox("Priority", ["Low", "Medium", "High", "Critical"], key="jpriority")

        auto_route = st.checkbox("Auto-route with Mr Brain", value=True)
        decision = route_decision(j_req, j_type, routing_cfg)
        recommended = decision["primary"]
        reviewer = decision["secondary"]
        st.caption(f"Suggested agent: **{recommended}**")
        st.caption(f"Why: {decision['reason']}")
        if reviewer:
            st.caption(f"Reviewer: **{reviewer}**")

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
                        "reviewer_agent": reviewer if auto_route else "",
                        "route_reason": decision["reason"] if auto_route else "manual assignment",
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
