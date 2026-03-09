import sqlite3
from pathlib import Path
from datetime import datetime, timedelta

DB_PATH = Path(__file__).parent / "mission_control.db"


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_conn() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS companies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE
            );

            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                company TEXT NOT NULL,
                project TEXT,
                owner TEXT,
                urgency TEXT DEFAULT 'Medium',
                status TEXT DEFAULT 'Open',
                due_date TEXT,
                snooze_until TEXT,
                needs_decision INTEGER DEFAULT 0,
                notes TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS comms (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source TEXT NOT NULL,
                company TEXT,
                subject TEXT NOT NULL,
                owner TEXT,
                priority TEXT DEFAULT 'Medium',
                action_required INTEGER DEFAULT 1,
                escalated INTEGER DEFAULT 0,
                status TEXT DEFAULT 'Open',
                notes TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS ai_jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_type TEXT NOT NULL, -- assistant|graphic|video|copy|programmer
                company TEXT,
                request TEXT NOT NULL,
                owner TEXT,
                priority TEXT DEFAULT 'Medium',
                status TEXT DEFAULT 'Queued',
                output TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS ai_job_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id INTEGER NOT NULL,
                event_type TEXT NOT NULL,
                details TEXT,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS agent_status (
                agent_name TEXT PRIMARY KEY,
                status TEXT DEFAULT 'Idle',
                current_task TEXT DEFAULT '',
                started_at TEXT DEFAULT '',
                updated_at TEXT DEFAULT ''
            );

            CREATE TABLE IF NOT EXISTS activity_feed (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                agent_name TEXT NOT NULL,
                event_type TEXT NOT NULL,
                message TEXT NOT NULL,
                job_id INTEGER,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS trend_feed (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company TEXT,
                category TEXT,
                title TEXT NOT NULL,
                summary TEXT,
                source_url TEXT,
                sentiment TEXT DEFAULT 'neutral',
                relevance TEXT DEFAULT 'Medium',
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS feedback_inbox (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company TEXT,
                source TEXT,
                customer TEXT,
                message TEXT NOT NULL,
                sentiment TEXT DEFAULT 'neutral',
                tags TEXT,
                status TEXT DEFAULT 'New',
                notes TEXT,
                created_at TEXT NOT NULL
            );
            """
        )

        # task priority score migration
        task_cols = [r[1] for r in conn.execute("PRAGMA table_info(tasks)").fetchall()]
        if "rice_reach" not in task_cols:
            conn.execute("ALTER TABLE tasks ADD COLUMN rice_reach INTEGER DEFAULT 0")
            conn.execute("ALTER TABLE tasks ADD COLUMN rice_impact REAL DEFAULT 1.0")
            conn.execute("ALTER TABLE tasks ADD COLUMN rice_confidence REAL DEFAULT 0.5")
            conn.execute("ALTER TABLE tasks ADD COLUMN rice_effort REAL DEFAULT 1.0")
            conn.execute("ALTER TABLE tasks ADD COLUMN rice_score REAL DEFAULT 0")

        for c in ["Mister Mobile", "Food Art", "Shared/Personal"]:
            conn.execute("INSERT OR IGNORE INTO companies(name) VALUES (?)", (c,))

        # lightweight migrations
        cols = [r[1] for r in conn.execute("PRAGMA table_info(ai_jobs)").fetchall()]
        if "assigned_agent" not in cols:
            conn.execute("ALTER TABLE ai_jobs ADD COLUMN assigned_agent TEXT DEFAULT 'Mr Brain'")
        if "reviewer_agent" not in cols:
            conn.execute("ALTER TABLE ai_jobs ADD COLUMN reviewer_agent TEXT DEFAULT ''")
        if "route_reason" not in cols:
            conn.execute("ALTER TABLE ai_jobs ADD COLUMN route_reason TEXT DEFAULT ''")


def now_iso():
    return datetime.now().isoformat(timespec="seconds")


def add_task(data: dict):
    ts = now_iso()
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO tasks(title, company, project, owner, urgency, status, due_date, snooze_until, needs_decision, notes, created_at, updated_at)
            VALUES(:title,:company,:project,:owner,:urgency,:status,:due_date,:snooze_until,:needs_decision,:notes,:created_at,:updated_at)
            """,
            {
                **data,
                "created_at": ts,
                "updated_at": ts,
            },
        )


def update_task(task_id: int, fields: dict):
    fields = {**fields, "updated_at": now_iso(), "id": task_id}
    cols = ", ".join([f"{k}=:{k}" for k in fields.keys() if k != "id"])
    with get_conn() as conn:
        conn.execute(f"UPDATE tasks SET {cols} WHERE id=:id", fields)


def add_comm(data: dict):
    ts = now_iso()
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO comms(source, company, subject, owner, priority, action_required, escalated, status, notes, created_at, updated_at)
            VALUES(:source,:company,:subject,:owner,:priority,:action_required,:escalated,:status,:notes,:created_at,:updated_at)
            """,
            {**data, "created_at": ts, "updated_at": ts},
        )


def log_ai_event(job_id: int, event_type: str, details: str = ""):
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO ai_job_events(job_id, event_type, details, created_at)
            VALUES(?,?,?,?)
            """,
            (job_id, event_type, details, now_iso()),
        )


def add_ai_job(data: dict):
    ts = now_iso()
    with get_conn() as conn:
        cur = conn.execute(
            """
            INSERT INTO ai_jobs(job_type, company, request, owner, priority, status, output, assigned_agent, reviewer_agent, route_reason, created_at, updated_at)
            VALUES(:job_type,:company,:request,:owner,:priority,:status,:output,:assigned_agent,:reviewer_agent,:route_reason,:created_at,:updated_at)
            """,
            {
                **data,
                "assigned_agent": data.get("assigned_agent", "Mr Brain"),
                "reviewer_agent": data.get("reviewer_agent", ""),
                "route_reason": data.get("route_reason", ""),
                "created_at": ts,
                "updated_at": ts,
            },
        )
        job_id = cur.lastrowid
        conn.execute(
            """
            INSERT INTO ai_job_events(job_id, event_type, details, created_at)
            VALUES(?,?,?,?)
            """,
            (job_id, "created", f"assigned={data.get('assigned_agent', 'Mr Brain')}", ts),
        )
        return job_id


def update_ai_job(job_id: int, fields: dict):
    fields = {**fields, "updated_at": now_iso(), "id": job_id}
    cols = ", ".join([f"{k}=:{k}" for k in fields.keys() if k != "id"])
    with get_conn() as conn:
        conn.execute(f"UPDATE ai_jobs SET {cols} WHERE id=:id", fields)
        details = "; ".join([f"{k}={v}" for k, v in fields.items() if k not in {"id", "updated_at"}])
        conn.execute(
            """
            INSERT INTO ai_job_events(job_id, event_type, details, created_at)
            VALUES(?,?,?,?)
            """,
            (job_id, "updated", details, fields["updated_at"]),
        )


def upsert_agent_status(agent: str, status: str, task: str = ""):
    ts = now_iso()
    with get_conn() as conn:
        conn.execute("""
            INSERT INTO agent_status(agent_name, status, current_task, started_at, updated_at)
            VALUES(?,?,?,?,?)
            ON CONFLICT(agent_name) DO UPDATE SET
              status=excluded.status,
              current_task=excluded.current_task,
              started_at=CASE WHEN excluded.status != agent_status.status THEN excluded.started_at ELSE agent_status.started_at END,
              updated_at=excluded.updated_at
        """, (agent, status, task, ts, ts))


def push_activity(agent: str, event_type: str, message: str, job_id: int = None):
    with get_conn() as conn:
        conn.execute("""
            INSERT INTO activity_feed(agent_name, event_type, message, job_id, created_at)
            VALUES(?,?,?,?,?)
        """, (agent, event_type, message, job_id, now_iso()))


def sync_agent_status(agent: str):
    jobs = fetch_df("""
        SELECT status, request, updated_at FROM ai_jobs
        WHERE assigned_agent=?
        ORDER BY updated_at DESC LIMIT 20
    """, [agent])
    if jobs.empty:
        upsert_agent_status(agent, "Idle")
        return
    in_prog = jobs[jobs["status"] == "In Progress"]
    queued = jobs[jobs["status"] == "Queued"]
    if not in_prog.empty:
        latest = in_prog.iloc[0]
        upsert_agent_status(agent, "Busy", str(latest["request"])[:80])
    elif not queued.empty:
        upsert_agent_status(agent, "Standby", f"{len(queued)} jobs queued")
    else:
        upsert_agent_status(agent, "Idle")


def add_trend(data: dict):
    ts = now_iso()
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO trend_feed(company, category, title, summary, source_url, sentiment, relevance, created_at)
            VALUES(:company,:category,:title,:summary,:source_url,:sentiment,:relevance,:created_at)
            """,
            {**data, "created_at": ts},
        )


def add_feedback(data: dict):
    ts = now_iso()
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO feedback_inbox(company, source, customer, message, sentiment, tags, status, notes, created_at)
            VALUES(:company,:source,:customer,:message,:sentiment,:tags,:status,:notes,:created_at)
            """,
            {**data, "created_at": ts},
        )


