from pathlib import Path

from app.services.analytics_service import AnalyticsService


def test_testclient_event_marked_in_event() -> None:
    """Test that testclient events are properly marked with is_testclient=True."""
    service = AnalyticsService(storage_path=Path("./tmp/test_marking.jsonl"))
    
    # Track a testclient event
    event = service.track_event(
        "page_view",
        user_agent="testclient"
    )
    
    assert event.get("is_testclient") is True


def test_production_event_not_marked_as_testclient() -> None:
    """Test that production events are not marked as testclient."""
    service = AnalyticsService(storage_path=Path("./tmp/test_marking.jsonl"))
    
    # Track a production event
    event = service.track_event(
        "page_view",
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    )
    
    assert event.get("is_testclient") is False


def test_no_user_agent_not_marked_as_testclient() -> None:
    """Test that events without user_agent are not marked as testclient."""
    service = AnalyticsService(storage_path=Path("./tmp/test_marking.jsonl"))
    
    # Track an event without user_agent
    event = service.track_event("page_view")
    
    assert event.get("is_testclient") is False


def test_dashboard_metrics_excludes_testclient_events(tmp_path: Path) -> None:
    """Test that build_dashboard_metrics excludes testclient events."""
    service = AnalyticsService(storage_path=tmp_path / "analytics.jsonl")
    
    # Track production events
    service.track_page_view(page_path="/", visitor_id="visitor-1", entry_type="direct")
    service.track_page_view(page_path="/tools/mp4-to-mp3", visitor_id="visitor-2", entry_type="organic")
    
    # Track testclient events (should be excluded from metrics)
    service.track_event("page_view", user_agent="testclient")
    service.track_event("page_view", user_agent="testclient")
    service.track_event("page_view", user_agent="testclient")
    
    metrics = service.build_dashboard_metrics()
    
    # Should only count the 2 production events, not the 3 testclient events
    assert metrics["total_visitor"] == 2
    assert metrics["unique_visitor"] == 2


def test_testclient_events_preserved_in_storage(tmp_path: Path) -> None:
    """Test that testclient events are preserved in storage (not deleted)."""
    service = AnalyticsService(storage_path=tmp_path / "analytics.jsonl")
    
    # Track both production and testclient events
    service.track_page_view(page_path="/", visitor_id="visitor-1", entry_type="direct")
    service.track_event("page_view", user_agent="testclient")
    
    # Load all events
    all_events = service._load_events()
    
    # Should have all events (production + testclient)
    assert len(all_events) == 2
    
    # One should be marked as testclient
    testclient_events = [e for e in all_events if e.get("is_testclient") is True]
    assert len(testclient_events) == 1
    
    # One should NOT be marked as testclient (production)
    production_events = [e for e in all_events if not e.get("is_testclient", False)]
    assert len(production_events) == 1


def test_page_path_attribute_present_in_events(tmp_path: Path) -> None:
    """Test that page attribution is present when context exists."""
    service = AnalyticsService(storage_path=tmp_path / "analytics.jsonl")
    
    event = service.track_page_view(
        page_path="/tools/pdf-to-jpg",
        visitor_id="visitor-1"
    )
    
    assert event.get("page_path") == "/tools/pdf-to-jpg"
    assert event.get("visitor_id") == "visitor-1"


def test_no_page_path_when_not_provided(tmp_path: Path) -> None:
    """Test that page_path can be empty when not provided."""
    service = AnalyticsService(storage_path=tmp_path / "analytics.jsonl")
    
    event = service.track_event("custom_event")
    
    assert event.get("page_path") == ""
    assert event.get("is_testclient") is False

