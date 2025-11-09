from pyrail_uk.api.referencedata import NationalRailReferenceDataRequestClient
from pyrail_uk.service.stations import find_crs_by_station_name, find_station_by_crs


class ReferenceDataClient:
    def __init__(self, token: str):
        self.client = NationalRailReferenceDataRequestClient(token)

    def get_station_name_by_crs(self, crs: str) -> str:
        """
        Returns the station name for a given CRS.

        ### Args

        crs : str
            The CRS code of the station you want to get the name of.

        ### Returns

        str: The name of the station that corresponds to the CRS given
        """
        stations = self.client.get_stations()
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
        stations = self.client.get_stations()
        return find_crs_by_station_name(stations, station_name)