def update_feedback(fb_id: int, fields: dict):
    fields = {**fields, "id": fb_id}
    cols = ", ".join([f"{k}=:{k}" for k in fields.keys() if k != "id"])
    with get_conn() as conn:
        conn.execute(f"UPDATE feedback_inbox SET {cols} WHERE id=:id", fields)


def update_rice_score(task_id: int, reach: int, impact: float, confidence: float, effort: float):
    score = (reach * impact * confidence) / max(effort, 0.1)
    with get_conn() as conn:
        conn.execute(
            """
            UPDATE tasks SET rice_reach=?, rice_impact=?, rice_confidence=?, rice_effort=?, rice_score=?, updated_at=?
            WHERE id=?
            """,
            (reach, impact, confidence, effort, round(score, 1), now_iso(), task_id),
        )


def fetch_df(query: str, params=()):
    import pandas as pd

    with get_conn() as conn:
        return pd.read_sql_query(query, conn, params=params)


def quick_seed():
    with get_conn() as conn:
        count = conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
        if count:
            return

    add_task(
        {
            "title": "Review weekly ad ROAS drop",
            "company": "Mister Mobile",
            "project": "Paid Ads",
            "owner": "Boss Kai",
            "urgency": "High",
            "status": "Open",
            "due_date": (datetime.now() + timedelta(days=1)).date().isoformat(),
            "snooze_until": "",
            "needs_decision": 1,
            "notes": "Need budget reallocation decision.",
        }
    )

    add_task(
        {
            "title": "Finalize Ramadan campaign creative",
            "company": "Food Art",
            "project": "Campaigns",
            "owner": "Design Team",
            "urgency": "Medium",
            "status": "In Progress",
            "due_date": (datetime.now() + timedelta(days=2)).date().isoformat(),
            "snooze_until": "",
            "needs_decision": 0,
            "notes": "Awaiting product shots.",
        }
    )

    add_ai_job(
        {
            "job_type": "copy",
            "company": "Food Art",
            "request": "Write 5 IG captions for Women’s Day soup promo",
            "owner": "Marketing",
            "priority": "Medium",
            "status": "Queued",
            "output": "",
            "assigned_agent": "Mr Marketing",
        }
    )
