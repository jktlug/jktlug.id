import os
import socket
import subprocess
import sys
import time

import pytest


def _find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _wait_for_server(host: str, port: int, timeout: float = 5.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with socket.create_connection((host, port), timeout=0.1):
                return
        except OSError:
            time.sleep(0.05)
    raise RuntimeError(f"Server {host}:{port} did not start within {timeout}s")


@pytest.fixture(scope="session")
def base_url():
    """Start a local HTTP server serving _site/ and yield its URL."""
    site_dir = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "_site")
    )
    if not os.path.isdir(site_dir):
        pytest.skip(
            f"Site not built: {site_dir} does not exist. "
            "Run `./Test` or `stack exec site-compiler rebuild` first."
        )

    port = _find_free_port()
    proc = subprocess.Popen(
        [sys.executable, "-m", "http.server", str(port), "--directory", site_dir],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    url = f"http://127.0.0.1:{port}"
    try:
        _wait_for_server("127.0.0.1", port)
        yield url
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
