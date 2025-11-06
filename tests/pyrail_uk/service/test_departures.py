import pytest

import pyrail_uk.service.departures as departures
from pyrail_uk.service.types import TrainStatus

from .testutils import MockCallingPoint, MockTrainServiceData

CALLING_POINTS = [
    MockCallingPoint("OXF", "16:30"),
    MockCallingPoint("DID", "17:00"),
    MockCallingPoint("RDG", "17:30"),
    MockCallingPoint("PAD", "18:00"),
]


class Test_Get_Train_Status_And_Reason:

    class Test_When_Trains_Are_Cancelled:

        def test_should_return_cancel_status_with_reason_when_available(self):
            payload = (
                MockTrainServiceData()
                .set_cancelled()
                .set_cancel_reason("Signal failure")
                .set_subsequent_calling_points(CALLING_POINTS)
                .build()
            )
            status, reason = departures.get_train_status_and_reason(payload)

            assert status == TrainStatus.CANCELLED
            assert reason == "Signal failure"

        def test_should_return_cancel_status_with_default_reason_when_not_provided(self):
            payload = MockTrainServiceData().set_cancelled().set_subsequent_calling_points(CALLING_POINTS).build()
            status, reason = departures.get_train_status_and_reason(payload)

            assert status == TrainStatus.CANCELLED
            assert isinstance(reason, str)

        # we need this test because the absence of subsequent calling points
        # suggests that the train has already departed
        def test_should_return_cancel_when_no_subsequent_calling_points_and_cancelled(self):
            payload = (
                MockTrainServiceData()
                .set_cancelled()
                .set_cancel_reason("Signal failure")
                .clear_subsequent_calling_points()
                .build()
            )
            status, reason = departures.get_train_status_and_reason(payload)

            assert status == TrainStatus.CANCELLED
            assert reason == "Signal failure"

    class Test_When_ETD_Is_On_Time:

        def test_should_return_on_time_status_with_no_reason(self):
            payload = MockTrainServiceData().set_subsequent_calling_points(CALLING_POINTS).set_etd("On time").build()
            status, reason = departures.get_train_status_and_reason(payload)

            assert status == TrainStatus.ON_TIME
            assert reason is None

    class Test_When_ETD_Is_Not_On_Time:

        @pytest.mark.parametrize("etd", ["18:31", "Delayed"])
        def test_should_return_delayed_status_with_delay_reason_when_available(self, etd):
            payload = (
                MockTrainServiceData()
                .set_subsequent_calling_points(CALLING_POINTS)
                .set_etd(etd)
                .set_delay_reason("trespassers on track")
                .build()
            )
            status, reason = departures.get_train_status_and_reason(payload)

            assert status == TrainStatus.DELAYED
            assert reason == "trespassers on track"

        def test_should_return_delayed_status_with_default_reason_when_not_provided(self):
            payload = MockTrainServiceData().set_subsequent_calling_points(CALLING_POINTS).set_etd("Delayed").build()
            status, reason = departures.get_train_status_and_reason(payload)

            assert status == TrainStatus.DELAYED
            assert reason == "No reason provided"

    class Test_When_There_Are_No_Subsequent_Calling_Points:

        def test_should_return_departed_status_with_no_reason_if_etd_on_time(self):
            payload = MockTrainServiceData().clear_subsequent_calling_points().set_etd("On time").build()
            status, reason = departures.get_train_status_and_reason(payload)

            assert status == TrainStatus.DEPARTED
            assert reason is None

        def test_should_return_delayed_departed_status_with_no_reason_if_etd_not_on_time(self):
            payload = MockTrainServiceData().clear_subsequent_calling_points().set_etd("18:31").build()
            status, reason = departures.get_train_status_and_reason(payload)

            assert status == TrainStatus.DELAYED_DEPARTED
            assert reason is None


class Test_Get_ETA:

    def test_should_return_none_if_no_subsequent_calling_points(self):
        payload = MockTrainServiceData().clear_subsequent_calling_points().build()
        eta = departures.get_eta(payload, "RDG")

        assert eta is None

    def test_should_return_none_if_target_crs_not_found(self):
        crs = "LHR"
        payload = MockTrainServiceData().set_subsequent_calling_points(CALLING_POINTS).build()
        eta = departures.get_eta(payload, crs)

        assert eta is None

    def test_should_return_et_for_target_crs(self):
        crs = "RDG"
        payload = MockTrainServiceData().set_subsequent_calling_points(CALLING_POINTS).build()
        eta = departures.get_eta(payload, crs)

        assert eta == "17:30"


class Test_Get_ATD:

    @pytest.mark.parametrize("train_status", [TrainStatus.ON_TIME, TrainStatus.DELAYED, TrainStatus.CANCELLED])
    def test_should_return_none_if_train_not_departed(self, train_status):
        payload = MockTrainServiceData().build()
        atd = departures.get_atd(payload, train_status)
        assert atd is None

    def test_should_return_std_if_train_departed_on_time(self):
        payload = MockTrainServiceData().set_etd("On time").set_std("17:20").build()
        atd = departures.get_atd(payload, TrainStatus.DEPARTED)
        assert atd == "17:20"

    def test_should_return_etd_if_train_departed_delayed(self):
        payload = MockTrainServiceData().set_etd("17:48").set_std("17:20").build()
        atd = departures.get_atd(payload, TrainStatus.DELAYED_DEPARTED)
        assert atd == "17:48"

    def test_should_return_std_if_train_departed_delayed_but_etd_on_time(self):
        payload = MockTrainServiceData().set_etd("On time").set_std("17:20").build()
        atd = departures.get_atd(payload, TrainStatus.DELAYED_DEPARTED)
        assert atd == "17:20"
