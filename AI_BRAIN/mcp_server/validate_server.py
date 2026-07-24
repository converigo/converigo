#!/usr/bin/env python3
"""Validate the AI_BRAIN MCP server and its tool/resource registry."""

from __future__ import annotations

from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parents[3]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from AI_BRAIN.mcp_server.server import (
    build_context_tool,
    list_resource_uris,
    list_tool_names,
    project_summary_tool,
)


def main() -> None:
    print("AI_BRAIN MCP Server Validation")
    print("==============================")

    tools = list_tool_names()
    resources = list_resource_uris()

    print("Available tools:")
    for tool in tools:
        print(f"- {tool}")

    print("\nAvailable resources:")
    for resource in resources:
        print(f"- {resource}")

    print("\nSample tool executions:")
    summary = project_summary_tool()
    print(f"project_summary -> {summary}")

    prompt = build_context_tool("Validate MCP server prompt generation")
    print(f"build_context -> task={prompt['task']} prompt_len={len(prompt['prompt'])}")


if __name__ == "__main__":
    main()
