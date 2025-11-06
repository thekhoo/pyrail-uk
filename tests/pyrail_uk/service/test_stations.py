import pytest

import pyrail_uk.core.exceptions as ex
import pyrail_uk.service.stations as st

STATIONS = [
    {"crs": "RDG", "Value": "Reading"},
    {"crs": "OXF", "Value": "Oxford"},
]


class Test_Find_Station_By_CRS:

    def test_should_raise_CRSNotFoundException_when_no_crs_found(self):
        with pytest.raises(ex.CRSNotFoundException):
            st.find_station_by_crs(STATIONS, "NAN")

    @pytest.mark.parametrize("crs", ["rdg", "rDg", "RDG", "Rdg"])
    def test_should_return_station_name_when_valid_crs_given(self, crs):
        assert st.find_station_by_crs(STATIONS, crs) == "Reading"


class Test_Find_CRS_By_Station_Name:

    def test_should_raise_StationNotFoundException_when_no_station_name_found(self):
        with pytest.raises(ex.StationNotFoundException):
            st.find_crs_by_station_name(STATIONS, "NotAStation")

    @pytest.mark.parametrize("station_name", ["Oxford", "OXFORD", "oxford", "OxFoRd"])
    def test_should_return_crs_when_valid_station_name_given(self, station_name):
        assert st.find_crs_by_station_name(STATIONS, station_name) == "OXF"
