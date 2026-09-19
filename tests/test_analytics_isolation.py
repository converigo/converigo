"""Analytics test-sink isolation regression tests (Option C1).

These tests prove that test traffic is written to the isolated test sink
(``tmp/test_analytics.jsonl``) and never to the production sink
(``app/logs/analytics.jsonl``).

Technique: every test sends a unique ``X-Conversion-Id`` request header. The
observability middleware captures it into ``request.state["conversion_id"]``
(``app/main.py``) and ``AnalyticsService._build_event`` persists it as the
event's ``conversion_id`` field. Grepping each sink for that exact value is an
unambiguous per-test marker, so pre-existing historical data can never create
a false positive and historical line counts are never used as an assertion.
"""
from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import time
import urllib.request
import uuid
from collections.abc import Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from playwright.sync_api import sync_playwright

import app.main as app_main
from app.main import app

REPO_ROOT = Path(__file__).resolve().parents[1]
PROD_SINK = (REPO_ROOT / "app" / "logs" / "analytics.jsonl").resolve()
TEST_SINK = Path(os.environ["ANALYTICS_LOG_FILE"]).resolve()

_TEST_MARKER_PREFIXES = ("iso-testclient-", "iso-e2e-")


def _read_events(path: Path) -> list[dict]:
    if not path.exists():
        return []
    events: list[dict] = []
    with path.open("r", encoding="utf-8") as handle:
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


def _events_for(path: Path, marker: str) -> list[dict]:
    return [event for event in _read_events(path) if event.get("conversion_id") == marker]


def _leaked_into_production() -> list[str]:
    """Return production sink lines carrying one of this session's test markers.

    Streams the file and does a substring check per line instead of parsing
    every event as JSON: the production sink is ~50 MB / ~90k events, and a
    full parse at session teardown would be needlessly slow.
    """
    if not PROD_SINK.exists():
        return []
    leaked: list[str] = []
    with PROD_SINK.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            if any(prefix in line for prefix in _TEST_MARKER_PREFIXES):
                leaked.append(line.strip())
    return leaked


@pytest.fixture(scope="session", autouse=True)
def _assert_no_isolation_markers_in_production_sink() -> Iterator[None]:
    """Final safety net: after the whole session, no test event reached production."""
    yield
    leaked = _leaked_into_production()
    assert leaked == [], f"isolation test events leaked into production: {leaked}"


def test_testclient_event_is_diverted_from_production_sink() -> None:
    """A TestClient request must not touch the production sink."""
    marker = f"iso-testclient-{uuid.uuid4()}"
    client = TestClient(app)
    response = client.get("/", headers={"X-Conversion-Id": marker})
    assert response.status_code < 500

    leaked = _events_for(PROD_SINK, marker)
    assert leaked == [], f"TestClient event leaked into the production sink: {leaked}"


def test_testclient_event_reaches_the_test_sink() -> None:
    """Positive proof that the diverted event was actually recorded."""
    marker = f"iso-testclient-{uuid.uuid4()}"
    client = TestClient(app)
    response = client.get("/", headers={"X-Conversion-Id": marker})
    assert response.status_code < 500

    hits = _events_for(TEST_SINK, marker)
    assert len(hits) == 1, f"expected exactly 1 test-sink event, found {len(hits)}"
    assert hits[0]["event_name"] == "page_view"
    assert hits[0]["user_agent"] == "testclient"


def test_configured_sink_is_the_test_sink() -> None:
    """The session-wide configured sink lives under tmp/ and is what the app bound."""
    assert os.environ["ANALYTICS_LOG_FILE"] == str(TEST_SINK)
    assert TEST_SINK.parent == (REPO_ROOT / "tmp").resolve()
    assert TEST_SINK != PROD_SINK
    assert app_main.analytics_service.storage_path.resolve() == TEST_SINK


def test_production_sink_contains_no_test_session_events() -> None:
    """The production sink must not contain any of this session's test markers."""
    leaked = _leaked_into_production()
    assert leaked == [], f"test events leaked into the production sink: {leaked}"


