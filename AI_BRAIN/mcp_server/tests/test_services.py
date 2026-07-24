#!/usr/bin/env python3
"""Tests for AI_BRAIN MCP services."""

from __future__ import annotations

import unittest
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from AI_BRAIN.mcp_server.services import (
    ArchitectureService,
    ConverterRegistryService,
    RepositorySearchService,
    RouteRegistryService,
    ServiceRegistryService,
    ImplementationPlanService,
)


class TestRepositorySearchService(unittest.TestCase):
    def setUp(self) -> None:
        self.service = RepositorySearchService()

    def test_search_repository_finds_files(self):
        result = self.service.search_repository("AI_BRAIN")
        self.assertIsInstance(result, dict)
        self.assertGreaterEqual(result["total_matches"], 1)
        self.assertIn("matches", result)

    def test_search_repository_filters_by_category(self):
        result = self.service.search_repository("AI_BRAIN", category="documentation")
        self.assertIn("matches", result)
        for item in result["matches"]:
            self.assertEqual(item["category"], "documentation")


class TestConverterRegistryService(unittest.TestCase):
    def setUp(self) -> None:
        self.service = ConverterRegistryService()

    def test_find_converter_returns_matches(self):
        result = self.service.find_converter("PDF")
        self.assertIsInstance(result, dict)
        self.assertIn("matches", result)


class TestRouteRegistryService(unittest.TestCase):
    def setUp(self) -> None:
        self.service = RouteRegistryService()

    def test_find_route_returns_matches(self):
        result = self.service.find_route("/health")
        self.assertIsInstance(result, dict)
        self.assertGreaterEqual(result["total_matches"], 1)


class TestServiceRegistryService(unittest.TestCase):
    def setUp(self) -> None:
        self.service = ServiceRegistryService()

    def test_find_service_returns_matches(self):
        result = self.service.find_service("Analytics")
        self.assertIsInstance(result, dict)
        self.assertGreaterEqual(result["total_matches"], 1)


class TestArchitectureService(unittest.TestCase):
    def setUp(self) -> None:
        self.service = ArchitectureService()

    def test_architecture_summary_returns_totals(self):
        result = self.service.architecture_summary()
        self.assertIn("totals", result)
        self.assertIn("categories", result)


class TestImplementationPlanService(unittest.TestCase):
    def setUp(self) -> None:
        self.service = ImplementationPlanService()

    def test_implementation_plan_returns_steps(self):
        result = self.service.implementation_plan("Improve PDF conversion support")
        self.assertIn("steps", result)
        self.assertGreaterEqual(len(result["steps"]), 1)


if __name__ == "__main__":
    unittest.main()
