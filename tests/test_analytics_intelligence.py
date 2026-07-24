"""Tests for Analytics Intelligence Service — Sprint 02.

Covers:
- Funnel calculation (TASK 1)
- Top converter ranking (TASK 2)
- Error aggregation (TASK 3)
- Device analytics (TASK 4)
- Geographic analytics (TASK 5)
- Performance metrics with threshold warnings (TASK 6)
- Growth metrics (TASK 7)
- SEO insights (TASK 8)
"""

from pathlib import Path

from app.services.analytics_intelligence_service import AnalyticsIntelligenceService
from app.services.analytics_service import AnalyticsService


def _seed_events(service: AnalyticsService) -> None:
    """Seed a rich set of test events covering all dashboards."""
    # ── Visitor 1: organic, full conversion flow ──
    service.track_page_view(page_path="/", visitor_id="v1", entry_type="organic")
    service.track_page_view(page_path="/tools/mp4-to-mp3", visitor_id="v1", entry_type="organic")
    service.track_upload_start(page_path="/convert", visitor_id="v1", converter_name="mp4-to-mp3", category="audio", input_format="mp4")
    service.track_upload_success(page_path="/convert", visitor_id="v1", converter_name="mp4-to-mp3", category="audio", input_format="mp4", processing_ms=150)
    service.track_conversion_start(page_path="/convert", visitor_id="v1", converter_name="mp4-to-mp3", category="audio", output_format="mp3")
    service.track_conversion_success(page_path="/convert", visitor_id="v1", converter_name="mp4-to-mp3", category="audio", output_format="mp3", processing_ms=2200)
    service.track_download(page_path="/download/mp4-to-mp3.mp3", visitor_id="v1", converter_name="mp4-to-mp3")
    service.track_page_view(page_path="/tools/jpg-to-pdf", visitor_id="v1", entry_type="organic")

    # ── Visitor 2: direct, partial flow (upload but no conversion) ──
    service.track_page_view(page_path="/", visitor_id="v2", entry_type="direct")
    service.track_upload_start(page_path="/convert", visitor_id="v2", converter_name="jpg-to-pdf", category="image", input_format="jpg")
    service.track_upload_success(page_path="/convert", visitor_id="v2", converter_name="jpg-to-pdf", category="image", input_format="jpg", processing_ms=200)
    service.track_error(page_path="/convert", visitor_id="v2", error_type="CONVERSION_ERROR", converter_name="jpg-to-pdf")

    # ── Visitor 3: direct, conversion failure ──
    service.track_page_view(page_path="/", visitor_id="v3", entry_type="direct")
    service.track_upload_start(page_path="/convert", visitor_id="v3", converter_name="png-to-jpg", category="image", input_format="png")
    service.track_conversion_start(page_path="/convert", visitor_id="v3", converter_name="png-to-jpg", category="image", output_format="jpg")
    service.track_conversion_failed(page_path="/convert", visitor_id="v3", converter_name="png-to-jpg", error_type="PROCESSING_ERROR")

    # ── Visitor 4: referral, full flow ──
    service.track_page_view(page_path="/", visitor_id="v4", entry_type="referral")
    service.track_page_view(page_path="/tools/pdf-to-word", visitor_id="v4", entry_type="referral")
    service.track_upload_start(page_path="/convert", visitor_id="v4", converter_name="pdf-to-word", category="document", input_format="pdf")
    service.track_conversion_start(page_path="/convert", visitor_id="v4", converter_name="pdf-to-word", category="document", output_format="word")
    service.track_conversion_success(page_path="/convert", visitor_id="v4", converter_name="pdf-to-word", category="document", output_format="word", processing_ms=3200)
    service.track_download(page_path="/download/pdf-to-word.docx", visitor_id="v4", converter_name="pdf-to-word")

    # ── Visitor 5: organic, browse only ──
    service.track_page_view(page_path="/", visitor_id="v5", entry_type="organic")

    # ── Performance metrics ──
    service.track_event("performance_metric", page_path="/", visitor_id="v1", metric_name="lcp", metric_value=1.23)
    service.track_event("performance_metric", page_path="/", visitor_id="v1", metric_name="cls", metric_value=0.02)
    service.track_event("performance_metric", page_path="/", visitor_id="v1", metric_name="inp", metric_value=45)
    service.track_event("performance_metric", page_path="/", visitor_id="v1", metric_name="ttfb", metric_value=320)
    service.track_event("performance_metric", page_path="/", visitor_id="v1", metric_name="fcp", metric_value=1100)
    service.track_event("performance_metric", page_path="/", visitor_id="v1", metric_name="lcp", metric_value=2.89)
    service.track_event("performance_metric", page_path="/", visitor_id="v2", metric_name="cls", metric_value=0.15)
    service.track_event("performance_metric", page_path="/", visitor_id="v2", metric_name="inp", metric_value=280)

    # ── SEO events ──
    service.track_event("landing_page_view", page_path="/", visitor_id="v1")
    service.track_event("organic_entry", page_path="/", visitor_id="v1")
    service.track_event("search_query", page_path="/", visitor_id="v1", search_query="mp4 to mp3")
    service.track_event("internal_link_click", page_path="/", visitor_id="v1", link_href="/tools/mp4-to-mp3")
    service.track_event("internal_link_click", page_path="/", visitor_id="v2", link_href="/tools/pdf-to-word")
    service.track_event("faq_expand", page_path="/tools/mp4-to-mp3", visitor_id="v1", faq_id="faq-1")
    service.track_event("faq_expand", page_path="/tools/mp4-to-mp3", visitor_id="v2", faq_id="faq-2")
    service.track_event("faq_expand", page_path="/tools/mp4-to-mp3", visitor_id="v3", faq_id="faq-3")


