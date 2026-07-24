#!/usr/bin/env python3
"""AI_BRAIN MCP Server v1 exposing tools, resources, and prompts via the official MCP SDK."""

from __future__ import annotations

import argparse
import anyio
import os
import sys
from typing import Any

# If executed directly, ensure the repo root (parent of AI_BRAIN) is on sys.path.
if __name__ == "__main__":
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    if repo_root not in sys.path:
        sys.path.insert(0, repo_root)

from mcp.server.fastmcp import FastMCP

from AI_BRAIN.mcp_server.resources import RESOURCE_FILES, load_resource
from AI_BRAIN.gateway.gateway import build_prompt_for_task
from AI_BRAIN.mcp_server.services import (
    ArchitectureService,
    ConverterRegistryService,
    ImplementationPlanService,
    RepositorySearchService,
    RouteRegistryService,
    ServiceRegistryService,
)


SERVER_NAME = "AI_BRAIN MCP Server"
SERVER_INSTRUCTIONS = (
    "Expose AI_BRAIN metadata and gateway utilities as a Model Context Protocol (MCP) server."
)

server = FastMCP(
    name=SERVER_NAME,
    instructions=SERVER_INSTRUCTIONS,
    json_response=True,
    host="127.0.0.1",
    port=8000,
    mount_path="/",
    streamable_http_path="/mcp",
)

repository_search_service = RepositorySearchService()
converter_registry_service = ConverterRegistryService()
route_registry_service = RouteRegistryService()
service_registry_service = ServiceRegistryService()
architecture_service = ArchitectureService()
implementation_plan_service = ImplementationPlanService()


@server.tool(
    name="repository_search",
    title="Repository Search",
    description="Search the repository metadata and generated file index for matching files, docs, and semantic objects.",
)
def repository_search_tool(query: str, category: str | None = None, limit: int = 10) -> dict[str, Any]:
    return repository_search_service.search_repository(query, category=category, limit=limit)


@server.tool(
    name="find_converter",
    title="Find Converter",
    description="Locate converter metadata by converter name or source file.",
)
def find_converter_tool(name: str) -> dict[str, Any]:
    return converter_registry_service.find_converter(name)


@server.tool(
    name="find_route",
    title="Find Route",
    description="Locate route metadata by endpoint, router, or source file.",
)
def find_route_tool(name: str) -> dict[str, Any]:
    return route_registry_service.find_route(name)


@server.tool(
    name="find_service",
    title="Find Service",
    description="Locate service metadata by service name or source file.",
)
def find_service_tool(name: str) -> dict[str, Any]:
    return service_registry_service.find_service(name)


@server.tool(
    name="architecture_summary",
    title="Architecture Summary",
    description="Summarize the project's architecture and high-level module categories.",
)
def architecture_summary_tool(detail_level: str = "summary") -> dict[str, Any]:
    return architecture_service.architecture_summary(detail_level=detail_level)


@server.tool(
    name="implementation_plan",
    title="Implementation Plan",
    description="Generate an implementation plan for a task using repository metadata and service context.",
)
def implementation_plan_tool(task: str, focus_module: str | None = None) -> dict[str, Any]:
    return implementation_plan_service.implementation_plan(task, focus_module=focus_module)


@server.tool(
    name="build_context",
    title="Build Context",
    description="Build an AI prompt for a task using AI_BRAIN gateway context.",
)
def build_context_tool(task: str) -> dict[str, Any]:
    return {"task": task, "prompt": build_prompt_for_task(task)}


@server.prompt(
    name="build_context_prompt",
    title="Build Context Prompt",
    description="Render an AI prompt message for a task using AI_BRAIN generated metadata.",
)
def build_context_prompt(task: str) -> list[dict[str, str]]:
    prompt = build_prompt_for_task(task)
    return [
        {
            "role": "assistant",
            "content": prompt,
        }
    ]


@server.resource(
    "resource://semantic_knowledge.json",
    name="semantic_knowledge",
    title="Semantic Knowledge",
    description="AI_BRAIN semantic knowledge metadata.",
)
def semantic_knowledge_resource() -> dict[str, Any]:
    return load_resource("semantic_knowledge.json")


@server.resource(
    "resource://relationships.json",
    name="relationships",
    title="Relationships",
    description="AI_BRAIN relationship metadata.",
)
def relationships_resource() -> dict[str, Any]:
    return load_resource("relationships.json")


@server.resource(
    "resource://dependency_graph.json",
    name="dependency_graph",
    title="Dependency Graph",
    description="AI_BRAIN dependency graph metadata.",
)
def dependency_graph_resource() -> dict[str, Any]:
    return load_resource("dependency_graph.json")


@server.resource(
    "resource://reasoning_context.json",
    name="reasoning_context",
    title="Reasoning Context",
    description="AI_BRAIN reasoning context metadata.",
)
def reasoning_context_resource() -> dict[str, Any]:
    return load_resource("reasoning_context.json")


def list_tool_names() -> list[str]:
    return [tool.name for tool in server._tool_manager.list_tools()]


def list_resource_uris() -> list[str]:
    return [resource.uri for resource in server._resource_manager.list_resources()]


def invoke_tool(name: str, arguments: dict[str, Any] | None = None) -> Any:
    """Invoke a registered MCP tool synchronously for local validation."""
    result = anyio.run(server.call_tool, name, arguments or {})
    if isinstance(result, tuple) and len(result) == 2:
        return result[1]
    return result


def load_resource_file(resource_name: str) -> dict[str, Any]:
    if resource_name not in RESOURCE_FILES:
        return {}
    return load_resource(resource_name)


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the AI_BRAIN MCP server.")
    parser.add_argument(
        "--transport",
        choices=["stdio", "sse", "streamable-http"],
        default="stdio",
        help="Transport protocol for the MCP server.",
    )
    parser.add_argument(
        "--mount-path",
        default="/",
        help="Mount path for SSE transport.",
    )
    args = parser.parse_args()

    if args.transport == "sse":
        server.run(transport="sse", mount_path=args.mount_path)
    else:
        server.run(transport=args.transport)


if __name__ == "__main__":
    main()
