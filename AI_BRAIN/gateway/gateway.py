#!/usr/bin/env python3
"""AI Gateway v1 for Converigo AI_BRAIN prompts."""

from __future__ import annotations

from .context_loader import load_context
from .context_ranker import rank_context
from .prompt_builder import build_prompt
from .task_detector import detect_task_category


def build_prompt_for_task(user_task: str) -> str:
    """Build an optimized prompt for the provided user task."""
    context = load_context()
    category = detect_task_category(user_task)
    ranked = rank_context(context, user_task)
    return build_prompt(user_task, {
        "reasoning_context": context.reasoning_context,
        "semantic_knowledge": context.semantic_knowledge,
    }, ranked, category)


if __name__ == "__main__":
    example_task = "Fix the upload crash when converting large PDF documents."
    print(build_prompt_for_task(example_task))
