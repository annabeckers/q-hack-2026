"""MCP (Model Context Protocol) client — connect agents to external tool servers.

MCP lets agents dynamically discover and call tools hosted on external servers.
This is how you extend agent capabilities without modifying agent code.

Usage:
    client = MCPToolClient("http://localhost:9000/mcp")
    tools = await client.list_tools()
    result = await client.call_tool("search", {"query": "hello"})

    # Or integrate with Strands SDK:
    from strands.tools.mcp.mcp_client import MCPClient
    mcp = MCPClient(lambda: streamablehttp_client(url))
    with mcp:
        agent = Agent(model=model, tools=agent_tools + mcp.list_tools_sync())
"""

import httpx
import structlog
from dataclasses import dataclass

log = structlog.get_logger()


@dataclass
class MCPTool:
    name: str
    description: str
    input_schema: dict


class MCPToolClient:
    """Lightweight MCP client for tool discovery and invocation.

    Supports the MCP Streamable HTTP transport. For stdio transport
    or SSE transport, use the official mcp Python package directly.
    """

    def __init__(self, server_url: str, headers: dict | None = None):
        self.server_url = server_url.rstrip("/")
        self.headers = headers or {}

    async def list_tools(self) -> list[MCPTool]:
        """Discover available tools from the MCP server."""
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                self.server_url,
                json={"jsonrpc": "2.0", "method": "tools/list", "id": 1},
                headers=self.headers,
            )
            resp.raise_for_status()
            data = resp.json()

        tools = []
        for tool in data.get("result", {}).get("tools", []):
            tools.append(MCPTool(
                name=tool["name"],
                description=tool.get("description", ""),
                input_schema=tool.get("inputSchema", {}),
            ))

        log.info("mcp_tools_discovered", server=self.server_url, count=len(tools))
        return tools

    async def call_tool(self, name: str, arguments: dict) -> str:
        """Invoke a tool on the MCP server."""
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                self.server_url,
                json={
                    "jsonrpc": "2.0",
                    "method": "tools/call",
                    "params": {"name": name, "arguments": arguments},
                    "id": 2,
                },
                headers=self.headers,
            )
            resp.raise_for_status()
            data = resp.json()

        result = data.get("result", {})
        content = result.get("content", [])

        # Extract text from content blocks
        texts = [c.get("text", "") for c in content if c.get("type") == "text"]
        return "\n".join(texts) if texts else str(result)

    def to_agent_tools(self, tools: list[MCPTool]) -> list[dict]:
        """Convert MCP tools to Anthropic tool format for direct API usage."""
        return [
            {
                "name": t.name,
                "description": t.description,
                "input_schema": t.input_schema,
            }
            for t in tools
        ]