# ═══════════════════════════════════════════════════════════════════
# TASK 1 — Conversion Funnel
# ═══════════════════════════════════════════════════════════════════

def test_funnel_metrics(tmp_path: Path) -> None:
    service = AnalyticsService(storage_path=tmp_path / "analytics.jsonl")
    _seed_events(service)
    events = service._load_events()
    intelligence = AnalyticsIntelligenceService(service)

    funnel = intelligence.build_funnel(events)

    assert funnel["total_visitors"] == 5
    assert funnel["upload_rate"] > 0
    assert funnel["conversion_rate"] > 0
    assert funnel["download_rate"] > 0
    assert funnel["overall_funnel_percentage"] > 0

    # Verify step ordering
    steps = funnel["steps"]
    assert steps[0]["label"] == "Visitor"
    assert steps[1]["label"] == "Upload"
    assert steps[2]["label"] == "Conversion Started"
    assert steps[3]["label"] == "Conversion Success"
    assert steps[4]["label"] == "Download"

    # Each subsequent step should have <= count of previous
    for i in range(len(steps) - 1):
        assert steps[i + 1]["count"] <= steps[i]["count"], f"{steps[i+1]['label']} > {steps[i]['label']}"


# ═══════════════════════════════════════════════════════════════════
# TASK 2 — Top Converter Analytics
# ═══════════════════════════════════════════════════════════════════

def test_top_converters_ranking(tmp_path: Path) -> None:
    service = AnalyticsService(storage_path=tmp_path / "analytics.jsonl")
    _seed_events(service)
    events = service._load_events()
    intelligence = AnalyticsIntelligenceService(service)

    top_converters = intelligence.build_top_converters(events)

    assert len(top_converters) > 0
    assert len(top_converters) <= 10

    # Verify structure of each converter entry
    for converter in top_converters:
        assert "converter_name" in converter
        assert "upload_count" in converter
        assert "conversion_count" in converter
        assert "download_count" in converter
        assert "success_rate" in converter
        assert "error_rate" in converter
        assert "average_processing_time" in converter

    # mp4-to-mp3 should be top (most conversions)
    assert top_converters[0]["converter_name"] == "mp4-to-mp3"
    assert top_converters[0]["conversion_count"] == 1
    assert top_converters[0]["success_rate"] == 100.0

    # png-to-jpg should have 100% error rate
    png_converter = next(c for c in top_converters if c["converter_name"] == "png-to-jpg")
    assert png_converter["error_rate"] == 100.0


