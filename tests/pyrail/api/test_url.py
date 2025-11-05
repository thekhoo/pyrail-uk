import pyrail.api.url as url


class Test_Get_URL:

    def test_should_return_url_with_dep_crs_only(self):
        actual_url = url.get_url("RDG")
        assert actual_url.endswith("/RDG")

    def test_should_return_url_with_dep_and_arr_crs(self):
        actual_url = url.get_url(dep_crs="RDG", arr_crs="OXF")
        assert actual_url.endswith("/RDG?filterCrs=OXF")

    def test_should_return_url_with_multiple_query_params(self):
        actual_url = url.get_url(dep_crs="RDG", arr_crs="OXF", timeoffset_mins=15)
        assert actual_url.endswith("/RDG?filterCrs=OXF&timeOffset=15")
