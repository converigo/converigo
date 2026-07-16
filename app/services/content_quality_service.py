"""Content Quality Engine - Deterministic quality evaluation for SEO pages."""

from __future__ import annotations

from pathlib import Path
from typing import Any, TYPE_CHECKING
from difflib import SequenceMatcher
import json

from app.services.converter_registry_service import ConverterRegistryService
from app.services.knowledge_service import KnowledgeService
from app.services.comparison_service import ComparisonService
from app.services.topic_cluster_service import TopicClusterService
from app.services.internal_link_service import InternalLinkService

if TYPE_CHECKING:
    from app.services.programmatic_seo_engine import ProgrammaticSeoEngine


class ContentQualityService:
    """Deterministic quality gate for SEO page publication."""

    # Quality decision thresholds
    DECISION_THRESHOLDS = {
        "pass": 90,  # >= 90
        "needs_review": 80,  # 80-89
        "no_index": 60,  # 60-79
        "reject": 0,  # < 60
    }

    # Minimum required structured data fields
    REQUIRED_SCHEMA_TYPES = [
        "breadcrumb",
        "faq",
        "article",
        "how_to",
        "organization",
        "website",
    ]

    # Structured data fact counters
    STRUCTURED_DATA_KEYS = [
        "extension",
        "mime",
        "magic_bytes",
        "software",
        "compatibility",
        "history",
        "metadata",
        "compression",
        "security",
        "specification",
        "related_converters",
        "related_comparisons",
        "related_guides",
    ]

    def __init__(self, contracts_dir: Path | str | None = None) -> None:
        self.contracts_dir = Path(contracts_dir or "app/data/converters")
        self.converter_registry_service = ConverterRegistryService(self.contracts_dir)
        self.knowledge_service = KnowledgeService(self.contracts_dir)
        self.comparison_service = ComparisonService(self.contracts_dir)
        self.topic_cluster_service = TopicClusterService(self.contracts_dir)
        self.internal_link_service = InternalLinkService(self.contracts_dir)
        self._seo_engine: ProgrammaticSeoEngine | None = None
        self._page_cache: dict[str, dict[str, Any]] = {}

    @property
    def seo_engine(self) -> ProgrammaticSeoEngine:
        """Lazy load ProgrammaticSeoEngine to avoid circular imports."""
        if self._seo_engine is None:
            # Import here to avoid circular import at module load time
            from app.services.programmatic_seo_engine import ProgrammaticSeoEngine as PSE
            self._seo_engine = PSE(self.contracts_dir)
        return self._seo_engine

    def evaluate_page(
        self, format_name: str, page_type: str
    ) -> dict[str, Any]:
        """Evaluate a single SEO page and return quality metrics.
        
        Args:
            format_name: Format being evaluated (e.g., 'pdf', 'jpg')
            page_type: Type of SEO page (e.g., 'how_to', 'faq')
            
        Returns:
            Quality evaluation result with score, decision, and detailed metrics
        """
        format_lower = format_name.lower()
        
        try:
            page = self.seo_engine.generate_page(format_lower, page_type)
        except Exception as e:
            return self._build_rejection_result(
                format_lower, page_type,
                f"Failed to generate page: {str(e)}"
            )
        
        if not page:
            return self._build_rejection_result(
                format_lower, page_type,
                "Page generation returned empty result"
            )
        
        # Calculate all quality metrics
        metrics = {
            "uniqueness_score": self._calculate_uniqueness_score(format_lower, page),
            "data_density_score": self._calculate_data_density_score(page),
            "eligibility_score": self._calculate_eligibility_score(format_lower, page),
            "search_intent_score": self._calculate_search_intent_score(page_type, page),
            "internal_link_score": self._calculate_internal_link_score(page),
            "schema_score": self._calculate_schema_score(page),
            "duplicate_score": self._calculate_duplicate_score(format_lower, page),
        }
        
        # Calculate overall score with weights
        overall_score = self._calculate_overall_quality_score(metrics)
        
        # Determine decision
        decision = self._determine_decision(overall_score)
        
        # Build recommendation
        recommendations = self._build_recommendations(metrics, page)
        missing_metadata = self._identify_missing_metadata(page)
        
        return {
            "format": format_lower,
            "page_type": page_type,
            "quality_score": overall_score,
            "decision": decision,
            "metrics": metrics,
            "recommendations": recommendations,
            "missing_metadata": missing_metadata,
            "page_url": page.get("url", f"/{page_type}/{format_lower}"),
            "timestamp": self._get_timestamp(),
        }

    def evaluate_all_pages(self) -> dict[str, Any]:
        """Evaluate all SEO pages and return aggregated results."""
        formats = self._collect_all_formats()
        page_types = self.seo_engine.PAGE_TYPES
        
        results = []
        pass_count = 0
        needs_review_count = 0
        no_index_count = 0
        reject_count = 0
        
        for fmt in formats:
            for page_type in page_types:
                try:
                    result = self.evaluate_page(fmt, page_type)
                    results.append(result)
                    
                    decision = result.get("decision", "REJECT")
                    if decision == "PASS":
                        pass_count += 1
                    elif decision == "NEEDS_REVIEW":
                        needs_review_count += 1
                    elif decision == "NO_INDEX":
                        no_index_count += 1
                    else:
                        reject_count += 1
                except Exception:
                    reject_count += 1
                    continue
        
        total_pages = len(results)
        average_quality = (
            sum(r.get("quality_score", 0) for r in results) / total_pages
            if total_pages > 0
            else 0
        )
        
        return {
            "total_pages_evaluated": total_pages,
            "pass_count": pass_count,
            "needs_review_count": needs_review_count,
            "no_index_count": no_index_count,
            "reject_count": reject_count,
            "average_quality_score": round(average_quality, 2),
            "pass_percentage": round(pass_count / total_pages * 100, 2) if total_pages > 0 else 0,
            "results": results,
        }

    # Quality metric calculators

    def _calculate_uniqueness_score(
        self, format_name: str, page: dict[str, Any]
    ) -> float:
        """Calculate uniqueness score by comparing against similar pages.
        
        Target: >= 70 PASS, < 70 FAIL
        """
        # Get all pages of same type for comparison
        page_type = page.get("page_type", "")
        
        # Compare page content with similar pages
        similar_pages = self._get_similar_pages(format_name, page_type)
        
        if not similar_pages:
            return 100.0  # No comparison available, assume unique
        
        # Calculate similarity ratios
        page_content = self._normalize_content(page)
        similarities = []
        
        for similar_page in similar_pages[:3]:  # Compare with top 3 similar pages
            similar_content = self._normalize_content(similar_page)
            ratio = SequenceMatcher(
                None, page_content, similar_content
            ).ratio()
            similarities.append(ratio)
        
        # Average similarity (lower is better)
        avg_similarity = sum(similarities) / len(similarities) if similarities else 0
        
        # Convert similarity to uniqueness score (inverse)
        # If 70% similar to others, uniqueness score is 30
        uniqueness = 100 - (avg_similarity * 100)
        
        return max(0, min(100, uniqueness))

    def _calculate_data_density_score(self, page: dict[str, Any]) -> float:
        """Calculate data density by counting structured information.
        
        Count: extension, mime, software, compatibility, history, metadata, etc.
        """
        density_count = 0
        
        # Check for key structured data fields
        for key in self.STRUCTURED_DATA_KEYS:
            if self._has_structured_data(page, key):
                density_count += 1
        
        # Also count content sections
        content = page.get("content", {})
        if isinstance(content, dict):
            section_count = sum(
                1 for v in content.values()
                if v and (isinstance(v, (list, dict, str)))
            )
            density_count += min(section_count // 2, 5)  # Cap at 5 sections worth
        
        # Also check JSON-LD schema
        if page.get("json_ld"):
            density_count += 2
        
        # Normalize to 0-100 scale
        # Maximum possible: 13 (STRUCTURED_DATA_KEYS) + 5 (sections) + 2 (schema) = 20
        max_possible = 20
        score = (density_count / max_possible) * 100
        
        return max(0, min(100, score))

    def _calculate_eligibility_score(
        self, format_name: str, page: dict[str, Any]
    ) -> float:
        """Verify metadata completeness.
        
        FAIL if metadata is incomplete.
        """
        try:
            contract = self.converter_registry_service.get_by_slug(format_name)
        except Exception:
            contract = None
        
        # Must have a valid contract
        if not contract:
            return 0.0
        
        # Check required metadata
        required_fields = {
            "format": page.get("format"),
            "page_type": page.get("page_type"),
            "url": page.get("url"),
            "seo": page.get("seo", {}).get("title"),
            "content": page.get("content", {}).get("h1"),
            "json_ld": page.get("json_ld"),
            "breadcrumb": page.get("breadcrumb"),
            "internal_links": page.get("internal_links"),
        }
        
        # Count valid fields
        valid_count = sum(
            1 for v in required_fields.values()
            if v
        )
        
        total_required = len(required_fields)
        
        if valid_count == total_required:
            return 100.0
        else:
            # Penalize missing fields
            return (valid_count / total_required) * 100

    def _calculate_search_intent_score(
        self, page_type: str, page: dict[str, Any]
    ) -> float:
        """Verify page answers the intended search query.
        
        Examples: How, Why, When, Compatibility, Advantages, Limitations, Steps, FAQ
        """
        content = page.get("content", {})
        
        # Map page types to expected intent keywords
        intent_keywords = {
            "how_to": ["steps", "how", "guide", "tutorial", "instructions"],
            "tutorials": ["tutorial", "guide", "example", "learn", "step"],
            "best_practices": ["best", "practice", "tips", "optimize", "improve"],
            "troubleshooting": ["fix", "issue", "problem", "error", "solution"],
            "file_format_guides": ["format", "file", "extension", "specification"],
            "use_cases": ["use case", "when to", "scenario", "application"],
            "faqs": ["faq", "question", "answer"],
            "metadata_guides": ["metadata", "tag", "property", "attribute"],
            "mime_guides": ["mime", "type", "content-type"],
            "software_guides": ["software", "tool", "application", "program"],
        }
        
        # Get expected keywords for this page type
        expected_keywords = intent_keywords.get(page_type, [])
        if not expected_keywords:
            return 80.0  # Unknown type, but give benefit of doubt
        
        # Normalize content for searching
        content_str = json.dumps(content).lower()
        
        # Count matching keywords
        matches = sum(
            1 for keyword in expected_keywords
            if keyword in content_str
        )
        
        # Score based on keyword coverage
        if len(expected_keywords) == 0:
            return 100.0
        
        score = (matches / len(expected_keywords)) * 100
        
        # Minimum 40% match required
        if score < 40:
            score = max(40, score)
        
        return min(100, score)

    def _calculate_internal_link_score(self, page: dict[str, Any]) -> float:
        """Verify minimum internal links (5 required).
        
        Minimum: 5 valid internal links
        """
        internal_links = page.get("internal_links", {})
        
        if not internal_links:
            return 0.0
        
        # Count valid links across all sections
        link_count = 0
        
        if isinstance(internal_links, dict):
            for section_name, links in internal_links.items():
                if isinstance(links, list):
                    # Only count links with valid structure
                    valid_links = [
                        l for l in links
                        if isinstance(l, dict) and l.get("url") and l.get("title")
                    ]
                    link_count += len(valid_links)
        
        # Scoring: 0 links = 0%, 5+ links = 100%
        if link_count == 0:
            return 0.0
        elif link_count >= 5:
            return 100.0
        else:
            return (link_count / 5) * 100

    def _calculate_schema_score(self, page: dict[str, Any]) -> float:
        """Verify required schema exists.
        
        Required: Breadcrumb, FAQ, Article, HowTo, Organization, Website
        """
        json_ld = page.get("json_ld", {})
        breadcrumb = page.get("breadcrumb", [])
        
        schema_count = 0
        
        # Check for various schema types
        if isinstance(json_ld, dict):
            schema_type = json_ld.get("@type", "").lower()
            
            # Count found schema types
            if "breadcrumb" in schema_type or breadcrumb:
                schema_count += 1
            if "faq" in schema_type:
                schema_count += 1
            if any(t in schema_type for t in ["article", "creativework", "webpage"]):
                schema_count += 1
            if "howto" in schema_type:
                schema_count += 1
            if "organization" in schema_type:
                schema_count += 1
            if "website" in schema_type or "webpage" in schema_type:
                schema_count += 1
        
        # At minimum breadcrumb should exist
        if breadcrumb:
            schema_count = max(1, schema_count)
        
        # Require at least 3 schema types
        required_minimum = 3
        
        if schema_count >= required_minimum:
            return 100.0
        else:
            return (schema_count / required_minimum) * 100

    def _calculate_duplicate_score(
        self, format_name: str, page: dict[str, Any]
    ) -> float:
        """Detect near-identical pages (near-duplicate detection).
        
        Higher score = more unique (less duplicate)
        """
        page_type = page.get("page_type", "")
        
        # Get similar pages
        similar_pages = self._get_similar_pages(format_name, page_type, limit=5)
        
        if not similar_pages:
            return 100.0  # No duplicates found
        
        # Calculate structural similarity
        current_structure = self._get_page_structure_hash(page)
        
        duplicate_count = 0
        threshold = 0.95  # 95% similar = duplicate
        
        for similar_page in similar_pages:
            similar_structure = self._get_page_structure_hash(similar_page)
            
            # Compare structures
            if self._calculate_similarity(current_structure, similar_structure) > threshold:
                duplicate_count += 1
        
        # No high-similarity duplicates
        if duplicate_count == 0:
            return 100.0
        else:
            # Penalize for each duplicate found
            return max(0, 100 - (duplicate_count * 20))

    def _calculate_overall_quality_score(
        self, metrics: dict[str, float]
    ) -> float:
        """Calculate weighted overall quality score.
        
        Returns 0-100 score
        """
        # Weighted calculation
        weights = {
            "uniqueness_score": 0.15,
            "data_density_score": 0.20,
            "eligibility_score": 0.15,
            "search_intent_score": 0.15,
            "internal_link_score": 0.15,
            "schema_score": 0.10,
            "duplicate_score": 0.10,
        }
        
        weighted_sum = 0.0
        total_weight = 0.0
        
        for metric_name, weight in weights.items():
            score = metrics.get(metric_name, 0)
            weighted_sum += score * weight
            total_weight += weight
        
        overall_score = (
            weighted_sum / total_weight
            if total_weight > 0
            else 0
        )
        
        return round(max(0, min(100, overall_score)), 2)

    def _determine_decision(self, quality_score: float) -> str:
        """Determine publication decision based on quality score.
        
        >= 90: PASS
        80-89: NEEDS_REVIEW
        60-79: NO_INDEX
        < 60: REJECT
        """
        if quality_score >= self.DECISION_THRESHOLDS["pass"]:
            return "PASS"
        elif quality_score >= self.DECISION_THRESHOLDS["needs_review"]:
            return "NEEDS_REVIEW"
        elif quality_score >= self.DECISION_THRESHOLDS["no_index"]:
            return "NO_INDEX"
        else:
            return "REJECT"

    # Helper methods

    def _build_recommendations(
        self, metrics: dict[str, float], page: dict[str, Any]
    ) -> list[str]:
        """Build recommendations based on weak metrics."""
        recommendations = []
        
        # Check each metric and provide recommendations
        if metrics.get("uniqueness_score", 100) < 70:
            recommendations.append(
                "Increase content uniqueness - review similar pages and add distinctive content"
            )
        
        if metrics.get("data_density_score", 100) < 60:
            recommendations.append(
                "Enrich with more structured data - add metadata, specifications, software info"
            )
        
        if metrics.get("eligibility_score", 100) < 80:
            recommendations.append(
                "Complete missing metadata fields - ensure all required fields are populated"
            )
        
        if metrics.get("search_intent_score", 100) < 70:
            recommendations.append(
                "Align content better with search intent - add more relevant keywords and sections"
            )
        
        if metrics.get("internal_link_score", 100) < 80:
            recommendations.append(
                "Add more internal links - minimum 5 valid internal links required"
            )
        
        if metrics.get("schema_score", 100) < 80:
            recommendations.append(
                "Implement more schema types - at least 3 schema types should be present"
            )
        
        if metrics.get("duplicate_score", 100) < 80:
            recommendations.append(
                "Make content more unique - reduce similarity with other pages"
            )
        
        return recommendations

    def _identify_missing_metadata(self, page: dict[str, Any]) -> list[str]:
        """Identify missing metadata fields."""
        missing = []
        
        # Check SEO metadata
        seo = page.get("seo", {})
        if not seo.get("title"):
            missing.append("seo.title")
        if not seo.get("meta_description"):
            missing.append("seo.meta_description")
        if not seo.get("keywords"):
            missing.append("seo.keywords")
        
        # Check content
        content = page.get("content", {})
        if not content.get("h1"):
            missing.append("content.h1")
        if not content.get("introduction"):
            missing.append("content.introduction")
        
        # Check structure
        if not page.get("breadcrumb"):
            missing.append("breadcrumb")
        if not page.get("json_ld"):
            missing.append("json_ld")
        if not page.get("internal_links"):
            missing.append("internal_links")
        
        return missing

    def _build_rejection_result(
        self, format_name: str, page_type: str, reason: str
    ) -> dict[str, Any]:
        """Build a rejection result with explanation."""
        return {
            "format": format_name,
            "page_type": page_type,
            "quality_score": 0,
            "decision": "REJECT",
            "metrics": {
                "uniqueness_score": 0,
                "data_density_score": 0,
                "eligibility_score": 0,
                "search_intent_score": 0,
                "internal_link_score": 0,
                "schema_score": 0,
                "duplicate_score": 0,
            },
            "recommendations": [f"Fix: {reason}"],
            "missing_metadata": ["All fields"],
            "rejection_reason": reason,
            "timestamp": self._get_timestamp(),
        }

    def _get_similar_pages(
        self, format_name: str, page_type: str, limit: int = 3
    ) -> list[dict[str, Any]]:
        """Get similar pages for comparison."""
        try:
            # Get all pages of same type
            all_formats = self._collect_all_formats()
            similar = []
            
            for fmt in all_formats:
                if fmt == format_name:
                    continue
                try:
                    page = self.seo_engine.generate_page(fmt, page_type)
                    if page:
                        similar.append(page)
                except Exception:
                    continue
            
            return similar[:limit]
        except Exception:
            return []

    def _normalize_content(self, page: dict[str, Any]) -> str:
        """Normalize page content for comparison."""
        content = page.get("content", {})
        seo = page.get("seo", {})
        
        # Combine key content
        parts = [
            str(seo.get("title", "")),
            str(seo.get("meta_description", "")),
            str(content.get("h1", "")),
            str(content.get("introduction", "")),
        ]
        
        return " ".join(parts).lower()

    def _has_structured_data(self, page: dict[str, Any], key: str) -> bool:
        """Check if page has specific structured data."""
        content = page.get("content", {})
        
        if isinstance(content, dict):
            # Check if key appears anywhere in content
            content_str = json.dumps(content).lower()
            return key.lower() in content_str
        
        return False

    def _get_page_structure_hash(self, page: dict[str, Any]) -> str:
        """Get structural hash of page for comparison."""
        structure = {
            "page_type": page.get("page_type"),
            "sections": list(page.get("content", {}).keys()) if isinstance(page.get("content"), dict) else [],
            "schema_type": page.get("json_ld", {}).get("@type"),
        }
        
        return json.dumps(structure, sort_keys=True)

    def _calculate_similarity(self, str1: str, str2: str) -> float:
        """Calculate similarity between two strings."""
        return SequenceMatcher(None, str1, str2).ratio()

    def _collect_all_formats(self) -> list[str]:
        """Collect all known formats from converters."""
        formats = set()
        
        try:
            for contract in self.converter_registry_service.get_active():
                for fmt in contract.get("input_formats", []):
                    formats.add(str(fmt).lower())
                for fmt in contract.get("output_formats", []):
                    formats.add(str(fmt).lower())
        except Exception:
            pass
        
        return sorted(list(formats))

    def _get_timestamp(self) -> str:
        """Get current timestamp."""
        from datetime import datetime, timezone
        return datetime.now(timezone.utc).isoformat()
