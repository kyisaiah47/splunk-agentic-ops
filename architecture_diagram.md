# Architecture — Splunk Agentic Ops

## Overview

Splunk Agentic Ops connects Splunk's observability platform to an autonomous AI agent powered by Claude. When a Splunk alert fires, the agent takes over: it runs targeted SPL queries, builds up evidence, identifies the root cause, and delivers a structured incident report to Slack — all within ~30 seconds, with no human in the loop.

---

## System Diagram

```
┌──────────────────────────────────────────────────────────────────────┐
│                         Splunk Enterprise                            │
│                                                                      │
│  ┌─────────────┐   HEC ingest   ┌──────────────────────────────┐   │
│  │ Log Sources  │──────────────▶│  Indexes (web_logs, app_logs, │   │
│  │ (web, app,   │               │   deploy_logs)                │   │
│  │  infra)      │               └──────────────┬───────────────┘   │
│  └─────────────┘                              │                    │
│                                ┌──────────────▼───────────────┐   │
│                                │    Saved Search / Alert       │   │
│                                │  (5xx spike, latency SLO,    │   │
│                                │   DB pool exhausted, ...)    │   │
│                                └──────────────┬───────────────┘   │
│                                               │  Webhook           │
└───────────────────────────────────────────────┼───────────────────┘
                                                │
                                                ▼
┌───────────────────────────────────────────────────────────────────┐
│                   Splunk Agentic Ops  (FastAPI / Python)          │
│                                                                   │
│  POST /webhook/splunk ──▶ AlertWebhook parsed                    │
│                                   │                              │
│                                   ▼                              │
│                       ┌─────────────────────┐                   │
│                       │  Background Task     │                   │
│                       │  investigate_alert() │                   │
│                       └──────────┬──────────┘                   │
│                                  │                              │
│  GET /investigations      ◀──────┤  In-memory investigation     │
│  GET /investigations/{id}        │  store (audit trail)         │
│                                  │                              │
└──────────────────────────────────┼──────────────────────────────┘
                                   │
               ┌───────────────────▼────────────────────────┐
               │           Claude claude-sonnet-4-6          │
               │            (Anthropic API)                  │
               │                                            │
               │  4-phase SRE Investigation Playbook:       │
               │  1. Triage      — scope & initial counts   │
               │  2. Impact      — baseline comparison,     │
               │                   blast radius             │
               │  3. Root Cause  — deploys, infra, deps     │
               │  4. Synthesis   — JSON report              │
               │                                            │
               │  Agentic tool-use loop (max 8 SPL calls):  │
               │  ┌─────────────────────┐                  │
               │  │  run_spl_search      │◀──────────────┐ │
               │  │  get_alert_context  │               │ │
               │  │  get_index_summary  │  results feed  │ │
               │  └──────────┬──────────┘  back to Claude│ │
               │             │                           │ │
               └─────────────┼───────────────────────────┼─┘
                             │                           │
             ┌───────────────▼──────────────┐           │
             │  Splunk MCP Server (primary)  │           │
             │  or                           │───────────┘
             │  Splunk REST API  (fallback)  │  SPL results
             └───────────────┬──────────────┘
                             │
                             ▼
                 ┌───────────────────────┐
                 │   Splunk Enterprise   │
                 │  (indexes, searches)  │
                 └───────────────────────┘

After investigation completes:

  Investigation Report
         │
         ├──▶  Slack (Block Kit)
         │     • Root cause + confidence score
         │     • Affected hosts / services
         │     • Timeline (first seen)
         │     • Evidence trail (N SPL queries)
         │     • Specific remediation recommendation
         │
         └──▶  Next.js Dashboard (real-time polling)
               • Command center hero with live status
               • Investigation cards with full detail
               • Persisted audit trail
```

---

## Data Flow

| Step | What happens |
|------|-------------|
| 1. Ingest | Log sources push events to Splunk via HEC → indexed in `web_logs`, `app_logs`, `deploy_logs` |
| 2. Alert | Splunk saved search detects anomaly (threshold / statistical) → fires webhook to `/webhook/splunk` |
| 3. Triage | FastAPI parses the alert payload, creates an investigation record, spawns a background task |
| 4. Investigate | Claude runs up to 8 targeted SPL queries via the Splunk MCP Server or REST API, building evidence iteratively |
| 5. Synthesize | Claude produces a structured JSON report: root cause, confidence (0–1), first seen, affected hosts, recommendation |
| 6. Notify | Report posted to Slack with Block Kit formatting; stored in the REST API for audit |

---

## AI Integration

| Component | Role |
|-----------|------|
| Claude claude-sonnet-4-6 | Core reasoning engine — runs the investigation playbook, decides which queries to run, synthesizes the final report |
| Anthropic Tool Use API | Agentic loop — Claude issues tool calls, receives results, iterates until it has enough evidence |
| Splunk MCP Server | Exposes Splunk search as MCP tools so any AI agent can query it natively (optional, unlocks MCP prize) |
| Splunk REST API | Fallback when MCP Server is unavailable — full feature parity via `splunklib` |

---

## Key Design Decisions

- **Claude as the reasoning layer, not a wrapper** — Claude doesn't just call a fixed set of queries. It reads the alert, decides what questions to answer, chooses the right SPL, and adapts its investigation based on what the data shows.
- **8-query budget** — Forces the agent to be targeted, not exhaustive. Mirrors how a skilled SRE triage looks.
- **Dual Splunk backend** — MCP mode for the hackathon prize track; REST fallback for production reliability.
- **In-memory store** — Appropriate for a hackathon demo. A production version would use a persistent store (Postgres, Redis).
