import typing as t

from pyrail_uk.api.departures import NationalRailAPIRequestClient
from pyrail_uk.service.departures import simplify_departures


class DepartureBoardClient:
    def __init__(self, token: str):
        self.client = NationalRailAPIRequestClient(token)

    def get_trains(
        self,
        dep_crs: str,
        arr_crs: t.Optional[str] = None,
        timeoffset_mins: int = 0,
        timewindow_mins: int = 120,
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

        ### Returns

        DepartureServiceResponse : The parsed version of the response by the SDK

        """
        res = self.client.get_departures(
            dep_crs, arr_crs, timeoffset_mins, timewindow_mins
        )
        return simplify_departures(departures_data=res)

    def get_trains_raw(
        self,
        dep_crs: str,
        arr_crs: t.Optional[str] = None,
        timeoffset_mins: int = 0,
        timewindow_mins: int = 120,
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

        ### Returns

        DepBoardWithDetailsResponseTypeDef : The raw response from national rail
        """
        return self.client.get_departures(
            dep_crs, arr_crs, timeoffset_mins, timewindow_mins
        )
