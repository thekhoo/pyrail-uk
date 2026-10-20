import threading
from datetime import datetime

import pytest

from pyrail_uk.clients.HistoricService import HistoricServiceClient


class FakeResponse:
    def __init__(self, payload: dict):
        self.payload = payload

    def raise_for_status(self) -> None:
        pass

    def json(self) -> dict:
        return self.payload


class FakeSession:
    """Stands in for requests.Session: one RID list per metrics call, details keyed by RID."""

    def __init__(self, metrics_rids: list[list[str]], details: dict[str, dict]):
        self.metrics_rids = iter(metrics_rids)
        self.details = details
        self.metrics_calls: list[dict] = []
        self.details_calls: list[str] = []

    def post(self, url: str, json: dict, timeout: float | None = None) -> FakeResponse:
        if url.endswith("serviceMetrics"):
            self.metrics_calls.append(json)
            return FakeResponse(metrics_response(next(self.metrics_rids)))
        self.details_calls.append(json["rid"])
        return FakeResponse(self.details[json["rid"]])


def metrics_response(rids: list[str]) -> dict:
    return {
        "header": {"from_location": "EUS", "to_location": "MAN"},
        "Services": [
            {
                "serviceAttributesMetrics": {
                    "origin_location": "EUS",
                    "destination_location": "MAN",
                    "gbtt_ptd": "0833",
                    "gbtt_pta": "1044",
                    "toc_code": "VT",
                    "matched_services": "1",
                    "rids": rids,
                },
                "Metrics": [],
            }
        ],
    }


def details_response(
    rid: str,
    service_date: str,
    dep: str = "0833",
    arr: str = "1044",
    actual_dep: str = "0833",
    actual_arr: str = "1059",
    reason: str = "",
    origin: str = "EUS",
) -> dict:
    return {
        "serviceAttributesDetails": {
            "date_of_service": service_date,
            "toc_code": "VT",
            "rid": rid,
            "locations": [
                {
                    "location": origin,
                    "gbtt_ptd": dep,
                    "gbtt_pta": "",
                    "actual_td": actual_dep,
                    "actual_ta": "",
                    "late_canc_reason": reason,
                },
                {
                    "location": "MAN",
                    "gbtt_ptd": "",
                    "gbtt_pta": arr,
                    "actual_td": "",
                    "actual_ta": actual_arr,
                    "late_canc_reason": reason,
                },
            ],
        }
    }


def make_client(session: FakeSession) -> HistoricServiceClient:
    return HistoricServiceClient(token="unused", session=session)  # type: ignore[arg-type]


def test_single_day_makes_one_metrics_call_with_day_type_and_window():
    session = FakeSession([["R1"]], {"R1": details_response("R1", "2026-08-29")})

    make_client(session).find_journeys(
        "EUS", "MAN", datetime(2026, 8, 29, 8, 0), datetime(2026, 8, 29, 9, 0)
    )

    assert session.metrics_calls == [
        {
            "from_loc": "EUS",
            "to_loc": "MAN",
            "from_time": "0800",
            "to_time": "0900",
            "from_date": "2026-08-29",
            "to_date": "2026-08-29",
            "days": "SATURDAY",
        }
    ]


def test_journey_has_scheduled_and_actual_times_and_delays():
    session = FakeSession([["R1"]], {"R1": details_response("R1", "2026-08-29")})

    (journey,) = make_client(session).find_journeys(
        "EUS", "MAN", datetime(2026, 8, 29, 8, 0), datetime(2026, 8, 29, 9, 0)
    )

    assert journey.rid == "R1"
    assert journey.toc_code == "VT"
    assert journey.origin == "EUS"
    assert journey.destination == "MAN"
    assert journey.scheduled_departure == datetime(2026, 8, 29, 8, 33)
    assert journey.actual_departure == datetime(2026, 8, 29, 8, 33)
    assert journey.scheduled_arrival == datetime(2026, 8, 29, 10, 44)
    assert journey.actual_arrival == datetime(2026, 8, 29, 10, 59)
    assert journey.departure_delay_mins == 0
    assert journey.arrival_delay_mins == 15
    assert journey.cancelled is False


def test_cancelled_journey_has_no_actuals_or_delays():
    cancelled = details_response(
        "R1", "2026-08-29", actual_dep="", actual_arr="", reason="522"
    )
    session = FakeSession([["R1"]], {"R1": cancelled})

    (journey,) = make_client(session).find_journeys(
        "EUS", "MAN", datetime(2026, 8, 29, 8, 0), datetime(2026, 8, 29, 9, 0)
    )

    assert journey.cancelled is True
    assert journey.reason_code == "522"
    assert journey.actual_departure is None
    assert journey.actual_arrival is None
    assert journey.departure_delay_mins is None
    assert journey.arrival_delay_mins is None


def test_arrival_after_midnight_rolls_to_next_day():
    overnight = details_response(
        "R1", "2026-08-29", dep="2350", arr="0120", actual_dep="2355", actual_arr="0130"
    )
    session = FakeSession([["R1"]], {"R1": overnight})

    (journey,) = make_client(session).find_journeys(
        "EUS", "MAN", datetime(2026, 8, 29, 23, 0), datetime(2026, 8, 29, 23, 59)
    )

    assert journey.scheduled_arrival == datetime(2026, 8, 30, 1, 20)
    assert journey.actual_arrival == datetime(2026, 8, 30, 1, 30)
    assert journey.arrival_delay_mins == 10


