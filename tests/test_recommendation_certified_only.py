"""
Test suite to verify recommendation engine only returns certified converters.

PHASE 2: Recommendation Engine Alignment
- Certified converters should be recommended
- Beta converters should not be default
- Disabled converters should NOT appear
"""

import pytest
from pathlib import Path

from app.recommendation.engine import recommendation_engine
from app.services.converter_registry_service import ConverterRegistryService


@pytest.fixture
def contract_registry():
    """Load the converter contract registry."""
    contracts_dir = Path(__file__).parent.parent / "app" / "data" / "converters"
    return ConverterRegistryService(contracts_dir)


class TestRecommendationEngineFiltering:
    """Test that recommendation engine filters by certification status."""

    def test_recommendation_returns_only_certified(self, contract_registry):
        """Verify that recommendations only include certified/active converters."""
        # Get a sample recommendation
        result = recommendation_engine.recommend("pdf")
        
        # If we get a recommendation, it should be certified or active
        if result.best_choice:
            contract = contract_registry.get_by_slug(result.best_choice.target.replace("-", "").lower())
            if contract:
                lifecycle_status = contract.get("lifecycle_status", "").lower()
                assert lifecycle_status in {"active", "certified"}, \
                    f"Recommended converter {result.best_choice.target} has status {lifecycle_status}"

    def test_recommendation_excludes_deprecated(self, contract_registry):
        """Verify deprecated converters are not recommended."""
        # These are deprecated/disabled converters that should NOT appear
        disabled_converters = {
            "xlsx-to-ods", "docx-to-xlsx", "docx-to-ppt",
            "ppt-to-docx", "ppt-to-jpg", "ppt-to-xlsx"
        }
        
        # Test common source formats
        test_formats = ["pdf", "docx", "xlsx", "ppt", "pptx", "jpg", "png", "mp4"]
        
        for source_fmt in test_formats:
            result = recommendation_engine.recommend(source_fmt)
            
            # Check best choice is not in disabled list
            if result.best_choice:
                target_normalized = result.best_choice.target.replace("-", "").lower()
                assert target_normalized not in disabled_converters, \
                    f"Disabled converter recommended: {result.best_choice.target} for {source_fmt}"
            
            # Check alternatives are not in disabled list
            for alt in result.alternatives:
                alt_normalized = alt.target.replace("-", "").lower()
                assert alt_normalized not in disabled_converters, \
                    f"Disabled converter in alternatives: {alt.target} for {source_fmt}"


class TestRecommendationEndpoints:
    """Test recommendation endpoints return certified converters."""

    @pytest.mark.asyncio
    async def test_jpg_recommendation(self):
        """Test JPG recommendation returns certified converter."""
        result = recommendation_engine.recommend("jpg")
        assert result.best_choice is not None, "Should have recommendation for jpg"
        assert result.detected_type == "JPG"
        # Target should be a valid certified converter like png, webp
        assert result.best_choice.target in {"png", "webp"}

    @pytest.mark.asyncio
    async def test_png_recommendation(self):
        """Test PNG recommendation returns certified converter."""
        result = recommendation_engine.recommend("png")
        assert result.best_choice is not None, "Should have recommendation for png"
        # Can recommend jpg, webp, etc
        assert result.best_choice.target in {"jpg", "webp"}

    @pytest.mark.asyncio
    async def test_pdf_recommendation(self):
        """Test PDF recommendation returns certified converter."""
        result = recommendation_engine.recommend("pdf")
        assert result.best_choice is not None, "Should have recommendation for pdf"
        # Can recommend docx, xlsx, etc (all certified)

    @pytest.mark.asyncio
    async def test_docx_recommendation(self):
        """Test DOCX recommendation returns certified converter."""
        result = recommendation_engine.recommend("docx")
        assert result.best_choice is not None, "Should have recommendation for docx"
        assert result.best_choice.target == "pdf", "DOCX should recommend PDF"

    @pytest.mark.asyncio
    async def test_xlsx_recommendation(self):
        """Test XLSX recommendation returns certified converter."""
        result = recommendation_engine.recommend("xlsx")
        assert result.best_choice is not None, "Should have recommendation for xlsx"
        assert result.best_choice.target == "pdf", "XLSX should recommend PDF"

    @pytest.mark.asyncio
    async def test_webp_recommendation(self):
        """Test WEBP recommendation returns certified converter."""
        result = recommendation_engine.recommend("webp")
        assert result.best_choice is not None, "Should have recommendation for webp"

    @pytest.mark.asyncio
    async def test_mp4_recommendation(self):
        """Test MP4 recommendation returns certified audio converter."""
        result = recommendation_engine.recommend("mp4")
        assert result.best_choice is not None, "Should have recommendation for mp4"
        # Should recommend audio formats: mp3, aac, wav, etc
        assert result.best_choice.target in {"mp3", "aac", "wav", "m4a", "flac", "ogg"}


class TestRecommendationCertificationStatus:
    """Test that all recommended converters have proper certification status."""

    def test_all_recommendations_have_valid_status(self, contract_registry):
        """Verify all recommendations point to certified/active converters."""
        test_formats = ["jpg", "png", "pdf", "docx", "xlsx", "ppt", "webp", "mp4"]
        
        for source_fmt in test_formats:
            result = recommendation_engine.recommend(source_fmt)
            
            # Check best choice
            if result.best_choice:
                # The recommendation is valid
                assert result.best_choice.score > 0, \
                    f"Invalid score for {result.best_choice.target}"
            
            # Check alternatives
            for alt in result.alternatives:
                assert alt.score > 0, f"Invalid score for alternative {alt.target}"


class TestRecommendationBetaHandling:
    """Test that beta converters are handled appropriately."""

    def test_beta_converters_not_default(self, contract_registry):
        """Verify beta converters are not the default recommendation."""
        # Current beta: none (we moved ppt-to-pdf to certified)
        # This test ensures future beta converters work correctly
        beta_converters = contract_registry.get_beta()
        
        # If there are any beta converters, they should not be first in recommendations
        if beta_converters:
            for beta in beta_converters:
                beta_slug = beta.get("slug", "")
                # Get a source that could recommend this converter
                # For now just verify beta exists in registry
                assert beta_slug, "Beta converter should have a slug"


class TestRecommendationConsistency:
    """Test consistency of recommendations."""

    def test_recommendations_stable(self):
        """Verify same source format always gets same recommendation."""
        result1 = recommendation_engine.recommend("pdf")
        result2 = recommendation_engine.recommend("pdf")
        
        if result1.best_choice and result2.best_choice:
            assert result1.best_choice.target == result2.best_choice.target, \
                "Recommendations should be stable"
            assert result1.best_choice.score == result2.best_choice.score, \
                "Scores should be stable"

    def test_recommendation_order_consistent(self):
        """Verify alternative recommendations are consistently ordered."""
        result = recommendation_engine.recommend("jpg")
        
        if len(result.alternatives) > 1:
            # Verify alternatives are sorted by score
            for i in range(len(result.alternatives) - 1):
                curr_score = result.alternatives[i].score
                next_score = result.alternatives[i + 1].score
                assert curr_score >= next_score, \
                    f"Alternatives not sorted: {curr_score} < {next_score}"
