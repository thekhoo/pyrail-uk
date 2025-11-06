from typing import Optional

import pyrail_uk.utils.array as array
from pyrail_uk.api.types import DepBoardWithDetailsResponseTypeDef, TrainServiceTypeDef

from .types import DepartureServiceResponse, TrainService, TrainStatus

ON_TIME_ETD = "On time"
DEFAULT_DELAY_REASON = "No reason provided"
DEFAULT_CANCEL_REASON = "No reason provided"


def get_train_status_and_reason(service_info: TrainServiceTypeDef) -> tuple[TrainStatus, Optional[str]]:
    if service_info.get("isCancelled", False) or service_info.get("filterLocationCancelled", False):
        status = TrainStatus.CANCELLED
        reason = service_info.get("cancelReason", DEFAULT_CANCEL_REASON)
        return status, reason

    if "subsequentCallingPoints" not in service_info:
        etd = service_info.get("etd")
        if etd == ON_TIME_ETD:
            return TrainStatus.DEPARTED, None
        else:
            return TrainStatus.DELAYED_DEPARTED, None

    etd = service_info.get("etd")
    if etd == ON_TIME_ETD:
        return TrainStatus.ON_TIME, None

    return TrainStatus.DELAYED, service_info.get("delayReason", DEFAULT_DELAY_REASON)


def get_eta(service_info: TrainServiceTypeDef, target_crs: str) -> Optional[str]:
    if "subsequentCallingPoints" not in service_info:
        return None

    calling_points = service_info["subsequentCallingPoints"][0]["callingPoint"]
    target_point = array.findfirst(calling_points, lambda cp: cp["crs"] == target_crs)

    if not target_point:
        return None

    return target_point.get("et")


def get_atd(service_info: TrainServiceTypeDef, train_status: TrainStatus) -> Optional[str]:
    """Gets the actual time of departure for the train service, if it has departed."""
    if train_status not in [TrainStatus.DEPARTED, TrainStatus.DELAYED_DEPARTED]:
        return None

    if train_status == TrainStatus.DELAYED_DEPARTED:
        etd = service_info.get("etd")
        return service_info.get("std") if etd == ON_TIME_ETD else etd

    if train_status == TrainStatus.DEPARTED:
        return service_info.get("std")


def simplify_service_info(service_info: TrainServiceTypeDef, target_crs: Optional[str]) -> TrainService:
    origin = service_info["origin"][0]
    destination = service_info["destination"][0]

    operator_code = service_info["operatorCode"]
    operator = service_info["operator"]

    status, reason = get_train_status_and_reason(service_info)

    atd = get_atd(service_info, status)
    eta = get_eta(service_info, target_crs or destination["crs"])  # handle no user destination cases

    return TrainService(
        # this origin is where the train originated from
        train_origin_crs=origin["crs"],
        train_origin=origin["locationName"],
        # this destination is the final destination of the train service
        train_destination_crs=destination["crs"],
        train_destination=destination["locationName"],
        # general information
        status=status,
        status_reason=reason,
        operator=operator,
        operator_code=operator_code,
        # time and location details,
        platform=service_info.get("platform"),
        std=service_info["std"],
        etd=service_info["etd"],
        atd=atd,
        eta=eta,
    )


def simplify_departures(departures_data: DepBoardWithDetailsResponseTypeDef):
    # this is for the user's journey and not the train journey
    # i.e.  the user is departing from OXF to RDF
    #       but the train is going from WXP to PAD
    origin_crs = departures_data.get("crs")
    origin_name = departures_data.get("locationName")
    destination_crs = departures_data.get("filtercrs", None)
    destination_name = departures_data.get("filterLocationName", None)

    services_raw = departures_data.get("trainServices", {})
    services = [simplify_service_info(service, destination_crs) for service in services_raw]
    num_services = departures_data.get("Xmlns", {}).get("Count", len(services))

    # all the messages are an array of {"Value": "..."}
    nrcc_warning_messages_raw = departures_data.get("nrccMessages", [])
    warning_messages = [msg["Value"] for msg in nrcc_warning_messages_raw]

    return DepartureServiceResponse(
        origin_crs=origin_crs,
        origin=origin_name,
        destination_crs=destination_crs,
        destination=destination_name,
        warning_messages=warning_messages,
        services=services,
        num_services=num_services,
    )
