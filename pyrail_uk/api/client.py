from urllib3.util.retry import Retry

from pyrail_uk.utils.request import BaseRequestClient

MINUTES_IN_SECONDS = 60
DEFAULT_TIMEOUT_SECONDS = 5 * MINUTES_IN_SECONDS  # 5 minutes


class APIClient(BaseRequestClient):
    """Client for APIs addressed by full URL; adds a default timeout to `BaseRequestClient`."""

    def __init__(
        self,
        token: str,
        headers: dict | None = None,
        retry_strategy: Retry | None = None,
        timeout: float | None = None,
    ):
        super().__init__(
            "",
            headers=headers,
            retry=retry_strategy,
            timeout=timeout if timeout is not None else DEFAULT_TIMEOUT_SECONDS,
        )
        self.token = token
