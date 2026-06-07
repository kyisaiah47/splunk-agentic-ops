"""
Simulates a Splunk alert webhook firing — use this to test the agent
without waiting for a real Splunk alert to trigger.

Usage:
    python demo/trigger_alert.py
    python demo/trigger_alert.py --severity critical --alert "Database Connection Exhausted"
"""
import argparse
import httpx
import json
from datetime import datetime, timezone

DEFAULT_HOST = "http://localhost:9000"

SAMPLE_ALERTS = {
    "5xx_spike": {
        "alert_name": "High 5xx Error Rate — Web Tier",
        "search_name": "alert_web_5xx_spike",
        "search_query": (
            'index=web_logs status>=500 earliest=-15m latest=now '
            '| stats count as errors by host '
            '| where errors > 50'
        ),
        "trigger_time": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "severity": "high",
        "trigger_reason": {
            "type": "number of events",
            "value": "847",
            "condition": "> 50 per host in 15 min",
        },
        "results": {
            "fields": ["host", "errors"],
            "rows": [["web-03", "512"], ["web-07", "335"]],
        },
    },
    "db_connections": {
        "alert_name": "Database Connection Pool Exhausted",
        "search_name": "alert_db_conn_exhausted",
        "search_query": (
            'index=app_logs "connection pool exhausted" OR "too many connections" '
            'earliest=-10m latest=now | stats count by host, database'
        ),
        "trigger_time": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "severity": "critical",
        "trigger_reason": {
            "type": "number of events",
            "value": "245",
            "condition": "> 10",
        },
    },
    "latency": {
        "alert_name": "P99 Latency Exceeds SLO (>2s)",
        "search_name": "alert_latency_slo_breach",
        "search_query": (
            'index=web_logs earliest=-15m latest=now '
            '| rex field=_raw "(?P<duration_ms>\\d+)ms$" '
            '| eventstats p99(duration_ms) as p99_ms '
            '| where p99_ms > 2000 '
            '| stats count by host'
        ),
        "trigger_time": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "severity": "high",
        "trigger_reason": {"type": "p99 latency", "value": "4823ms", "condition": "> 2000ms"},
    },
}


def fire_alert(alert_key: str = "5xx_spike", host: str = DEFAULT_HOST, severity_override: str = "", alert_name_override: str = ""):
    payload = SAMPLE_ALERTS.get(alert_key, SAMPLE_ALERTS["5xx_spike"]).copy()
    if severity_override:
        payload["severity"] = severity_override
    if alert_name_override:
        payload["alert_name"] = alert_name_override

    print(f"Firing alert: {payload['alert_name']}")
    print(f"  Severity:  {payload['severity'].upper()}")
    print(f"  Endpoint:  {host}/webhook/splunk")
    print()

    r = httpx.post(f"{host}/webhook/splunk", json=payload, timeout=10)
    r.raise_for_status()
    data = r.json()
    print(f"Investigation started — ID: {data['investigation_id']}")
    print(f"Poll status: {host}/investigations/{data['investigation_id']}")
    return data["investigation_id"]


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--alert", choices=list(SAMPLE_ALERTS.keys()), default="5xx_spike")
    parser.add_argument("--severity", default="")
    parser.add_argument("--name", default="")
    parser.add_argument("--host", default=DEFAULT_HOST)
    args = parser.parse_args()

    fire_alert(args.alert, args.host, args.severity, args.name)
