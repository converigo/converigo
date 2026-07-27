#!/usr/bin/env python3
"""Prompt templates and helper utilities for the MCP server."""

from __future__ import annotations

from typing import Any


def tool_description(tool_name: str, description: str) -> str:
    return f"Tool: {tool_name}\nDescription: {description}\n"


def build_tool_list(tools: list[str]) -> str:
    if not tools:
        return "No tools available."
    return "\n".join([f"- {tool}" for tool in tools])


def build_resource_list(resources: list[str]) -> str:
    if not resources:
        return "No resources available."
    return "\n".join([f"- {resource}" for resource in resources])
