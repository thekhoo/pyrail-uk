import typing as t

from pyrail_uk.api.departures import NationalRailAPIRequestClient


class NationalRailClient:

    def __init__(self, departure_board_token: str):
        self.departure_board_token = departure_board_token
        self.dep_client = NationalRailAPIRequestClient(departure_board_token)

    def get_trains(
        self,
        dep_crs: str,
        arr_crs: t.Optional[str] = None,
        timeoffset_mins: int = 0,
        timewindow_mins: int = 120,
        simplified: bool = False,
    ):
        res = self.dep_client.get_departures(dep_crs, arr_crs, timeoffset_mins, timewindow_mins)

        # allow users the option to get the full response
        if not simplified:
            return res
