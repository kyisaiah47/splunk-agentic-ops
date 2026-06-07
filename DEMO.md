# Demo Walkthrough

## Prerequisites

- Splunk Enterprise running on `localhost:8000` with `web_logs`, `app_logs`, and `deploy_logs` indexes
- `.env` filled in (see `.env.example`)
- Python venv active: `source .venv/bin/activate`
- Next.js frontend running: `cd frontend && npm run dev`

---

## 1. Start the backend

```bash
python main.py
# Splunk Agentic Ops running at http://localhost:9000
```

---

## 2. Load sample data into Splunk

Run all three scenario datasets (takes ~2 minutes total):

```bash
python demo/generate_logs.py --mode normal        # 30 min baseline traffic
python demo/generate_logs.py --mode incident      # 5xx spike on web-03 / web-07 + deploy event
python demo/generate_logs.py --mode latency       # P99 latency SLO breach across all hosts
python demo/generate_logs.py --mode db_connections # DB connection pool exhaustion in app_logs
```

---

## 3. Open the dashboard

`http://localhost:3002` — you'll see the command center with live status, stats, and the investigation feed.

---

## 4. Trigger demo alerts

Click **Trigger Alert** in the dashboard and choose a scenario, or use the CLI:

```bash
# Bad deployment — 5xx spike
python demo/trigger_alert.py --alert 5xx_spike

# SLO breach — P99 latency
python demo/trigger_alert.py --alert latency

# Database crisis
python demo/trigger_alert.py --alert db_connections
```

---

## 5. Watch the agent work

In the terminal running `python main.py` you'll see the investigation start. The dashboard polls every 2 seconds and shows the card flip from **Investigating** → **Resolved** as Claude finishes.

Each investigation runs **up to 8 SPL queries**, working through:
1. **Triage** — confirm the alert, scope the blast radius
2. **Impact** — compare against 7-day baseline, build a timeline
3. **Root Cause** — check deploy logs, infra events, upstream dependencies
4. **Synthesis** — structured JSON report with confidence score and specific recommendation

---

## 6. Check Slack

If `SLACK_WEBHOOK_URL` is set, a Block Kit report posts automatically with:
- Root cause summary
- Confidence score
- Affected hosts
- Evidence trail
- Specific remediation step

---

## Demo script (for recording)

| Time | Action |
|------|--------|
| 0:00 | Show dashboard (empty state) — explain the concept in one sentence |
| 0:20 | Click Trigger Alert → High 5xx Error Rate |
| 0:25 | Show the card appear as "Investigating" with the pulsing badge |
| 0:35 | Narrate what the agent is doing (running SPL queries in the background) |
| 1:00 | Card flips to "Resolved" — walk through root cause, confidence, affected hosts, recommendation |
| 1:20 | Show Slack notification |
| 1:30 | Trigger a second alert (latency) — show two cards side by side in the grid |
| 1:50 | Quick architecture overview |
