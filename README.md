<div align="center">

<img src="assets/banner.png" alt="banner" width="100%" />

# 🔍 Splunk Agentic Ops

**Autonomous alert investigation — Claude triages your Splunk alerts and posts incident reports to Slack**

![Claude](https://img.shields.io/badge/Claude-CC785C?style=flat-square) ![Splunk](https://img.shields.io/badge/Splunk-000000?style=flat-square&logo=splunk&logoColor=white) ![Slack](https://img.shields.io/badge/Slack-4A154B?style=flat-square&logo=slack&logoColor=white)

</div>

<br/>

When a Splunk alert fires, Claude autonomously takes over: it runs up to 8 targeted SPL queries via the Splunk MCP Server, compares baselines, hunts for root causes, and synthesises a confidence-scored incident report — all delivered to Slack via Block Kit within ~30 seconds. No human triage required.

## ✨ Features

- **Agentic investigation loop** — Claude (claude-sonnet-4-6) drives the full investigation from alert receipt to report delivery
- **Splunk MCP Server integration** — queries logs directly via MCP or falls back to the Splunk REST API
- **Root-cause synthesis** — produces a structured report with confidence score, timeline, and recommended remediation
- **Slack Block Kit reports** — rich, actionable incident summaries posted automatically to your Slack channel
- **Live dashboard** — Next.js frontend at `localhost:3002` shows investigations in real time
- **Demo scenarios** — pre-built log generators for 5xx spikes, latency breaches, and DB connection exhaustion

## 🎥 Demo

[![Watch Demo](https://img.shields.io/badge/YouTube-Watch%20Demo-FF0000?style=for-the-badge&logo=youtube&logoColor=white)](https://www.youtube.com/watch?v=Nj25zOJiZf0)

## 🛠️ Tech Stack

Claude (Anthropic) · Splunk · Slack · FastAPI · Next.js 16 · Tailwind CSS v4 · shadcn/ui · TypeScript · Python

## 🚀 Getting Started

```bash
# 1. Install dependencies
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 2. Configure environment
cp .env.example .env
# Fill in ANTHROPIC_API_KEY, SPLUNK_*, SLACK_WEBHOOK_URL

# 3. Start the backend
python main.py
# → http://localhost:9000

# 4. Start the dashboard
cd frontend && npm install && npm run dev
# → http://localhost:3002

# 5. Fire a test alert
python demo/trigger_alert.py --alert 5xx_spike
# or: latency / db_connections
```

Watch the dashboard at `http://localhost:3002` — then check Slack ~30 seconds later.

## 📄 License

MIT
