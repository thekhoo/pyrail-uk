import json
from datetime import date, time
from pathlib import Path

import pytest
from pydantic import ValidationError

from pyrail_uk.clients.HistoricService import (
    ServiceDetailsResponse,
    ServiceMetricsResponse,
)

FIXTURES = Path(__file__).parents[2]


def load(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text())


def test_service_metrics_response_validates_fixture():
    res = ServiceMetricsResponse.model_validate(load("historic_service_response.json"))

    assert res.header.from_location == "EUS"
    assert res.header.to_location == "MAN"

    first = res.services[0]
    attrs = first.service_attributes_metrics
    assert attrs.origin_location == "EUS"
    assert attrs.destination_location == "MAN"
    assert attrs.gbtt_ptd == time(8, 13)
    assert attrs.gbtt_pta == time(10, 19)
    assert attrs.toc_code == "VT"
    assert attrs.matched_services == 1
    assert attrs.rids == ["202608298733782"]

    metric = first.metrics[0]
    assert metric.tolerance_value == 0
    assert metric.num_not_tolerance == 1
    assert metric.num_tolerance == 0
    assert metric.percent_tolerance == 0.0
    assert metric.global_tolerance is True


def test_service_metrics_response_rejects_missing_field():
    data = load("historic_service_response.json")
    del data["header"]

    with pytest.raises(ValidationError):
        ServiceMetricsResponse.model_validate(data)


def test_service_details_delayed_service():
    res = ServiceDetailsResponse.model_validate(
        load("historic_service_details_delayed_response.json")
    )

    details = res.service_attributes_details
    assert details.date_of_service == date(2026, 8, 29)
    assert details.toc_code == "VT"
    assert details.rid == "202608298733695"

    origin, *_, destination = details.locations
    # the origin has no arrival and the destination has no departure
    assert origin.location == "EUS"
    assert origin.gbtt_pta is None
    assert origin.actual_ta is None
    assert origin.gbtt_ptd == time(8, 33)
    assert origin.actual_td == time(8, 33)
    assert origin.late_canc_reason is None

    assert destination.location == "MAN"
    assert destination.gbtt_ptd is None
    assert destination.actual_td is None
    assert destination.gbtt_pta == time(10, 44)
    assert destination.actual_ta == time(10, 59)
    assert destination.late_canc_reason == "895"


def test_service_details_cancelled_service_has_no_actuals():
    res = ServiceDetailsResponse.model_validate(
        load("historic_service_details_cancelled_response.json")
    )

    locations = res.service_attributes_details.locations
    assert all(loc.actual_td is None and loc.actual_ta is None for loc in locations)
    assert all(loc.late_canc_reason == "522" for loc in locations)


def test_service_details_rejects_malformed_time():
    data = load("historic_service_details_delayed_response.json")
    data["serviceAttributesDetails"]["locations"][0]["gbtt_ptd"] = "not-a-time"

    with pytest.raises(ValidationError):
        ServiceDetailsResponse.model_validate(data)
