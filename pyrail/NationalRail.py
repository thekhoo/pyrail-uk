import typing as t

from pyrail.api.departures import NationalRailAPIRequestClient


class NationalRailClient:

    def __init__(self, token: str):
        self.token = token
        self.dep_client = NationalRailAPIRequestClient(token)

    def get_trains(
        self, dep_crs: str, arr_crs: t.Optional[str] = None, timeoffset_mins: int = 0, timewindow_mins: int = 120
    ):
        res = self.dep_client.get_departures(dep_crs, arr_crs, timeoffset_mins, timewindow_mins)
        return res
