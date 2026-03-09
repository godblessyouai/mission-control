import json
from pathlib import Path
from datetime import datetime, timedelta

import streamlit as st
import pandas as pd

from db import (
    init_db, quick_seed, fetch_df, add_task, update_task, add_comm,
    add_ai_job, update_ai_job, add_trend, add_feedback, update_feedback, update_rice_score,
)

st.set_page_config(page_title="Mr Kai's Mission Control", layout="wide", page_icon="🧭")
init_db()
quick_seed()

# ---------- Custom CSS for WOW factor ----------
st.markdown("""
<style>
/* Sidebar styling */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0f0c29 0%, #302b63 50%, #24243e 100%);
    color: white;
}
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] .stSelectbox label,
[data-testid="stSidebar"] span {
    color: #e0e0e0 !important;
}
[data-testid="stSidebar"] hr {
    border-color: rgba(255,255,255,0.1);
}
[data-testid="stSidebar"] .stSelectbox > div > div,
[data-testid="stSidebar"] .stMultiSelect > div > div,
[data-testid="stSidebar"] .stTextInput > div > div > input {
    background: rgba(255,255,255,0.08) !important;
    border-color: rgba(255,255,255,0.15) !important;
    color: white !important;
}
[data-testid="stSidebar"] .stCheckbox label span {
    color: #e0e0e0 !important;
}

/* Agent cards hover effect */
.agent-card {
    text-align: center;
    padding: 16px 12px;
    border-radius: 16px;
    transition: all 0.3s ease;
    cursor: default;
    backdrop-filter: blur(10px);
}
.agent-card:hover {
    transform: translateY(-4px);
    box-shadow: 0 8px 25px rgba(0,0,0,0.15);
}

/* KPI metrics glow */
[data-testid="stMetric"] {
    background: rgba(255,255,255,0.03);
    border-radius: 12px;
    padding: 12px !important;
    border: 1px solid rgba(0,0,0,0.06);
}

/* Tab styling */
.stTabs [data-baseweb="tab-list"] {
    gap: 8px;
    background: rgba(0,0,0,0.02);
    border-radius: 12px;
    padding: 4px;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 8px;
    padding: 8px 16px;
    font-weight: 600;
}

/* Alert cards */
.alert-card {
    padding: 10px 16px;
    border-radius: 10px;
    margin: 4px 0;
    background: rgba(255,255,255,0.5);
    border-left: 4px solid;
}

/* Quick command bar */
.quick-cmd {
    background: linear-gradient(90deg, #6C5CE7 0%, #a29bfe 100%);
    border-radius: 16px;
    padding: 2px;
}

/* Expander styling */
.streamlit-expanderHeader {
    font-weight: 600 !important;
    font-size: 15px !important;
}

/* Data tables */
[data-testid="stDataFrame"] {
    border-radius: 12px;
    overflow: hidden;
}

/* Hide Streamlit branding but keep sidebar toggle */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}

/* Hide sidebar completely */
[data-testid="stSidebar"] {
    display: none !important;
}
[data-testid="collapsedControl"] {
    display: none !important;
}
</style>
""", unsafe_allow_html=True)

# ---------- Agent team ----------
AGENTS = {
    "Mr Brain": {"emoji": "🧠", "role": "Orchestrator + Product", "color": "#6C5CE7", "skills": 7},
    "Mr Engineering": {"emoji": "💻", "role": "Engineering Lead", "color": "#0984E3", "skills": 10},
    "Mr Design": {"emoji": "🎨", "role": "Design Lead", "color": "#E17055", "skills": 9},
    "Mr Marketing": {"emoji": "📢", "role": "Marketing Lead", "color": "#00B894", "skills": 8},
}

st.markdown("""
<div style="display:flex; align-items:center; gap:12px; margin-bottom:4px;">
    <span style="font-size:42px;">🧭</span>
    <div>
        <h1 style="margin:0; padding:0; font-size:32px; background: linear-gradient(90deg, #6C5CE7, #0984E3); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">Mr Kai's Mission Control</h1>
        <p style="margin:0; color:#888; font-size:14px;">Executive command center · Mister Mobile & Food Art · Powered by Mr Brain + 3 specialist agents</p>
    </div>
</div>
""", unsafe_allow_html=True)

