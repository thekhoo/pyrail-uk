import typing as t

DEPARTURE_URL = (
    "https://api1.raildata.org.uk/1010-live-departure-board-dep1_2/LDBWS/api/20220120/GetDepBoardWithDetails"
)

STATION_LIST_URL = "https://api1.raildata.org.uk/1010-reference-data1_0/LDBSVWS/api/ref/20211101/GetStationList"

# NOTE: This is an alternate URL that can be used for less verbose details
# it also has carriage information but weirdly, only for Elizabeth Line trains...
# DEPARTURE_URL = "https://api1.raildata.org.uk/1010-live-departure-board-dep1_2/LDBWS/api/20220120/GetDepartureBoard"


def get_departure_board_url(
    dep_crs: str,
    arr_crs: t.Optional[str] = None,
    timeoffset_mins: t.Optional[int] = None,
    timewindow_mins: t.Optional[int] = None,
):
    url = f"{DEPARTURE_URL}/{dep_crs}"
    query_params = []

    if arr_crs:
        query_params.append(f"filterCrs={arr_crs}")

    if timeoffset_mins:
        query_params.append(f"timeOffset={timeoffset_mins}")

    if timewindow_mins:
        query_params.append(f"timeWindow={timewindow_mins}")

    if query_params:
        url += "?" + "&".join(query_params)

    return url


def get_station_list_url(version: int = 1):
    return f"{STATION_LIST_URL}/{version}"