def test_journeys_outside_the_window_are_dropped():
    session = FakeSession(
        [["IN", "OUT"]],
        {
            "IN": details_response("IN", "2026-08-29", dep="0833"),
            "OUT": details_response("OUT", "2026-08-29", dep="0933"),
        },
    )

    journeys = make_client(session).find_journeys(
        "EUS", "MAN", datetime(2026, 8, 29, 8, 0), datetime(2026, 8, 29, 9, 0)
    )

    assert [j.rid for j in journeys] == ["IN"]


def test_multi_day_range_splits_by_day_type_with_exact_edge_windows():
    session = FakeSession(
        [["FRI"], ["SAT"], ["SUN"], ["MON"]],
        {
            "FRI": details_response("FRI", "2026-08-28", dep="1033"),
            "SAT": details_response("SAT", "2026-08-29"),
            "SUN": details_response("SUN", "2026-08-30"),
            "MON": details_response("MON", "2026-08-31", dep="0833"),
        },
    )

    journeys = make_client(session).find_journeys(
        "EUS", "MAN", datetime(2026, 8, 28, 10, 0), datetime(2026, 8, 31, 12, 0)
    )

    windows = [
        (c["days"], c["from_date"], c["to_date"], c["from_time"], c["to_time"])
        for c in session.metrics_calls
    ]
    assert windows == [
        ("WEEKDAY", "2026-08-28", "2026-08-28", "1000", "2359"),
        ("SATURDAY", "2026-08-29", "2026-08-29", "0000", "2359"),
        ("SUNDAY", "2026-08-30", "2026-08-30", "0000", "2359"),
        ("WEEKDAY", "2026-08-31", "2026-08-31", "0000", "1200"),
    ]
    assert [j.rid for j in journeys] == ["FRI", "SAT", "SUN", "MON"]


def test_middle_weekdays_share_one_call():
    session = FakeSession([[], [], []], {})

    make_client(session).find_journeys(
        "EUS", "MAN", datetime(2026, 8, 17, 8, 0), datetime(2026, 8, 21, 18, 0)
    )

    middle = session.metrics_calls[1]
    assert len(session.metrics_calls) == 3
    assert (middle["days"], middle["from_date"], middle["to_date"]) == (
        "WEEKDAY",
        "2026-08-18",
        "2026-08-20",
    )


def test_duplicate_rids_are_fetched_once():
    session = FakeSession(
        [["R1"], ["R1"]], {"R1": details_response("R1", "2026-08-29")}
    )

    journeys = make_client(session).find_journeys(
        "EUS", "MAN", datetime(2026, 8, 28, 8, 0), datetime(2026, 8, 29, 9, 0)
    )

    assert session.details_calls == ["R1"]
    assert len(journeys) == 1


def test_services_that_do_not_call_at_the_origin_are_skipped():
    session = FakeSession(
        [["R1"]], {"R1": details_response("R1", "2026-08-29", origin="WFJ")}
    )

    journeys = make_client(session).find_journeys(
        "EUS", "MAN", datetime(2026, 8, 29, 8, 0), datetime(2026, 8, 29, 9, 0)
    )

    assert journeys == []


def test_results_are_sorted_by_scheduled_departure():
    session = FakeSession(
        [["LATE", "EARLY"]],
        {
            "LATE": details_response("LATE", "2026-08-29", dep="0853"),
            "EARLY": details_response("EARLY", "2026-08-29", dep="0813"),
        },
    )

    journeys = make_client(session).find_journeys(
        "EUS", "MAN", datetime(2026, 8, 29, 8, 0), datetime(2026, 8, 29, 9, 0)
    )

    assert [j.rid for j in journeys] == ["EARLY", "LATE"]


def test_threads_are_off_by_default():
    session = FakeSession([["R1"]], {"R1": details_response("R1", "2026-08-29")})
    seen: set[str] = set()
    original = session.post

    def post(url, json, timeout=None):
        seen.add(threading.current_thread().name)
        return original(url, json, timeout)

    session.post = post  # type: ignore[method-assign]
    make_client(session).find_journeys(
        "EUS", "MAN", datetime(2026, 8, 29, 8, 0), datetime(2026, 8, 29, 9, 0)
    )

    assert seen == {threading.current_thread().name}


@pytest.mark.parametrize("use_threads", [True, False])
def test_threaded_and_sequential_fetch_give_the_same_journeys(use_threads: bool):
    rids = [f"R{n}" for n in range(8)]
    session = FakeSession(
        [rids],
        {
            rid: details_response(rid, "2026-08-29", dep=f"08{n:02d}")
            for n, rid in enumerate(rids)
        },
    )

    journeys = make_client(session).find_journeys(
        "EUS",
        "MAN",
        datetime(2026, 8, 29, 8, 0),
        datetime(2026, 8, 29, 9, 0),
        use_threads=use_threads,
    )

    assert [j.rid for j in journeys] == rids
    assert sorted(session.details_calls) == rids


def test_start_after_end_raises():
    client = make_client(FakeSession([], {}))

    with pytest.raises(ValueError):
        client.find_journeys(
            "EUS", "MAN", datetime(2026, 8, 29, 9, 0), datetime(2026, 8, 29, 8, 0)
        )
