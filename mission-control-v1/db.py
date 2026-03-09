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
            """
        )

        for c in ["Mister Mobile", "Food Art", "Shared/Personal"]:
            conn.execute("INSERT OR IGNORE INTO companies(name) VALUES (?)", (c,))

        # lightweight migrations
        cols = [r[1] for r in conn.execute("PRAGMA table_info(ai_jobs)").fetchall()]
        if "assigned_agent" not in cols:
            conn.execute("ALTER TABLE ai_jobs ADD COLUMN assigned_agent TEXT DEFAULT 'Mr Brain'")


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


def add_ai_job(data: dict):
    ts = now_iso()
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO ai_jobs(job_type, company, request, owner, priority, status, output, assigned_agent, created_at, updated_at)
            VALUES(:job_type,:company,:request,:owner,:priority,:status,:output,:assigned_agent,:created_at,:updated_at)
            """,
            {**data, "assigned_agent": data.get("assigned_agent", "Mr Brain"), "created_at": ts, "updated_at": ts},
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
