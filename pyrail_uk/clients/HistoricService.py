import logging
from datetime import date, datetime, time
from enum import StrEnum
from typing import Annotated, Any

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field
from requests import Session
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

from pyrail_uk.api.client import DEFAULT_RETRY_STRATEGY

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
        self.timeout = timeout
        self.session = session or self._get_session(token, retry)

    def _get_session(self, token: str, retry: Retry | None = None) -> Session:
        logger.debug("Initializing new session for HistoricServiceClient")
        session = Session()
        session.headers.update(
            {
                "x-apikey": token,
                "Content-Type": "application/json",
                "Accept": "*/*",
                "User-Agent": "pyrail-sdk",
            }
        )

        strategy = retry if retry is not None else DEFAULT_RETRY_STRATEGY
        # pyrefly: ignore [bad-argument-type]
        adapter = HTTPAdapter(max_retries=strategy)
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        return session

    def _post(self, endpoint: str, body: dict) -> dict:
        url = f"{self.BASE_URL}/{endpoint.lstrip('/')}"

        # NOTE: when timeout is None, requests will go on indefinitely.
        # needed because: # https://raildata.org.uk/dashboard/community/category/topic/postDetail/142
        logger.debug("POST %s", url)
        res = self.session.post(url, json=body, timeout=self.timeout)
        res.raise_for_status()
        return res.json()

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
            self._post(self.SERVICE_METRICS_ENDPOINT, req)
        )

    def get_service_details(self, rid: str) -> ServiceDetailsResponse:
        logger.info("Fetching service details for rid %s", rid)
        return ServiceDetailsResponse.model_validate(
            self._post(self.SERVICE_DETAILS_ENDPOINT, {"rid": rid})
        )
