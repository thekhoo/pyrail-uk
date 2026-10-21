import pytest

from pyrail_uk.api.client import DEFAULT_TIMEOUT_SECONDS, APIClient
from pyrail_uk.utils.request import DEFAULT_RETRY_STRATEGY, BaseRequestClient


@pytest.mark.parametrize("method", ["GET", "POST"])
@pytest.mark.parametrize("status", [429, 500, 502, 503, 504])
def test_default_retry_strategy_retries_transient_failures(method: str, status: int):
    assert DEFAULT_RETRY_STRATEGY.is_retry(method, status)


def test_default_retry_strategy_does_not_retry_client_errors():
    assert not DEFAULT_RETRY_STRATEGY.is_retry("POST", 400)


def test_api_client_is_built_on_the_shared_request_client():
    assert issubclass(APIClient, BaseRequestClient)


def test_api_client_defaults_to_a_five_minute_timeout():
    assert APIClient("token").timeout == DEFAULT_TIMEOUT_SECONDS == 300
    assert APIClient("token", timeout=7).timeout == 7


def test_api_client_sends_headers_and_gets_full_urls():
    class Session:
        headers: dict = {}

        def get(self, url, timeout=None):
            self.called = (url, timeout)
            return type(
                "R",
                (),
                {"raise_for_status": lambda s: None, "json": lambda s: {"a": 1}},
            )()

    client = APIClient("token", headers={"x-apikey": "token"})
    client.session = Session()  # type: ignore[assignment]

    assert client.get(url="https://example.com/x?y=1") == {"a": 1}
    assert client.session.called == ("https://example.com/x?y=1", 300)  # type: ignore[attr-defined]
