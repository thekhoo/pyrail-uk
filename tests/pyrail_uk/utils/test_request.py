import json
import threading
from collections.abc import Iterator
from http.server import BaseHTTPRequestHandler, HTTPServer

import pytest
from requests.adapters import HTTPAdapter
from requests.exceptions import HTTPError, RetryError
from urllib3.util import Retry

from pyrail_uk.utils.request import DEFAULT_RETRY_STRATEGY, BaseRequestClient

FAST_RETRY = Retry(
    total=3,
    backoff_factor=0,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["GET", "POST"],
)


class StubServer:
    """Local HTTP server that replies with a scripted list of status codes, then 200."""

    def __init__(self, statuses: list[int]):
        self.statuses = list(statuses)
        self.requests: list[dict] = []
        stub = self

        class Handler(BaseHTTPRequestHandler):
            def _handle(self) -> None:
                length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(length).decode() if length else None
                stub.requests.append(
                    {
                        "method": self.command,
                        "path": self.path,
                        "body": body,
                        "headers": dict(self.headers),
                    }
                )
                status = stub.statuses.pop(0) if stub.statuses else 200
                payload = json.dumps({"ok": status == 200}).encode()
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(payload)))
                self.end_headers()
                self.wfile.write(payload)

            do_GET = do_POST = _handle

            def log_message(self, format: str, *args) -> None:
                pass

        self.httpd = HTTPServer(("127.0.0.1", 0), Handler)
        self.url = f"http://127.0.0.1:{self.httpd.server_port}/base"
        threading.Thread(target=self.httpd.serve_forever, daemon=True).start()

    def close(self) -> None:
        self.httpd.shutdown()
        self.httpd.server_close()


@pytest.fixture
def stub_server() -> Iterator[type[StubServer]]:
    servers: list[StubServer] = []

    def make(statuses: list[int] | None = None) -> StubServer:
        server = StubServer(statuses or [])
        servers.append(server)
        return server

    yield make  # type: ignore[misc]
    for server in servers:
        server.close()


def test_default_retry_strategy_covers_429_and_5xx_for_get_and_post():
    assert 429 in DEFAULT_RETRY_STRATEGY.status_forcelist
    assert {500, 502, 503, 504} <= set(DEFAULT_RETRY_STRATEGY.status_forcelist)
    allowed_methods = DEFAULT_RETRY_STRATEGY.allowed_methods
    assert allowed_methods is not None
    assert {"GET", "POST"} <= set(allowed_methods)


def test_default_client_mounts_the_default_retry_strategy():
    client = BaseRequestClient("https://example.com")

    adapter = client.session.get_adapter("https://example.com")
    assert isinstance(adapter, HTTPAdapter)
    assert (
        adapter.max_retries.status_forcelist == DEFAULT_RETRY_STRATEGY.status_forcelist
    )


def test_get_joins_base_url_and_path_and_sends_headers(stub_server):
    server = stub_server()
    client = BaseRequestClient(server.url, headers={"x-apikey": "secret"})

    assert client.get("/api/v1/thing") == {"ok": True}

    (req,) = server.requests
    assert (req["method"], req["path"]) == ("GET", "/base/api/v1/thing")
    assert req["headers"]["x-apikey"] == "secret"


def test_post_sends_json_body(stub_server):
    server = stub_server()
    client = BaseRequestClient(server.url)

    assert client.post("thing", {"rid": "1"}) == {"ok": True}

    (req,) = server.requests
    assert (req["method"], req["path"]) == ("POST", "/base/thing")
    assert json.loads(req["body"]) == {"rid": "1"}


@pytest.mark.parametrize("status", [429, 500, 503])
def test_retries_get_and_post_on_429_and_5xx_then_succeeds(stub_server, status):
    server = stub_server([status, status])
    client = BaseRequestClient(server.url, retry=FAST_RETRY)

    assert client.get("thing") == {"ok": True}
    assert len(server.requests) == 3

    server.requests.clear()
    server.statuses = [status]
    assert client.post("thing", {}) == {"ok": True}
    assert len(server.requests) == 2


def test_gives_up_after_the_retries_are_exhausted(stub_server):
    server = stub_server([429] * 10)
    client = BaseRequestClient(server.url, retry=FAST_RETRY)

    with pytest.raises(RetryError):
        client.get("thing")

    assert len(server.requests) == 4  # first attempt + 3 retries


def test_does_not_retry_other_client_errors(stub_server):
    server = stub_server([404])
    client = BaseRequestClient(server.url, retry=FAST_RETRY)

    with pytest.raises(HTTPError):
        client.get("thing")

    assert len(server.requests) == 1


def test_uses_an_injected_session():
    class Session:
        headers: dict = {}

        def get(self, url, timeout=None):
            raise AssertionError("not called")

    session = Session()
    client = BaseRequestClient("https://example.com", session=session)  # type: ignore[arg-type]

    assert client.session is session


def test_absolute_urls_are_not_prefixed_with_the_base_url(stub_server):
    server = stub_server()
    client = BaseRequestClient("http://unused.invalid")

    assert client.get(url=f"{server.url}/full/path") == {"ok": True}

    (req,) = server.requests
    assert req["path"] == "/base/full/path"
