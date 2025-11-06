import logging
import typing as t

from cachetools import TTLCache
from urllib3.util.retry import Retry

from .client import APIClient
from .types import StationCRSTypeDef, StationListResponseTypeDef
from .url import get_station_list_url

logger = logging.getLogger(__name__)


class NationalRailReferenceDataRequestClient(APIClient):

    def __init__(self, token: str, retry_strategy: t.Optional[Retry] = None, cache_ttl_seconds: t.Optional[int] = 300):
        super().__init__(
            token,
            headers={"x-apikey": token, "Accept": "*/*", "User-Agent": "pyrail-sdk", "Origin": "localhost"},
            retry_strategy=retry_strategy,
        )

        self.cache = TTLCache(maxsize=1, ttl=float(cache_ttl_seconds))

    def get_stations(self) -> list[StationCRSTypeDef]:
        if "stations" in self.cache:
            logger.debug("stations data found within the cache, not requesting!")
            return self.cache["stations"]

        url = get_station_list_url()
        res: StationListResponseTypeDef = self.get(url)

        stations = res.get("StationList", [])
        self.cache["stations"] = stations
        return stations
