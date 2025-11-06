import logging
import typing as t

import requests as r
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from .types import DepBoardWithDetailsResponseTypeDef
from .url import get_url

logger = logging.getLogger(__name__)


class APIClient:

    def __init__(self, token: str, headers: t.Optional[dict] = None, retry_strategy: t.Optional[Retry] = None):
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


class NationalRailAPIRequestClient(APIClient):

    def __init__(self, token: str, retry_strategy: t.Optional[Retry] = None):
        super().__init__(
            token,
            headers={"x-apikey": token, "Accept": "*/*", "User-Agent": "pyrail-sdk", "Origin": "localhost"},
            retry_strategy=retry_strategy,
        )

    def get_departures(
        self, dep_crs: str, arr_crs: t.Optional[str] = None, timeoffset_mins: int = 0, timewindow_mins: int = 120
    ) -> DepBoardWithDetailsResponseTypeDef:
        url = get_url(dep_crs, arr_crs=arr_crs, timeoffset_mins=timeoffset_mins, timewindow_mins=timewindow_mins)
        return self.get(url=url)
