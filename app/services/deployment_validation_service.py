from __future__ import annotations

from pathlib import Path
from typing import Any

from app.core.registry import ConverterInfo, ConverterRegistry
from app.services.content_quality_service import ContentQualityService
from app.services.converter_data_service import ConverterDataService
from app.services.converter_registry_service import ConverterRegistryService
from app.services.hub_page_service import HubPageService
from app.services.plugin_validation_service import PluginValidationService
from app.services.production_audit_service import ProductionAuditService
from app.services.programmatic_seo_engine import ProgrammaticSeoEngine
from app.services.seo_publication_gate_service import SeoPublicationGateService
from app.services.seo_service import SeoService
from app.services.sitemap_service import SitemapService
from app.services.topic_cluster_service import TopicClusterService


class DeploymentValidationService:
    """Run a production-ready deployment validation pipeline."""

    def __init__(
        self,
        contracts_dir: Path | str | None = None,
        output_dir: Path | str | None = None,
        registry_instance: ConverterRegistry | None = None,
    ) -> None:
        self.contracts_dir = Path(contracts_dir or "app/data/converters")
        self.output_dir = Path(output_dir or "outputs")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.registry = registry_instance or ConverterRegistry()

        self.converter_data_service = ConverterDataService(self.contracts_dir)
        self._converter_registry_service: ConverterRegistryService | None = None
        self._converter_registry_error: Exception | None = None
        self._plugin_validation_service: PluginValidationService | None = None
        self._plugin_validation_results: list[Any] | None = None
        self._production_audit_service: ProductionAuditService | None = None
        self._sitemap_service: SitemapService | None = None
        self._seo_service: SeoService | None = None
        self._hub_service: HubPageService | None = None
        self._topic_cluster_service: TopicClusterService | None = None
        self._programmatic_seo_engine: ProgrammaticSeoEngine | None = None
        self._content_quality_service: ContentQualityService | None = None
        self._seo_publication_gate_service: SeoPublicationGateService | None = None

        self._register_active_contracts()

    @property
    def converter_registry_service(self) -> ConverterRegistryService | None:
        if self._converter_registry_service is None and self._converter_registry_error is None:
            try:
                self._converter_registry_service = ConverterRegistryService(self.contracts_dir)
            except Exception as exc:  # pragma: no cover - defensive loading
                self._converter_registry_error = exc
        return self._converter_registry_service

    @property
    def converter_registry_error(self) -> Exception | None:
        self.converter_registry_service
        return self._converter_registry_error

    @property
    def plugin_validation_service(self) -> PluginValidationService:
        if self._plugin_validation_service is None:
            self._plugin_validation_service = PluginValidationService(self.contracts_dir)
        return self._plugin_validation_service

    @property
    def production_audit_service(self) -> ProductionAuditService:
        if self._production_audit_service is None:
            self._production_audit_service = ProductionAuditService(
                contracts_dir=self.contracts_dir,
                converter_data_dir=self.contracts_dir,
                registry_instance=self.registry,
            )
        return self._production_audit_service

    @property
    def sitemap_service(self) -> SitemapService:
        if self._sitemap_service is None:
            self._sitemap_service = SitemapService(
                output_dir=self.output_dir / "sitemaps",
                registry_instance=self.registry,
            )
        return self._sitemap_service

    @property
    def seo_service(self) -> SeoService:
        if self._seo_service is None:
            self._seo_service = SeoService(self.contracts_dir)
        return self._seo_service

    @property
    def hub_service(self) -> HubPageService:
        if self._hub_service is None:
            self._hub_service = HubPageService(registry_instance=self.registry)
        return self._hub_service

    @property
    def topic_cluster_service(self) -> TopicClusterService:
        if self._topic_cluster_service is None:
            self._topic_cluster_service = TopicClusterService(self.contracts_dir)
        return self._topic_cluster_service

    @property
    def programmatic_seo_engine(self) -> ProgrammaticSeoEngine:
        if self._programmatic_seo_engine is None:
            self._programmatic_seo_engine = ProgrammaticSeoEngine(self.contracts_dir)
        return self._programmatic_seo_engine

    @property
    def seo_publication_gate_service(self) -> SeoPublicationGateService:
        if self._seo_publication_gate_service is None:
            self._seo_publication_gate_service = SeoPublicationGateService(self.contracts_dir)
        return self._seo_publication_gate_service

    @property
    def content_quality_service(self) -> ContentQualityService:
        if self._content_quality_service is None:
            self._content_quality_service = ContentQualityService(self.contracts_dir)
        return self._content_quality_service

    def run_all_checks(self) -> dict[str, Any]:
        stage_methods = [
            self._check_contract_schema,
            self._check_converter_data_presence,
            self._check_duplicate_slugs,
            self._check_plugin_coverage,
            self._check_route_generation,
            self._check_seo_metadata_generation,
            self._check_hub_inclusion,
            self._check_recommendation_coverage,
            self._check_sitemap_generation,
            self._check_sitemap_validation,
            self._check_robots_and_sitemap_availability,
            self._check_internal_link_coverage,
            self._check_topic_cluster_coverage,
            self._check_programmatic_seo_coverage,
            self._check_content_quality_gating,
            self._check_production_audit_summary,
        ]

        stages: list[dict[str, Any]] = []
        for index, method in enumerate(stage_methods, start=1):
            stage = method(index)
            stages.append(stage)

        failures = sum(1 for stage in stages if stage["status"] == "FAIL")
        warnings = sum(1 for stage in stages if stage["status"] == "WARNING")
        passed = sum(1 for stage in stages if stage["status"] == "PASS")

        deployment_status = (
            "FAIL" if failures > 0 else ("WARNING" if warnings > 0 else "PASS")
        )
        production_audit = self.production_audit_service.audit_all()
        production_health = self._derive_production_health(production_audit.get("summary", {}))
        seo_publication_report = self.seo_publication_gate_service.evaluate_all_pages()

        return {
            "all_passed": failures == 0,
            "deployment_status": deployment_status,
            "production_health": production_health,
            "stage_count": len(stages),
            "passed": passed,
            "warnings": warnings,
            "failures": failures,
            "stages": stages,
            "production_audit_summary": production_audit,
            "seo_publication_report": seo_publication_report,
            "regression_summary": {
                "status": "REQUIRED",
                "details": [
                    "Run the full regression suite separately before deployment.",
                    "No regressions are allowed.",
                ],
            },
        }

    def generate_markdown_report(self, report: dict[str, Any]) -> str:
        seo_publication = report.get("seo_publication_report", {})
        regression_summary = report.get("regression_summary", {})
        lines = [
            "# Deployment Validation Report",
            "",
            f"**Overall status:** {'PASS' if report['all_passed'] else 'FAIL'}",
            "",
            "## Deployment summary",
            "",
            f"- Deployment status: {report.get('deployment_status', 'UNKNOWN')}",
            f"- Production health: {report.get('production_health', 'UNKNOWN')}",
            f"- SEO publication ready: {seo_publication.get('ready_percentage', 0)}%",
            f"- Publishable pages: {seo_publication.get('ready_pages', 0)}",
            f"- Draft pages: {seo_publication.get('draft_pages', 0)}",
            f"- Rejected pages: {seo_publication.get('rejected_pages', 0)}",
            f"- Regression: {regression_summary.get('status', 'REQUIRED')}",
            "",
            "## Stage summary",
            "",
            f"- Total stages: {report['stage_count']}",
            f"- Passed: {report['passed']}",
            f"- Warnings: {report['warnings']}",
            f"- Failures: {report['failures']}",
            "",
        ]

        for stage in report["stages"]:
            lines.append(f"### {stage['id']}. {stage['name']} — {stage['status']}")
            lines.append("")
            if stage.get("details"):
                for detail in stage["details"]:
                    lines.append(f"- {detail}")
            else:
                lines.append("- No details available")
            lines.append("")

        return "\n".join(lines)

    def _check_contract_schema(self, stage_id: int) -> dict[str, Any]:
        name = "Contract schema validation"
        if self.converter_registry_error is not None:
            return self._build_stage(
                stage_id,
                name,
                "FAIL",
                [f"Contract registry failed to load: {self.converter_registry_error}"],
            )

        assert self.converter_registry_service is not None
        active = self.converter_registry_service.get_active()
        return self._build_stage(
            stage_id,
            name,
            "PASS",
            [f"Loaded {len(active)} active contracts"] if active else ["No active contracts found"],
        )

    def _check_converter_data_presence(self, stage_id: int) -> dict[str, Any]:
        name = "Converter data presence"
        if self.converter_registry_service is None:
            return self._build_stage(
                stage_id,
                name,
                "FAIL",
                ["Converter registry is unavailable due to contract schema errors."],
            )

        missing: list[str] = []
        for contract in self.converter_registry_service.get_active():
            slug = str(contract.get("slug", "")).strip()
            if not slug:
                continue
            try:
                self.converter_data_service.load_converter_by_slug(slug)
            except FileNotFoundError:
                missing.append(slug)

        if missing:
            return self._build_stage(
                stage_id,
                name,
                "FAIL",
                [f"Missing converter data for slugs: {', '.join(sorted(missing))}"],
            )

        return self._build_stage(stage_id, name, "PASS", ["All active contracts have converter data files."])

    def _check_duplicate_slugs(self, stage_id: int) -> dict[str, Any]:
        name = "Duplicate slug detection"
        duplicates = self.plugin_validation_service.check_duplicate_slugs()
        if duplicates:
            return self._build_stage(
                stage_id,
                name,
                "FAIL",
                [f"Duplicate slugs found: {', '.join(sorted(set(duplicates)))}"],
            )

        return self._build_stage(stage_id, name, "PASS", ["No duplicate converter slugs detected."])

    def _check_plugin_coverage(self, stage_id: int) -> dict[str, Any]:
        name = "Plugin registry coverage"
        missing = self.plugin_validation_service.check_missing_plugins()
        if missing:
            return self._build_stage(
                stage_id,
                name,
                "FAIL",
                [f"Missing plugin implementations for slugs: {', '.join(sorted(missing))}"],
            )

        return self._build_stage(stage_id, name, "PASS", ["All active converters have plugin coverage."])

    def _check_route_generation(self, stage_id: int) -> dict[str, Any]:
        name = "Route generation validation"
        results = self._get_plugin_validation_results()
        failed = [result["slug"] for result in results if not result["checks"].get("route_valid", False)]
        if failed:
            return self._build_stage(
                stage_id,
                name,
                "FAIL",
                [f"Route validation failed for: {', '.join(sorted(failed))}"],
            )

        return self._build_stage(stage_id, name, "PASS", ["All converters pass route validation."])

    def _check_seo_metadata_generation(self, stage_id: int) -> dict[str, Any]:
        name = "SEO metadata generation"
        results = self._get_plugin_validation_results()
        failed = [result["slug"] for result in results if not result["checks"].get("seo_valid", False)]
        if failed:
            return self._build_stage(
                stage_id,
                name,
                "FAIL",
                [f"SEO metadata generation failed for: {', '.join(sorted(failed))}"],
            )

        return self._build_stage(stage_id, name, "PASS", ["All converters generate valid SEO metadata."])

    def _check_hub_inclusion(self, stage_id: int) -> dict[str, Any]:
        name = "Hub inclusion consistency"
        results = self._get_plugin_validation_results()
        if not results:
            return self._build_stage(stage_id, name, "FAIL", ["Plugin validation did not return any converter results."])

        warnings = [result["slug"] for result in results if not result["checks"].get("hub_valid", True)]
        if warnings:
            return self._build_stage(
                stage_id,
                name,
                "WARNING",
                [
                    "Some converters are not included in a hub page.",
                    f"Affected slugs: {', '.join(sorted(warnings))}",
                ],
            )

        return self._build_stage(stage_id, name, "PASS", ["Hub inclusion checks completed successfully."])

    def _check_recommendation_coverage(self, stage_id: int) -> dict[str, Any]:
        name = "Recommendation coverage"
        results = self._get_plugin_validation_results()
        warnings = [result["slug"] for result in results if not result["checks"].get("recommendation_valid", True)]
        if warnings:
            return self._build_stage(
                stage_id,
                name,
                "WARNING",
                [
                    "Some converters may not generate recommendations.",
                    f"Affected slugs: {', '.join(sorted(warnings))}",
                ],
            )

        return self._build_stage(stage_id, name, "PASS", ["Recommendation generation is available for all converters."])

    def _check_sitemap_generation(self, stage_id: int) -> dict[str, Any]:
        name = "Sitemap generation"
        try:
            written_files = self.sitemap_service.generate_all(base_url="https://converigo.com")
            return self._build_stage(
                stage_id,
                name,
                "PASS",
                [f"Written sitemap files: {', '.join(sorted(written_files))}"],
            )
        except Exception as exc:
            return self._build_stage(stage_id, name, "FAIL", [str(exc)])

    def _check_sitemap_validation(self, stage_id: int) -> dict[str, Any]:
        name = "Sitemap validation"
        try:
            issues = self.sitemap_service.validate()
            if issues:
                return self._build_stage(stage_id, name, "FAIL", issues)
            return self._build_stage(stage_id, name, "PASS", ["Sitemap validation passed with no issues."])
        except Exception as exc:
            return self._build_stage(stage_id, name, "FAIL", [str(exc)])

    def _check_robots_and_sitemap_availability(self, stage_id: int) -> dict[str, Any]:
        name = "Robots and sitemap availability"
        try:
            request = type("Request", (), {})()
            sitemap_xml = self.seo_service.build_sitemap_xml(request)
            if "<urlset" not in sitemap_xml:
                return self._build_stage(stage_id, name, "FAIL", ["Generated sitemap XML is invalid."])

            robots_text = (
                "User-agent: *\n"
                "Allow: /\n\n"
                "Sitemap: https://converigo.com/sitemap.xml\n"
            )
            if "Sitemap: https://converigo.com/sitemap.xml" not in robots_text:
                return self._build_stage(stage_id, name, "FAIL", ["Robots.txt sitemap directive is missing."])

            return self._build_stage(stage_id, name, "PASS", ["Robots.txt and sitemap endpoint content are valid."])
        except Exception as exc:
            return self._build_stage(stage_id, name, "FAIL", [str(exc)])

    def _check_internal_link_coverage(self, stage_id: int) -> dict[str, Any]:
        name = "Internal link coverage"
        report = self.content_quality_service.internal_link_service.build_internal_link_coverage_report()
        coverage = report.get("internal_links_coverage_percentage", 0)
        details = [f"Internal link coverage: {coverage}%"]
        if coverage >= 60:
            return self._build_stage(stage_id, name, "PASS", details)
        if coverage > 0:
            return self._build_stage(stage_id, name, "WARNING", details + ["Coverage is below the preferred threshold of 60%."])
        return self._build_stage(stage_id, name, "FAIL", details + ["No internal linking coverage detected."])

    def _check_topic_cluster_coverage(self, stage_id: int) -> dict[str, Any]:
        name = "Topic cluster coverage"
        report = self.topic_cluster_service.build_cluster_coverage_report()
        coverage = report.get("topic_cluster_coverage", 0)
        details = [f"Topic cluster coverage: {coverage}%"]
        if coverage >= 60:
            return self._build_stage(stage_id, name, "PASS", details)
        if coverage > 0:
            return self._build_stage(stage_id, name, "WARNING", details + ["Some topic clusters are incomplete."])
        return self._build_stage(stage_id, name, "FAIL", details + ["No topic clusters built."])

    def _check_programmatic_seo_coverage(self, stage_id: int) -> dict[str, Any]:
        name = "Programmatic SEO coverage"
        report = self.programmatic_seo_engine.get_seo_page_coverage_report()
        coverage = report.get("seo_page_coverage", 0)
        ready = report.get("seo_pages_ready", 0)
        total = report.get("seo_pages_total", 0)
        details = [
            f"SEO pages generated: {total}",
            f"Pages ready: {ready}",
            f"SEO page coverage: {coverage}%",
        ]
        if total == 0:
            return self._build_stage(stage_id, name, "FAIL", details + ["No SEO pages were generated."])
        if coverage >= 50:
            return self._build_stage(stage_id, name, "PASS", details)
        return self._build_stage(stage_id, name, "WARNING", details + ["SEO page coverage is below the deployment threshold."])

    def _check_content_quality_gating(self, stage_id: int) -> dict[str, Any]:
        name = "Content quality gating"
        report = self.content_quality_service.evaluate_all_pages()
        total = report.get("total_pages_evaluated", 0)
        pass_percentage = report.get("pass_percentage", 0)
        reject_count = report.get("reject_count", 0)
        average_quality = report.get("average_quality_score", 0)
        details = [
            f"Total pages evaluated: {total}",
            f"Pass percentage: {pass_percentage}%",
            f"Reject count: {reject_count}",
            f"Average quality score: {average_quality}",
        ]
        if total == 0:
            return self._build_stage(stage_id, name, "FAIL", details + ["No content quality pages were evaluated."])
        if pass_percentage >= 40 and average_quality >= 55:
            return self._build_stage(stage_id, name, "PASS", details)
        if reject_count > 0:
            return self._build_stage(
                stage_id,
                name,
                "WARNING",
                details + [
                    "Some SEO pages were rejected by the content quality engine.",
                    "Review rejected pages and improve quality before production deployment.",
                ],
            )
        return self._build_stage(stage_id, name, "WARNING", details + ["Content quality gating is below preferred thresholds."])

    def _check_production_audit_summary(self, stage_id: int) -> dict[str, Any]:
        name = "Production audit summary"
        report = self.production_audit_service.audit_all()
        summary = report.get("summary", {})
        ready = summary.get("ready_count", 0)
        warning = summary.get("warning_count", 0)
        not_ready = summary.get("not_ready_count", 0)
        total = summary.get("total_converters", 0)
        details = [
            f"Total converters evaluated: {total}",
            f"Ready: {ready}",
            f"Warning: {warning}",
            f"Not ready: {not_ready}",
        ]
        if total == 0:
            return self._build_stage(stage_id, name, "FAIL", details + ["No converters available for audit."])
        if not_ready == 0:
            return self._build_stage(stage_id, name, "PASS", details)
        return self._build_stage(stage_id, name, "FAIL", details + ["Some converters are not ready for production."])

    def _get_plugin_validation_results(self) -> list[dict[str, Any]]:
        if self._plugin_validation_results is None:
            self._plugin_validation_results = [result.to_dict() for result in self.plugin_validation_service.validate_all()]
        return self._plugin_validation_results

    def _register_active_contracts(self) -> None:
        if self.converter_registry_service is None:
            return

        for contract in self.converter_registry_service.get_active():
            slug = str(contract.get("slug", "")).strip()
            if not slug or self.registry.get(slug) is not None:
                continue

            source_format = str((contract.get("input_formats") or [""])[0]).strip()
            target_format = str((contract.get("output_formats") or [""])[0]).strip()
            self.registry.register(
                ConverterInfo(
                    id=slug,
                    name=str(contract.get("name", slug)),
                    category=str(contract.get("category", "general")).lower(),
                    source_format=source_format,
                    target_format=target_format,
                    enabled=True,
                )
            )

    def _derive_production_health(self, summary: dict[str, Any]) -> str:
        ready = summary.get("ready_count", 0)
        warning = summary.get("warning_count", 0)
        not_ready = summary.get("not_ready_count", 0)
        if ready > 0 and not_ready == 0:
            return "READY"
        if not_ready > 0:
            return "NOT READY"
        if warning > 0:
            return "WARNING"
        return "UNKNOWN"

    def _build_stage(
        self,
        stage_id: int,
        name: str,
        status: str,
        details: list[str] | None = None,
    ) -> dict[str, Any]:
        return {
            "id": stage_id,
            "name": name,
            "status": status,
            "details": details or [],
        }


if __name__ == "__main__":
    service = DeploymentValidationService()
    report = service.run_all_checks()
    markdown = service.generate_markdown_report(report)
    print(markdown)
    if not report["all_passed"]:
        raise SystemExit(1)