def test_all_module_level_analytics_services_bind_the_test_sink() -> None:
    """Import-order regression: every module-level AnalyticsService() uses the test sink."""
    import app.routers.convert as convert_router
    import app.routers.dashboard as dashboard_router
    import app.routers.upload as upload_router

    bound = {
        "app.main": app_main.analytics_service.storage_path,
        "app.routers.convert": convert_router.analytics_service.storage_path,
        "app.routers.upload": upload_router.analytics_service.storage_path,
        "app.routers.dashboard": dashboard_router.analytics_service.storage_path,
    }
    not_bound = {name: str(path) for name, path in bound.items() if path.resolve() != TEST_SINK}
    assert not not_bound, (
        "these AnalyticsService instances did not bind the test sink (the "
        f"conftest override must run before the app is imported): {not_bound}"
    )


def test_production_environment_still_uses_the_production_sink() -> None:
    """Negative proof: with the override absent, production resolves to app/logs/."""
    env = os.environ.copy()
    env.pop("ANALYTICS_LOG_FILE", None)
    repo_root = str(REPO_ROOT)
    env["PYTHONPATH"] = repo_root + os.pathsep + env.get("PYTHONPATH", "")
    probe = "from app.core.settings import settings; print(settings.ANALYTICS_LOG_FILE)"
    result = subprocess.run(
        [sys.executable, "-c", probe],
        capture_output=True,
        text=True,
        env=env,
        cwd=repo_root,
    )
    assert result.returncode == 0, f"clean-env probe failed: {result.stderr}"
    resolved = Path(result.stdout.strip()).resolve()
    assert resolved == PROD_SINK, f"production default sink changed: {resolved}"


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _wait_for_health(base_url: str, timeout_seconds: float = 60.0) -> None:
    deadline = time.time() + timeout_seconds
    last_error: Exception | None = None
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(f"{base_url}/health", timeout=2) as response:
                if getattr(response, "status", 0) < 500:
                    return
        except Exception as exc:  # pragma: no cover - startup race
            last_error = exc
        time.sleep(0.25)
    raise RuntimeError(f"server at {base_url} not ready within {timeout_seconds}s: {last_error}")


def test_e2e_headless_chrome_uses_the_test_sink() -> None:
    """The browser channel must write to the test sink via the inherited env.

    Starts its own uvicorn subprocess on a free port rather than reusing the
    session ``app_base_url`` server: that fixture reuses an already-open port
    when one exists, and a server started outside pytest would not carry the
    ANALYTICS_LOG_FILE override -- which would leak into production. Spawning
    here makes the env-inheritance assertion deterministic.
    """
    port = _free_port()
    base_url = f"http://127.0.0.1:{port}"
    marker = f"iso-e2e-{uuid.uuid4()}"

    env = os.environ.copy()
    env["PYTHONPATH"] = str(REPO_ROOT) + os.pathsep + env.get("PYTHONPATH", "")
    env["CONVERIGO_BASE_URL"] = base_url
    assert env["ANALYTICS_LOG_FILE"] == str(TEST_SINK)

    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "app.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
            "--log-level",
            "warning",
        ],
        cwd=str(REPO_ROOT),
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    try:
        _wait_for_health(base_url)
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            page = browser.new_page()
            try:
                page.set_extra_http_headers({"X-Conversion-Id": marker})
                page.goto(f"{base_url}/", wait_until="domcontentloaded")
                page.wait_for_timeout(500)
            finally:
                browser.close()
    finally:
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=10)

    hits = _events_for(TEST_SINK, marker)
    assert hits, "E2E HeadlessChrome event did not reach the test sink"
    agents = {event.get("user_agent") for event in hits}
    assert all("HeadlessChrome" in str(agent) for agent in agents), (
        f"unexpected user_agent in test-sink events: {agents}"
    )

    leaked = _events_for(PROD_SINK, marker)
    assert leaked == [], f"E2E HeadlessChrome event leaked into the production sink: {leaked}"
