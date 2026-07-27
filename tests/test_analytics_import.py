from app.services.analytics_service import AnalyticsService


def test_analytics_service_imports() -> None:
    assert AnalyticsService.__name__ == "AnalyticsService"