# ---------- Agent avatar row ----------
agent_cols = st.columns(4)
for col, (name, info) in zip(agent_cols, AGENTS.items()):
    with col:
        active_count = 0
        done_count = 0
        try:
            active_df = fetch_df(
                "SELECT COUNT(*) as cnt FROM ai_jobs WHERE assigned_agent = ? AND status IN ('Queued','In Progress')",
                [name],
            )
            active_count = int(active_df.iloc[0]["cnt"] or 0)
            done_df = fetch_df(
                "SELECT COUNT(*) as cnt FROM ai_jobs WHERE assigned_agent = ? AND status = 'Done'",
                [name],
            )
            done_count = int(done_df.iloc[0]["cnt"] or 0)
        except Exception:
            pass
        status_dot = "🟢" if active_count > 0 else "⚪"
        glow = f"box-shadow: 0 0 20px {info['color']}40;" if active_count > 0 else ""
        st.markdown(
            f"""
            <div class="agent-card" style="background: linear-gradient(135deg, {info['color']}08, {info['color']}18); border: 2px solid {info['color']}30; {glow}">
                <div style="font-size:52px; filter: drop-shadow(0 2px 4px rgba(0,0,0,0.2));">{info['emoji']}</div>
                <div style="font-weight:800; font-size:15px; margin-top:6px; color:#2d3436;">{name}</div>
                <div style="font-size:11px; color:{info['color']}; font-weight:600; text-transform:uppercase; letter-spacing:0.5px;">{info['role']}</div>
                <div style="display:flex; justify-content:center; gap:8px; margin-top:8px; font-size:11px; color:#636e72;">
                    <span>{status_dot} {active_count} active</span>
                    <span>·</span>
                    <span>✅ {done_count} done</span>
                    <span>·</span>
                    <span>🔧 {info['skills']} skills</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

# ---------- Quick Command (Sprint 1, Item 3) ----------
with st.form("quick_command_form", clear_on_submit=True):
    qc1, qc2 = st.columns([5, 1])
    with qc1:
        quick_cmd = st.text_input(
            "⚡ Quick Command",
            placeholder="Type a task or request — Mr Brain will route it to the right agent...",
            label_visibility="collapsed",
        )
    with qc2:
        quick_send = st.form_submit_button("🧠 Send", use_container_width=True)

    if quick_send and quick_cmd.strip():
        _cfg = None
        try:
            cfg_path = Path(__file__).parent / "agent-routing.json"
            with open(cfg_path, "r", encoding="utf-8") as f:
                _cfg = json.load(f)
        except Exception:
            _cfg = {
                "orchestrator": "Mr Brain",
                "agents": [
                    {"name": "Mr Engineering", "triggers": ["build", "api", "bug", "devops", "security"]},
                    {"name": "Mr Design", "triggers": ["ui", "ux", "brand", "creative"]},
                    {"name": "Mr Marketing", "triggers": ["campaign", "growth", "social", "content", "ads"]},
                ],
                "routingPolicy": {"default": "Mr Marketing"},
            }

        # inline route
        txt = quick_cmd.lower()
        best_agent = _cfg.get("routingPolicy", {}).get("default", "Mr Marketing")
        best_score = -1
        for agent in _cfg.get("agents", []):
            score = sum(1 for t in agent.get("triggers", []) if t.lower() in txt)
            if agent.get("name") == "Mr Engineering" and any(w in txt for w in ["build", "code", "fix", "deploy"]):
                score += 1
            if agent.get("name") == "Mr Design" and any(w in txt for w in ["design", "ui", "brand", "logo"]):
                score += 1
            if agent.get("name") == "Mr Marketing" and any(w in txt for w in ["post", "campaign", "ad", "content"]):
                score += 1
            if score > best_score:
                best_score = score
                best_agent = agent.get("name", best_agent)

        add_ai_job(
            {
                "job_type": "assistant",
                "company": "Shared/Personal",
                "request": quick_cmd.strip(),
                "owner": "Mr Kai",
                "priority": "Medium",
                "status": "Queued",
                "output": "",
                "assigned_agent": best_agent,
                "reviewer_agent": "",
                "route_reason": f"quick command → {best_agent}",
            }
        )
        st.success(f"✅ Routed to **{best_agent}** → Check AI Workers tab")

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

# ---------- Top filter bar ----------
companies = ["All"] + fetch_df("SELECT name FROM companies ORDER BY name")["name"].tolist()

with st.expander("🔍 Filters", expanded=False):
    fc1, fc2, fc3, fc4, fc5, fc6 = st.columns([1.5, 1.5, 2, 2, 2, 1])
    with fc1:
        company_f = st.selectbox("Company", companies, key="top_company")
    with fc2:
        owner_f = st.text_input("Owner", key="top_owner")
    with fc3:
        text_f = st.text_input("Search", placeholder="title/project/notes", key="top_search")
    with fc4:
        urgency_f = st.multiselect(
            "Urgency",
            ["Low", "Medium", "High", "Critical"],
            default=["Low", "Medium", "High", "Critical"],
            key="top_urgency",
        )
    with fc5:
        status_f = st.multiselect(
            "Task status",
            ["Open", "In Progress", "Blocked", "Done", "Snoozed"],
            default=["Open", "In Progress", "Blocked", "Done", "Snoozed"],
            key="top_status",
        )
    with fc6:
        hide_done = st.checkbox("Hide done", value=True, key="top_hide_done")

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
open_tasks_val = int(kpi.iloc[0]["open_tasks"] or 0)
escalations_val = int(kpi.iloc[0]["escalations"] or 0)
overdue_val = int(kpi.iloc[0]["overdue"] or 0)
due_today_val = int(kpi.iloc[0]["due_today"] or 0)
c1.metric("Open tasks", open_tasks_val)
c2.metric("Escalations", escalations_val)
c3.metric("Overdue", overdue_val)
c4.metric("Due today", due_today_val)

# ---------- Smart Alerts (Sprint 1, Item 2) ----------
alerts = []
if overdue_val > 0:
    alerts.append(f"🔴 **{overdue_val} overdue task(s)** — need attention now")
if escalations_val > 0:
    alerts.append(f"🟠 **{escalations_val} escalation(s)** — waiting for your decision")
if due_today_val > 0:
    alerts.append(f"🟡 **{due_today_val} task(s) due today** — check before EOD")

# Check for stale in-progress jobs
stale_jobs = fetch_df(
    """
    SELECT COUNT(*) as cnt FROM ai_jobs
    WHERE status = 'In Progress'
    AND datetime(updated_at) < datetime('now', '-24 hours')
    """
)
stale_count = int(stale_jobs.iloc[0]["cnt"] or 0)
if stale_count > 0:
    alerts.append(f"⚪ **{stale_count} AI job(s)** stuck In Progress for 24h+")

# Agent utilization
agent_util = fetch_df(
    """
    SELECT assigned_agent, COUNT(*) as cnt
    FROM ai_jobs
    WHERE status IN ('Queued', 'In Progress')
    GROUP BY assigned_agent
    ORDER BY cnt DESC
    """
)
if not agent_util.empty:
    busiest = agent_util.iloc[0]
    if int(busiest["cnt"]) >= 5:
        alerts.append(f"📊 **{busiest['assigned_agent']}** has {int(busiest['cnt'])} active jobs — consider rebalancing")

if alerts:
    with st.expander(f"🔔 Smart Alerts ({len(alerts)})", expanded=True):
        for a in alerts:
            st.markdown(a)
else:
    st.caption("🔔 No alerts — all clear")

# ---------- KPI Pulse (Sprint 1, Item 4) ----------
with st.expander("📈 KPI Pulse — Executive Snapshot"):
    pulse_jobs = fetch_df(
        """
        SELECT
          COUNT(*) as total,
          SUM(CASE WHEN status = 'Queued' THEN 1 ELSE 0 END) as queued,
          SUM(CASE WHEN status = 'In Progress' THEN 1 ELSE 0 END) as in_progress,
          SUM(CASE WHEN status = 'Done' THEN 1 ELSE 0 END) as done
        FROM ai_jobs
        """
    )
    pj = pulse_jobs.iloc[0]
    p1, p2, p3, p4 = st.columns(4)
    p1.metric("Total AI jobs", int(pj["total"] or 0))
    p2.metric("Queued", int(pj["queued"] or 0))
    p3.metric("In Progress", int(pj["in_progress"] or 0))
    p4.metric("Completed", int(pj["done"] or 0))

    # Agent workload distribution
    agent_dist = fetch_df(
        """
        SELECT assigned_agent, status, COUNT(*) as cnt
        FROM ai_jobs
        GROUP BY assigned_agent, status
        ORDER BY assigned_agent
        """
    )
    if not agent_dist.empty:
        st.caption("Agent workload distribution")
        pivot = agent_dist.pivot_table(index="assigned_agent", columns="status", values="cnt", fill_value=0, aggfunc="sum")
        st.dataframe(pivot, use_container_width=True)

    # Today's summary
    today_str = datetime.now().strftime("%Y-%m-%d")
    st.markdown(f"""
**Daily Pulse ({today_str})**
- 📋 {open_tasks_val} open tasks · {overdue_val} overdue · {due_today_val} due today
- 🚨 {escalations_val} escalations pending decision
- 🤖 {int(pj['in_progress'] or 0)} AI jobs running · {int(pj['queued'] or 0)} queued
- {'⚠️ Attention needed' if overdue_val > 0 or escalations_val > 0 else '✅ On track'}
    """)

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
tab_team, tab_tasks, tab_escalations, tab_comms, tab_ai, tab_trends, tab_feedback, tab_auto = st.tabs(
    ["🤖 Team", "Tasks", "Escalations", "Communications", "AI Workers", "🔍 Trends", "💬 Feedback", "Automation"]
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
        t_auto_assign = st.checkbox("Auto-create AI job for this task", value=False)
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

                if t_auto_assign:
                    import re
                    combined = f"{t_title} {t_notes} {t_project}".lower()
                    auto_rules = {
                        r"build|code|api|bug|deploy|server|database|security|devops|mobile|app": "Mr Engineering",
                        r"design|ui|ux|brand|logo|creative|visual|layout|wireframe|mockup": "Mr Design",
                        r"campaign|marketing|ads|social|content|instagram|tiktok|growth|seo|email.blast": "Mr Marketing",
                    }
                    matched_agent = "Mr Brain"
                    for pattern, agent_name in auto_rules.items():
                        if re.search(pattern, combined):
                            matched_agent = agent_name
                            break
                    add_ai_job({
                        "job_type": "assistant",
                        "company": t_company,
                        "request": t_title.strip(),
                        "owner": t_owner.strip(),
                        "priority": t_urgency,
                        "status": "Queued",
                        "output": "",
                        "assigned_agent": matched_agent,
                        "reviewer_agent": "",
                        "route_reason": f"auto-assigned from task creation → {matched_agent}",
                    })
                    st.success(f"Task added + AI job auto-assigned to **{matched_agent}**")
                else:
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

    with st.expander("🎯 RICE Priority Scoring"):
        rice_tasks = fetch_df(
            """
            SELECT id, title, rice_reach, rice_impact, rice_confidence, rice_effort, rice_score
            FROM tasks
            WHERE status != 'Done'
            ORDER BY rice_score DESC, id DESC
            LIMIT 50
            """
        )
        if rice_tasks.empty:
            st.info("No active tasks to score.")
        else:
            st.dataframe(rice_tasks, use_container_width=True, hide_index=True)

            rice_map = {
                f"#{row['id']} — {row['title']} (score: {row['rice_score']})": int(row["id"])
                for _, row in rice_tasks.iterrows()
            }
            rice_label = st.selectbox("Score a task", list(rice_map.keys()), key="rice_pick")
            rice_id = rice_map[rice_label]

            rc1, rc2, rc3, rc4 = st.columns(4)
            with rc1:
                r_reach = st.number_input("Reach (users/month)", min_value=0, value=100, step=10, key="r_reach")
            with rc2:
                r_impact = st.selectbox("Impact", [0.25, 0.5, 1.0, 2.0, 3.0], index=2, key="r_impact")
            with rc3:
                r_conf = st.selectbox("Confidence %", [0.25, 0.5, 0.8, 1.0], index=1, key="r_conf")
            with rc4:
                r_effort = st.number_input("Effort (person-weeks)", min_value=0.1, value=1.0, step=0.5, key="r_effort")

            st.caption(f"RICE Score preview: **{round((r_reach * r_impact * r_conf) / max(r_effort, 0.1), 1)}**")

            if st.button("Save RICE score"):
                update_rice_score(rice_id, r_reach, r_impact, r_conf, r_effort)
                st.success("RICE score saved")
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

with tab_trends:
    st.subheader("🔍 Trend Feed — Market Intelligence")
    st.caption("Competitor moves, market signals, and opportunities for Mister Mobile + Food Art")

    trends = fetch_df(
        """
        SELECT id, company, category, title, summary, source_url, sentiment, relevance, created_at
        FROM trend_feed
        ORDER BY id DESC
        LIMIT 50
        """
    )
    if trends.empty:
        st.info("No trends captured yet. Add manually or let Mr Brain auto-populate from web research.")
    else:
        tf1, tf2 = st.columns(2)
        with tf1:
            trend_co = st.selectbox("Filter company", ["All"] + sorted(trends["company"].dropna().unique().tolist()), key="trend_co")
        with tf2:
            trend_cat = st.selectbox("Filter category", ["All"] + sorted(trends["category"].dropna().unique().tolist()), key="trend_cat")
        filtered_trends = trends.copy()
        if trend_co != "All":
            filtered_trends = filtered_trends[filtered_trends["company"] == trend_co]
        if trend_cat != "All":
            filtered_trends = filtered_trends[filtered_trends["category"] == trend_cat]
        st.dataframe(filtered_trends, use_container_width=True, hide_index=True)

    with st.expander("➕ Add trend"):
        tr_company = st.selectbox("Company", companies[1:] if len(companies) > 1 else ["Shared/Personal"], key="tr_co")
        tr_cat = st.selectbox("Category", ["Competitor", "Market", "Technology", "Consumer", "Regulation", "Other"], key="tr_cat")
        tr_title = st.text_input("Title", key="tr_title")
        tr_summary = st.text_area("Summary", key="tr_summary")
        tr_url = st.text_input("Source URL", key="tr_url")
        tr_sent = st.selectbox("Sentiment", ["positive", "neutral", "negative"], index=1, key="tr_sent")
        tr_rel = st.selectbox("Relevance", ["Low", "Medium", "High", "Critical"], index=1, key="tr_rel")
        if st.button("Save trend"):
            if tr_title.strip():
                add_trend({
                    "company": tr_company,
                    "category": tr_cat,
                    "title": tr_title.strip(),
                    "summary": tr_summary.strip(),
                    "source_url": tr_url.strip(),
                    "sentiment": tr_sent,
                    "relevance": tr_rel,
                })
                st.success("Trend added")
                st.rerun()

with tab_feedback:
    st.subheader("💬 Feedback Inbox — Customer Signals")
    st.caption("Centralized feedback from all channels, auto-tagged by sentiment")

    feedbacks = fetch_df(
        """
        SELECT id, company, source, customer, message, sentiment, tags, status, notes, created_at
        FROM feedback_inbox
        ORDER BY id DESC
        LIMIT 100
        """
    )

    if feedbacks.empty:
        st.info("No feedback captured yet. Add manually or integrate with customer channels.")
    else:
        fb_status_filter = st.selectbox("Filter status", ["All", "New", "Reviewed", "Actioned", "Archived"], key="fb_status")
        filtered_fb = feedbacks if fb_status_filter == "All" else feedbacks[feedbacks["status"] == fb_status_filter]

        # Sentiment summary
        sent_counts = feedbacks["sentiment"].value_counts()
        s1, s2, s3 = st.columns(3)
        s1.metric("😊 Positive", int(sent_counts.get("positive", 0)))
        s2.metric("😐 Neutral", int(sent_counts.get("neutral", 0)))
        s3.metric("😞 Negative", int(sent_counts.get("negative", 0)))

        st.dataframe(filtered_fb, use_container_width=True, hide_index=True)

    with st.expander("➕ Add feedback"):
        fb_company = st.selectbox("Company", companies[1:] if len(companies) > 1 else ["Shared/Personal"], key="fb_co")
        fb_source = st.selectbox("Source", ["Google Review", "Instagram", "TikTok", "Email", "WhatsApp", "Telegram", "In-Store", "Website", "Other"], key="fb_src")
        fb_customer = st.text_input("Customer name", key="fb_cust")
        fb_msg = st.text_area("Feedback message", key="fb_msg")
        fb_sent = st.selectbox("Sentiment", ["positive", "neutral", "negative"], index=1, key="fb_sent")
        fb_tags = st.text_input("Tags (comma-separated)", key="fb_tags")
        if st.button("Save feedback"):
            if fb_msg.strip():
                add_feedback({
                    "company": fb_company,
                    "source": fb_source,
                    "customer": fb_customer.strip(),
                    "message": fb_msg.strip(),
                    "sentiment": fb_sent,
                    "tags": fb_tags.strip(),
                    "status": "New",
                    "notes": "",
                })
                st.success("Feedback added")
                st.rerun()

with tab_auto:
    st.subheader("Automation Center (v2)")

    auto_col1, auto_col2 = st.columns(2)

    with auto_col1:
        st.markdown("#### Sprint 3 — Automation")
        st.markdown(
            """
- ✅ Daily 9am executive summary (`scripts/daily_pulse.py`)
- ✅ End-of-day summary (script ready)
- ✅ Weekly management report by company (below)
- ✅ SLA/overdue alert rules (Smart Alerts live)
- ✅ Auto-assign on task creation (below)
- ✅ Calendar export (ICS download)
            """
        )

    with auto_col2:
        st.markdown("#### Sprint 4 — Scale")
        st.markdown(
            """
- ✅ Plugin system (skills auto-discovered from workspace)
- ✅ Multi-user Telegram submission (via Quick Command / `/ai`)
- ✅ Mobile-responsive layout (Streamlit native)
- ✅ Agent skill registry (below)
            """
        )

    st.divider()

    # --- Auto-assign toggle ---
    st.markdown("##### 🤖 Auto-Assign Rules")
    st.caption("When enabled, new tasks are auto-routed to an agent based on title + notes content.")

    auto_assign_rules = {
        "build|code|api|bug|deploy|server|database|security|devops|mobile|app": "Mr Engineering",
        "design|ui|ux|brand|logo|creative|visual|layout|wireframe|mockup": "Mr Design",
        "campaign|marketing|ads|social|content|instagram|tiktok|growth|seo|email blast": "Mr Marketing",
    }

    st.markdown("Current rules:")
    for pattern, agent in auto_assign_rules.items():
        keywords = pattern.replace("|", ", ")
        st.caption(f"**{agent}** ← _{keywords}_")

    # --- Weekly Report Generator ---
    st.divider()
    st.markdown("##### 📊 Weekly Report Generator")

    if st.button("Generate Weekly Report Now"):
        report_lines = [f"## 📊 Weekly Report — {datetime.now().strftime('%Y-%m-%d %H:%M')}"]
        for co_name in ["Mister Mobile", "Food Art", "Shared/Personal"]:
            co_tasks = fetch_df(
                """
                SELECT status, COUNT(*) as cnt
                FROM tasks
                WHERE company = ?
                GROUP BY status
                """,
                [co_name],
            )
            co_jobs = fetch_df(
                """
                SELECT status, COUNT(*) as cnt
                FROM ai_jobs
                WHERE company = ?
                GROUP BY status
                """,
                [co_name],
            )
            report_lines.append(f"\n### {co_name}")
            if co_tasks.empty:
                report_lines.append("No tasks.")
            else:
                for _, r in co_tasks.iterrows():
                    report_lines.append(f"- Tasks {r['status']}: {r['cnt']}")
            if not co_jobs.empty:
                for _, r in co_jobs.iterrows():
                    report_lines.append(f"- AI Jobs {r['status']}: {r['cnt']}")

        report_text = "\n".join(report_lines)
        st.markdown(report_text)
        st.download_button(
            "📥 Download Report (.md)",
            report_text,
            file_name=f"weekly-report-{datetime.now().strftime('%Y%m%d')}.md",
            mime="text/markdown",
        )

    # --- Calendar Export (ICS) ---
    st.divider()
    st.markdown("##### 📅 Calendar Export")
    st.caption("Download all tasks with due dates as an ICS calendar file.")

    if st.button("Export Calendar (ICS)"):
        cal_tasks = fetch_df(
            """
            SELECT title, company, due_date, urgency, status
            FROM tasks
            WHERE due_date != '' AND due_date IS NOT NULL AND status != 'Done'
            ORDER BY due_date
            """
        )
        if cal_tasks.empty:
            st.info("No tasks with due dates to export.")
        else:
            ics_lines = [
                "BEGIN:VCALENDAR",
                "VERSION:2.0",
                "PRODID:-//MissionControl//EN",
                "CALSCALE:GREGORIAN",
            ]
            for _, row in cal_tasks.iterrows():
                due = str(row["due_date"]).replace("-", "")
                ics_lines.extend([
                    "BEGIN:VEVENT",
                    f"DTSTART;VALUE=DATE:{due}",
                    f"DTEND;VALUE=DATE:{due}",
                    f"SUMMARY:[{row['urgency']}] {row['title']} ({row['company']})",
                    f"DESCRIPTION:Status: {row['status']}\\nCompany: {row['company']}\\nUrgency: {row['urgency']}",
                    "END:VEVENT",
                ])
            ics_lines.append("END:VCALENDAR")
            ics_content = "\r\n".join(ics_lines)
            st.download_button(
                "📥 Download .ics",
                ics_content,
                file_name=f"mission-control-{datetime.now().strftime('%Y%m%d')}.ics",
                mime="text/calendar",
            )

    # --- Agent Skill Registry ---
    st.divider()
    st.markdown("##### 🧩 Agent Skill Registry")
    st.caption("Auto-discovered skills from each agent workspace.")

    skill_dirs = {
        "🧠 Mr Brain": Path.home() / ".openclaw/workspace/skills",
        "💻 Mr Engineering": Path.home() / ".openclaw/workspace-mr-engineering/skills",
        "🎨 Mr Design": Path.home() / ".openclaw/workspace-mr-design/skills",
        "📢 Mr Marketing": Path.home() / ".openclaw/workspace-mr-marketing/skills",
    }

    for agent_label, skill_path in skill_dirs.items():
        if skill_path.exists():
            skill_names = sorted([
                d.name for d in skill_path.iterdir()
                if d.is_dir() and (d / "SKILL.md").exists()
            ])
            with st.expander(f"{agent_label} — {len(skill_names)} skills"):
                if skill_names:
                    for sn in skill_names:
                        st.caption(f"• {sn}")
                else:
                    st.caption("No skills found.")
        else:
            with st.expander(f"{agent_label} — workspace not found"):
                st.caption(f"Path: {skill_path}")
