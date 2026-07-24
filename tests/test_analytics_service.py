from pathlib import Path

from app.services.analytics_service import AnalyticsService


def test_analytics_service_tracks_events_and_builds_dashboard_metrics(tmp_path: Path) -> None:
    service = AnalyticsService(storage_path=tmp_path / "analytics.jsonl")

    service.track_page_view(page_path="/", visitor_id="visitor-1", entry_type="direct")
    service.track_page_view(page_path="/tools/mp4-to-mp3", visitor_id="visitor-2", entry_type="organic")
    service.track_upload_start(page_path="/convert", visitor_id="visitor-1", category="audio", input_format="mp4")
    service.track_upload_success(page_path="/convert", visitor_id="visitor-1", category="audio", input_format="mp4", processing_ms=120)
    service.track_conversion_start(page_path="/convert", visitor_id="visitor-1", converter_name="mp4-to-mp3", category="audio", output_format="mp3")
    service.track_conversion_success(page_path="/convert", visitor_id="visitor-1", converter_name="mp4-to-mp3", category="audio", output_format="mp3", processing_ms=1800)
    service.track_download(page_path="/download/mp4-to-mp3.mp3", visitor_id="visitor-1", converter_name="mp4-to-mp3")
    service.track_error(page_path="/convert", visitor_id="visitor-1", error_type="UPLOAD_ERROR")
    service.track_event("landing_page_view", page_path="/", visitor_id="visitor-1")
    service.track_event("organic_entry", page_path="/", visitor_id="visitor-2")
    service.track_event("search_query", page_path="/", visitor_id="visitor-2", search_query="mp4 to mp3")
    service.track_event("internal_link_click", page_path="/", visitor_id="visitor-2", link_href="/tools/mp4-to-mp3")
    service.track_event("faq_expand", page_path="/", visitor_id="visitor-2", faq_id="faq-1")
    service.track_event("performance_metric", page_path="/", visitor_id="visitor-1", metric_name="lcp", metric_value=1.23)
    service.track_event("performance_metric", page_path="/", visitor_id="visitor-1", metric_name="cls", metric_value=0.02)

    metrics = service.build_dashboard_metrics()

    assert metrics["total_visitor"] == 2
    assert metrics["unique_visitor"] == 2
    assert metrics["upload_count"] == 1
    assert metrics["upload_success_rate"] == 100.0
    assert metrics["conversion_count"] == 1
    assert metrics["conversion_success_rate"] == 100.0
    assert metrics["download_count"] == 1
    assert metrics["average_processing_time"] == 1800.0
    assert metrics["top_converter"] == "mp4-to-mp3"
    assert metrics["most_used_category"] == "audio"
    assert metrics["error_counts"]["upload_error"] == 1
    assert metrics["performance"]["lcp"] == 1.23
    assert metrics["performance"]["cls"] == 0.02
    assert metrics["seo"]["landing_page_view"] == 1
    assert metrics["seo"]["organic_entry"] == 1
    assert metrics["seo"]["search_query"] == 1
    assert metrics["seo"]["internal_link_click"] == 1
    assert metrics["seo"]["faq_expand"] == 1
