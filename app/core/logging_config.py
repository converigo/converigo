import logging
import sys
from logging.handlers import RotatingFileHandler

from app.core.observability import JsonLogFormatter, ObservabilityFilter
from app.core.settings import settings


def configure_logging() -> None:
    settings.LOG_DIR.mkdir(parents=True, exist_ok=True)

    formatter = JsonLogFormatter()
    observability_filter = ObservabilityFilter()

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    stream_handler.addFilter(observability_filter)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    for handler in list(root_logger.handlers):
        root_logger.removeHandler(handler)

    root_logger.addHandler(stream_handler)
    
    # Only add file handler if not running tests (avoids Windows file lock on parallel pytest)
    if "pytest" not in sys.modules:
        file_handler = RotatingFileHandler(
            filename=str(settings.LOG_FILE),
            maxBytes=5 * 1024 * 1024,
            backupCount=3,
            encoding="utf-8",
            delay=True,
        )
        file_handler.setFormatter(formatter)
        file_handler.addFilter(observability_filter)
        root_logger.addHandler(file_handler)
        logging.getLogger("uvicorn").handlers = [stream_handler, file_handler]
    else:
        logging.getLogger("uvicorn").handlers = [stream_handler]

    logging.getLogger("uvicorn.error").handlers = list(logging.getLogger("uvicorn").handlers)
    logging.getLogger("uvicorn.access").handlers = list(logging.getLogger("uvicorn").handlers)
