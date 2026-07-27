import contextvars
import hashlib
import json
import logging
import threading
import time
import uuid
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.datastructures import MutableHeaders

from app.core.settings import settings


request_id_var: contextvars.ContextVar[str | None] = contextvars.ContextVar("request_id", default=None)
conversion_id_var: contextvars.ContextVar[str | None] = contextvars.ContextVar("conversion_id", default=None)
user_agent_var: contextvars.ContextVar[str | None] = contextvars.ContextVar("user_agent", default=None)
ip_hash_var: contextvars.ContextVar[str | None] = contextvars.ContextVar("ip_hash", default=None)
converter_var: contextvars.ContextVar[str | None] = contextvars.ContextVar("converter", default=None)

STAGE_METRICS = {
    "upload": "converigo_upload_duration_seconds",
    "conversion": "converigo_conversion_duration_seconds",
    "download": "converigo_download_duration_seconds",
    "queue": "converigo_queue_duration_seconds",
    "validation": "converigo_validation_duration_seconds",
    "cleanup": "converigo_cleanup_duration_seconds",
}


def _utc_timestamp(created: float | None = None) -> str:
    value = datetime.now(timezone.utc) if created is None else datetime.fromtimestamp(created, tz=timezone.utc)
    return value.isoformat(timespec="milliseconds").replace("+00:00", "Z")


def generate_request_id() -> str:
    return uuid.uuid4().hex


def generate_conversion_id() -> str:
    return uuid.uuid4().hex


def current_request_id() -> str | None:
    return request_id_var.get()


def current_conversion_id() -> str | None:
    return conversion_id_var.get()


def current_converter() -> str | None:
    return converter_var.get()


def get_client_ip(request: Request) -> str | None:
    forwarded_for = request.headers.get("x-forwarded-for", "").strip()
    if forwarded_for:
        return forwarded_for.split(",", 1)[0].strip() or None

    if request.client and request.client.host:
        return request.client.host

    return None


def hash_ip(ip_address: str | None) -> str | None:
    if not ip_address:
        return None

    digest = hashlib.sha256()
    digest.update(settings.IP_HASH_SALT.encode("utf-8"))
    digest.update(b":")
    digest.update(ip_address.encode("utf-8"))
    return digest.hexdigest()[:16]


def bind_request_context(
    request_id: str,
    user_agent: str | None,
    ip_hash: str | None,
    conversion_id: str | None = None,
    converter: str | None = None,
) -> dict[str, contextvars.Token[Any]]:
    return {
        "request_id": request_id_var.set(request_id),
        "user_agent": user_agent_var.set(user_agent),
        "ip_hash": ip_hash_var.set(ip_hash),
        "conversion_id": conversion_id_var.set(conversion_id),
        "converter": converter_var.set(converter),
    }


def reset_request_context(tokens: dict[str, contextvars.Token[Any]]) -> None:
    request_id_var.reset(tokens["request_id"])
    user_agent_var.reset(tokens["user_agent"])
    ip_hash_var.reset(tokens["ip_hash"])
    conversion_id_var.reset(tokens["conversion_id"])
    converter_var.reset(tokens["converter"])


def bind_conversion_id(conversion_id: str | None) -> str | None:
    if conversion_id:
        conversion_id_var.set(conversion_id)
    return conversion_id


def bind_converter(converter: str | None) -> str | None:
    if converter:
        converter_var.set(converter)
    return converter


def start_timer() -> int:
    return time.perf_counter_ns()


def elapsed_ms(start_ns: int) -> float:
    return round((time.perf_counter_ns() - start_ns) / 1_000_000, 3)


def normalize_error_code(value: Any, fallback: str = "HTTP_ERROR") -> str:
    candidate = value
    if isinstance(value, dict):
        candidate = value.get("code") or value.get("error_code") or value.get("detail")

    text = str(candidate or fallback).strip().upper()
    normalized: list[str] = []
    previous_underscore = False
    for char in text:
        if char.isalnum():
            normalized.append(char)
            previous_underscore = False
        elif not previous_underscore:
            normalized.append("_")
            previous_underscore = True

    code = "".join(normalized).strip("_")
    return code or fallback


