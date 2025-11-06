import typing as t

from pyrail_uk.api.departures import NationalRailAPIRequestClient
from pyrail_uk.api.referencedata import NationalRailReferenceDataRequestClient

from .service.departures import simplify_departures
from .service.stations import find_crs_by_station_name, find_station_by_crs


class NationalRailClient:

    def __init__(self, departure_board_token: str, reference_data_token: str):
        self.dep_client = NationalRailAPIRequestClient(departure_board_token)
        self.ref_data_client = NationalRailReferenceDataRequestClient(reference_data_token)

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

        return simplify_departures(departures_data=res)

    def get_station_name_by_crs(self, crs: str) -> str:
        stations = self.ref_data_client.get_stations()
        return find_station_by_crs(stations, crs)

    def get_crs_by_station_name(self, station_name: str) -> str:
        stations = self.ref_data_client.get_stations()
        return find_crs_by_station_name(stations, station_name)
