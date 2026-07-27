"""
Converigo
Analytics Intelligence Service
Version : 1.0.0

Wraps AnalyticsService.build_dashboard_metrics() and provides
pre-aggregated, dashboard-specific intelligence payloads.

Do NOT modify architecture, routing, or converter engine.
"""

from __future__ import annotations

import re
from collections import Counter, defaultdict
from typing import Any

from app.services.analytics_service import AnalyticsService


class AnalyticsIntelligenceService:
    """Compute analytics intelligence from existing AnalyticsService event data.

    All methods are read-only aggregations over the JSONL event store.
    No new tracking — only existing events are analysed.
    """

    # Performance thresholds (Web Vitals)
    LCP_THRESHOLD_MS = 2500
    CLS_THRESHOLD = 0.1
    INP_THRESHOLD_MS = 200
    TTFB_THRESHOLD_MS = 800
    FCP_THRESHOLD_MS = 1800

    def __init__(self, analytics_service: AnalyticsService | None = None) -> None:
        self.analytics_service = analytics_service or AnalyticsService()

    def build_intelligence(self) -> dict[str, Any]:
        """Build the full analytics intelligence payload."""
        metrics = self.analytics_service.build_dashboard_metrics()
        events = self.analytics_service._load_events()

        return {
            "funnel": self.build_funnel(events),
            "top_converters": self.build_top_converters(events),
            "error_analytics": self.build_error_analytics(events),
            "device_analytics": self.build_device_analytics(events),
            "geographic_analytics": self.build_geographic_analytics(events),
            "performance": self.build_performance_insights(events, metrics),
            "growth": self.build_growth(events),
            "seo": self.build_seo_insights(events, metrics),
        }

    # ── TASK 1: Conversion Funnel ──────────────────────────────────

    def build_funnel(self, events: list[dict[str, Any]]) -> dict[str, Any]:
        """Build conversion funnel from raw events."""
        visitors = set()
        uploaders = set()
        converters = set()
        success_converters = set()
        downloaders = set()

        for event in events:
            vid = event.get("visitor_id", "")
            name = event.get("event_name", "")

            if name == "page_view":
                visitors.add(vid)
            elif name == "upload_start":
                uploaders.add(vid)
            elif name == "conversion_start":
                converters.add(vid)
            elif name == "conversion_success":
                success_converters.add(vid)
            elif name == "download":
                downloaders.add(vid)

        total_visitors = len(visitors)
        steps = [
            {"label": "Visitor", "count": total_visitors, "rate": 100.0},
            {"label": "Upload", "count": len(uploaders), "rate": self._pct(len(uploaders), total_visitors)},
            {"label": "Conversion Started", "count": len(converters), "rate": self._pct(len(converters), total_visitors)},
            {"label": "Conversion Success", "count": len(success_converters), "rate": self._pct(len(success_converters), total_visitors)},
            {"label": "Download", "count": len(downloaders), "rate": self._pct(len(downloaders), total_visitors)},
        ]

        # Overall funnel % = downloaders / visitors
        overall = self._pct(len(downloaders), total_visitors) if total_visitors else 0.0

        return {
            "steps": steps,
            "overall_funnel_percentage": overall,
            "total_visitors": total_visitors,
            "upload_rate": self._pct(len(uploaders), total_visitors),
            "conversion_rate": self._pct(len(converters), total_visitors),
            "download_rate": self._pct(len(downloaders), total_visitors),
        }

    # ── TASK 2: Top Converter Analytics ─────────────────────────────

    def build_top_converters(self, events: list[dict[str, Any]], top_n: int = 10) -> list[dict[str, Any]]:
        """Rank converters by usage."""
        converter_data: dict[str, dict[str, Any]] = {}

        for event in events:
            name = event.get("event_name", "")
            converter = event.get("converter_name", "") or ""
            if not converter:
                continue

            if converter not in converter_data:
                converter_data[converter] = {
                    "converter_name": converter,
                    "upload_count": 0,
                    "conversion_count": 0,
                    "download_count": 0,
                    "success_count": 0,
                    "error_count": 0,
                    "processing_times": [],
                }

            data = converter_data[converter]

            if name == "upload_start":
                data["upload_count"] += 1
            elif name == "conversion_start":
                data["conversion_count"] += 1
            elif name == "download":
                data["download_count"] += 1
            elif name == "conversion_success":
                data["success_count"] += 1
                ms = event.get("processing_ms")
                if ms is not None:
                    try:
                        data["processing_times"].append(float(ms))
                    except (TypeError, ValueError):
                        pass
            elif name == "conversion_failed":
                data["error_count"] += 1
            elif name == "error":
                data["error_count"] += 1

        results = []
        for converter, data in converter_data.items():
            total = data["success_count"] + data["error_count"]
            results.append({
                "converter_name": converter,
                "upload_count": data["upload_count"],
                "conversion_count": data["conversion_count"],
                "download_count": data["download_count"],
                "success_rate": round((data["success_count"] / total) * 100, 2) if total else 0.0,
                "error_rate": round((data["error_count"] / total) * 100, 2) if total else 0.0,
                "average_processing_time": round(sum(data["processing_times"]) / len(data["processing_times"]), 2) if data["processing_times"] else 0.0,
            })

        results.sort(key=lambda x: x["conversion_count"], reverse=True)
        return results[:top_n]

    # ── TASK 3: Error Analytics ────────────────────────────────────

    def build_error_analytics(self, events: list[dict[str, Any]]) -> dict[str, Any]:
        """Break down errors by converter, category, and error type."""
        by_converter: Counter[str] = Counter()
        by_category: Counter[str] = Counter()
        by_error_type: Counter[str] = Counter()
        trend: dict[str, int] = defaultdict(int)

        for event in events:
            if event.get("event_name") not in ("error", "conversion_failed"):
                continue

            converter = event.get("converter_name", "") or "unknown"
            category = event.get("category", "") or "general"
            error_type = event.get("error_type", "") or "UNKNOWN_ERROR"
            timestamp = event.get("timestamp", "")[:7]  # YYYY-MM

            by_converter[converter] += 1
            by_category[category] += 1
            by_error_type[error_type] += 1
            trend[timestamp] += 1

        return {
            "total_errors": sum(by_error_type.values()),
            "by_converter": dict(by_converter.most_common(20)),
            "by_category": dict(by_category.most_common(10)),
            "by_error_type": dict(by_error_type.most_common(20)),
            "trend": dict(sorted(trend.items())),
        }

    # ── TASK 4: Device Analytics ───────────────────────────────────

    @staticmethod
    def _classify_device(user_agent: str) -> str:
        """Classify device type from User-Agent string."""
        ua = user_agent.lower()
        if not ua:
            return "Unknown"
        if any(pat in ua for pat in ("tablet", "ipad", "playbook", "silk")):
            return "Tablet"
        if any(pat in ua for pat in ("mobile", "iphone", "ipod", "android", "blackberry", "windows phone")):
            return "Mobile"
        return "Desktop"

    @staticmethod
    def _classify_browser(user_agent: str) -> str:
        """Classify browser from User-Agent string."""
        ua = user_agent.lower()
        if not ua:
            return "Unknown"
        if "edg/" in ua or "edge/" in ua:
            return "Edge"
        if "chrome/" in ua and "chromium" not in ua:
            return "Chrome"
        if "firefox/" in ua:
            return "Firefox"
        if "safari/" in ua and "chrome/" not in ua:
            return "Safari"
        if "opera/" in ua or "opr/" in ua:
            return "Opera"
        return "Other"

    @staticmethod
    def _classify_os(user_agent: str) -> str:
        """Classify OS from User-Agent string."""
        ua = user_agent.lower()
        if not ua:
            return "Unknown"
        if "windows" in ua:
            return "Windows"
        if "mac os" in ua or "macintosh" in ua:
            return "macOS"
        if "linux" in ua and "android" not in ua:
            return "Linux"
        if "android" in ua:
            return "Android"
        if "iphone" in ua or "ipad" in ua or "ipod" in ua:
            return "iOS"
        if "chrome os" in ua or "cros" in ua:
            return "ChromeOS"
        return "Other"

    @staticmethod
    def _extract_resolution(event: dict[str, Any]) -> str:
        """Extract screen resolution from event payload."""
        res = event.get("screen_resolution", "") or ""
        if res:
            return res
        return "Unknown"

    def build_device_analytics(self, events: list[dict[str, Any]]) -> dict[str, Any]:
        """Aggregate device metrics from User-Agent data."""
        device_types: Counter[str] = Counter()
        browsers: Counter[str] = Counter()
        oss: Counter[str] = Counter()
        resolutions: Counter[str] = Counter()
        unique_visitors_by_device: dict[str, set[str]] = defaultdict(set)

        for event in events:
            ua = event.get("user_agent", "") or ""
            vid = event.get("visitor_id", "") or ""

            device = self._classify_device(ua)
            browser = self._classify_browser(ua)
            os_name = self._classify_os(ua)
            resolution = self._extract_resolution(event)

            device_types[device] += 1
            browsers[browser] += 1
            oss[os_name] += 1
            resolutions[resolution] += 1

            if vid:
                unique_visitors_by_device[device].add(vid)

        return {
            "device_types": dict(device_types.most_common(10)),
            "browsers": dict(browsers.most_common(10)),
            "operating_systems": dict(oss.most_common(10)),
            "screen_resolutions": dict(resolutions.most_common(10)),
            "unique_visitors_by_device": {k: len(v) for k, v in unique_visitors_by_device.items()},
        }

    # ── TASK 5: Geographic Analytics ───────────────────────────────

    def build_geographic_analytics(self, events: list[dict[str, Any]]) -> dict[str, Any]:
        """Aggregate geographic metrics from anonymized ip_hash data.

        No raw IPs are stored — only hashed identifiers.
        This provides high-level geographic distribution without PII.
        """
        # ip_hash uniqueness gives a sense of distinct origins
        ip_hashes: set[str] = set()
        languages: Counter[str] = Counter()
        timezones: Counter[str] = Counter()

        # Attempt to extract locale hints from page_path or event payload
        for event in events:
            ip_hash = event.get("ip_hash", "") or ""
            if ip_hash:
                ip_hashes.add(ip_hash)

            lang = event.get("language", "") or ""
            if lang:
                languages[lang] += 1

            tz = event.get("timezone", "") or ""
            if tz:
                timezones[tz] += 1

        return {
            "unique_ip_hashes": len(ip_hashes),
            "languages": dict(languages.most_common(20)),
            "timezones": dict(timezones.most_common(10)),
            "note": "Geographic data is anonymized. No IPs stored, only SHA-256 hashes.",
        }

    # ── TASK 6: Performance Dashboard ──────────────────────────────

    def build_performance_insights(self, events: list[dict[str, Any]], metrics: dict[str, Any]) -> dict[str, Any]:
        """Build performance dashboard with threshold warnings."""
        existing = metrics.get("performance", {})

        lcp = existing.get("lcp", 0.0)
        cls_val = existing.get("cls", 0.0)
        inp = existing.get("inp", 0.0)
        ttfb = existing.get("ttfb", 0.0)
        fcp = existing.get("fcp", 0.0)

        def _warn(label: str, value: float, threshold: float, unit: str = "ms") -> dict[str, Any]:
            exceeded = value > threshold
            return {
                "label": label,
                "value_ms" if unit == "ms" else "value": round(value, 3) if unit == "score" else round(value, 1),
                "threshold": threshold,
                "unit": unit,
                "status": "warning" if exceeded else "pass",
                "message": f"{label} {'exceeds' if exceeded else 'within'} threshold ({value:.1f}{'ms' if unit == 'ms' else ''} / {threshold}{'ms' if unit == 'ms' else ''})",
            }

        performance_warnings = [
            _warn("LCP", lcp, self.LCP_THRESHOLD_MS),
            _warn("CLS", cls_val, self.CLS_THRESHOLD, unit="score"),
            _warn("INP", inp, self.INP_THRESHOLD_MS),
            _warn("TTFB", ttfb, self.TTFB_THRESHOLD_MS),
            _warn("FCP", fcp, self.FCP_THRESHOLD_MS),
        ]

        any_warning = any(m["status"] == "warning" for m in performance_warnings)

        return {
            "average_lcp": lcp,
            "average_cls": cls_val,
            "average_inp": inp,
            "average_ttfb": ttfb,
            "average_fcp": fcp,
            "threshold_warnings": performance_warnings,
            "has_warnings": any_warning,
            "overall_status": "warning" if any_warning else "pass",
        }

    # ── TASK 7: Growth Dashboard ───────────────────────────────────

    def build_growth(self, events: list[dict[str, Any]]) -> dict[str, Any]:
        """Build growth metrics: visitor sources, returning visitors, top pages."""
        organic_ids: set[str] = set()
        direct_ids: set[str] = set()
        referral_ids: set[str] = set()

        visitor_page_views: dict[str, list[str]] = defaultdict(list)
        entry_type_counts: Counter[str] = Counter()
        landing_page_counts: Counter[str] = Counter()
        exit_page_counts: Counter[str] = Counter()

        # Track page visit sequences per visitor for landing/exit
        page_sequences: dict[str, list[str]] = defaultdict(list)

        for event in events:
            name = event.get("event_name", "")
            vid = event.get("visitor_id", "") or ""
            path = event.get("page_path", "") or ""
            entry = event.get("entry_type", "") or ""

            if name == "page_view":
                if entry == "organic":
                    organic_ids.add(vid)
                elif entry == "direct":
                    direct_ids.add(vid)
                elif entry == "referral":
                    referral_ids.add(vid)

                visitor_page_views[vid].append(path)
                page_sequences[vid].append(path)
                landing_page_counts[path] += 1

                if entry:
                    entry_type_counts[entry] += 1

        # Determine returning visitors (visitors with >1 page_view event)
        returning_ids = {vid for vid, paths in visitor_page_views.items() if len(paths) > 1}

        # Determine exit pages (last page in each visitor's sequence)
        for vid, seq in page_sequences.items():
            if seq:
                exit_page_counts[seq[-1]] += 1

        total_categorized = len(organic_ids | direct_ids | referral_ids) or 1

        return {
            "organic_visitors": len(organic_ids),
            "direct_visitors": len(direct_ids),
            "referral_visitors": len(referral_ids),
            "organic_rate": round(len(organic_ids) / total_categorized * 100, 2),
            "direct_rate": round(len(direct_ids) / total_categorized * 100, 2),
            "referral_rate": round(len(referral_ids) / total_categorized * 100, 2),
            "returning_visitors": len(returning_ids),
            "returning_rate": round(len(returning_ids) / max(len(set(vid for event in events for vid in [event.get("visitor_id", "")] if vid)), 1) * 100, 2),
            "entry_type_distribution": dict(entry_type_counts),
            "top_landing_pages": dict(landing_page_counts.most_common(10)),
            "top_exit_pages": dict(exit_page_counts.most_common(10)),
        }

    # ── TASK 8: SEO Dashboard ──────────────────────────────────────

    def build_seo_insights(self, events: list[dict[str, Any]], metrics: dict[str, Any]) -> dict[str, Any]:
        """Build enhanced SEO dashboard metrics."""
        seo_data = metrics.get("seo", {})

        # Most visited SEO pages via page_view events
        page_view_counts: Counter[str] = Counter()
        landing_page_perf: dict[str, dict[str, Any]] = defaultdict(lambda: {"views": 0, "organic": 0, "direct": 0})

        for event in events:
            name = event.get("event_name", "")
            path = event.get("page_path", "") or ""
            entry = event.get("entry_type", "") or ""

            if name == "page_view" and path:
                page_view_counts[path] += 1
                landing_page_perf[path]["views"] += 1
                if entry == "organic":
                    landing_page_perf[path]["organic"] += 1
                elif entry == "direct":
                    landing_page_perf[path]["direct"] += 1

        internal_clicks = seo_data.get("internal_link_click", 0)
        faq_expands = seo_data.get("faq_expand", 0)
        search_entries = seo_data.get("search_query", 0)
        organic_entries = seo_data.get("organic_entry", 0)
        landing_views = seo_data.get("landing_page_view", 0)

        # Compute click rates
        total_seo_events = internal_clicks + faq_expands + search_entries + organic_entries + landing_views or 1

        return {
            "most_visited_seo_pages": dict(page_view_counts.most_common(20)),
            "internal_link_clicks": internal_clicks,
            "internal_link_click_rate": round(internal_clicks / total_seo_events * 100, 2),
            "faq_expand_count": faq_expands,
            "faq_expand_rate": round(faq_expands / total_seo_events * 100, 2),
            "search_entry_count": search_entries,
            "search_entry_rate": round(search_entries / total_seo_events * 100, 2),
            "organic_entry_count": organic_entries,
            "landing_page_views": landing_views,
            "landing_page_performance": dict(landing_page_perf),
        }

    # ── Helpers ────────────────────────────────────────────────────

    @staticmethod
    def _pct(part: int, total: int) -> float:
        return round((part / total) * 100, 2) if total else 0.0

