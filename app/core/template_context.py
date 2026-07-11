from app.core.settings import settings


def build_template_context() -> dict:
    return {
        "app_name": settings.APP_NAME,
        "app_version": settings.APP_VERSION,
        "ga_measurement_id": settings.GA_MEASUREMENT_ID,
    }
