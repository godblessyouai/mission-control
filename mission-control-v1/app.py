import json
import os
import socket
from pathlib import Path
from datetime import datetime, timedelta

import streamlit as st
import pandas as pd
import streamlit.components.v1 as components

from db import (
    init_db, quick_seed, fetch_df, add_task, update_task, add_comm,
    add_ai_job, update_ai_job, add_trend, add_feedback, update_feedback, update_rice_score,
    upsert_agent_status, push_activity, sync_agent_status,
)

st.set_page_config(page_title="Mr Kai's Mission Control", layout="wide", page_icon="🧭")

# ---------- Design System CSS (Section 6 of Design Spec) ----------
st.markdown("""
<style>
:root {
  --bg-app: #F6F8FC;
  --bg-surface: #FFFFFF;
  --bg-surface-soft: #F9FAFB;
  --bg-header: #1A1A2E;
  --border-subtle: #E5E7EB;
  --border-strong: #D1D5DB;
  --text-primary: #111827;
  --text-secondary: #4B5563;
  --text-muted: #6B7280;
  --text-on-dark: #F9FAFB;
  --accent-primary: #6C5CE7;
  --accent-primary-hover: #5B4BD6;
  --status-queued: #3B82F6;
  --status-inprogress: #F59E0B;
  --status-done: #10B981;
  --status-blocked: #EF4444;
  --radius-card: 16px;
  --radius-md: 12px;
  --radius-sm: 8px;
  --space-1: 4px;
  --space-2: 8px;
  --space-3: 16px;
  --space-4: 24px;
}

html, body, [class*="css"]  {
  font-family: Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
  color: var(--text-primary);
}

.stApp {
  background: var(--bg-app);
}

.main .block-container {
  max-width: 1440px;
  padding-top: 1rem;
  padding-bottom: 2rem;
}

/* Hide default Streamlit chrome */
#MainMenu, footer, [data-testid="stSidebar"], [data-testid="collapsedControl"] {
  visibility: hidden;
  display: none !important;
}

/* Sticky top header wrapper */
.mc-sticky-header {
  position: sticky;
  top: 0;
  z-index: 90;
  background: linear-gradient(135deg, #1A1A2E 0%, #232347 100%);
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 16px;
  padding: 12px 16px;
  margin-bottom: 16px;
  box-shadow: 0 8px 24px rgba(17,24,39,0.18);
}

.mc-title {
  font-size: 24px;
  line-height: 32px;
  font-weight: 700;
  color: var(--text-on-dark);
  margin: 0;
}

.mc-subtitle {
  font-size: 12px;
  line-height: 18px;
  font-weight: 500;
  color: #D1D5DB;
  margin: 2px 0 0;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
  gap: 8px;
  background: transparent;
  border-bottom: 1px solid var(--border-subtle);
  padding: 0 0 8px 0;
}

.stTabs [data-baseweb="tab"] {
  height: 36px;
  border-radius: 10px;
  padding: 0 12px;
  font-size: 14px;
  font-weight: 600;
  color: var(--text-secondary);
}

.stTabs [data-baseweb="tab"][aria-selected="true"] {
  background: #EEF2FF;
  color: #3730A3;
}

/* KPI metric cards */
[data-testid="stMetric"] {
  background: var(--bg-surface);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-card);
  padding: 14px 16px !important;
  box-shadow: 0 2px 8px rgba(17,24,39,0.04);
}

[data-testid="stMetricLabel"] {
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: var(--text-muted);
}

[data-testid="stMetricValue"] {
  font-size: 28px;
  font-weight: 700;
  color: var(--text-primary);
}

/* Cards / containers */
div[data-testid="stVerticalBlock"] div[data-testid="stVerticalBlockBorderWrapper"] {
  border-radius: 16px;
}

.mc-card {
  background: var(--bg-surface);
  border: 1px solid var(--border-subtle);
  border-radius: 16px;
  padding: 16px;
}

.mc-agent-card {
  background: var(--bg-surface);
  border: 1px solid var(--border-subtle);
  border-radius: 16px;
  padding: 16px;
  min-height: 148px;
  transition: transform .18s ease, box-shadow .18s ease, border-color .18s ease;
}

.mc-agent-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 24px rgba(17,24,39,0.10);
  border-color: var(--border-strong);
}

/* Row cards for jobs/tasks */
.mc-row-card {
  background: var(--bg-surface);
  border: 1px solid var(--border-subtle);
  border-radius: 12px;
  padding: 12px 14px;
}

.mc-row-card:hover {
  background: var(--bg-surface-soft);
}

.mc-urgency-low { border-left: 4px solid #10B981; }
.mc-urgency-medium { border-left: 4px solid #F59E0B; }
.mc-urgency-high { border-left: 4px solid #F97316; }
.mc-urgency-critical { border-left: 4px solid #EF4444; }

/* Pills */
.mc-pill {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  height: 24px;
  padding: 0 10px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 600;
  border: 1px solid transparent;
}

.mc-pill-queued { background: #EFF6FF; color: #1D4ED8; border-color: #BFDBFE; }
.mc-pill-inprogress { background: #FFFBEB; color: #B45309; border-color: #FCD34D; }
.mc-pill-done { background: #ECFDF5; color: #047857; border-color: #86EFAC; }
.mc-pill-blocked { background: #FEF2F2; color: #B91C1C; border-color: #FCA5A5; }
.mc-pill-open { background: #EFF6FF; color: #1D4ED8; border-color: #BFDBFE; }
.mc-pill-snoozed { background: #F3F4F6; color: #6B7280; border-color: #D1D5DB; }
.mc-pill-new { background: #EFF6FF; color: #1D4ED8; border-color: #BFDBFE; }

/* Alerts */
.mc-alert {
  border-radius: 12px;
  padding: 10px 12px;
  border: 1px solid;
  margin-bottom: 8px;
  font-size: 14px;
  line-height: 20px;
}

.mc-alert-danger { background:#FEF2F2; border-color:#FCA5A5; color:#991B1B; }
.mc-alert-warning { background:#FFFBEB; border-color:#FCD34D; color:#92400E; }
.mc-alert-info { background:#EFF6FF; border-color:#93C5FD; color:#1E3A8A; }
.mc-alert-success { background:#ECFDF5; border-color:#86EFAC; color:#065F46; }

/* Quick command strip */
.mc-command-bar {
  background: linear-gradient(135deg, #1A1A2E 0%, #232347 100%);
  border: 1px solid rgba(255,255,255,0.08);
  border-radius: 16px;
  padding: 12px;
  margin: 8px 0 16px;
}

.stTextInput input, .stTextArea textarea, .stSelectbox div[data-baseweb="select"] {
  border-radius: 10px !important;
  border: 1px solid var(--border-strong) !important;
}

.stTextInput input:focus, .stTextArea textarea:focus {
  border-color: var(--accent-primary) !important;
  box-shadow: 0 0 0 3px rgba(108,92,231,.20) !important;
}

.stButton > button {
  border-radius: 10px !important;
  border: 1px solid var(--border-subtle) !important;
  height: 38px;
  font-weight: 600;
}

/* Primary action button if wrapped in class context */
.mc-primary-btn .stButton > button {
  background: var(--accent-primary) !important;
  color: #fff !important;
  border-color: var(--accent-primary) !important;
}

.mc-primary-btn .stButton > button:hover {
  background: var(--accent-primary-hover) !important;
  border-color: var(--accent-primary-hover) !important;
}

/* Dataframe readability */
[data-testid="stDataFrame"] {
  border: 1px solid var(--border-subtle);
  border-radius: 12px;
  overflow: hidden;
}

.streamlit-expanderHeader {
  font-size: 14px !important;
  font-weight: 600 !important;
  color: var(--text-primary) !important;
}

.skill-chip {
  display: inline-block;
  padding: 3px 10px;
  margin: 2px;
  border-radius: 12px;
  font-size: 11px;
  font-weight: 600;
}
</style>
""", unsafe_allow_html=True)

