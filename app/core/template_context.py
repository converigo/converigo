import os

from app.core.settings import settings


def build_template_context() -> dict:
    verification_token = os.getenv("GOOGLE_SITE_VERIFICATION", settings.GOOGLE_SITE_VERIFICATION or "")
    bing_verification_token = os.getenv("BING_SITE_VERIFICATION", settings.BING_SITE_VERIFICATION or "")
    ga_measurement_id = os.getenv("GA4_MEASUREMENT_ID", os.getenv("GA_MEASUREMENT_ID", settings.GA_MEASUREMENT_ID or "")).strip()

    return {
        "app_name": settings.APP_NAME,
        "app_version": settings.APP_VERSION,
        "ga_measurement_id": ga_measurement_id,
        "verification_token": verification_token,
        "bing_verification_token": bing_verification_token,
        "disable_analytics": settings.DISABLE_ANALYTICS,
    }