def response_status_label(status_code: int) -> str:
    return "success" if status_code < 400 else "failure"


class ObservabilityFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        if getattr(record, "request_id", None) is None:
            record.request_id = current_request_id()
        if getattr(record, "conversion_id", None) is None:
            record.conversion_id = current_conversion_id()
        if getattr(record, "user_agent", None) is None:
            record.user_agent = user_agent_var.get()
        if getattr(record, "ip_hash", None) is None:
            record.ip_hash = ip_hash_var.get()
        if getattr(record, "converter", None) is None:
            record.converter = current_converter()

        for field_name in ("duration_ms", "status", "error_code", "path", "method", "stage", "status_code"):
            if not hasattr(record, field_name):
                setattr(record, field_name, None)

        return True


class JsonLogFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": _utc_timestamp(record.created),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": getattr(record, "request_id", None),
            "conversion_id": getattr(record, "conversion_id", None),
            "user_agent": getattr(record, "user_agent", None),
            "ip_hash": getattr(record, "ip_hash", None),
            "converter": getattr(record, "converter", None),
            "duration_ms": getattr(record, "duration_ms", None),
            "status": getattr(record, "status", None),
            "error_code": getattr(record, "error_code", None),
        }

        optional_fields = {
            "method": getattr(record, "method", None),
            "path": getattr(record, "path", None),
            "stage": getattr(record, "stage", None),
            "status_code": getattr(record, "status_code", None),
        }
        for key, value in optional_fields.items():
            if value is not None:
                payload[key] = value

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(payload, ensure_ascii=True)


class MetricsRegistry:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._counters: dict[tuple[str, tuple[tuple[str, str], ...]], float] = defaultdict(float)
        self._summaries: dict[tuple[str, tuple[tuple[str, str], ...]], dict[str, float]] = defaultdict(
            lambda: {"count": 0.0, "sum": 0.0}
        )

    def _labels_key(self, labels: dict[str, Any]) -> tuple[tuple[str, str], ...]:
        return tuple(sorted((key, str(value)) for key, value in labels.items()))

    def increment(self, name: str, amount: float = 1.0, **labels: Any) -> None:
        with self._lock:
            self._counters[(name, self._labels_key(labels))] += amount

    def observe(self, name: str, value: float, **labels: Any) -> None:
        with self._lock:
            metric = self._summaries[(name, self._labels_key(labels))]
            metric["count"] += 1.0
            metric["sum"] += value

    def counter_value(self, name: str) -> float:
        with self._lock:
            return sum(value for (metric_name, _labels), value in self._counters.items() if metric_name == name)

    def render(self) -> str:
        lines: list[str] = []
        with self._lock:
            counter_items = sorted(self._counters.items())
            summary_items = sorted(self._summaries.items())

        emitted_help: set[str] = set()
        for (name, labels), value in counter_items:
            if name not in emitted_help:
                lines.append(f"# HELP {name} Converigo metric {name}")
                lines.append(f"# TYPE {name} counter")
                emitted_help.add(name)
            lines.append(f"{name}{self._format_labels(labels)} {value}")

        for (name, labels), values in summary_items:
            if name not in emitted_help:
                lines.append(f"# HELP {name} Converigo metric {name}")
                lines.append(f"# TYPE {name} summary")
                emitted_help.add(name)
            lines.append(f"{name}_count{self._format_labels(labels)} {values['count']}")
            lines.append(f"{name}_sum{self._format_labels(labels)} {values['sum']}")

        total_requests = self.counter_value("converigo_requests_total")
        success_total = self.counter_value("converigo_success_total")
        failure_total = self.counter_value("converigo_failure_total")

        lines.append("# HELP converigo_success_rate Successful request ratio")
        lines.append("# TYPE converigo_success_rate gauge")
        lines.append(f"converigo_success_rate {success_total / total_requests if total_requests else 0.0}")
        lines.append("# HELP converigo_failure_rate Failed request ratio")
        lines.append("# TYPE converigo_failure_rate gauge")
        lines.append(f"converigo_failure_rate {failure_total / total_requests if total_requests else 0.0}")

        return "\n".join(lines) + "\n"

    @staticmethod
    def _format_labels(labels: tuple[tuple[str, str], ...]) -> str:
        if not labels:
            return ""
        return "{" + ",".join(f'{key}="{value}"' for key, value in labels) + "}"


