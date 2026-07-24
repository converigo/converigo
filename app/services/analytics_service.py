from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import json
import threading
from pathlib import Path
from typing import Any

from fastapi import Request

from app.core.observability import metrics_registry
from app.core.settings import settings


class AnalyticsService:
    """Persist and aggregate lightweight analytics events for production reporting."""

    IGNORED_PATH_PREFIXES = (
        "/static",
        "/outputs",
        "/metrics",
        "/health",
        "/ready",
        "/openapi.json",
        "/docs",
        "/redoc",
    )

    def __init__(self, storage_path: Path | str | None = None) -> None:
        self.storage_path = Path(storage_path or settings.ANALYTICS_LOG_FILE)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()

    def track_event(self, event_name: str, request: Request | None = None, **payload: Any) -> dict[str, Any]:
        event = self._build_event(event_name, request=request, **payload)
        return self._write_event(event)

    def track_page_view(self, request: Request | None = None, **payload: Any) -> dict[str, Any]:
        return self.track_event("page_view", request=request, **payload)

    def track_upload_start(self, request: Request | None = None, **payload: Any) -> dict[str, Any]:
        return self.track_event("upload_start", request=request, **payload)

    def track_upload_success(self, request: Request | None = None, **payload: Any) -> dict[str, Any]:
        return self.track_event("upload_success", request=request, **payload)

    def track_conversion_start(self, request: Request | None = None, **payload: Any) -> dict[str, Any]:
        return self.track_event("conversion_start", request=request, **payload)

    def track_conversion_success(self, request: Request | None = None, **payload: Any) -> dict[str, Any]:
        return self.track_event("conversion_success", request=request, **payload)

    def track_conversion_failed(self, request: Request | None = None, **payload: Any) -> dict[str, Any]:
        return self.track_event("conversion_failed", request=request, **payload)

    def track_download(self, request: Request | None = None, **payload: Any) -> dict[str, Any]:
        return self.track_event("download", request=request, **payload)

    def track_error(self, request: Request | None = None, **payload: Any) -> dict[str, Any]:
        return self.track_event("error", request=request, **payload)

    def build_dashboard_metrics(self) -> dict[str, Any]:
        events = self._load_events()
        counts = Counter(event.get("event_name", "") for event in events)
        page_views = [event for event in events if event.get("event_name") == "page_view"]
        upload_starts = [event for event in events if event.get("event_name") == "upload_start"]
        upload_successes = [event for event in events if event.get("event_name") == "upload_success"]
        conversion_starts = [event for event in events if event.get("event_name") == "conversion_start"]
        conversion_successes = [event for event in events if event.get("event_name") == "conversion_success"]
        downloads = [event for event in events if event.get("event_name") == "download"]
        errors = [event for event in events if event.get("event_name") == "error"]

        unique_visitors = {event.get("visitor_id") for event in page_views if event.get("visitor_id")}
        processing_times = [float(event.get("processing_ms", 0) or 0) for event in conversion_successes if event.get("processing_ms") is not None]
        category_counts = Counter(self._normalize_token(event.get("category")) for event in conversion_starts if event.get("category"))
        converter_counts = Counter(self._normalize_token(event.get("converter_name")) for event in conversion_starts if event.get("converter_name"))
        performance = self._build_performance_metrics(events)
        seo = self._build_seo_metrics(events)

        upload_count = len(upload_starts)
        conversion_count = len(conversion_starts)

        return {
            "total_visitor": len(page_views),
            "unique_visitor": len(unique_visitors),
            "upload_count": upload_count,
            "upload_success_rate": round((len(upload_successes) / upload_count) * 100, 2) if upload_count else 0.0,
            "conversion_count": conversion_count,
            "conversion_success_rate": round((len(conversion_successes) / conversion_count) * 100, 2) if conversion_count else 0.0,
            "download_count": len(downloads),
            "average_processing_time": round(sum(processing_times) / len(processing_times), 2) if processing_times else 0.0,
            "top_converter": converter_counts.most_common(1)[0][0] if converter_counts else "",
            "most_used_category": category_counts.most_common(1)[0][0] if category_counts else "",
            "error_counts": self._summarize_errors(errors),
            "performance": performance,
            "seo": seo,
            "event_counts": dict(counts),
        }

    def _build_performance_metrics(self, events: list[dict[str, Any]]) -> dict[str, float]:
        metrics: dict[str, list[float]] = defaultdict(list)
        for event in events:
            if event.get("event_name") != "performance_metric":
                continue
            metric_name = self._normalize_token(event.get("metric_name"))
            metric_value = event.get("metric_value")
            try:
                numeric_value = float(metric_value)
            except (TypeError, ValueError):
                continue
            if metric_name:
                metrics[metric_name].append(numeric_value)

        return {
            metric: round(sum(values) / len(values), 3)
            for metric, values in metrics.items()
            if values
        }

    def _build_seo_metrics(self, events: list[dict[str, Any]]) -> dict[str, int]:
        seo_events = Counter()
        for event in events:
            event_name = str(event.get("event_name", "")).strip()
            if event_name in {"landing_page_view", "organic_entry", "search_query", "internal_link_click", "faq_expand"}:
                seo_events[event_name] += 1
        return dict(seo_events)

    def _summarize_errors(self, events: list[dict[str, Any]]) -> dict[str, int]:
        counts = Counter(self._normalize_token(event.get("error_type")) for event in events if event.get("error_type"))
        return dict(counts)

    def _build_event(self, event_name: str, request: Request | None = None, **payload: Any) -> dict[str, Any]:
        request_state = getattr(request, "state", None) if request is not None else None
        path = self._string_value(payload.pop("page_path", None)) or (str(getattr(request, "url", None).path) if request and getattr(request, "url", None) else "")
        event = {
            "timestamp": self._utc_now(),
            "event_name": event_name,
            "page_path": path,
            "page_title": self._string_value(payload.pop("page_title", None)),
            "converter_name": self._string_value(payload.pop("converter_name", None)),
            "category": self._string_value(payload.pop("category", None)),
            "input_format": self._string_value(payload.pop("input_format", None)),
            "output_format": self._string_value(payload.pop("output_format", None)),
            "error_type": self._string_value(payload.pop("error_type", None)),
            "event_status": self._string_value(payload.pop("event_status", None)),
            "metric_name": self._string_value(payload.pop("metric_name", None)),
            "metric_value": self._numeric_or_string(payload.pop("metric_value", None)),
            "processing_ms": self._numeric_or_string(payload.pop("processing_ms", None)),
            "search_query": self._string_value(payload.pop("search_query", None)),
            "link_href": self._string_value(payload.pop("link_href", None)),
            "faq_id": self._string_value(payload.pop("faq_id", None)),
            "entry_type": self._string_value(payload.pop("entry_type", None)),
            "referrer": self._string_value(payload.pop("referrer", None)),
            "request_id": self._string_value(getattr(request_state, "request_id", None)),
            "conversion_id": self._string_value(getattr(request_state, "conversion_id", None)),
            "user_agent": self._string_value(getattr(request_state, "user_agent", None)),
            "ip_hash": self._string_value(getattr(request_state, "ip_hash", None)),
            "visitor_id": self._build_visitor_id(request, payload),
        }

        for key, value in payload.items():
            normalized_value = self._string_value(value)
            if normalized_value:
                event[key] = normalized_value

        if event.get("page_title") == "":
            event.pop("page_title", None)

        return event

    def _write_event(self, event: dict[str, Any]) -> dict[str, Any]:
        serialized = json.dumps(event, ensure_ascii=True, separators=(",", ":"))
        with self._lock:
            self.storage_path.parent.mkdir(parents=True, exist_ok=True)
            with self.storage_path.open("a", encoding="utf-8") as handle:
                handle.write(serialized + "\n")

        metrics_registry.increment("converigo_analytics_events_total", event_name=event.get("event_name", "unknown"))
        metrics_registry.increment(f"converigo_analytics_{event.get('event_name', 'unknown')}_total")
        return event

    def _load_events(self) -> list[dict[str, Any]]:
        if not self.storage_path.exists():
            return []

        events: list[dict[str, Any]] = []
        with self.storage_path.open("r", encoding="utf-8") as handle:
            for line in handle:
                raw = line.strip()
                if not raw:
                    continue
                try:
                    event = json.loads(raw)
                except json.JSONDecodeError:
                    continue
                if isinstance(event, dict):
                    events.append(event)
        return events

    def _build_visitor_id(self, request: Request | None, payload: dict[str, Any]) -> str:
        explicit = self._string_value(payload.get("visitor_id"))
        if explicit:
            return explicit

        request_state = getattr(request, "state", None) if request is not None else None
        source = "|".join(
            value
            for value in [
                self._string_value(getattr(request_state, "ip_hash", None)),
                self._string_value(getattr(request_state, "user_agent", None)),
                self._string_value(getattr(request, "client", None).host if request and getattr(request, "client", None) else None),
            ]
            if value
        )
        if not source:
            source = "analytics"
        digest = hashlib.sha256(source.encode("utf-8")).hexdigest()
        return digest[:24]

    def _utc_now(self) -> str:
        return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")

    def _string_value(self, value: Any) -> str:
        if value is None:
            return ""
        if isinstance(value, str):
            return value.strip()
        if isinstance(value, (int, float)):
            return str(value)
        return str(value).strip()

    def _numeric_or_string(self, value: Any) -> float | str | None:
        if value is None:
            return None
        if isinstance(value, (int, float)):
            return float(value)
        try:
            return float(str(value))
        except (TypeError, ValueError):
            text = self._string_value(value)
            return text or None

    def _normalize_token(self, value: Any) -> str:
        token = self._string_value(value).lower().strip()
        return token.replace(" ", "_")