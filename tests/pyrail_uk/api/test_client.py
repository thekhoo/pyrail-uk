import pytest

from pyrail_uk.api.client import DEFAULT_RETRY_STRATEGY


@pytest.mark.parametrize("method", ["GET", "POST"])
@pytest.mark.parametrize("status", [429, 502, 503, 504])
def test_default_retry_strategy_retries_transient_failures(method: str, status: int):
    assert DEFAULT_RETRY_STRATEGY.is_retry(method, status)


def test_default_retry_strategy_does_not_retry_client_errors():
    assert not DEFAULT_RETRY_STRATEGY.is_retry("POST", 400)
