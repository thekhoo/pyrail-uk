import logging
from typing import Any

from requests import Session
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

logger = logging.getLogger(__name__)

DEFAULT_RETRY_STRATEGY = Retry(
    total=3,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["GET", "POST"],
)


class BaseRequestClient:
    """
    Shared HTTP layer for the API clients: a base URL, default headers, a timeout and a
    session that retries 429 and 5xx responses with exponential backoff.

    ### Args

    base_url : str
        Prepended to every relative request URL; absolute URLs are used as given.

    headers : dict | None
        Default headers (e.g. the API key) sent with every request.

    retry : Retry | None
        Overrides `DEFAULT_RETRY_STRATEGY`.

    timeout : float | None
        Seconds before a request times out. `None` waits indefinitely, which the Rail Data
        Marketplace needs for slow responses.

    session : Session | None
        An existing session to use instead of building one; `headers` and `retry` are then
        ignored.
    """

    def __init__(
        self,
        base_url: str,
        headers: dict | None = None,
        retry: Retry | None = None,
        timeout: float | None = None,
        session: Session | None = None,
    ):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.session = session or self._build_session(headers, retry)

    @staticmethod
    def _build_session(headers: dict | None, retry: Retry | None) -> Session:
        logger.debug("Initializing new session")
        session = Session()
        if headers:
            session.headers.update(headers)

        strategy = retry if retry is not None else DEFAULT_RETRY_STRATEGY
        # pyrefly: ignore [bad-argument-type]
        adapter = HTTPAdapter(max_retries=strategy)
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        return session

    def _full_url(self, url: str) -> str:
        """Absolute URLs pass through; anything else is joined onto the base URL."""
        if url.startswith(("http://", "https://")):
            return url
        return f"{self.base_url}/{url.lstrip('/')}"

    def get(self, url: str, **kwargs) -> Any:
        full_url = self._full_url(url)
        logger.debug("GET %s", full_url)
        response = self.session.get(full_url, timeout=self.timeout, **kwargs)
        response.raise_for_status()
        return response.json()

    def post(self, url: str, body: dict, **kwargs) -> Any:
        full_url = self._full_url(url)
        logger.debug("POST %s", full_url)
        response = self.session.post(
            full_url, json=body, timeout=self.timeout, **kwargs
        )
        response.raise_for_status()
        return response.json()
