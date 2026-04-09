"""Extensible tool registry — register, discover, and invoke agent tools.

Tools are registered with metadata (name, description, schema) and can be
used by any agent framework. The registry handles:
- Tool discovery (list available tools)
- Schema generation (for LLM function calling)
- Invocation with type validation
- Framework-specific format conversion (Anthropic, OpenAI, Strands)

Usage:
    @tool_registry.register
    async def get_weather(location: str, units: str = "metric") -> str:
        '''Get current weather for a location.'''
        ...

    tools = tool_registry.list_tools()
    result = await tool_registry.invoke("get_weather", {"location": "Berlin"})
    anthropic_tools = tool_registry.to_anthropic_format()
"""

import inspect
import json
from dataclasses import dataclass, field
from typing import Any, Callable, get_type_hints

import structlog

log = structlog.get_logger()


@dataclass
class ToolDefinition:
    name: str
    description: str
    parameters: dict  # JSON Schema
    fn: Callable
    tags: list[str] = field(default_factory=list)


class ToolRegistry:
    """Central registry for all agent tools."""

    def __init__(self):
        self._tools: dict[str, ToolDefinition] = {}

    def register(self, fn: Callable = None, *, tags: list[str] | None = None):
        """Register a tool function. Works as decorator or direct call."""
        def decorator(f: Callable) -> Callable:
            name = f.__name__
            description = (f.__doc__ or "").strip().split("\n")[0]
            parameters = self._extract_schema(f)
            self._tools[name] = ToolDefinition(
                name=name, description=description, parameters=parameters,
                fn=f, tags=tags or [],
            )
            log.debug("tool_registered", name=name, tags=tags)
            return f

        if fn is not None:
            return decorator(fn)
        return decorator

    def list_tools(self, tag: str | None = None) -> list[ToolDefinition]:
        """List all registered tools, optionally filtered by tag."""
        tools = list(self._tools.values())
        if tag:
            tools = [t for t in tools if tag in t.tags]
        return tools

    async def invoke(self, name: str, arguments: dict) -> str:
        """Invoke a tool by name with arguments."""
        if name not in self._tools:
            return json.dumps({"error": f"Unknown tool: {name}"})

        tool = self._tools[name]
        log.info("tool_invoke", name=name, args=list(arguments.keys()))

        try:
            result = tool.fn(**arguments)
            if inspect.iscoroutine(result):
                result = await result
            return str(result) if not isinstance(result, str) else result
        except Exception as e:
            log.error("tool_error", name=name, error=str(e))
            return json.dumps({"error": str(e)})

    def to_anthropic_format(self, tag: str | None = None) -> list[dict]:
        """Convert tools to Anthropic API format."""
        return [
            {"name": t.name, "description": t.description, "input_schema": t.parameters}
            for t in self.list_tools(tag)
        ]

    def to_openai_format(self, tag: str | None = None) -> list[dict]:
        """Convert tools to OpenAI function calling format."""
        return [
            {"type": "function", "function": {
                "name": t.name, "description": t.description, "parameters": t.parameters,
            }}
            for t in self.list_tools(tag)
        ]

    def to_gemini_format(self, tag: str | None = None) -> list[dict]:
        """Convert tools to Gemini function declaration format.

        Returns a list of dicts compatible with google.genai types.Tool.
        """
        declarations = []
        for t in self.list_tools(tag):
            decl = {
                "name": t.name,
                "description": t.description,
            }
            if t.parameters.get("properties"):
                decl["parameters"] = t.parameters
            declarations.append(decl)
        return declarations

    def _extract_schema(self, fn: Callable) -> dict:
        """Extract JSON Schema from function signature + type hints."""
        hints = get_type_hints(fn)
        sig = inspect.signature(fn)
        properties = {}
        required = []

        for name, param in sig.parameters.items():
            if name in ("self", "cls"):
                continue
            hint = hints.get(name, str)
            prop = {"type": self._python_type_to_json(hint)}
            if param.default is inspect.Parameter.empty:
                required.append(name)
            else:
                prop["default"] = param.default
            properties[name] = prop

        return {"type": "object", "properties": properties, "required": required}

    @staticmethod
    def _python_type_to_json(t) -> str:
        mapping = {str: "string", int: "integer", float: "number", bool: "boolean", list: "array"}
        return mapping.get(t, "string")


# Global instance — import and use everywhere
tool_registry = ToolRegistry()
