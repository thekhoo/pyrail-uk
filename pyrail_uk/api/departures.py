import logging

from urllib3.util.retry import Retry

from .client import APIClient
from .types import DepBoardWithDetailsResponseTypeDef
from .url import get_departure_board_url

logger = logging.getLogger(__name__)


class NationalRailAPIRequestClient(APIClient):

    def __init__(self, token: str, retry_strategy: Retry | None = None):
        super().__init__(
            token,
            headers={"x-apikey": token, "Accept": "*/*", "User-Agent": "pyrail-sdk", "Origin": "localhost"},
            retry_strategy=retry_strategy,
        )

    def get_departures(
        self, dep_crs: str, arr_crs: str | None = None, timeoffset_mins: int = 0, timewindow_mins: int = 120
    ) -> DepBoardWithDetailsResponseTypeDef:
        url = get_departure_board_url(
            dep_crs, arr_crs=arr_crs, timeoffset_mins=timeoffset_mins, timewindow_mins=timewindow_mins
        )
        return self.get(url=url)
