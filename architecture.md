# Architecture Diagram

```
┌──────────────────────────────────────────────────────────────────────┐
│                         Splunk Enterprise                            │
│                                                                      │
│  ┌─────────────┐   HEC ingest   ┌──────────────────────────────┐   │
│  │  Log Sources │──────────────▶│  Indexes (web_logs, app_logs) │   │
│  │  (web, app,  │               └──────────────┬───────────────┘   │
│  │   infra)     │                              │                    │
│  └─────────────┘               ┌──────────────▼───────────────┐   │
│                                 │    Saved Search / Alert       │   │
│                                 │  (5xx spike, latency SLO,    │   │
│                                 │   DB pool exhausted, ...)    │   │
│                                 └──────────────┬───────────────┘   │
│                                                │  Webhook           │
└────────────────────────────────────────────────┼───────────────────┘
                                                 │
                                                 ▼
┌────────────────────────────────────────────────────────────────────┐
│                   Splunk Agentic Ops Service (FastAPI)             │
│                                                                    │
│  POST /webhook/splunk ──▶ [AlertWebhook parsed]                   │
│                                    │                              │
│                                    ▼                              │
│                        ┌─────────────────────┐                   │
│                        │  Background Task     │                   │
│                        │  investigate_alert() │                   │
│                        └──────────┬──────────┘                   │
│                                   │                              │
└───────────────────────────────────┼──────────────────────────────┘
                                    │
                ┌───────────────────▼──────────────────────┐
                │         Claude claude-sonnet-4-6 (Anthropic API)        │
                │                                          │
                │  System prompt: SRE Investigation        │
                │  Playbook (triage → impact →             │
                │  root cause → synthesis)                 │
                │                                          │
                │  Tool use loop (max 8 calls):            │
                │  ┌──────────────┐                       │
                │  │ run_spl_search│◀──────────────────┐  │
                │  │ get_alert_   │                    │  │
                │  │  context     │  Tool results      │  │
                │  │ get_index_   │  feed back to      │  │
                │  │  summary     │  Claude for next   │  │
                │  └──────┬───────┘  reasoning step    │  │
                │         │                            │  │
                └─────────┼────────────────────────────┼──┘
                          │                            │
          ┌───────────────▼────────────────┐          │
          │                                │          │
          │  Splunk MCP Server  (primary)  │          │
          │  or                            │──────────┘
          │  Splunk REST API    (fallback) │  SPL query results
          │                                │
          └───────────────┬────────────────┘
                          │ SPL queries
                          ▼
              ┌───────────────────────┐
              │  Splunk Enterprise    │
              │  (indexes, alerts,    │
              │   saved searches)     │
              └───────────────────────┘

After investigation completes:

  Investigation Report
         │
         ▼
  ┌─────────────────────────────────┐
  │  Slack (Block Kit)              │
  │  • Root cause + confidence bar  │
  │  • Affected hosts/services      │
  │  • Timeline (first seen)        │
  │  • Evidence trail (N queries)   │
  │  • Specific recommendation      │
  └─────────────────────────────────┘

  + GET /investigations/{id}  (REST API for audit trail)
```

## Data Flow Summary

1. **Ingestion**: Log sources → Splunk HEC → indexed in Splunk
2. **Alerting**: Splunk saved search detects anomaly → fires webhook
3. **Triage**: FastAPI receives webhook, spawns background investigation task
4. **Investigation**: Claude iteratively queries Splunk (via MCP Server or REST) to gather evidence
5. **Synthesis**: Claude produces structured JSON report (root cause, confidence, recommendation)
6. **Notification**: Report posted to Slack with full evidence trail

## AI Integration Points

| Component | Role |
|-----------|------|
| Claude claude-sonnet-4-6 | Investigation reasoning, tool-use orchestration, natural-language synthesis |
| Splunk MCP Server | Exposes Splunk data as MCP tools consumable by any AI agent |
| Splunk Hosted Models | (Optional) Anomaly detection / baseline comparison within Splunk |
| Anthropic Tool Use | Agentic loop — Claude decides which queries to run based on evidence |
