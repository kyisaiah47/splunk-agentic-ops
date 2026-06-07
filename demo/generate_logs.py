"""
Generates realistic Apache-style web logs and injects them into Splunk via HEC.

Usage:
    python demo/generate_logs.py --mode normal   # 30 min of healthy traffic
    python demo/generate_logs.py --mode incident # inject a 5xx spike (simulates deployment gone wrong)

Requires SPLUNK_HEC_TOKEN and SPLUNK_HEC_URL in your .env
"""
import argparse
import os
import random
import time
from datetime import datetime, timedelta, timezone

import httpx
from dotenv import load_dotenv

load_dotenv()

HEC_URL = os.getenv("SPLUNK_HEC_URL", "https://localhost:8088/services/collector/event")
HEC_TOKEN = os.getenv("SPLUNK_HEC_TOKEN", "")

HOSTS = ["web-01", "web-02", "web-03", "web-04", "web-05", "web-06", "web-07", "web-08"]
ENDPOINTS = [
    "/api/checkout", "/api/cart", "/api/products", "/api/user/profile",
    "/api/search", "/api/payments", "/", "/static/main.js",
]
USER_AGENTS = [
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0)",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
    "python-httpx/0.27.0",
]

NORMAL_STATUS_WEIGHTS = [200] * 90 + [301] * 4 + [404] * 4 + [500] * 2
INCIDENT_STATUS_WEIGHTS_HEALTHY = [200] * 90 + [301] * 4 + [404] * 4 + [500] * 2
INCIDENT_STATUS_WEIGHTS_BROKEN = [500] * 60 + [503] * 20 + [200] * 20


def make_log_event(host: str, status_pool: list, ts: datetime) -> str:
    status = random.choice(status_pool)
    endpoint = random.choice(ENDPOINTS)
    # 500s cluster on /api/checkout in the incident scenario
    if status >= 500:
        endpoint = "/api/checkout"
    ua = random.choice(USER_AGENTS)
    ip = f"10.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}"
    duration_ms = random.randint(50, 200) if status < 500 else random.randint(5000, 30000)
    return (
        f'{ip} - - [{ts.strftime("%d/%b/%Y:%H:%M:%S +0000")}] '
        f'"GET {endpoint} HTTP/1.1" {status} {random.randint(200,8000)} '
        f'"{ua}" {duration_ms}ms'
    )


def send_batch(events: list):
    if not HEC_TOKEN:
        print("[HEC] SPLUNK_HEC_TOKEN not set — printing instead:")
        for e in events[:3]:
            print(" ", e["event"])
        return

    payload = "\n".join(
        '{"time":' + str(e["time"]) + ',"host":"' + e["host"] + '","sourcetype":"' + e.get("sourcetype", "access_combined") + '","index":"' + e.get("index", "web_logs") + '","event":"' + e["event"].replace('"', '\\"') + '"}'
        for e in events
    )
    try:
        r = httpx.post(
            HEC_URL,
            content=payload,
            headers={"Authorization": f"Splunk {HEC_TOKEN}"},
            verify=False,
            timeout=10,
        )
        print(f"[HEC] Sent {len(events)} events → {r.status_code}")
    except Exception as exc:
        print(f"[HEC] Error: {exc}")


def generate_normal(minutes: int = 30):
    print(f"Generating {minutes} min of normal traffic...")
    now = datetime.now(timezone.utc)
    events = []
    for m in range(minutes * 60):
        ts = now - timedelta(seconds=(minutes * 60 - m))
        for _ in range(random.randint(2, 8)):
            host = random.choice(HOSTS)
            log = make_log_event(host, NORMAL_STATUS_WEIGHTS, ts)
            events.append({"time": ts.timestamp(), "host": host, "event": log})
        if len(events) >= 200:
            send_batch(events)
            events = []
    if events:
        send_batch(events)