# ═══════════════════════════════════════════════════════════════════
# TASK 3 — Error Analytics
# ═══════════════════════════════════════════════════════════════════

def test_error_analytics(tmp_path: Path) -> None:
    service = AnalyticsService(storage_path=tmp_path / "analytics.jsonl")
    _seed_events(service)
    events = service._load_events()
    intelligence = AnalyticsIntelligenceService(service)

    error_analytics = intelligence.build_error_analytics(events)

    assert error_analytics["total_errors"] > 0
    assert "by_converter" in error_analytics
    assert "by_category" in error_analytics
    assert "by_error_type" in error_analytics
    assert "trend" in error_analytics

    # At least 2 error types present
    assert len(error_analytics["by_error_type"]) >= 2

    # jpg-to-pdf and png-to-jpg should have errors
    assert error_analytics["by_converter"].get("jpg-to-pdf", 0) >= 1
    assert error_analytics["by_converter"].get("png-to-jpg", 0) >= 1


# ═══════════════════════════════════════════════════════════════════
# TASK 4 — Device Analytics
# ═══════════════════════════════════════════════════════════════════

def test_device_analytics(tmp_path: Path) -> None:
    service = AnalyticsService(storage_path=tmp_path / "analytics.jsonl")
    events = service._load_events()
    intelligence = AnalyticsIntelligenceService(service)

    # Test device classification helpers
    assert intelligence._classify_device("Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120") == "Desktop"
    assert intelligence._classify_device("Mozilla/5.0 (iPhone; CPU iPhone OS 17_0) Mobile") == "Mobile"
    assert intelligence._classify_device("Mozilla/5.0 (iPad; CPU OS 17_0)") == "Tablet"

    # Test browser classification
    assert intelligence._classify_browser("Chrome/120.0.0.0") == "Chrome"
    assert intelligence._classify_browser("Firefox/121.0") == "Firefox"
    assert intelligence._classify_browser("Safari/605.1") == "Safari"
    assert intelligence._classify_browser("Edg/120.0") == "Edge"

    # Test OS classification
    assert intelligence._classify_os("Windows NT 10.0") == "Windows"
    assert intelligence._classify_os("Macintosh; Intel Mac OS X 10_15") == "macOS"
    assert intelligence._classify_os("Linux x86_64") == "Linux"
    assert intelligence._classify_os("Android 14") == "Android"
    assert intelligence._classify_os("iPhone; CPU iPhone OS 17_0") == "iOS"

    # Test device analytics with user_agent data in events
    device_analytics = intelligence.build_device_analytics(events)
    assert "device_types" in device_analytics
    assert "browsers" in device_analytics
    assert "operating_systems" in device_analytics
    assert "screen_resolutions" in device_analytics
    assert "unique_visitors_by_device" in device_analytics


# ═══════════════════════════════════════════════════════════════════
# TASK 5 — Geographic Analytics
# ═══════════════════════════════════════════════════════════════════

def test_geographic_analytics(tmp_path: Path) -> None:
    service = AnalyticsService(storage_path=tmp_path / "analytics.jsonl")
    _seed_events(service)
    events = service._load_events()
    intelligence = AnalyticsIntelligenceService(service)

    geo = intelligence.build_geographic_analytics(events)

    assert "unique_ip_hashes" in geo
    assert "languages" in geo
    assert "timezones" in geo
    assert "note" in geo
    assert "anonymized" in geo["note"].lower()
    assert geo["unique_ip_hashes"] >= 0


# ═══════════════════════════════════════════════════════════════════
# TASK 6 — Performance Dashboard
# ═══════════════════════════════════════════════════════════════════

def test_performance_metrics(tmp_path: Path) -> None:
    service = AnalyticsService(storage_path=tmp_path / "analytics.jsonl")
    _seed_events(service)
    events = service._load_events()
    metrics = service.build_dashboard_metrics()
    intelligence = AnalyticsIntelligenceService(service)

    perf = intelligence.build_performance_insights(events, metrics)

    assert "average_lcp" in perf
    assert "average_cls" in perf
    assert "average_inp" in perf
    assert "average_ttfb" in perf
    assert "average_fcp" in perf
    assert "threshold_warnings" in perf
    assert "has_warnings" in perf
    assert "overall_status" in perf

    # Verify threshold structure
    warnings = perf["threshold_warnings"]
    assert len(warnings) == 5  # LCP, CLS, INP, TTFB, FCP

    for w in warnings:
        assert "label" in w
        assert "threshold" in w
        assert "status" in w
        assert "message" in w

    # Some metrics may have warnings depending on seed data
    assert isinstance(perf["has_warnings"], bool)


