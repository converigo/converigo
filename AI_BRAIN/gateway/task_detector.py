#!/usr/bin/env python3
"""Detect task categories from a user request."""

from __future__ import annotations

from enum import Enum
from typing import Any


class TaskCategory(str, Enum):
    BUG_FIX = "Bug Fix"
    FEATURE = "Feature"
    REFACTOR = "Refactor"
    UI = "UI"
    SEO = "SEO"
    DEPLOYMENT = "Deployment"
    TESTING = "Testing"
    DOCUMENTATION = "Documentation"
    UNKNOWN = "Unknown"


TASK_KEYWORDS: dict[TaskCategory, tuple[str, ...]] = {
    TaskCategory.BUG_FIX: ("fix", "bug", "error", "crash", "failure", "issue", "debug", "resolve"),
    TaskCategory.FEATURE: ("add", "implement", "build", "support", "feature", "enable", "create"),
    TaskCategory.REFACTOR: ("refactor", "clean", "restructure", "simplify", "optimize", "rewrite"),
    TaskCategory.UI: ("ui", "interface", "screen", "page", "layout", "frontend", "button", "modal", "dialog"),
    TaskCategory.SEO: ("seo", "search", "ranking", "keyword", "metadata", "schema", "crawl"),
    TaskCategory.DEPLOYMENT: ("deploy", "deployment", "pipeline", "release", "infrastructure", "docker", "kubernetes"),
    TaskCategory.TESTING: ("test", "tests", "coverage", "spec", "suite", "validate", "verify", "regression", "validate"),
    TaskCategory.DOCUMENTATION: ("docs", "documentation", "readme", "guide", "manual", "doc", "specification"),
}


def normalize_text(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    return value.strip().lower()


def tokenize_text(value: str) -> set[str]:
    normalized = normalize_text(value)
    if not normalized:
        return set()
    tokens: set[str] = set()
    current: list[str] = []
    for character in normalized:
        if character.isalnum():
            current.append(character)
        else:
            if current:
                tokens.add("".join(current))
                current = []
    if current:
        tokens.add("".join(current))
    return tokens


def detect_task_category(user_task: str) -> TaskCategory:
    """Return the best matching task category for a user request."""
    normalized = normalize_text(user_task)
    tokens = tokenize_text(user_task)
    if not normalized:
        return TaskCategory.UNKNOWN

    matches: dict[TaskCategory, int] = {category: 0 for category in TaskCategory}

    for category, keywords in TASK_KEYWORDS.items():
        for keyword in keywords:
            if keyword in tokens:
                matches[category] += 1

    ranked = sorted(matches.items(), key=lambda pair: (-pair[1], pair[0].value))
    best_category, best_score = ranked[0]
    if best_score <= 0:
        return TaskCategory.UNKNOWN
    return best_category