def generate_incident(spike_at_minutes_ago: int = 10):
    """
    Generate normal traffic for 30 min then inject a 5xx spike starting
    spike_at_minutes_ago minutes ago on web-03 and web-07 (simulating a bad deploy).
    Also injects a deploy log entry 2 minutes before the spike.
    """
    print("Generating incident scenario...")
    now = datetime.now(timezone.utc)
    events = []
    spike_start = now - timedelta(minutes=spike_at_minutes_ago)

    # 30 min of background normal traffic
    for m in range(30 * 60):
        ts = now - timedelta(seconds=(30 * 60 - m))
        pool = (
            INCIDENT_STATUS_WEIGHTS_BROKEN
            if ts >= spike_start and random.choice(HOSTS) in ("web-03", "web-07")
            else INCIDENT_STATUS_WEIGHTS_HEALTHY
        )
        for _ in range(random.randint(2, 8)):
            host = random.choice(HOSTS)
            if ts >= spike_start and host in ("web-03", "web-07"):
                pool = INCIDENT_STATUS_WEIGHTS_BROKEN
            else:
                pool = INCIDENT_STATUS_WEIGHTS_HEALTHY
            log = make_log_event(host, pool, ts)
            events.append({"time": ts.timestamp(), "host": host, "event": log})
        if len(events) >= 200:
            send_batch(events)
            events = []

    if events:
        send_batch(events)

    # Inject deploy event to deploy_logs index (separate from web_logs)
    deploy_ts = spike_start - timedelta(minutes=2)
    deploy_event = (
        f'[{deploy_ts.strftime("%Y-%m-%dT%H:%M:%SZ")}] '
        f'INFO deploy: service=web version=v2.4.1 hosts=web-03,web-07 '
        f'deployer=ci-bot status=success rollback_version=v2.4.0'
    )
    send_batch([{
        "time": deploy_ts.timestamp(),
        "host": "deploy-runner",
        "index": "deploy_logs",
        "sourcetype": "deploy_log",
        "event": deploy_event,
    }])

    print(f"Done. Spike started at {spike_start.strftime('%H:%M UTC')}")
    print("Affected hosts: web-03, web-07")
    print("Correlated deploy: v2.4.1 at", deploy_ts.strftime("%H:%M UTC"))


def generate_latency_spike(spike_at_minutes_ago: int = 10):
    """Inject a P99 latency spike on api-gateway — all requests slow, no errors."""
    print("Generating latency spike scenario...")
    now = datetime.now(timezone.utc)
    events = []
    spike_start = now - timedelta(minutes=spike_at_minutes_ago)

    for m in range(30 * 60):
        ts = now - timedelta(seconds=(30 * 60 - m))
        for _ in range(random.randint(2, 6)):
            host = random.choice(HOSTS)
            endpoint = random.choice(ENDPOINTS)
            status = 200
            # During spike: latency balloons to 8-30 seconds on all hosts
            if ts >= spike_start:
                duration_ms = random.randint(8000, 30000)
            else:
                duration_ms = random.randint(50, 300)
            ip = f"10.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(1,254)}"
            ua = random.choice(USER_AGENTS)
            log = (
                f'{ip} - - [{ts.strftime("%d/%b/%Y:%H:%M:%S +0000")}] '
                f'"GET {endpoint} HTTP/1.1" {status} {random.randint(200,8000)} '
                f'"{ua}" {duration_ms}ms'
            )
            events.append({"time": ts.timestamp(), "host": host, "event": log})
        if len(events) >= 200:
            send_batch(events)
            events = []

    if events:
        send_batch(events)

    print(f"Done. Latency spike started at {spike_start.strftime('%H:%M UTC')}")
    print("All hosts affected — no errors, just extreme slowness")


def generate_db_exhaustion(spike_at_minutes_ago: int = 10):
    """Inject connection pool exhaustion events into app_logs."""
    print("Generating DB connection pool exhaustion scenario...")
    now = datetime.now(timezone.utc)
    events = []
    spike_start = now - timedelta(minutes=spike_at_minutes_ago)

    for m in range(30 * 60):
        ts = now - timedelta(seconds=(30 * 60 - m))
        for _ in range(random.randint(1, 4)):
            host = random.choice(HOSTS)
            if ts >= spike_start:
                msg = random.choice([
                    "ERROR connection pool exhausted: no available connections for db=orders_db",
                    "ERROR too many connections: db=orders_db current=250 max=250",
                    "WARN connection pool exhausted: retrying in 500ms db=orders_db",
                    "ERROR timeout waiting for connection from pool db=orders_db after 5000ms",
                ])
            else:
                msg = f"INFO db connection acquired: db=orders_db pool_size={random.randint(10,50)} available={random.randint(5,40)}"
            log = f'[{ts.strftime("%Y-%m-%dT%H:%M:%S.000Z")}] {msg} host={host}'
            events.append({"time": ts.timestamp(), "host": host, "index": "app_logs", "sourcetype": "app_log", "event": log})
        if len(events) >= 200:
            send_batch(events)
            events = []

    if events:
        send_batch(events)

    print(f"Done. DB exhaustion started at {spike_start.strftime('%H:%M UTC')}")
    print("All hosts affected — orders_db connection pool at max capacity")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["normal", "incident", "latency", "db_connections"], default="incident")
    args = parser.parse_args()

    if args.mode == "normal":
        generate_normal(30)
    elif args.mode == "latency":
        generate_latency_spike(spike_at_minutes_ago=10)
    elif args.mode == "db_connections":
        generate_db_exhaustion(spike_at_minutes_ago=10)
    else:
        generate_incident(spike_at_minutes_ago=10)
