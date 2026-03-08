# Mission Control v1 (Fast Usable Build)

A practical multi-company executive assistant cockpit.

## What v1 already does

- Multi-company task board (Mister Mobile / Food Art / Shared)
- Priority + owner + due date + escalation flags
- Quick actions: assign/reassign, mark done, snooze, set deadline
- Unified dashboard filters: company / owner / urgency / status
- Escalation view (decision-required items)
- Communications triage inbox (email/slack/customer/staff items)
- AI worker queue modules:
  - assistant
  - graphic
  - video
  - copy
  - programmer
- Automation center skeleton + summary script

## Architecture (v1)

- **UI:** Streamlit (`app.py`)
- **Storage:** SQLite (`mission_control.db`)
- **Domain modules:**
  - `tasks`
  - `comms`
  - `ai_jobs`
- **Automation:** `summary.py` (for daily 9am / EOD / weekly reports)

This is intentionally simple for speed + reliability.

## Run

```bash
cd mission-control-v1
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Open the local URL shown by Streamlit.

## Daily summary (CLI)

```bash
cd mission-control-v1
python3 summary.py
```

## Suggested next upgrades (v1.1)

1. Telegram command bridge (`/task`, `/escalate`, `/summary`)
2. Slack + Gmail ingestion into `comms`
3. KPI anomaly alerts
4. Role-based owners/teams
5. CSV import/export + audit log

## Cron examples

Daily 9am:
```bash
0 9 * * * cd /Users/ai/.openclaw/workspace/mission-control-v1 && /usr/bin/python3 summary.py
```

End-of-day 6pm:
```bash
0 18 * * * cd /Users/ai/.openclaw/workspace/mission-control-v1 && /usr/bin/python3 summary.py
```
