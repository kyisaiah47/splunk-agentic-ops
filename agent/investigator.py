"""
Core agentic investigation loop.

The agent uses Claude with tool use to iteratively query Splunk, build up
evidence, and synthesise a root-cause report. It supports two Splunk backends:
  - MCP mode  (USE_MCP=true)  — via the Splunk MCP Server
  - REST mode (default)       — via the Splunk Python SDK
"""
import asyncio
import json
import os
import re
import uuid
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

import anthropic

from agent.prompts import SYSTEM_PROMPT, build_investigation_prompt
from agent.tools import INVESTIGATION_TOOLS
from models import AlertWebhook, Evidence, Investigation

MAX_TOOL_CALLS = 8


def _get_client() -> anthropic.Anthropic:
    return anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

async def investigate_alert(alert: AlertWebhook, inv_id: Optional[str] = None) -> Investigation:
    inv = Investigation(
        id=inv_id or str(uuid.uuid4())[:8],
        alert_name=alert.alert_name,
        severity=alert.severity,
    )

    use_mcp = os.getenv("USE_MCP", "false").lower() == "true"

    try:
        if use_mcp:
            inv = await _run_with_mcp(alert, inv)
        else:
            inv = await _run_with_rest(alert, inv)
    except Exception as exc:
        inv.status = "failed"
        inv.error = str(exc)
        inv.completed_at = datetime.utcnow()

    return inv


# ---------------------------------------------------------------------------
# Backend-specific wrappers
# ---------------------------------------------------------------------------

async def _run_with_mcp(alert: AlertWebhook, inv: Investigation) -> Investigation:
    from agent.mcp_bridge import get_mcp_tools, call_mcp_tool

    tools = await get_mcp_tools()

    async def call_tool(name: str, inp: Dict) -> Any:
        return await call_mcp_tool(name, inp)

    return await _agent_loop(alert, inv, tools, call_tool)


async def _run_with_rest(alert: AlertWebhook, inv: Investigation) -> Investigation:
    from splunk.client import SplunkClient

    splunk = SplunkClient()
    tools = INVESTIGATION_TOOLS
    loop = asyncio.get_event_loop()

    async def call_tool(name: str, inp: Dict) -> Any:
        return await loop.run_in_executor(None, splunk.execute_tool, name, inp)

    return await _agent_loop(alert, inv, tools, call_tool)


# ---------------------------------------------------------------------------
# Agent loop
# ---------------------------------------------------------------------------

async def _agent_loop(
    alert: AlertWebhook,
    inv: Investigation,
    tools: List[Dict],
    call_tool: Callable,
) -> Investigation:
    messages: List[Dict] = [
        {"role": "user", "content": build_investigation_prompt(alert)}
    ]
    evidence: List[Evidence] = []
    tool_call_count = 0

    loop = asyncio.get_event_loop()

    for _ in range(MAX_TOOL_CALLS + 5):
        response = await loop.run_in_executor(
            None,
            lambda: _get_client().messages.create(
                model="claude-sonnet-4-6",
                max_tokens=4096,
                system=SYSTEM_PROMPT,
                tools=tools,
                messages=messages,
            ),
        )

        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason == "end_turn":
            final_text = "\n".join(
                b.text for b in response.content if hasattr(b, "text")
            )
            _parse_report(inv, final_text)
            break

        if response.stop_reason != "tool_use":
            break

        # Always provide tool_result for every tool_use block — required by the API.
        # When over the limit, return a stub result asking for synthesis.
        tool_results = []
        for block in response.content:
            if block.type != "tool_use":
                continue

            over_limit = tool_call_count >= MAX_TOOL_CALLS

            if over_limit:
                result_str = "Tool call budget exhausted. Write your final JSON report now using the evidence gathered so far."
            else:
                tool_call_count += 1
                raw_result = await call_tool(block.name, block.input)
                result_str = (
                    json.dumps(raw_result)
                    if not isinstance(raw_result, str)
                    else raw_result
                )
                evidence.append(
                    Evidence(
                        tool=block.name,
                        query=block.input,
                        result_preview=result_str[:600],
                    )
                )

            tool_results.append({
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": result_str,
            })

        messages.append({"role": "user", "content": tool_results})

    inv.evidence = evidence
    inv.completed_at = datetime.utcnow()
    inv.status = "completed"
    return inv


# ---------------------------------------------------------------------------
# Report parser
# ---------------------------------------------------------------------------

def _parse_report(inv: Investigation, text: str) -> None:
    match = re.search(r"```json\s*(\{.*?\})\s*```", text, re.DOTALL)
    if not match:
        # Try bare JSON object as fallback
        match = re.search(r"\{[^{}]*\"root_cause\"[^{}]*\}", text, re.DOTALL)

    if match:
        try:
            data = json.loads(match.group(1) if "```" in match.group(0) else match.group(0))
            inv.root_cause = data.get("root_cause")
            inv.confidence = float(data.get("confidence", 0.0))
            inv.first_seen = data.get("first_seen")
            inv.affected_hosts = data.get("affected_hosts", [])
            inv.affected_services = data.get("affected_services", [])
            inv.summary = data.get("summary")
            inv.recommendation = data.get("recommendation")
            inv.severity = data.get("severity_assessment", inv.severity)
            return
        except (json.JSONDecodeError, ValueError):
            pass

    # Fallback: store raw text as summary
    inv.summary = text[:1000]
    inv.root_cause = "See summary (JSON parse failed)"
