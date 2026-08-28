import logging

import requests as r
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)


class APIClient:

    def __init__(self, token: str, headers: dict | None = None, retry_strategy: Retry | None = None):
        self.token = token
        self.session = r.Session()

        if headers:
            self.session.headers.update(headers)

        if retry_strategy:
            adapter = HTTPAdapter(max_retries=retry_strategy)
            self.session.mount("https://", adapter)
            self.session.mount("http://", adapter)

    def get(self, url: str):
        logger.debug(f"Making GET request to URL: {url}")
        res = self.session.get(url=url)
        res.raise_for_status()
        return res.json()
