import os
import signal
import socket
import subprocess
import sys
import time
from pathlib import Path

import pytest


@pytest.fixture(scope="session")
def app_server(request):
    host = os.environ.get("CONVERIGO_HOST", "127.0.0.1")
    port = int(os.environ.get("CONVERIGO_PORT", "8000"))

    def _is_port_open(host_name: str, port_number: int) -> bool:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(0.5)
            return sock.connect_ex((host_name, port_number)) == 0

    if _is_port_open(host, port):
        yield {"host": host, "port": port}
        return

    repo_root = Path(__file__).resolve().parents[1]
    env = os.environ.copy()
    env.setdefault("PYTHONPATH", str(repo_root))

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
        ],
        cwd=repo_root,
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    try:
        for _ in range(60):
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


@pytest.fixture(autouse=True)
def ensure_app_server(app_server):
    return app_server
