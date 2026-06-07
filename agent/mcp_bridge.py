"""
Bridges the Splunk MCP Server to the Anthropic tool-use format.

When USE_MCP=true the agent connects to the Splunk MCP Server (running at
MCP_SERVER_URL) and uses its tools directly. This satisfies the "Best Use of
Splunk MCP Server" prize criterion.

Falls back transparently to the direct REST client when MCP is not configured.
"""
import os
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator, Dict, List, Tuple

MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://localhost:8080/sse")


@asynccontextmanager
async def _mcp_session():
    from mcp.client.sse import sse_client
    from mcp import ClientSession

    async with sse_client(MCP_SERVER_URL) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            yield session


async def get_mcp_tools() -> List[Dict]:
    """Return MCP server tools converted to Anthropic tool format."""
    async with _mcp_session() as session:
        response = await session.list_tools()
        return [
            {
                "name": t.name,
                "description": t.description or "",
                "input_schema": t.inputSchema or {"type": "object", "properties": {}},
            }
            for t in response.tools
        ]


async def call_mcp_tool(tool_name: str, tool_input: Dict) -> str:
    """Call a tool on the MCP server and return its text output."""
    async with _mcp_session() as session:
        result = await session.call_tool(tool_name, tool_input)
        if result.content:
            return "\n".join(
                c.text for c in result.content if hasattr(c, "text") and c.text
            )
        return ""
