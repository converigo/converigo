#!/usr/bin/env python3
"""Validation tests for AI_BRAIN gateway v1."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT_DIR = Path(__file__).resolve().parents[2]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from AI_BRAIN.gateway import context_loader, context_ranker, gateway as gateway_module, prompt_builder, task_detector


class TestContextLoader(unittest.TestCase):
    def test_loads_all_required_metadata(self):
        context = context_loader.load_context()
        self.assertIsInstance(context.context, dict)
        self.assertIsInstance(context.semantic_knowledge, dict)
        self.assertIsInstance(context.relationships, dict)
        self.assertIsInstance(context.dependency_graph, dict)
        self.assertIsInstance(context.reasoning_context, dict)

    def test_handles_missing_files_gracefully(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            required = ["context.json", "semantic_knowledge.json", "relationships.json", "dependency_graph.json", "reasoning_context.json"]
            (temp_path / "context.json").write_text(json.dumps({"ok": True}), encoding="utf-8")
            with patch.object(context_loader, "generated_dir", return_value=temp_path):
                context = context_loader.load_context()
            self.assertEqual(context.context, {"ok": True})
            self.assertEqual(context.semantic_knowledge, {})
            self.assertEqual(context.relationships, {})
            self.assertEqual(context.dependency_graph, {})
            self.assertEqual(context.reasoning_context, {})


class TestTaskDetector(unittest.TestCase):
    def test_detects_bug_fix(self):
        category = task_detector.detect_task_category("Fix the upload crash in document conversion")
        self.assertEqual(category.value, "Bug Fix")

    def test_detects_feature(self):
        category = task_detector.detect_task_category("Add support for HEIC to PNG conversion")
        self.assertEqual(category.value, "Feature")

    def test_detects_refactor(self):
        category = task_detector.detect_task_category("Refactor the prompt builder for clarity")
        self.assertEqual(category.value, "Refactor")

    def test_detects_ui(self):
        category = task_detector.detect_task_category("Update the upload interface for better user experience")
        self.assertEqual(category.value, "UI")

    def test_detects_seo(self):
        category = task_detector.detect_task_category("Improve SEO metadata generation for articles")
        self.assertEqual(category.value, "SEO")

    def test_detects_deployment(self):
        category = task_detector.detect_task_category("Prepare deployment pipeline and release artifacts")
        self.assertEqual(category.value, "Deployment")

    def test_detects_testing(self):
        category = task_detector.detect_task_category("Write tests for the new converter service")
        self.assertEqual(category.value, "Testing")

    def test_detects_documentation(self):
        category = task_detector.detect_task_category("Update the documentation and README for the gateway")
        self.assertEqual(category.value, "Documentation")


class TestContextRanker(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.context = context_loader.load_context()

    def test_returns_ranked_modules(self):
        ranked = context_ranker.rank_context(self.context, "Refactor AI_BRAIN gateway prompt builder")
        self.assertIsInstance(ranked.modules, list)
        self.assertIsInstance(ranked.summary, dict)

    def test_returns_ranked_services(self):
        ranked = context_ranker.rank_context(self.context, "Optimize analytics service and conversion flow")
        self.assertIsInstance(ranked.services, list)

    def test_returns_ranked_routes(self):
        ranked = context_ranker.rank_context(self.context, "Update routing and API endpoints for new feature")
        self.assertIsInstance(ranked.routes, list)

    def test_returns_ranked_converters(self):
        ranked = context_ranker.rank_context(self.context, "Improve converter plugin handling for image formats")
        self.assertIsInstance(ranked.converters, list)


class TestPromptBuilder(unittest.TestCase):
    def test_prompt_contains_required_sections(self):
        prompt = gateway_module.build_prompt_for_task("Fix the upload crash when converting large PDF documents.")
        self.assertIsInstance(prompt, str)
        self.assertIn("Project Summary", prompt)
        self.assertIn("Task", prompt)
        self.assertIn("Relevant Modules", prompt)
        self.assertIn("Dependencies", prompt)
        self.assertIn("Coding Rules", prompt)
        self.assertIn("Known Risks", prompt)
        self.assertIn("Context", prompt)

    def test_gateway_build_prompt(self):
        prompt = gateway_module.build_prompt_for_task("Add SEO metadata extraction for converter documentation.")
        self.assertTrue(prompt.strip())
        self.assertIn("Category:", prompt)
        self.assertIn("Task:", prompt)


def run_gateway_validation() -> None:
    suite = unittest.defaultTestLoader.loadTestsFromModule(sys.modules[__name__])
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    report = {
        "passed": result.testsRun - len(result.failures) - len(result.errors),
        "failed": len(result.failures) + len(result.errors),
        "coverage": f"{((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%" if result.testsRun else "0.0%",
        "missing_metadata": [],
    }

    generated_dir = Path(__file__).resolve().parents[1] / "generated"
    required_files = [
        "context.json",
        "semantic_knowledge.json",
        "relationships.json",
        "dependency_graph.json",
        "reasoning_context.json",
    ]
    for filename in required_files:
        if not (generated_dir / filename).exists():
            report["missing_metadata"].append(filename)

    report_path = Path(__file__).resolve().parent / "gateway_validation_report.json"
    with report_path.open("w", encoding="utf-8") as report_file:
        json.dump(report, report_file, indent=2)

    if not result.wasSuccessful():
        raise SystemExit(1)


if __name__ == "__main__":
    run_gateway_validation()
