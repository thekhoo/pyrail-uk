import pytest

import pyrail_uk.service.departures as departures
from pyrail_uk.service.types import TrainService, TrainStatus

from .testutils import MockCallingPoint, MockDepartureData, MockTrainServiceData

CALLING_POINTS = [
    MockCallingPoint("OXF", "16:30"),
    MockCallingPoint("DID", "17:00"),
    MockCallingPoint("RDG", "17:30"),
    MockCallingPoint("PAD", "18:00"),
]

CANCELLED_TRAIN_SERVICE = (
    MockTrainServiceData()
    .set_cancelled()
    .set_cancel_reason("more trains than usual needing repairs")
    .set_subsequent_calling_points(CALLING_POINTS)
    .build()
)

ON_TIME_TRAIN_SERVICE = (
    MockTrainServiceData().set_etd("On time").set_std("16:30").set_subsequent_calling_points(CALLING_POINTS).build()
)

DELAYED_TRAIN_SERVICE = (
    MockTrainServiceData().set_etd("16:52").set_std("16:30").set_subsequent_calling_points(CALLING_POINTS).build()
)

DEPARTED_TRAIN_SERVICE = (
    MockTrainServiceData().clear_subsequent_calling_points().set_std("17:22").set_etd("On time").build()
)

DELAYED_DEPARTED_TRAIN_SERVICE = (
    MockTrainServiceData().clear_subsequent_calling_points().set_etd("17:32").set_std("17:22").build()
)


class Test_Simplify_Service_Info:

    # test general properties
    def test_returns_non_service_related_fields_correctly(self):
        res = departures.simplify_service_info(ON_TIME_TRAIN_SERVICE, "RDG")

        assert res.train_origin == "Oxford"
        assert res.train_origin_crs == "OXF"
        assert res.train_destination == "London Paddington"
        assert res.train_destination_crs == "PAD"
        assert res.operator == "Great Western Railway"
        assert res.operator_code == "GW"
        assert res.platform == "3"

    def test_when_train_is_cancelled(self):
        res = departures.simplify_service_info(CANCELLED_TRAIN_SERVICE, "RDG")
        assert res.status == TrainStatus.CANCELLED
        assert res.status_reason == "more trains than usual needing repairs"

    def test_when_train_is_on_time(self):
        res = departures.simplify_service_info(ON_TIME_TRAIN_SERVICE, "RDG")
        assert res.status == TrainStatus.ON_TIME
        assert res.status_reason == None
        assert res.etd == "On time"
        assert res.eta == "17:30"

    def test_when_train_is_delayed(self):
        res = departures.simplify_service_info(DELAYED_TRAIN_SERVICE, "RDG")
        assert res.status == TrainStatus.DELAYED
        assert res.status_reason == "No reason provided"

    def test_when_train_has_departed(self):
        res = departures.simplify_service_info(DEPARTED_TRAIN_SERVICE, "RDG")
        assert res.status == TrainStatus.DEPARTED
        assert res.status_reason == None
        assert res.atd == "17:22"

    def test_when_train_has_departed_late(self):
        res = departures.simplify_service_info(DELAYED_DEPARTED_TRAIN_SERVICE, "RDG")
        assert res.status == TrainStatus.DELAYED_DEPARTED
        assert res.status_reason == None
        assert res.atd == "17:32"


DEPARTURE_INFO_TRAINS_AVAILABLE = (
    MockDepartureData()
    .set_service_available()
    .set_train_services([ON_TIME_TRAIN_SERVICE, CANCELLED_TRAIN_SERVICE, DELAYED_DEPARTED_TRAIN_SERVICE])
    .set_count(3)
    .set_nrcc_messages(["Delayed due to storm eowyn"])
    .build()
)

DEPARTURE_INFO_NO_TRAINS = (
    MockDepartureData().set_service_available().set_count(0).set_nrcc_messages(["Delayed due to storm eowyn"]).build()
)


class Test_Simplify_Departures:

    def test_when_no_trains_available(self):
        res = departures.simplify_departures(DEPARTURE_INFO_NO_TRAINS)
        assert res.origin_crs == "RDG"
        assert res.origin == "Reading"
        assert res.destination_crs == "OXF"
        assert res.destination == "Oxford"
        assert res.warning_messages == ["Delayed due to storm eowyn"]
        assert res.services == []

    def test_when_trains_are_available(self):
        res = departures.simplify_departures(DEPARTURE_INFO_TRAINS_AVAILABLE)
        assert res.origin_crs == "RDG"
        assert res.origin == "Reading"
        assert res.destination_crs == "OXF"
        assert res.destination == "Oxford"
        assert res.warning_messages == ["Delayed due to storm eowyn"]
        assert res.num_services == 3
        assert len(res.services) == 3  # don't actually check the event, just make sure number is correct
