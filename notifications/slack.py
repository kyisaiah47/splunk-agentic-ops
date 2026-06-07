import os
import json
import httpx
from models import Investigation

SEVERITY_EMOJI = {
    "critical": ":red_circle:",
    "high": ":large_orange_circle:",
    "medium": ":large_yellow_circle:",
    "low": ":white_circle:",
}

CONFIDENCE_BAR = {
    (0.9, 1.01): "████████████ 90%+",
    (0.7, 0.9):  "█████████░░░ 70-89%",
    (0.5, 0.7):  "██████░░░░░░ 50-69%",
    (0.0, 0.5):  "███░░░░░░░░░ <50%",
}


def _conf_bar(confidence: float) -> str:
    for (lo, hi), bar in CONFIDENCE_BAR.items():
        if lo <= confidence < hi:
            return bar
    return "unknown"


def build_slack_blocks(inv: Investigation) -> list:
    emoji = SEVERITY_EMOJI.get(inv.severity.lower(), ":white_circle:")
    duration = ""
    if inv.completed_at and inv.started_at:
        secs = int((inv.completed_at - inv.started_at).total_seconds())
        duration = f"  |  _{secs}s investigation_"

    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"{emoji}  {inv.alert_name}",
                "emoji": True,
            },
        },
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f"*ID:* `{inv.id}`  |  *Severity:* {inv.severity.upper()}{duration}",
                }
            ],
        },
        {"type": "divider"},
    ]

    # Root cause
    if inv.root_cause:
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*:mag: Root Cause*\n{inv.root_cause}\n\n*Confidence:* `{_conf_bar(inv.confidence)}`",
            },
        })

    # Affected
    if inv.affected_hosts or inv.affected_services:
        hosts_str = ", ".join(f"`{h}`" for h in inv.affected_hosts) or "_none identified_"
        svcs_str = ", ".join(f"`{s}`" for s in inv.affected_services) or "_none identified_"
        blocks.append({
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": f"*Affected Hosts*\n{hosts_str}"},
                {"type": "mrkdwn", "text": f"*Affected Services*\n{svcs_str}"},
            ],
        })

    if inv.first_seen:
        blocks.append({
            "type": "section",
            "text": {"type": "mrkdwn", "text": f":clock1: *First seen:* {inv.first_seen}"},
        })

    blocks.append({"type": "divider"})

    # Summary
    if inv.summary:
        blocks.append({
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"*:memo: Summary*\n{inv.summary}"},
        })

    # Recommendation
    if inv.recommendation:
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f":white_check_mark: *Recommendation*\n{inv.recommendation}",
            },
        })

    # Evidence trail
    if inv.evidence:
        ev_lines = "\n".join(
            f"• `{e.tool}` — {list(e.query.values())[0] if e.query else ''}..."
            for e in inv.evidence[:5]
        )
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*:bar_chart: Evidence ({len(inv.evidence)} queries)*\n{ev_lines}",
            },
        })

    blocks.append({
        "type": "context",
        "elements": [
            {"type": "mrkdwn", "text": "_Powered by Splunk Agentic Ops · Claude claude-sonnet-4-6_"}
        ],
    })

    return blocks


async def post_investigation_report(inv: Investigation) -> bool:
    webhook_url = os.getenv("SLACK_WEBHOOK_URL", "")
    if not webhook_url:
        print("[Slack] SLACK_WEBHOOK_URL not set — skipping notification.")
        return False

    payload = {
        "text": f"Incident investigation complete: {inv.alert_name}",
        "blocks": build_slack_blocks(inv),
    }

    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(webhook_url, json=payload)
        if resp.status_code != 200:
            print(f"[Slack] Post failed: {resp.status_code} {resp.text}")
            return False
        return True
