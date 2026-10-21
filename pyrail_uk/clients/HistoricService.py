import logging
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, time, timedelta
from enum import StrEnum
from typing import Annotated, Any

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field
from requests import Session
from urllib3.util import Retry

from pyrail_uk.utils.request import BaseRequestClient

logger = logging.getLogger(__name__)


class HistoricServiceDayType(StrEnum):
    WEEKDAY = "WEEKDAY"
    SATURDAY = "SATURDAY"
    SUNDAY = "SUNDAY"


def _parse_hhmm(value: Any) -> Any:
    """Parse the API's "HHMM" strings; empty strings (no call at that stop) become None."""
    if value == "":
        return None
    if isinstance(value, str):
        return time(int(value[:2]), int(value[2:]))
    return value


def _empty_to_none(value: Any) -> Any:
    return None if value == "" else value


HHMM = Annotated[time, BeforeValidator(_parse_hhmm)]
OptionalHHMM = Annotated[time | None, BeforeValidator(_parse_hhmm)]
OptionalStr = Annotated[str | None, BeforeValidator(_empty_to_none)]


class _HistoricModel(BaseModel):
    """Base for HSP responses: accepts the API's camelCase/PascalCase aliases or field names."""

    model_config = ConfigDict(populate_by_name=True, frozen=True)


class ServiceMetricsHeader(_HistoricModel):
    from_location: str  # CRS code
    to_location: str  # CRS code


class ServiceAttributesMetrics(_HistoricModel):
    origin_location: str  # CRS code
    destination_location: str  # CRS code
    gbtt_ptd: HHMM  # scheduled public departure
    gbtt_pta: HHMM  # scheduled public arrival
    toc_code: str
    matched_services: int
    rids: list[str]


class ServiceMetric(_HistoricModel):
    tolerance_value: int  # minutes
    num_not_tolerance: int
    num_tolerance: int
    percent_tolerance: float
    global_tolerance: bool


class ServiceMetrics(_HistoricModel):
    service_attributes_metrics: ServiceAttributesMetrics = Field(
        alias="serviceAttributesMetrics"
    )
    metrics: list[ServiceMetric] = Field(alias="Metrics")


class ServiceMetricsResponse(_HistoricModel):
    header: ServiceMetricsHeader
    services: list[ServiceMetrics] = Field(alias="Services")


class ServiceDetailsLocation(_HistoricModel):
    location: str  # CRS code
    gbtt_ptd: OptionalHHMM  # None at the destination
    gbtt_pta: OptionalHHMM  # None at the origin
    actual_td: OptionalHHMM  # None at the destination, or if the call was cancelled
    actual_ta: OptionalHHMM  # None at the origin, or if the call was cancelled
    late_canc_reason: OptionalStr  # delay/cancellation reason code


class ServiceAttributesDetails(_HistoricModel):
    date_of_service: date
    toc_code: str
    rid: str
    locations: list[ServiceDetailsLocation]


class ServiceDetailsResponse(_HistoricModel):
    service_attributes_details: ServiceAttributesDetails = Field(
        alias="serviceAttributesDetails"
    )


class HistoricJourney(_HistoricModel):
    """One historic train journey between two stations, combining HSP metrics and details."""

    rid: str
    toc_code: str
    origin: str  # CRS code
    destination: str  # CRS code
    scheduled_departure: datetime
    scheduled_arrival: datetime
    actual_departure: datetime | None  # None if cancelled
    actual_arrival: datetime | None  # None if cancelled
    reason_code: OptionalStr = None  # delay/cancellation reason code

    @property
    def cancelled(self) -> bool:
        return self.actual_departure is None and self.actual_arrival is None

    @property
    def departure_delay_mins(self) -> int | None:
        return _delay_mins(self.scheduled_departure, self.actual_departure)

    @property
    def arrival_delay_mins(self) -> int | None:
        return _delay_mins(self.scheduled_arrival, self.actual_arrival)


