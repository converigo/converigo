import os
import socket
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

import pytest


def _is_port_open(host_name: str, port_number: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.5)
        return sock.connect_ex((host_name, port_number)) == 0


def _wait_for_http_ready(url: str, timeout_seconds: int = 60) -> None:
    deadline = time.time() + timeout_seconds
    last_error: Exception | None = None

    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=2) as response:
                if getattr(response, "status", 0) < 500:
                    return
        except Exception as exc:  # pragma: no cover - defensive for startup races
            last_error = exc
        time.sleep(0.25)

    raise RuntimeError(f"Server at {url} did not become reachable within {timeout_seconds}s: {last_error}")


@pytest.fixture(scope="session")
def app_server(request):
    """Start a uvicorn server for tests that require a live app.

    Behavior:
    - Honors `CONVERIGO_HOST` and `CONVERIGO_PORT` env vars when provided.
    - If running under xdist, offset the port by the worker index to avoid collisions.
    - Sets `CONVERIGO_BASE_URL` env var so tests use the correct base URL.
    """
    host = os.environ.get("CONVERIGO_HOST", "127.0.0.1")
    base_port = int(os.environ.get("CONVERIGO_PORT", "8000"))

    # xdist worker id (e.g. gw0, gw1) may be present in environment
    worker = os.environ.get("PYTEST_XDIST_WORKER")
    if worker and worker.startswith("gw"):
        try:
            idx = int(worker.replace("gw", ""))
        except ValueError:
            idx = 0
    else:
        idx = 0

    port = base_port + idx

    # If port already open (maybe a manually started server), reuse it
    if _is_port_open(host, port):
        base_url = f"http://{host}:{port}"
        os.environ.setdefault("CONVERIGO_BASE_URL", base_url)
        yield {"host": host, "port": port}
        return

    repo_root = Path(__file__).resolve().parents[1]
    env = os.environ.copy()
    env.setdefault("PYTHONPATH", str(repo_root))

    # Ensure tests will use the started server
    base_url = f"http://{host}:{port}"
    env["CONVERIGO_BASE_URL"] = base_url
    os.environ.setdefault("CONVERIGO_BASE_URL", base_url)

    # Start uvicorn as a subprocess
    process = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "app.main:app",
            "--host",
            host,
            "--port",
            str(port),
            "--log-level",
            "info",
        ],
        cwd=repo_root,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    try:
        for _ in range(120):
            if _is_port_open(host, port):
                break
            if process.poll() is not None:
                output = process.stdout.read() if process.stdout else ""
                raise RuntimeError(f"Uvicorn server exited early: {output}")
            time.sleep(0.5)
        else:
            output = process.stdout.read() if process.stdout else ""
            raise RuntimeError(f"Uvicorn server did not become ready: {output}")

        yield {"host": host, "port": port, "process": process}

    finally:
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=10)


@pytest.fixture(scope="session")
def app_base_url(app_server):
    """Return the reachable base URL for browser-based tests."""
    base_url = os.environ.get("CONVERIGO_BASE_URL")
    if not base_url:
        raise RuntimeError("CONVERIGO_BASE_URL was not set by the app server fixture")

    _wait_for_http_ready(f"{base_url}/health")
    return base_url


# Not autouse — only tests that explicitly request app_server or use the
# `needs_server` marker will start the uvicorn subprocess.
@pytest.fixture
def ensure_app_server(app_server):
    return app_server
