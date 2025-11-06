from dataclasses import dataclass
from enum import Enum
from typing import Optional


class TrainStatus(str, Enum):
    ON_TIME = "ON_TIME"
    DELAYED = "DELAYED"
    CANCELLED = "CANCELLED"
    DEPARTED = "DEPARTED"
    DELAYED_DEPARTED = "DELAYED_DEPARTED"


@dataclass
class TrainService:
    # information about the train journey
    train_origin_crs: str
    train_origin: str
    train_destination_crs: str
    train_destination: str

    # train status
    status: TrainStatus
    status_reason: Optional[str]

    # information about the train operator
    operator_code: str
    operator: str

    # timing and platform information
    # NOTE: std - scheduled time of departure
    #       etd - estimated time of departure
    #       atd - actual time of departure
    #       eta - estimated time of arrival
    platform: Optional[str]  # not present if train cancelled
    std: str
    etd: str
    atd: Optional[str]  # not present if train not departed
    eta: Optional[str]  # not present if train cancelled


@dataclass
class DepartureServiceResponse:
    origin_crs: str
    origin: str
    destination_crs: str
    destination: str
    warning_messages: list[str]
    # metadata about services
    services: list[TrainService]
    num_services: int


@dataclass
class Station:
    crs: str
    name: str
