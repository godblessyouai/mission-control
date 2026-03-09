# HEARTBEAT.md

## Mission Control Job Queue Check
- Run: `python3 /Users/ai/.openclaw/workspace/mission-control-v1/scripts/job_runner.py`
- If queued jobs exist: pick them up, mark In Progress, spawn the right agent, save output back to DB
- Notify Mr Kai on Telegram when jobs complete
