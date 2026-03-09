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

## Agent setup (v1.2 in progress)

Mr Brain orchestration stack:
- Mr Brain (orchestrator) → `skills/mr-brain`
- Mr Engineering → `skills/mr-engineering`
- Mr Design → `skills/mr-design`
- Mr Marketing → `skills/mr-marketing`

Routing config:
- `agent-routing.json`

## Suggested next upgrades (v1.2)

1. Add agent dropdown + auto-routing in `AI Workers` tab
2. One-click "Run with Mr Engineering/Design/Marketing"
3. Save structured specialist outputs into `ai_jobs.output`
4. Telegram command bridge (`/task`, `/escalate`, `/summary`)
5. KPI anomaly alerts + notification hooks

## Cron examples

Daily 9am:
```bash
0 9 * * * cd /Users/ai/.openclaw/workspace/mission-control-v1 && /usr/bin/python3 summary.py
```

End-of-day 6pm:
```bash
0 18 * * * cd /Users/ai/.openclaw/workspace/mission-control-v1 && /usr/bin/python3 summary.py
```
