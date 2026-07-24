#!/usr/bin/env python3
"""Rank relevant AI_BRAIN context for a given user task."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .context_loader import GatewayContext, tokenize


@dataclass(frozen=True)
class RankedContext:
    modules: list[dict[str, Any]]
    services: list[dict[str, Any]]
    routes: list[dict[str, Any]]
    converters: list[dict[str, Any]]
    summary: dict[str, Any]


def extract_semantic_objects(semantic_knowledge: dict[str, Any]) -> list[dict[str, Any]]:
    data = semantic_knowledge.get("semantic_objects")
    return data if isinstance(data, list) else []


def extract_relationships(relationships: dict[str, Any]) -> list[dict[str, Any]]:
    data = relationships.get("relationships")
    return data if isinstance(data, list) else []


def build_lookup_by_type(relationships: list[dict[str, Any]]) -> dict[str, set[str]]:
    buckets: dict[str, set[str]] = {
        "module": set(),
        "service": set(),
        "router": set(),
        "converter": set(),
    }
    for record in relationships:
        source_type = record.get("source_type")
        target_type = record.get("target_type")
        source = record.get("source")
        target = record.get("target")
        if source_type in buckets and isinstance(source, str):
            buckets[source_type].add(source)
        if target_type in buckets and isinstance(target, str):
            buckets[target_type].add(target)
    return buckets


def score_entity(tokens: set[str], entity_name: str | None, source_file: str | None) -> int:
    score = 0
    if entity_name and isinstance(entity_name, str) and tokenize(entity_name) & tokens:
        score += 3
    if source_file and isinstance(source_file, str) and tokenize(source_file) & tokens:
        score += 2
    return score


def rank_modules(context: GatewayContext, task_tokens: set[str]) -> list[dict[str, Any]]:
    objects = extract_semantic_objects(context.semantic_knowledge)
    scored = []
    for item in objects:
        source = item.get("module")
        category = item.get("category")
        purpose = item.get("purpose")
        token_hits = tokenize(source) | tokenize(category) | tokenize(purpose)
        score = len(task_tokens & token_hits) * 5
        score += len(task_tokens & set(item.get("related_services", []))) * 3
        score += len(task_tokens & set(item.get("related_routes", []))) * 3
        score += len(task_tokens & set(item.get("related_documentation", []))) * 2
        if item.get("status") == "linked":
            score += 1
        if score > 0:
            scored.append((score, item))
    scored.sort(key=lambda pair: (-pair[0], str(pair[1].get("module", ""))))
    return [item for _, item in scored[:10]]


def rank_services(context: GatewayContext, task_tokens: set[str]) -> list[dict[str, Any]]:
    objects = extract_semantic_objects(context.semantic_knowledge)
    scored = []
    for item in objects:
        for service in item.get("related_services", []):
            score = len(task_tokens & tokenize(service)) * 5
            score += len(task_tokens & tokenize(item.get("category"))) * 2
            if score > 0:
                scored.append((score, {"service": service, "module": item.get("module"), "category": item.get("category")}))
    scored.sort(key=lambda pair: (-pair[0], pair[1].get("service", "")))
    unique = []
    seen = set()
    for _, record in scored:
        service_name = record.get("service")
        if service_name and service_name not in seen:
            seen.add(service_name)
            unique.append(record)
        if len(unique) >= 10:
            break
    return unique


def rank_routes(context: GatewayContext, task_tokens: set[str]) -> list[dict[str, Any]]:
    relationships = extract_relationships(context.relationships)
    scored = []
    for relation in relationships:
        if relation.get("relationship") != "module_to_router":
            continue
        target = relation.get("target")
        score = len(task_tokens & tokenize(target)) * 5
        if score > 0:
            scored.append((score, relation))
    scored.sort(key=lambda pair: (-pair[0], str(pair[1].get("target", ""))))
    return [relation for _, relation in scored[:10]]


def rank_converters(context: GatewayContext, task_tokens: set[str]) -> list[dict[str, Any]]:
    objects = extract_semantic_objects(context.semantic_knowledge)
    scored = []
    for item in objects:
        for converter in item.get("related_documentation", []):
            if converter.lower().startswith("plugin:"):
                score = len(task_tokens & tokenize(converter)) * 5
                if score > 0:
                    scored.append((score, {"converter": converter, "module": item.get("module")}))
    scored.sort(key=lambda pair: (-pair[0], str(pair[1].get("converter", ""))))
    return [record for _, record in scored[:10]]


def build_dependency_summary(context: GatewayContext, ranked_modules: list[dict[str, Any]]) -> list[dict[str, Any]]:
    dependency_index = context.dependency_graph.get("by_source", {})
    summary = []
    for item in ranked_modules[:5]:
        source = item.get("module")
        counts = dependency_index.get(source, {})
        summary.append(
            {
                "source_file": source,
                "internal_dependencies": int(counts.get("internal", 0)),
                "external_dependencies": int(counts.get("external", 0)),
            }
        )
    return summary


def rank_context(context: GatewayContext, user_task: str) -> RankedContext:
    task_tokens = tokenize(user_task)
    ranked_modules = rank_modules(context, task_tokens)
    ranked_services = rank_services(context, task_tokens)
    ranked_routes = rank_routes(context, task_tokens)
    ranked_converters = rank_converters(context, task_tokens)
    dependency_summary = build_dependency_summary(context, ranked_modules)
    return RankedContext(
        modules=ranked_modules,
        services=ranked_services,
        routes=ranked_routes,
        converters=ranked_converters,
        summary={
            "module_count": len(ranked_modules),
            "service_count": len(ranked_services),
            "route_count": len(ranked_routes),
            "converter_count": len(ranked_converters),
            "dependency_summary": dependency_summary,
        },
    )