# ═══════════════════════════════════════════════════════════════════
# TASK 7 — Growth Dashboard
# ═══════════════════════════════════════════════════════════════════

def test_growth_metrics(tmp_path: Path) -> None:
    service = AnalyticsService(storage_path=tmp_path / "analytics.jsonl")
    _seed_events(service)
    events = service._load_events()
    intelligence = AnalyticsIntelligenceService(service)

    growth = intelligence.build_growth(events)

    assert "organic_visitors" in growth
    assert "direct_visitors" in growth
    assert "referral_visitors" in growth
    assert "organic_rate" in growth
    assert "direct_rate" in growth
    assert "referral_rate" in growth
    assert "returning_visitors" in growth
    assert "returning_rate" in growth
    assert "entry_type_distribution" in growth
    assert "top_landing_pages" in growth
    assert "top_exit_pages" in growth

    # Verify organic/direct/referral counts from seed data
    assert growth["organic_visitors"] >= 2  # v1 and v5
    assert growth["direct_visitors"] >= 2   # v2 and v3
    assert growth["referral_visitors"] >= 1  # v4

    # Landing pages should include "/" and "/tools/mp4-to-mp3" etc.
    landing = growth["top_landing_pages"]
    assert "/" in landing

    # Entry type distribution
    dist = growth["entry_type_distribution"]
    assert dist.get("organic", 0) > 0
    assert dist.get("direct", 0) > 0


# ═══════════════════════════════════════════════════════════════════
# TASK 8 — SEO Dashboard
# ═══════════════════════════════════════════════════════════════════

def test_seo_metrics(tmp_path: Path) -> None:
    service = AnalyticsService(storage_path=tmp_path / "analytics.jsonl")
    _seed_events(service)
    events = service._load_events()
    metrics = service.build_dashboard_metrics()
    intelligence = AnalyticsIntelligenceService(service)

    seo = intelligence.build_seo_insights(events, metrics)

    assert "most_visited_seo_pages" in seo
    assert "internal_link_clicks" in seo
    assert "internal_link_click_rate" in seo
    assert "faq_expand_count" in seo
    assert "faq_expand_rate" in seo
    assert "search_entry_count" in seo
    assert "search_entry_rate" in seo
    assert "organic_entry_count" in seo
    assert "landing_page_views" in seo
    assert "landing_page_performance" in seo

    # Verify counts from seed data
    assert seo["internal_link_clicks"] == 2
    assert seo["faq_expand_count"] == 3
    assert seo["search_entry_count"] >= 1

    # Landing page performance should have per-path breakdown
    lpp = seo["landing_page_performance"]
    assert len(lpp) > 0


# ═══════════════════════════════════════════════════════════════════
# INTEGRATION: Full intelligence build
# ═══════════════════════════════════════════════════════════════════

def test_full_intelligence_payload(tmp_path: Path) -> None:
    service = AnalyticsService(storage_path=tmp_path / "analytics.jsonl")
    _seed_events(service)
    intelligence = AnalyticsIntelligenceService(service)

    payload = intelligence.build_intelligence()

    assert "funnel" in payload
    assert "top_converters" in payload
    assert "error_analytics" in payload
    assert "device_analytics" in payload
    assert "geographic_analytics" in payload
    assert "performance" in payload
    assert "growth" in payload
    assert "seo" in payload

    # Verify all 8 dashboards present
    assert len(payload) == 8

    # Funnel steps
    assert len(payload["funnel"]["steps"]) == 5

    # Top converters should be sorted
    converters = payload["top_converters"]
    if len(converters) >= 2:
        assert converters[0]["conversion_count"] >= converters[1]["conversion_count"]