metrics_registry = MetricsRegistry()


def attach_correlation_headers(headers: MutableHeaders | dict[str, str], request: Request) -> None:
    request_id = getattr(request.state, "request_id", None) or current_request_id()
    conversion_id = getattr(request.state, "conversion_id", None) or current_conversion_id()

    headers["X-Request-ID"] = request_id or generate_request_id()
    if conversion_id:
        headers["X-Conversion-ID"] = conversion_id


def enrich_error_content(request: Request, content: Any) -> dict[str, Any]:
    payload = dict(content) if isinstance(content, dict) else {"detail": content}
    payload["request_id"] = getattr(request.state, "request_id", None) or current_request_id()
    conversion_id = getattr(request.state, "conversion_id", None) or current_conversion_id()
    if conversion_id:
        payload["conversion_id"] = conversion_id
    return payload


def build_error_response(
    request: Request,
    *,
    status_code: int,
    content: Any,
    headers: dict[str, str] | None = None,
) -> JSONResponse:
    response_headers = dict(headers or {})
    request_id = getattr(request.state, "request_id", None) or current_request_id()
    conversion_id = getattr(request.state, "conversion_id", None) or current_conversion_id()
    response_headers["X-Request-ID"] = request_id or generate_request_id()
    if conversion_id:
        response_headers["X-Conversion-ID"] = conversion_id
    return JSONResponse(
        status_code=status_code,
        content=enrich_error_content(request, content),
        headers=response_headers,
    )


class ConversionTracker:
    def __init__(self, request: Request) -> None:
        self.request = request
        self.logger = logging.getLogger("app.observability.conversion")
        existing_id = getattr(request.state, "conversion_id", None) or request.headers.get("x-conversion-id")
        self.conversion_id = existing_id or generate_conversion_id()
        request.state.conversion_id = self.conversion_id
        request.scope.setdefault("state", {})["conversion_id"] = self.conversion_id
        bind_conversion_id(self.conversion_id)
        self.converter = getattr(request.state, "converter", None)
        self._stage_starts: dict[str, int] = {}
        self._queue_recorded = False

    def set_converter(self, converter: str | None) -> None:
        self.converter = converter
        self.request.state.converter = converter
        self.request.scope.setdefault("state", {})["converter"] = converter
        bind_converter(converter)

    def observe_queue(self) -> float | None:
        if self._queue_recorded:
            return None

        request_started_ns = getattr(self.request.state, "request_started_ns", None)
        if request_started_ns is None:
            return None

        duration_ms = elapsed_ms(request_started_ns)
        metrics_registry.observe(STAGE_METRICS["queue"], duration_ms / 1000, status="success")
        self.logger.info(
            "Conversion stage completed",
            extra={"stage": "queue", "duration_ms": duration_ms, "status": "success"},
        )
        self._queue_recorded = True
        return duration_ms

    def start(self, stage: str) -> None:
        self._stage_starts[stage] = start_timer()

    def finish(self, stage: str, status: str = "success", error_code: str | None = None) -> float | None:
        started = self._stage_starts.pop(stage, None)
        if started is None:
            return None

        duration_ms = elapsed_ms(started)
        metric_name = STAGE_METRICS.get(stage)
        if metric_name:
            labels: dict[str, str] = {"status": status}
            if self.converter:
                labels["converter"] = self.converter
            metrics_registry.observe(metric_name, duration_ms / 1000, **labels)

        self.logger.info(
            "Conversion stage completed",
            extra={
                "stage": stage,
                "duration_ms": duration_ms,
                "status": status,
                "error_code": error_code,
            },
        )
        return duration_ms

    def fail(self, stage: str, error_code: str) -> float | None:
        return self.finish(stage, status="failure", error_code=error_code)