def _delay_mins(scheduled: datetime, actual: datetime | None) -> int | None:
    return None if actual is None else int((actual - scheduled).total_seconds() // 60)


def _at_or_after(t: time, anchor: datetime) -> datetime:
    """The first datetime at `t` that is not before `anchor` (rolls over midnight)."""
    candidate = datetime.combine(anchor.date(), t)
    return candidate if candidate >= anchor else candidate + timedelta(days=1)


def _nearest_to(t: time, anchor: datetime) -> datetime:
    """The datetime at `t` closest to `anchor`, for actual times that may straddle midnight."""
    day = anchor.date()
    candidates = (datetime.combine(day + timedelta(days=d), t) for d in (-1, 0, 1))
    return min(candidates, key=lambda c: abs(c - anchor))


def _day_type(d: date) -> HistoricServiceDayType:
    if d.weekday() == 5:
        return HistoricServiceDayType.SATURDAY
    if d.weekday() == 6:
        return HistoricServiceDayType.SUNDAY
    return HistoricServiceDayType.WEEKDAY


_START_OF_DAY = time(0, 0)
_END_OF_DAY = time(23, 59)


def _metrics_queries(
    start_dt: datetime, end_dt: datetime
) -> list[tuple[datetime, datetime, HistoricServiceDayType]]:
    """
    Split a datetime range into the fewest serviceMetrics queries that cover it exactly.

    The API applies one daily time-of-day window and one day type to a date range, so the
    first and last days get their own query (with the real start/end times) and the days in
    between are whole days, grouped by day type.
    """
    first, last = start_dt.date(), end_dt.date()
    if first == last:
        return [(start_dt, end_dt, _day_type(first))]

    queries = [
        (start_dt, datetime.combine(first, _END_OF_DAY), _day_type(first)),
    ]
    middle = [first + timedelta(days=n) for n in range(1, (last - first).days)]
    for day_type in HistoricServiceDayType:
        days = [d for d in middle if _day_type(d) == day_type]
        if days:
            queries.append(
                (
                    datetime.combine(days[0], _START_OF_DAY),
                    datetime.combine(days[-1], _END_OF_DAY),
                    day_type,
                )
            )
    queries.append((datetime.combine(last, _START_OF_DAY), end_dt, _day_type(last)))
    return queries


DEFAULT_MAX_WORKERS = 5


class HistoricServiceClient:
    BASE_URL = (
        "https://api1.raildata.org.uk/1010-historical-service-performance-_hsp_v1"
    )

    SERVICE_DETAILS_ENDPOINT = "api/v1/serviceDetails"
    SERVICE_METRICS_ENDPOINT = "api/v1/serviceMetrics"

    def __init__(
        self,
        token: str,
        retry: Retry | None = None,
        timeout: float | None = None,
        session: Session | None = None,
    ):
        # NOTE: when timeout is None, requests will go on indefinitely.
        # needed because: # https://raildata.org.uk/dashboard/community/category/topic/postDetail/142
        self.http = BaseRequestClient(
            self.BASE_URL,
            headers={
                "x-apikey": token,
                "Content-Type": "application/json",
                "Accept": "*/*",
                "User-Agent": "pyrail-sdk",
            },
            retry=retry,
            timeout=timeout,
            session=session,
        )

    @staticmethod
    def get_time_str(dt: datetime) -> str:
        return dt.strftime("%H%M")

    @staticmethod
    def get_date_str(dt: datetime) -> str:
        return dt.strftime("%Y-%m-%d")

    def get_service_metrics(
        self,
        dep: str,
        arr: str,
        start_dt: datetime,
        end_dt: datetime,
        day_type: HistoricServiceDayType,
    ) -> ServiceMetricsResponse:
        req = {
            "from_loc": dep,
            "to_loc": arr,
            "from_time": self.get_time_str(start_dt),
            "to_time": self.get_time_str(end_dt),
            "from_date": self.get_date_str(start_dt),
            "to_date": self.get_date_str(end_dt),
            "days": day_type.value,
        }
        logger.info("Fetching service metrics %s -> %s", dep, arr)
        return ServiceMetricsResponse.model_validate(
            self.http.post(self.SERVICE_METRICS_ENDPOINT, req)
        )

    def get_service_details(self, rid: str) -> ServiceDetailsResponse:
        logger.info("Fetching service details for rid %s", rid)
        return ServiceDetailsResponse.model_validate(
            self.http.post(self.SERVICE_DETAILS_ENDPOINT, {"rid": rid})
        )

    def find_journeys(
        self,
        origin: str,
        destination: str,
        start_dt: datetime,
        end_dt: datetime,
        use_threads: bool = False,
        max_workers: int = DEFAULT_MAX_WORKERS,
    ) -> list[HistoricJourney]:
        """
        Find historic journeys between two stations that were scheduled to depart in a window.

        Combines both HSP endpoints: serviceMetrics finds the RIDs scheduled in the range, then
        serviceDetails is called once per RID for the real date and actual times. Wide ranges
        therefore make many requests, which can run in a thread pool. Failed requests
        are retried with backoff (429 and 5xx) by the shared `BaseRequestClient`.

        ### Args

        origin, destination : str
            CRS codes of the stations the journey starts and ends at.

        start_dt, end_dt : datetime
            Inclusive window, applied to the scheduled departure from `origin`.

        use_threads : bool = False
            Fetch service details concurrently. Off by default: against the live API a thread
            pool was slower than sequential requests (likely server-side throttling).

        max_workers : int = 5
            Size of the thread pool when `use_threads` is `True`.

        ### Returns

        list[HistoricJourney] : sorted by scheduled departure. Services that do not call at
        both stations are skipped.
        """
        if start_dt > end_dt:
            raise ValueError("start_dt must not be after end_dt")

        rids: dict[
            str, None
        ] = {}  # ordered set: a RID can appear in more than one query
        for q_start, q_end, day_type in _metrics_queries(start_dt, end_dt):
            metrics = self.get_service_metrics(
                origin, destination, q_start, q_end, day_type
            )
            for service in metrics.services:
                rids.update(dict.fromkeys(service.service_attributes_metrics.rids))

        logger.info("Fetching details for %d services", len(rids))
        if use_threads:
            with ThreadPoolExecutor(max_workers=max_workers) as pool:
                all_details = list(pool.map(self.get_service_details, rids))
        else:
            all_details = [self.get_service_details(rid) for rid in rids]
        journeys = (self._build_journey(d, origin, destination) for d in all_details)
        return sorted(
            (
                j
                for j in journeys
                if j is not None and start_dt <= j.scheduled_departure <= end_dt
            ),
            key=lambda j: j.scheduled_departure,
        )

    @staticmethod
    def _build_journey(
        res: ServiceDetailsResponse, origin: str, destination: str
    ) -> HistoricJourney | None:
        details = res.service_attributes_details
        dep_loc = next(
            (
                loc
                for loc in details.locations
                if loc.location == origin and loc.gbtt_ptd
            ),
            None,
        )
        arr_loc = None
        if dep_loc is not None:
            after_origin = details.locations[details.locations.index(dep_loc) + 1 :]
            arr_loc = next(
                (
                    loc
                    for loc in after_origin
                    if loc.location == destination and loc.gbtt_pta
                ),
                None,
            )
        if dep_loc is None or dep_loc.gbtt_ptd is None:
            logger.warning("Service %s does not depart from %s", details.rid, origin)
            return None
        if arr_loc is None or arr_loc.gbtt_pta is None:
            logger.warning("Service %s does not call at %s", details.rid, destination)
            return None

        sched_dep = datetime.combine(details.date_of_service, dep_loc.gbtt_ptd)
        sched_arr = _at_or_after(arr_loc.gbtt_pta, sched_dep)
        return HistoricJourney(
            rid=details.rid,
            toc_code=details.toc_code,
            origin=origin,
            destination=destination,
            scheduled_departure=sched_dep,
            scheduled_arrival=sched_arr,
            actual_departure=(
                _nearest_to(dep_loc.actual_td, sched_dep) if dep_loc.actual_td else None
            ),
            actual_arrival=(
                _nearest_to(arr_loc.actual_ta, sched_arr) if arr_loc.actual_ta else None
            ),
            reason_code=arr_loc.late_canc_reason or dep_loc.late_canc_reason,
        )