init_db()
quick_seed()

# ---------- Agent team ----------
AGENTS = {
    "Mr Brain": {"emoji": "🧠", "role": "Orchestrator + Product", "color": "#6C5CE7", "skills": 20},
    "Mr Engineering": {"emoji": "💻", "role": "Engineering Lead", "color": "#0984E3", "skills": 10},
    "Mr Design": {"emoji": "🎨", "role": "Design Lead", "color": "#E17055", "skills": 9},
    "Mr Marketing": {"emoji": "📢", "role": "Marketing Lead", "color": "#00B894", "skills": 8},
    "Mr Analytics": {"emoji": "📊", "role": "Data & Insights Lead", "color": "#6F42C1", "skills": 10},
    "Mr Support": {"emoji": "🤝", "role": "Customer & Compliance Lead", "color": "#E84393", "skills": 9},
    "Mr Spatial": {"emoji": "🥽", "role": "Spatial Computing & XR Lead", "color": "#00CEC9", "skills": 9},
    "Mr QA": {"emoji": "🧪", "role": "Testing & Quality Lead", "color": "#A29BFE", "skills": 11},
}

AGENT_WORKSPACES = {
    "Mr Brain": Path.home() / ".openclaw/workspace/skills",
    "Mr Engineering": Path.home() / ".openclaw/workspace-mr-engineering/skills",
    "Mr Design": Path.home() / ".openclaw/workspace-mr-design/skills",
    "Mr Marketing": Path.home() / ".openclaw/workspace-mr-marketing/skills",
    "Mr Analytics": Path.home() / ".openclaw/workspace-mr-analytics/skills",
    "Mr Support": Path.home() / ".openclaw/workspace-mr-support/skills",
    "Mr Spatial": Path.home() / ".openclaw/workspace-mr-spatial/skills",
    "Mr QA": Path.home() / ".openclaw/workspace-mr-qa/skills",
}


# ---------- Helper: status pill HTML ----------
def pill(label: str) -> str:
    """Return an HTML status pill badge for a given status/urgency label."""
    mapping = {
        "Queued": "queued",
        "In Progress": "inprogress",
        "Done": "done",
        "Blocked": "blocked",
        "Open": "open",
        "Snoozed": "snoozed",
        "New": "new",
        "Low": "done",
        "Medium": "queued",
        "High": "inprogress",
        "Critical": "blocked",
    }
    cls = mapping.get(label, "queued")
    return f'<span class="mc-pill mc-pill-{cls}">{label}</span>'


def urgency_class(urgency: str) -> str:
    return {
        "Low": "mc-urgency-low",
        "Medium": "mc-urgency-medium",
        "High": "mc-urgency-high",
        "Critical": "mc-urgency-critical",
    }.get(urgency, "mc-urgency-medium")


# ===================== ROUTING =====================
def load_agent_routing():
    cfg_path = Path(__file__).parent / "agent-routing.json"
    if not cfg_path.exists():
        return {"orchestrator": "Mr Brain", "agents": [], "routingPolicy": {"default": "Mr Marketing"}}
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
    reason_text = "matched: " + ", ".join(reasons.get(primary, [])) if reasons.get(primary) else "fallback routing"
    return {"primary": primary, "secondary": secondary, "confidence": confidence, "reason": reason_text}


routing_cfg = load_agent_routing()
agent_names = [a.get("name") for a in routing_cfg.get("agents", []) if a.get("name")]


