import logging

import requests as r
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)

DEFAULT_RETRY_STRATEGY = Retry(
    total=3,
    backoff_factor=1,
    status_forcelist=[429, 502, 503, 504],
    allowed_methods=["GET", "POST"],
)

MINUTES_IN_SECONDS = 60
DEFAULT_TIMEOUT_SECONDS = 5 * MINUTES_IN_SECONDS  # 5 minutes


class APIClient:
    def __init__(
        self,
        token: str,
        headers: dict | None = None,
        retry_strategy: Retry | None = None,
        timeout: float | None = None,
    ):
        self.token = token
        self.session = r.Session()
        self.timeout = timeout if timeout is not None else DEFAULT_TIMEOUT_SECONDS

        if headers:
            self.session.headers.update(headers)

        strategy = (
            retry_strategy if retry_strategy is not None else DEFAULT_RETRY_STRATEGY
        )
        # pyrefly: ignore [bad-argument-type]
        adapter = HTTPAdapter(max_retries=strategy)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)

    def get(self, url: str):
        logger.debug(f"Making GET request to URL: {url}")
        res = self.session.get(url=url, timeout=self.timeout)
        res.raise_for_status()
        return res.json()
