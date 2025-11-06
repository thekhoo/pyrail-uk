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
        """
        Returns the available trains for the specified station CRS codes and time offset windows.

        ### Args

        dep_crs : str
            The CRS code of the station that the train will depart from.

        arr_crs : Optional[str] = None
            The CRS code of the statoin that the train will arrive at. If none is given, all trains from
            the departure CRS is returned.

        timeoffset_mins : int = 0
            The offset in minutes from the current time to search for train journeys.
            Valid values are -120 < x < 120

        timeoffset_window : int = 120
            the window in minutes from the current time + offset that journeys are returned for

        simplified : bool = False
            If `True`, will return an SDK parsed version of the train journeys. Leave as `False` to get the raw
            output from National Rail.

        ### Returns

        DepBoardWithDetailsResponseTypeDef : The raw response from national rail

        DepartureServiceResponse : The parsed version of the response by the SDK

        """
        res = self.dep_client.get_departures(dep_crs, arr_crs, timeoffset_mins, timewindow_mins)

        # allow users the option to get the full response
        if not simplified:
            return res

        return simplify_departures(departures_data=res)

    def get_station_name_by_crs(self, crs: str) -> str:
        """
        Returns the station name for a given CRS.

        ### Args

        crs : str
            The CRS code of the station you want to get the name of.

        ### Returns

        str: The name of the station that corresponds to the CRS given
        """
        stations = self.ref_data_client.get_stations()
        return find_station_by_crs(stations, crs)

    def get_crs_by_station_name(self, station_name: str) -> str:
        """
        Returns the CRS for a given station name.

        ### Args

        station_name : str
            The name of the station you want to get the CRS for.

        ### Returns

        str: The CRS of the station that corresponds to the station name given.
        """
        stations = self.ref_data_client.get_stations()
        return find_crs_by_station_name(stations, station_name)