# ===================== AGENT DETAIL PAGE =====================
def render_agent_page(agent_name):
    """Render individual agent detail page."""
    info = AGENTS.get(agent_name, {})
    if not info:
        st.error(f"Unknown agent: {agent_name}")
        return

    if st.button("← Back to Dashboard"):
        st.query_params.clear()
        st.rerun()

    st.markdown(f"""
    <div style="display:flex;align-items:center;gap:16px;margin-bottom:20px;">
        <span style="font-size:64px;filter:drop-shadow(0 3px 8px rgba(0,0,0,0.2));">{info['emoji']}</span>
        <div>
            <h1 style="margin:0;font-size:28px;color:#2d3436;">{agent_name}</h1>
            <p style="margin:0;color:{info['color']};font-weight:600;text-transform:uppercase;letter-spacing:1px;font-size:13px;">{info['role']}</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    sync_agent_status(agent_name)
    s_df = fetch_df("SELECT * FROM agent_status WHERE agent_name = ?", [agent_name])
    status = "Idle"
    current_task = ""
    if not s_df.empty:
        status = s_df.iloc[0].get("status", "Idle")
        current_task = s_df.iloc[0].get("current_task", "") or ""

    status_colors = {"Busy": "#00B894", "Standby": "#FDCB6E", "Idle": "#B2BEC3", "Away": "#D63031"}
    status_labels = {"Busy": "🟢 WORKING", "Standby": "🟡 STANDBY", "Idle": "⚪ IDLE", "Away": "🔴 AWAY"}
    sc = status_colors.get(status, "#B2BEC3")

    stats = fetch_df("""
        SELECT
            SUM(CASE WHEN status = 'Queued' THEN 1 ELSE 0 END) as queued,
            SUM(CASE WHEN status = 'In Progress' THEN 1 ELSE 0 END) as in_progress,
            SUM(CASE WHEN status = 'Done' THEN 1 ELSE 0 END) as done,
            COUNT(*) as total
        FROM ai_jobs WHERE assigned_agent = ?
    """, [agent_name])
    sr = stats.iloc[0] if not stats.empty else {}

    k1, k2, k3, k4 = st.columns(4)
    k1.markdown(f"""<div style="text-align:center;padding:12px;border-radius:12px;background:{sc}15;border:1px solid {sc}30;">
        <div style="font-size:11px;color:#636e72;text-transform:uppercase;letter-spacing:1px;">Status</div>
        <div style="font-size:18px;font-weight:700;color:{sc};">{status_labels.get(status, '⚪ IDLE')}</div>
    </div>""", unsafe_allow_html=True)
    k2.metric("Queued", int(sr.get("queued", 0) or 0))
    k3.metric("In Progress", int(sr.get("in_progress", 0) or 0))
    k4.metric("Done", int(sr.get("done", 0) or 0))

    if current_task:
        st.info(f"💬 Currently working on: **{current_task}**")

    a_tab1, a_tab2, a_tab3, a_tab4 = st.tabs(["📋 Active Jobs", "✅ Completed", "📜 Activity Log", "🔧 Skills"])

    with a_tab1:
        active = fetch_df("""
            SELECT id, request, status, priority, output, created_at, updated_at
            FROM ai_jobs WHERE assigned_agent = ? AND status != 'Done'
            ORDER BY CASE priority WHEN 'Critical' THEN 1 WHEN 'High' THEN 2 WHEN 'Medium' THEN 3 ELSE 4 END, id DESC
        """, [agent_name])
        if active.empty:
            st.caption("No active jobs. This agent is available.")
        else:
            for _, job in active.iterrows():
                priority_colors = {"Critical": "🔴", "High": "🟠", "Medium": "🟡", "Low": "🟢"}
                pc = priority_colors.get(job["priority"], "⚪")
                with st.expander(f"{pc} #{job['id']} — {str(job['request'])[:80]} [{job['status']}]", expanded=True):
                    st.markdown(f"**Priority:** {job['priority']} · **Status:** {job['status']}")
                    st.markdown(f"**Created:** {job['created_at']} · **Updated:** {job['updated_at']}")
                    if job.get("output"):
                        st.markdown("**Output:**")
                        st.markdown(str(job["output"]))
                    c1, c2, c3 = st.columns(3)
                    with c1:
                        if st.button("▶️ Run", key=f"run_{job['id']}"):
                            update_ai_job(int(job['id']), {"status": "In Progress"})
                            st.rerun()
                    with c2:
                        if st.button("✅ Done", key=f"done_{job['id']}"):
                            update_ai_job(int(job['id']), {"status": "Done"})
                            st.rerun()
                    with c3:
                        if st.button("↩️ Re-queue", key=f"requeue_{job['id']}"):
                            update_ai_job(int(job['id']), {"status": "Queued"})
                            st.rerun()

    with a_tab2:
        done = fetch_df("""
            SELECT id, request, output, priority, created_at, updated_at
            FROM ai_jobs WHERE assigned_agent = ? AND status = 'Done'
            ORDER BY updated_at DESC LIMIT 20
        """, [agent_name])
        if done.empty:
            st.caption("No completed jobs yet.")
        else:
            for _, job in done.iterrows():
                with st.expander(f"✅ #{job['id']} — {str(job['request'])[:80]}"):
                    st.markdown(f"**Completed:** {job['updated_at']} · **Priority:** {job['priority']}")
                    st.markdown("---")
                    st.markdown(str(job.get("output", "") or "No output saved."))

    with a_tab3:
        events = fetch_df("""
            SELECT e.created_at, e.event_type, e.details, e.job_id
            FROM ai_job_events e
            JOIN ai_jobs j ON j.id = e.job_id
            WHERE j.assigned_agent = ?
            ORDER BY e.id DESC LIMIT 30
        """, [agent_name])
        if events.empty:
            st.caption("No activity recorded yet.")
        else:
            for _, ev in events.iterrows():
                icon = "✏️" if ev["event_type"] == "updated" else "➕"
                st.markdown(f"""<div style="font-size:12px;padding:4px 0;border-bottom:1px solid #f0f0f0;">
                    {icon} <strong>Job #{ev['job_id']}</strong> — {ev['details']}
                    <span style="color:#b2bec3;float:right;">{ev['created_at']}</span>
                </div>""", unsafe_allow_html=True)

    with a_tab4:
        ws_path = AGENT_WORKSPACES.get(agent_name)
        if ws_path and ws_path.exists():
            skill_list = sorted([
                d.name for d in ws_path.iterdir()
                if d.is_dir() and (d / "SKILL.md").exists()
            ])
            if skill_list:
                chips = ""
                for sn in skill_list:
                    chips += f'<span class="skill-chip" style="background:{info["color"]}15;color:{info["color"]};border:1px solid {info["color"]}30;">{sn}</span>'
                st.markdown(f'<div style="margin:8px 0;">{chips}</div>', unsafe_allow_html=True)
                st.caption(f"{len(skill_list)} skills installed")
                for sn in skill_list:
                    skill_md = ws_path / sn / "SKILL.md"
                    if skill_md.exists():
                        desc = ""
                        for line in skill_md.read_text().split("\n"):
                            if line.startswith("description:"):
                                desc = line.replace("description:", "").strip().strip('"')[:120]
                                break
                        st.markdown(f"**{sn}** — {desc}" if desc else f"**{sn}**")
            else:
                st.caption("No skills found.")
        else:
            st.caption("Workspace not accessible.")


# ===================== CHECK FOR AGENT PAGE =====================
params = st.query_params
if params.get("agent"):
    render_agent_page(params["agent"])
    st.stop()


# ===================== MAIN DASHBOARD =====================

# ---------- Read-only mode for cloud deployment ----------
_hostname = socket.getfqdn().lower()
READONLY = (
    os.environ.get("READONLY", "0") == "1"
    or "streamlit" in _hostname
    or not Path.home().joinpath(".openclaw").exists()
)

# ---------- Sticky header with dark background ----------
st.markdown("""
<div class="mc-sticky-header">
  <p class="mc-title">🧭 Mr Kai's Mission Control</p>
  <p class="mc-subtitle">Executive command center · Powered by Mr Brain + 7 specialist agents</p>
</div>
""", unsafe_allow_html=True)

# ---------- Agent cards — single row of 8 ----------
agent_items = list(AGENTS.items())
agent_cols = st.columns(8)
for col, (name, info) in zip(agent_cols, agent_items):
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
        glow_style = f"box-shadow: 0 0 0 2px {info['color']}33, 0 10px 24px rgba(17,24,39,0.12);" if active_count > 0 else ""
        st.markdown(
            f"""<div class="mc-agent-card" style="{glow_style}">
                <div style="text-align:center;">
                    <div style="font-size:36px;filter:drop-shadow(0 2px 4px rgba(0,0,0,0.15));">{info['emoji']}</div>
                    <div style="font-weight:800;font-size:12px;margin-top:4px;color:#111827;">{name}</div>
                    <div style="font-size:10px;color:{info['color']};font-weight:600;text-transform:uppercase;letter-spacing:0.5px;margin-top:2px;">{info['role'][:18]}</div>
                    <div style="display:flex;justify-content:center;gap:4px;margin-top:6px;font-size:10px;color:#6B7280;flex-wrap:wrap;">
                        <span>{status_dot} {active_count}</span><span>·</span><span>✅{done_count}</span>
                    </div>
                </div>
            </div>""",
            unsafe_allow_html=True,
        )
        if st.button(f"Open", key=f"open_{name}", use_container_width=True):
            st.query_params["agent"] = name
            st.rerun()

st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

# ---------- Quick Command Bar ----------
if not READONLY:
    st.markdown('<div class="mc-command-bar">', unsafe_allow_html=True)
    with st.form("quick_command_form", clear_on_submit=True):
        qc1, qc2 = st.columns([5, 1])
        with qc1:
            quick_cmd = st.text_input(
                "⚡ Quick Command",
                placeholder="Type a task — Mr Brain routes it to the right agent automatically...",
                label_visibility="collapsed",
            )
        with qc2:
            quick_send = st.form_submit_button("🧠 Send", use_container_width=True)

        if quick_send and quick_cmd.strip():
            txt = quick_cmd.lower()
            best_agent = routing_cfg.get("routingPolicy", {}).get("default", "Mr Marketing")
            best_score = -1
            for agent in routing_cfg.get("agents", []):
                score = sum(1 for t in agent.get("triggers", []) if t.lower() in txt)
                if score > best_score:
                    best_score = score
                    best_agent = agent.get("name", best_agent)

            job_id = add_ai_job({
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
            })
            if job_id:
                update_ai_job(job_id, {"status": "In Progress", "route_reason": f"auto-triggered → {best_agent}"})
            st.success(f"✅ Auto-triggered **{best_agent}** — Job #{job_id}")
    st.markdown('</div>', unsafe_allow_html=True)

# ---------- Filters ----------
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
        urgency_f = st.multiselect("Urgency", ["Low", "Medium", "High", "Critical"], default=["Low", "Medium", "High", "Critical"], key="top_urgency")
    with fc5:
        status_f = st.multiselect("Task status", ["Open", "In Progress", "Blocked", "Done", "Snoozed"], default=["Open", "In Progress", "Blocked", "Done", "Snoozed"], key="top_status")
    with fc6:
        hide_done = st.checkbox("Hide done", value=True, key="top_hide_done")

where = ["1=1"]
filter_params = []
if company_f != "All":
    where.append("company = ?"); filter_params.append(company_f)
if owner_f.strip():
    where.append("owner LIKE ?"); filter_params.append(f"%{owner_f.strip()}%")
if text_f.strip():
    where.append("(title LIKE ? OR project LIKE ? OR notes LIKE ?)")
    like = f"%{text_f.strip()}%"; filter_params.extend([like, like, like])
if urgency_f:
    where.append("urgency IN ({})".format(",".join(["?"] * len(urgency_f)))); filter_params.extend(urgency_f)
if status_f:
    where.append("status IN ({})".format(",".join(["?"] * len(status_f)))); filter_params.extend(status_f)
if hide_done:
    where.append("status != 'Done'")

where_clause = " AND ".join(where)

# ---------- KPI row ----------
kpi = fetch_df(f"""
    SELECT
      SUM(CASE WHEN status IN ('Open','In Progress','Blocked','Snoozed') THEN 1 ELSE 0 END) AS open_tasks,
      SUM(CASE WHEN needs_decision = 1 AND status != 'Done' THEN 1 ELSE 0 END) AS escalations,
      SUM(CASE WHEN due_date != '' AND due_date IS NOT NULL AND date(due_date) < date('now') AND status != 'Done' THEN 1 ELSE 0 END) AS overdue,
      SUM(CASE WHEN due_date != '' AND due_date IS NOT NULL AND date(due_date) = date('now') AND status != 'Done' THEN 1 ELSE 0 END) AS due_today
    FROM tasks WHERE {where_clause}
""", filter_params)

c1, c2, c3, c4 = st.columns(4)
open_tasks_val = int(kpi.iloc[0]["open_tasks"] or 0)
escalations_val = int(kpi.iloc[0]["escalations"] or 0)
overdue_val = int(kpi.iloc[0]["overdue"] or 0)
due_today_val = int(kpi.iloc[0]["due_today"] or 0)
c1.metric("Open Tasks", open_tasks_val)
c2.metric("Escalations", escalations_val)
c3.metric("Overdue", overdue_val)
c4.metric("Due Today", due_today_val)

# ---------- Smart Alerts (using mc-alert CSS classes) ----------
alerts_html = []
if overdue_val > 0:
    alerts_html.append(f'<div class="mc-alert mc-alert-danger">🔴 <strong>{overdue_val} overdue task(s)</strong> — need attention now</div>')
if escalations_val > 0:
    alerts_html.append(f'<div class="mc-alert mc-alert-warning">🟠 <strong>{escalations_val} escalation(s)</strong> — waiting for your decision</div>')
if due_today_val > 0:
    alerts_html.append(f'<div class="mc-alert mc-alert-info">🟡 <strong>{due_today_val} task(s) due today</strong> — check before EOD</div>')

stale_jobs = fetch_df("SELECT COUNT(*) as cnt FROM ai_jobs WHERE status = 'In Progress' AND datetime(updated_at) < datetime('now', '-24 hours')")
stale_count = int(stale_jobs.iloc[0]["cnt"] or 0)
if stale_count > 0:
    alerts_html.append(f'<div class="mc-alert mc-alert-warning">⚪ <strong>{stale_count} AI job(s)</strong> stuck In Progress for 24h+</div>')

if alerts_html:
    with st.expander(f"🔔 Smart Alerts ({len(alerts_html)})", expanded=True):
        st.markdown("".join(alerts_html), unsafe_allow_html=True)
else:
    st.markdown('<div class="mc-alert mc-alert-success">🔔 No alerts — all clear</div>', unsafe_allow_html=True)

# ---------- Today Focus ----------
focus = fetch_df(f"""
    SELECT id, title, company, owner, urgency, status, due_date
    FROM tasks WHERE {where_clause}
    ORDER BY CASE urgency WHEN 'Critical' THEN 1 WHEN 'High' THEN 2 WHEN 'Medium' THEN 3 ELSE 4 END,
             COALESCE(NULLIF(due_date,''), '9999-12-31')
    LIMIT 5
""", filter_params)

with st.expander("🎯 Today Focus (Top 5)", expanded=True):
    if focus.empty:
        st.info("No tasks in current filter.")
    else:
        st.dataframe(focus, use_container_width=True, hide_index=True)

# ---------- 5 Tabs ----------
tab_office, tab_jobs, tab_tasks, tab_inbox, tab_settings = st.tabs(
    ["🏢 Office", "🤖 Jobs", "📋 Tasks", "📨 Inbox", "⚙️ Settings"]
)


# ==================== OFFICE TAB ====================
with tab_office:
    for aname in AGENTS:
        sync_agent_status(aname)

    statuses_df = fetch_df("SELECT * FROM agent_status")
    agent_statuses = {row["agent_name"]: dict(row) for _, row in statuses_df.iterrows()} if not statuses_df.empty else {}

    office_html_path = Path(__file__).parent / "components" / "virtual_office.html"
    if office_html_path.exists():
        office_html = office_html_path.read_text()
        agent_map = {
            "brain": "Mr Brain", "engineering": "Mr Engineering", "design": "Mr Design",
            "marketing": "Mr Marketing", "analytics": "Mr Analytics", "support": "Mr Support",
            "spatial": "Mr Spatial", "qa": "Mr QA",
        }
        update_js = "<script>document.addEventListener('DOMContentLoaded', function(){ "
        for key, full_name in agent_map.items():
            s = agent_statuses.get(full_name, {})
            status = s.get("status", "Idle")
            task = (s.get("current_task", "") or "").replace("'", "\\'")[:80]
            update_js += f"updateAgent('{key}', '{status}', '{task}'); "
        update_js += "});</script>"
        office_html = office_html.replace("</body>", update_js + "</body>")
        components.html(office_html, height=560, scrolling=False)
    else:
        st.info("Virtual office component not found.")

    STATUS_META = {
        "Busy": {"dot": "🟢", "label": "WORKING"},
        "Standby": {"dot": "🟡", "label": "STANDBY"},
        "Idle": {"dot": "⚪", "label": "IDLE"},
        "Away": {"dot": "🔴", "label": "AWAY"},
    }

    for aname, ainfo in AGENTS.items():
        s = agent_statuses.get(aname, {})
        status = s.get("status", "Idle")
        sm = STATUS_META.get(status, STATUS_META["Idle"])
        with st.expander(f"{ainfo['emoji']} {aname} — {sm['dot']} {sm['label']}", expanded=False):
            st.markdown(f"[🔗 Open full agent page](?agent={aname.replace(' ', '+')})")
            agent_jobs = fetch_df("""
                SELECT id, request, status, priority, updated_at FROM ai_jobs
                WHERE assigned_agent = ? AND status != 'Done'
                ORDER BY CASE priority WHEN 'Critical' THEN 1 WHEN 'High' THEN 2 WHEN 'Medium' THEN 3 ELSE 4 END, id DESC LIMIT 10
            """, [aname])
            if agent_jobs.empty:
                st.caption("No active jobs.")
            else:
                st.dataframe(agent_jobs, use_container_width=True, hide_index=True)

            done_jobs = fetch_df("SELECT id, request, output, updated_at FROM ai_jobs WHERE assigned_agent = ? AND status = 'Done' ORDER BY updated_at DESC LIMIT 3", [aname])
            if not done_jobs.empty:
                st.caption(f"**Recently completed ({len(done_jobs)})**")
                for _, dj in done_jobs.iterrows():
                    with st.expander(f"✅ #{dj['id']} — {str(dj['request'])[:60]}"):
                        st.markdown(str(dj.get("output", "") or "No output saved."))

    if st.button("🔄 Refresh Office"):
        st.rerun()


# ==================== JOBS TAB (Team + AI Workers merged) ====================
with tab_jobs:
    job_section_team, job_section_ai = st.tabs(["👥 Team Overview", "🤖 AI Workers"])

    # -- Team Overview sub-tab --
    with job_section_team:
        st.subheader("Agent Team Overview")
        for name, info in AGENTS.items():
            with st.expander(f"{info['emoji']} {name} — {info['role']}", expanded=False):
                st.markdown(f"[🔗 Open full agent page](?agent={name.replace(' ', '+')})")
                team_jobs = fetch_df("SELECT status, COUNT(*) as cnt FROM ai_jobs WHERE assigned_agent = ? GROUP BY status", [name])
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
                recent = fetch_df("SELECT id, request, status, updated_at FROM ai_jobs WHERE assigned_agent = ? ORDER BY updated_at DESC LIMIT 5", [name])
                if not recent.empty:
                    st.dataframe(recent, use_container_width=True, hide_index=True)

    # -- AI Workers sub-tab --
    with job_section_ai:
        st.subheader("AI Workers")
        jobs = fetch_df("SELECT id, assigned_agent, reviewer_agent, job_type, company, request, owner, priority, status, route_reason, output FROM ai_jobs ORDER BY id DESC")

        view_agents = ["All"] + sorted([a for a in jobs["assigned_agent"].dropna().unique().tolist() if a]) if not jobs.empty else ["All"]
        vf1, vf2 = st.columns(2)
        with vf1:
            agent_view = st.selectbox("Filter by agent", view_agents, key="ai_filter_agent")
        with vf2:
            status_view = st.selectbox("Filter by status", ["All", "Queued", "In Progress", "Done", "Blocked"], key="ai_filter_status")

        filtered_jobs = jobs.copy()
        if agent_view != "All":
            filtered_jobs = filtered_jobs[filtered_jobs["assigned_agent"] == agent_view]
        if status_view != "All":
            filtered_jobs = filtered_jobs[filtered_jobs["status"] == status_view]

        # Summary table with status pills
        if not filtered_jobs.empty:
            agent_emojis = {n: i["emoji"] for n, i in AGENTS.items()}
            # Build display with HTML pills
            rows_html = ""
            for _, jrow in filtered_jobs.iterrows():
                ae = agent_emojis.get(jrow["assigned_agent"], "🤖")
                req_snippet = str(jrow["request"])[:60] + ("…" if len(str(jrow["request"])) > 60 else "")
                status_badge = pill(jrow["status"])
                pri_badge = pill(jrow["priority"])
                rows_html += f"""<tr>
                  <td style="padding:6px 10px;font-size:13px;color:#6B7280;">#{int(jrow['id'])}</td>
                  <td style="padding:6px 10px;font-size:13px;">{ae} {jrow['assigned_agent']}</td>
                  <td style="padding:6px 10px;font-size:13px;max-width:300px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">{req_snippet}</td>
                  <td style="padding:6px 10px;">{status_badge}</td>
                  <td style="padding:6px 10px;">{pri_badge}</td>
                </tr>"""
            st.markdown(f"""
            <table style="width:100%;border-collapse:collapse;background:#fff;border:1px solid #E5E7EB;border-radius:12px;overflow:hidden;">
              <thead>
                <tr style="background:#F9FAFB;font-size:12px;text-transform:uppercase;letter-spacing:0.04em;color:#6B7280;">
                  <th style="padding:8px 10px;text-align:left;font-weight:600;">ID</th>
                  <th style="padding:8px 10px;text-align:left;font-weight:600;">Agent</th>
                  <th style="padding:8px 10px;text-align:left;font-weight:600;">Request</th>
                  <th style="padding:8px 10px;text-align:left;font-weight:600;">Status</th>
                  <th style="padding:8px 10px;text-align:left;font-weight:600;">Priority</th>
                </tr>
              </thead>
              <tbody>{rows_html}</tbody>
            </table>
            """, unsafe_allow_html=True)
        else:
            st.info("No jobs match filters.")

        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

        # Clear done button
        done_count = int(fetch_df("SELECT COUNT(*) as cnt FROM ai_jobs WHERE status='Done'").iloc[0]["cnt"] or 0)
        if done_count > 0:
            if st.button(f"🗑️ Clear all done jobs ({done_count})", key="clear_done_jobs"):
                from db import get_conn
                with get_conn() as conn:
                    conn.execute("DELETE FROM ai_job_events WHERE job_id IN (SELECT id FROM ai_jobs WHERE status='Done')")
                    conn.execute("DELETE FROM ai_jobs WHERE status='Done'")
                st.rerun()

        # Per-job management via expanders with status pill + dropdown reassign
        st.markdown("##### Manage Jobs")
        manage_jobs = fetch_df("SELECT id, assigned_agent, status, request, priority FROM ai_jobs ORDER BY id DESC LIMIT 50")
        if not manage_jobs.empty:
            priority_icons = {"Critical": "🔴", "High": "🟠", "Medium": "🟡", "Low": "🟢"}
            for _, jrow in manage_jobs.iterrows():
                jid = int(jrow["id"])
                agent_emoji = AGENTS.get(jrow["assigned_agent"], {}).get("emoji", "🤖")
                pi = priority_icons.get(jrow["priority"], "⚪")
                req_short = str(jrow["request"])[:55]
                with st.expander(f"{pi} #{jid} — {agent_emoji} {jrow['assigned_agent']} · {req_short}", expanded=False):
                    full_job = fetch_df("SELECT * FROM ai_jobs WHERE id = ?", [jid]).iloc[0].to_dict()

                    # Status pill display
                    st.markdown(pill(jrow["status"]), unsafe_allow_html=True)

                    # Status + Reassign row
                    jr1, jr2 = st.columns(2)
                    with jr1:
                        new_status_j = st.selectbox("Status", ["Queued", "In Progress", "Done", "Blocked"],
                                                    index=["Queued", "In Progress", "Done", "Blocked"].index(jrow["status"]) if jrow["status"] in ["Queued", "In Progress", "Done", "Blocked"] else 0,
                                                    key=f"js_{jid}")
                    with jr2:
                        all_names = list(AGENTS.keys())
                        current_idx = all_names.index(jrow["assigned_agent"]) if jrow["assigned_agent"] in all_names else 0
                        new_agent = st.selectbox("Reassign to", all_names, index=current_idx, key=f"ja_{jid}")

                    jb1, jb2, jb3 = st.columns(3)
                    with jb1:
                        if st.button("💾 Save", key=f"jsave_{jid}", use_container_width=True):
                            update_ai_job(jid, {"status": new_status_j, "assigned_agent": new_agent, "route_reason": f"manual → {new_agent}"})
                            st.rerun()
                    with jb2:
                        if st.button("📄 Clone", key=f"jclone_{jid}", use_container_width=True):
                            add_ai_job({"job_type": full_job.get("job_type", "assistant"), "company": full_job.get("company", ""),
                                       "request": full_job.get("request", ""), "owner": full_job.get("owner", ""),
                                       "priority": full_job.get("priority", "Medium"), "status": "Queued", "output": "",
                                       "assigned_agent": full_job.get("assigned_agent", "Mr Brain"),
                                       "reviewer_agent": "", "route_reason": f"cloned from #{jid}"}); st.rerun()
                    with jb3:
                        if st.button("🗑️ Delete", key=f"jdel_{jid}", use_container_width=True):
                            from db import get_conn
                            with get_conn() as conn:
                                conn.execute("DELETE FROM ai_job_events WHERE job_id=?", [jid])
                                conn.execute("DELETE FROM ai_jobs WHERE id=?", [jid])
                            st.rerun()

                    if full_job.get("output"):
                        with st.expander("📄 View Output"):
                            st.markdown(str(full_job["output"]))

                    if full_job.get("route_reason"):
                        st.caption(f"Routing: {full_job['route_reason']}")

        with st.expander("➕ Queue AI job"):
            j_type = st.selectbox("Type", ["assistant", "graphic", "video", "copy", "programmer"])
            j_company = st.selectbox("Company", companies[1:] if len(companies) > 1 else ["Shared/Personal"], key="jcompany")
            j_req = st.text_area("Request")
            j_owner = st.text_input("Owner", key="jowner")
            j_priority = st.selectbox("Priority", ["Low", "Medium", "High", "Critical"], key="jpriority")
            decision = route_decision(j_req, j_type, routing_cfg)
            st.caption(f"Suggested: **{decision['primary']}** — {decision['reason']}")
            all_agent_names = list(AGENTS.keys())
            selected_agent = st.selectbox("Assigned agent", all_agent_names,
                                          index=all_agent_names.index(decision["primary"]) if decision["primary"] in all_agent_names else 0)
            if st.button("Add AI job"):
                if j_req.strip():
                    add_ai_job({"job_type": j_type, "company": j_company, "request": j_req.strip(), "owner": j_owner.strip(),
                               "priority": j_priority, "status": "Queued", "output": "", "assigned_agent": selected_agent,
                               "reviewer_agent": decision.get("secondary", ""), "route_reason": decision["reason"]})
                    st.success("Queued"); st.rerun()


# ==================== TASKS TAB ====================
with tab_tasks:
    st.subheader("Task + Follow-up Control")
    tasks = fetch_df(f"""
        SELECT id, title, company, project, owner, urgency, status, due_date, snooze_until, needs_decision, notes
        FROM tasks WHERE {where_clause}
        ORDER BY CASE urgency WHEN 'Critical' THEN 1 WHEN 'High' THEN 2 WHEN 'Medium' THEN 3 ELSE 4 END,
                 COALESCE(NULLIF(due_date,''), '9999-12-31')
    """, filter_params)

    if tasks.empty:
        st.info("No tasks match your filters.")
    else:
        for _, task in tasks.iterrows():
            tid = int(task["id"])
            urg = task["urgency"]
            urg_css = urgency_class(urg)
            status_badge = pill(task["status"])
            due_str = task["due_date"] or "no date"
            owner_str = task["owner"] or "—"

            # Task row card with urgency stripe
            st.markdown(f"""
            <div class="mc-row-card {urg_css}" style="margin-bottom:6px;">
              <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:8px;">
                <div style="flex:1;min-width:0;">
                  <span style="font-size:14px;font-weight:600;color:#111827;">#{tid} — {task['title']}</span>
                  <span style="margin-left:8px;">{status_badge}</span>
                </div>
                <div style="font-size:12px;color:#6B7280;white-space:nowrap;">
                  {task['company']} · {owner_str} · {due_str}
                </div>
              </div>
              {f'<div style="font-size:12px;color:#4B5563;margin-top:4px;">📝 {task["notes"]}</div>' if task.get("notes") else ""}
            </div>
            """, unsafe_allow_html=True)

            # Actions in expander for cleaner look
            with st.expander(f"⚙️ Actions — #{tid}", expanded=False):
                # Quick actions
                bc1, bc2, bc3 = st.columns(3)
                with bc1:
                    if st.button("✅ Done", key=f"done_t_{tid}", use_container_width=True):
                        update_task(tid, {"status": "Done"}); st.rerun()
                with bc2:
                    if st.button("💤 Snooze", key=f"snz_{tid}", use_container_width=True):
                        update_task(tid, {"status": "Snoozed", "snooze_until": (datetime.now() + timedelta(days=1)).date().isoformat()}); st.rerun()
                with bc3:
                    if st.button("🗑️ Delete", key=f"del_{tid}", use_container_width=True):
                        from db import get_conn
                        with get_conn() as conn:
                            conn.execute("DELETE FROM tasks WHERE id=?", [tid])
                        st.rerun()

                # Edit — hidden in nested expander
                with st.expander("✏️ Edit", expanded=False):
                    ec1, ec2 = st.columns(2)
                    with ec1:
                        new_status = st.selectbox("Status", ["Open", "In Progress", "Blocked", "Done", "Snoozed"],
                                                  index=["Open", "In Progress", "Blocked", "Done", "Snoozed"].index(task["status"]) if task["status"] in ["Open", "In Progress", "Blocked", "Done", "Snoozed"] else 0,
                                                  key=f"ts_{tid}")
                        new_urgency = st.selectbox("Urgency", ["Low", "Medium", "High", "Critical"],
                                                   index=["Low", "Medium", "High", "Critical"].index(task["urgency"]) if task["urgency"] in ["Low", "Medium", "High", "Critical"] else 1,
                                                   key=f"tu_{tid}")
                    with ec2:
                        new_owner = st.text_input("Owner", value=task["owner"] or "", key=f"to_{tid}")
                        new_notes = st.text_input("Notes", value=task["notes"] or "", key=f"tn_{tid}")
                    sc1, sc2 = st.columns(2)
                    with sc1:
                        if st.button("💾 Save changes", key=f"save_{tid}", use_container_width=True):
                            update_task(tid, {"status": new_status, "urgency": new_urgency, "owner": new_owner.strip(), "notes": new_notes.strip()})
                            st.rerun()
                    with sc2:
                        if st.button("🤖 Create AI Job", key=f"aijob_{tid}", use_container_width=True):
                            decision = route_decision(f"{task['title']} {task.get('notes','')}", "assistant", routing_cfg)
                            add_ai_job({"job_type": "assistant", "company": task["company"], "request": task["title"],
                                       "owner": task.get("owner", ""), "priority": task["urgency"], "status": "Queued", "output": "",
                                       "assigned_agent": decision["primary"], "reviewer_agent": "", "route_reason": decision["reason"]})
                            st.success(f"AI job created → {decision['primary']}"); st.rerun()

    # Clear done tasks button
    done_tasks_count = int(fetch_df("SELECT COUNT(*) as cnt FROM tasks WHERE status='Done'").iloc[0]["cnt"] or 0)
    if done_tasks_count > 0:
        if st.button(f"🗑️ Clear all done tasks ({done_tasks_count})", key="clear_done_tasks"):
            from db import get_conn
            with get_conn() as conn:
                conn.execute("DELETE FROM tasks WHERE status='Done'")
            st.rerun()

    st.divider()

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
            if t_title.strip():
                add_task({"title": t_title.strip(), "company": t_company, "project": t_project.strip(),
                          "owner": t_owner.strip(), "urgency": t_urgency, "status": t_status,
                          "due_date": t_due.isoformat() if t_due else "", "snooze_until": "",
                          "needs_decision": 1 if t_decision else 0, "notes": t_notes.strip()})
                if t_auto_assign:
                    combined = f"{t_title} {t_notes} {t_project}".lower()
                    decision = route_decision(combined, "assistant", routing_cfg)
                    add_ai_job({"job_type": "assistant", "company": t_company, "request": t_title.strip(),
                               "owner": t_owner.strip(), "priority": t_urgency, "status": "Queued", "output": "",
                               "assigned_agent": decision["primary"], "reviewer_agent": decision.get("secondary", ""),
                               "route_reason": decision["reason"]})
                    st.success(f"Task added + AI job → **{decision['primary']}**")
                else:
                    st.success("Task added")
                st.rerun()


# ==================== INBOX TAB (Escalations + Comms + Trends + Feedback) ====================
with tab_inbox:
    inbox_esc, inbox_comms, inbox_trends, inbox_feedback = st.tabs(
        ["🚨 Escalations", "📨 Comms", "🔍 Trends", "💬 Feedback"]
    )

    # -- Escalations --
    with inbox_esc:
        st.subheader("Escalations needing decision")
        esc = fetch_df("""
            SELECT id, title, company, project, owner, urgency, due_date, notes
            FROM tasks WHERE needs_decision = 1 AND status != 'Done'
            ORDER BY CASE urgency WHEN 'Critical' THEN 1 WHEN 'High' THEN 2 WHEN 'Medium' THEN 3 ELSE 4 END
        """)
        if esc.empty:
            st.markdown('<div class="mc-alert mc-alert-success">✅ No escalations pending</div>', unsafe_allow_html=True)
        else:
            for _, row in esc.iterrows():
                urg_css = urgency_class(row["urgency"])
                urg_badge = pill(row["urgency"])
                st.markdown(f"""
                <div class="mc-row-card {urg_css}" style="margin-bottom:6px;">
                  <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:8px;">
                    <div><span style="font-size:14px;font-weight:600;">#{int(row['id'])} — {row['title']}</span> {urg_badge}</div>
                    <div style="font-size:12px;color:#6B7280;">{row['company']} · {row.get('owner','—')} · {row.get('due_date','no date')}</div>
                  </div>
                  {f'<div style="font-size:12px;color:#4B5563;margin-top:4px;">{row["notes"]}</div>' if row.get("notes") else ""}
                </div>
                """, unsafe_allow_html=True)

    # -- Comms --
    with inbox_comms:
        st.subheader("Comms triage")
        comms = fetch_df("SELECT * FROM comms ORDER BY id DESC")
        if comms.empty:
            st.info("No communications logged.")
        else:
            # Display with status pills
            for _, row in comms.iterrows():
                pri_badge = pill(row.get("priority", "Medium"))
                status_badge = pill(row.get("status", "Open"))
                st.markdown(f"""
                <div class="mc-row-card" style="margin-bottom:6px;">
                  <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:8px;">
                    <div><span style="font-size:14px;font-weight:600;">{row['subject']}</span> {pri_badge} {status_badge}</div>
                    <div style="font-size:12px;color:#6B7280;">{row.get('source','—')} · {row.get('company','—')} · {row.get('owner','—')}</div>
                  </div>
                  {f'<div style="font-size:12px;color:#4B5563;margin-top:4px;">{row["notes"]}</div>' if row.get("notes") else ""}
                </div>
                """, unsafe_allow_html=True)

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
                    add_comm({"source": source, "company": company, "subject": subject.strip(), "owner": owner.strip(),
                              "priority": priority, "action_required": 1 if action else 0, "escalated": 1 if escalated else 0,
                              "status": "Open", "notes": notes.strip()})
                    st.success("Added"); st.rerun()

    # -- Trends --
    with inbox_trends:
        st.subheader("🔍 Trend Feed")
        trends = fetch_df("SELECT * FROM trend_feed ORDER BY id DESC LIMIT 50")
        if trends.empty:
            st.info("No trends yet.")
        else:
            for _, row in trends.iterrows():
                rel_badge = pill(row.get("relevance", "Medium"))
                sent_color = {"positive": "#065F46", "negative": "#991B1B", "neutral": "#4B5563"}.get(row.get("sentiment", "neutral"), "#4B5563")
                sent_bg = {"positive": "#ECFDF5", "negative": "#FEF2F2", "neutral": "#F3F4F6"}.get(row.get("sentiment", "neutral"), "#F3F4F6")
                sent_html = f'<span style="background:{sent_bg};color:{sent_color};padding:2px 8px;border-radius:999px;font-size:11px;font-weight:600;">{row.get("sentiment","neutral")}</span>'
                st.markdown(f"""
                <div class="mc-row-card" style="margin-bottom:6px;">
                  <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:8px;">
                    <div><span style="font-size:14px;font-weight:600;">{row['title']}</span> {rel_badge} {sent_html}</div>
                    <div style="font-size:12px;color:#6B7280;">{row.get('company','—')} · {row.get('category','—')}</div>
                  </div>
                  {f'<div style="font-size:12px;color:#4B5563;margin-top:4px;">{row["summary"]}</div>' if row.get("summary") else ""}
                  {f'<div style="font-size:11px;margin-top:4px;"><a href="{row["source_url"]}" target="_blank" style="color:#6C5CE7;">🔗 Source</a></div>' if row.get("source_url") else ""}
                </div>
                """, unsafe_allow_html=True)

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
                    add_trend({"company": tr_company, "category": tr_cat, "title": tr_title.strip(),
                              "summary": tr_summary.strip(), "source_url": tr_url.strip(), "sentiment": tr_sent, "relevance": tr_rel})
                    st.rerun()

    # -- Feedback --
    with inbox_feedback:
        st.subheader("💬 Feedback Inbox")
        feedbacks = fetch_df("SELECT * FROM feedback_inbox ORDER BY id DESC LIMIT 100")
        if feedbacks.empty:
            st.info("No feedback yet.")
        else:
            sent_counts = feedbacks["sentiment"].value_counts()
            s1, s2, s3 = st.columns(3)
            s1.metric("😊 Positive", int(sent_counts.get("positive", 0)))
            s2.metric("😐 Neutral", int(sent_counts.get("neutral", 0)))
            s3.metric("😞 Negative", int(sent_counts.get("negative", 0)))

            for _, row in feedbacks.iterrows():
                sent_color = {"positive": "#065F46", "negative": "#991B1B", "neutral": "#4B5563"}.get(row.get("sentiment", "neutral"), "#4B5563")
                sent_bg = {"positive": "#ECFDF5", "negative": "#FEF2F2", "neutral": "#F3F4F6"}.get(row.get("sentiment", "neutral"), "#F3F4F6")
                sent_html = f'<span style="background:{sent_bg};color:{sent_color};padding:2px 8px;border-radius:999px;font-size:11px;font-weight:600;">{row.get("sentiment","neutral")}</span>'
                status_badge = pill(row.get("status", "New"))
                st.markdown(f"""
                <div class="mc-row-card" style="margin-bottom:6px;">
                  <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:8px;">
                    <div><span style="font-size:13px;font-weight:600;">{row.get('customer','Anonymous')}</span> {sent_html} {status_badge}</div>
                    <div style="font-size:12px;color:#6B7280;">{row.get('source','—')} · {row.get('company','—')}</div>
                  </div>
                  <div style="font-size:13px;color:#374151;margin-top:4px;">{str(row.get('message',''))[:150]}</div>
                  {f'<div style="font-size:11px;color:#6B7280;margin-top:2px;">🏷️ {row["tags"]}</div>' if row.get("tags") else ""}
                </div>
                """, unsafe_allow_html=True)

        with st.expander("➕ Add feedback"):
            fb_company = st.selectbox("Company", companies[1:] if len(companies) > 1 else ["Shared/Personal"], key="fb_co")
            fb_source = st.selectbox("Source", ["Google Review", "Instagram", "TikTok", "Email", "WhatsApp", "Telegram", "In-Store", "Other"], key="fb_src")
            fb_customer = st.text_input("Customer name", key="fb_cust")
            fb_msg = st.text_area("Feedback message", key="fb_msg")
            fb_sent = st.selectbox("Sentiment", ["positive", "neutral", "negative"], index=1, key="fb_sent")
            fb_tags = st.text_input("Tags (comma-separated)", key="fb_tags")
            if st.button("Save feedback"):
                if fb_msg.strip():
                    add_feedback({"company": fb_company, "source": fb_source, "customer": fb_customer.strip(),
                                 "message": fb_msg.strip(), "sentiment": fb_sent, "tags": fb_tags.strip(), "status": "New", "notes": ""})
                    st.rerun()


# ==================== SETTINGS TAB (Automation) ====================
with tab_settings:
    st.subheader("⚙️ Automation Center")

    st.markdown("##### 🧩 Agent Skill Registry")
    for agent_label, ws_path in AGENT_WORKSPACES.items():
        info = AGENTS.get(agent_label, {})
        if ws_path.exists():
            skill_names = sorted([d.name for d in ws_path.iterdir() if d.is_dir() and (d / "SKILL.md").exists()])
            with st.expander(f"{info.get('emoji', '🤖')} {agent_label} — {len(skill_names)} skills"):
                if skill_names:
                    chips = ""
                    for sn in skill_names:
                        c = info.get("color", "#666")
                        chips += f'<span class="skill-chip" style="background:{c}15;color:{c};border:1px solid {c}30;">{sn}</span>'
                    st.markdown(f'<div>{chips}</div>', unsafe_allow_html=True)
                else:
                    st.caption("No skills found.")

    st.divider()
    st.markdown("##### 📊 Weekly Report")
    if st.button("Generate Weekly Report Now"):
        report_lines = [f"## 📊 Weekly Report — {datetime.now().strftime('%Y-%m-%d %H:%M')}"]
        for co_name in ["Mister Mobile", "Food Art", "Shared/Personal"]:
            co_tasks = fetch_df("SELECT status, COUNT(*) as cnt FROM tasks WHERE company = ? GROUP BY status", [co_name])
            co_jobs = fetch_df("SELECT status, COUNT(*) as cnt FROM ai_jobs WHERE company = ? GROUP BY status", [co_name])
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
        st.download_button("📥 Download (.md)", report_text, file_name=f"weekly-report-{datetime.now().strftime('%Y%m%d')}.md", mime="text/markdown")

    st.divider()
    st.markdown("##### 📅 Calendar Export")
    if st.button("Export Calendar (ICS)"):
        cal_tasks = fetch_df("SELECT title, company, due_date, urgency, status FROM tasks WHERE due_date != '' AND due_date IS NOT NULL AND status != 'Done' ORDER BY due_date")
        if cal_tasks.empty:
            st.info("No tasks with due dates.")
        else:
            ics_lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//MissionControl//EN", "CALSCALE:GREGORIAN"]
            for _, row in cal_tasks.iterrows():
                due = str(row["due_date"]).replace("-", "")
                ics_lines.extend(["BEGIN:VEVENT", f"DTSTART;VALUE=DATE:{due}", f"DTEND;VALUE=DATE:{due}",
                                  f"SUMMARY:[{row['urgency']}] {row['title']} ({row['company']})", "END:VEVENT"])
            ics_lines.append("END:VCALENDAR")
            st.download_button("📥 Download .ics", "\r\n".join(ics_lines), file_name=f"mission-control-{datetime.now().strftime('%Y%m%d')}.ics", mime="text/calendar")
