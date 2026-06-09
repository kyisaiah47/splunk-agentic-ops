<div align="center">

<img src="assets/banner.png" alt="banner" width="100%" />

# 🔍 Splunk Agentic Ops

**Autonomous AI agent that receives Splunk alerts and delivers root-cause incident reports to Slack in ~30 seconds**

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Claude](https://img.shields.io/badge/Claude-Sonnet-D4A017?style=for-the-badge&logo=anthropic&logoColor=white)
![Splunk](https://img.shields.io/badge/Splunk-000000?style=for-the-badge&logo=splunk&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)
![License: MIT](https://img.shields.io/badge/License-MIT-22C55E?style=for-the-badge)

Built for the [Splunk Agentic Ops Hackathon](https://splunk.devpost.com/) — Observability Track.

</div>

<br/>

An AI agent that receives Splunk alerts and autonomously investigates them — querying logs, comparing baselines, hunting for root causes, and posting a full incident report to Slack — all within ~30 seconds.

## ✨ Features

- **Agentic investigation loop** — Claude (`claude-sonnet-4-6`) runs up to 8 targeted SPL queries via the Splunk MCP Server (or direct REST API) to isolate the root cause
- **Structured root-cause reports** — each report includes a confidence score, contributing factors, and a recommended remediation step
- **Slack Block Kit reporting** — formatted incident reports posted to Slack the moment the investigation completes
- **Live dashboard** — real-time Next.js dashboard showing all investigations and their current status
- **Demo mode** — built-in log generators for 3 scenarios (5xx spike, latency breach, DB connection exhaustion) so you can reproduce incidents without a production Splunk instance
- **Dual transport** — runs against the Splunk MCP Server (`USE_MCP=true`) or falls back to the Splunk REST API directly

## 🏗️ Architecture

See [`architecture_diagram.md`](architecture_diagram.md) for the full system diagram.

```
splunk-agentic-ops/
├── main.py                   FastAPI app + webhook handler
├── models.py                 Pydantic data models
├── agent/
│   ├── investigator.py       Agentic loop (Claude + tool use)
│   ├── prompts.py            System prompt + investigation playbook
│   ├── tools.py              Anthropic tool definitions
│   └── mcp_bridge.py         Splunk MCP Server client
├── splunk/
│   └── client.py             Direct Splunk REST API fallback
├── notifications/
│   └── slack.py              Slack Block Kit report formatter
├── demo/
│   ├── trigger_alert.py      Simulate a Splunk alert webhook
│   └── generate_logs.py      Generate + inject sample log data via HEC
└── frontend/                 Next.js dashboard
```

## 🛠️ Tech Stack

| Package | Purpose |
|---------|---------|
| `anthropic` | Claude API — agentic investigation loop |
| `fastapi` + `uvicorn` | Backend web server |
| `splunk-sdk` | Splunk REST API client (fallback mode) |
| `httpx` | Async HTTP (HEC ingest, Slack notifications) |
| `pydantic` | Request/response data models |
| `python-dotenv` | Environment variable loading |

Frontend: Next.js 16, Tailwind CSS v4, shadcn/ui, TypeScript

## 🚀 Getting Started

### 1. Install dependencies

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
# Fill in ANTHROPIC_API_KEY, SPLUNK_*, SLACK_WEBHOOK_URL
```

### 3. Start the backend

```bash
python main.py
# → http://localhost:9000
```

### 4. Start the dashboard

```bash
cd frontend
npm install
npm run dev
# → http://localhost:3002
```

### 5. Generate sample incident data

```bash
python demo/generate_logs.py --mode normal        # 30 min baseline traffic
python demo/generate_logs.py --mode incident      # 5xx spike + bad deploy
python demo/generate_logs.py --mode latency       # P99 SLO breach
python demo/generate_logs.py --mode db_connections # DB connection pool exhausted
```

### 6. Fire a test alert

```bash
python demo/trigger_alert.py --alert 5xx_spike
# or: latency / db_connections
```

Watch the dashboard at `http://localhost:3002` — then check Slack ~30 seconds later.

## Splunk Setup

### Create indexes

```
Settings → Indexes → New Index → Name: web_logs
Settings → Indexes → New Index → Name: app_logs
```

### Configure HEC (for log ingestion)

```
Settings → Data Inputs → HTTP Event Collector → Global Settings → Enable
Settings → Data Inputs → HTTP Event Collector → New Token → default index: web_logs
Add SPLUNK_HEC_TOKEN and SPLUNK_HEC_URL to .env
```

### Enable Splunk MCP Server (optional)

> **Note:** This step is only required when `USE_MCP=true`. The `mcp` client
> library (`mcp>=1.0.0`) must be installed in addition to the Splunk MCP
> server package so the agent can connect over SSE.

```bash
pip install "mcp>=1.0.0"
pip install splunk-mcp
python -m splunk_mcp --port 8080
```

Then set in `.env`:
```
USE_MCP=true
MCP_SERVER_URL=http://localhost:8080/sse
```

## 🔌 API Reference

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/webhook/splunk` | Receive Splunk alert webhook |
| `GET`  | `/investigations` | List all investigations |
| `GET`  | `/investigations/{id}` | Get investigation details |
| `GET`  | `/health` | Liveness check |

## 📄 License

MIT
