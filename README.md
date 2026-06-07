# Splunk Agentic Ops — Autonomous Incident Investigator

An AI agent that receives Splunk alerts and autonomously investigates them — querying logs, comparing baselines, hunting for root causes, and posting a full incident report to Slack — all within ~30 seconds.

Built for the **Splunk Agentic Ops Hackathon** (Observability track).

**Live Demo:** https://splunk-agentic-ops.loca.lt

---

## How it works

1. A Splunk alert fires → sends a webhook to this service
2. Claude (claude-sonnet-4-6) receives the alert and begins an agentic investigation loop
3. The agent runs up to 8 targeted SPL queries via the **Splunk MCP Server** (or direct REST API)
4. It synthesises a root-cause report with confidence score and recommendation
5. The report is posted to Slack using Block Kit and displayed on the live dashboard

---

## Quick Start

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
# Load logs for all 3 demo scenarios
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

---

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

### Create the alert (optional — demo scripts bypass this)

```
Search: index=web_logs status>=500 earliest=-15m | stats count as errors by host | where errors > 50
Save As → Alert → Webhook → URL: http://<your-server>:9000/webhook/splunk
```

### Enable Splunk MCP Server (optional — unlocks MCP prize track)

```bash
pip install splunk-mcp
python -m splunk_mcp --port 8080
```

Then set in `.env`:
```
USE_MCP=true
MCP_SERVER_URL=http://localhost:8080/sse
```

---

## Dependencies

| Package | Purpose |
|---------|---------|
| `anthropic` | Claude API — agentic investigation loop |
| `fastapi` + `uvicorn` | Backend web server |
| `splunk-sdk` | Splunk REST API client (fallback mode) |
| `httpx` | Async HTTP (HEC ingest, Slack notifications) |
| `pydantic` | Request/response data models |
| `python-dotenv` | Environment variable loading |

Frontend: Next.js 16, Tailwind CSS v4, shadcn/ui, TypeScript

---

## API

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/webhook/splunk` | Receive Splunk alert webhook |
| `GET`  | `/investigations` | List all investigations |
| `GET`  | `/investigations/{id}` | Get investigation details |
| `GET`  | `/health` | Liveness check |

---

## Project Structure

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
├── frontend/                 Next.js dashboard
├── architecture_diagram.md   System architecture
└── DEMO.md                   Demo walkthrough + recording script
```

---

## License

MIT
