import pyrail_uk.utils.array as array

from ..api.types import StationCRSTypeDef
from ..core.exceptions import CRSNotFoundException, StationNotFoundException


def find_station_by_crs(stations: list[StationCRSTypeDef], crs: str) -> str:
    station = array.findone(stations, lambda s: s["crs"] == crs.upper())
    if not station:
        raise CRSNotFoundException(f"{crs} is not a valid CRS")

    return station.get("Value")


def find_crs_by_station_name(stations: list[StationCRSTypeDef], station_name: str) -> str:
    station = array.findone(stations, lambda s: s["Value"].lower() == station_name.lower())

    if not station:
        raise StationNotFoundException(f"{station_name} is not a valid station, please check your spelling!")

    return station.get("crs")
