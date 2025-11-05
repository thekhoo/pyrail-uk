from typing import NotRequired, TypedDict


class DepartureResponseMetadataTypeDef(TypedDict):
    Count: int


class NRCCMessagesTypeDef(TypedDict):
    Value: str


class DestinationTypeDef(TypedDict):
    crs: str
    locationName: str
    assocIsCancelled: bool


class CallingPointTypeDef(TypedDict):
    locationName: str
    crs: str

    st: str  # Scheduled time
    et: str  # Estimated time

    isCancelled: bool
    length: int
    detachFront: bool
    affectedByDiversion: bool
    rerouteDelay: int


class SubsequentCallingPointsTypeDef(TypedDict):
    callingPoint: list[CallingPointTypeDef]
    serviceType: str
    serviceChangeRequired: bool
    assocIsCancelled: bool


class TrainServiceTypeDef(TypedDict):
    serviceID: str
    cancelReason: NotRequired[str]
    isReverseFormation: bool
    detachFront: bool
    length: int
    serviceType: str
    filterLocationCancelled: bool
    isCancelled: bool
    isCircularRoute: bool

    operatorCode: str
    operator: str

    platform: NotRequired[str]
    etd: str  # Estimated Time of Departure
    std: str  # Scheduled Time of Departure
    rsid: str

    # i honestly have no idea what these 2 fields mean... they're always false
    futureCancellation: bool
    futureDelay: bool

    currentDestinations: list[DestinationTypeDef]
    origin: list[DestinationTypeDef]
    destination: list[DestinationTypeDef]

    subsequentCallingPoints: list[SubsequentCallingPointsTypeDef]


class DepBoardWithDetailsResponseTypeDef(TypedDict):
    Xmlns: DepartureResponseMetadataTypeDef
    areServicesAvailable: bool
    crs: str
    filterLocationName: str
    filterType: str
    filtercrs: str
    generatedAt: str
    locationName: str
    nrccMessages: list[NRCCMessagesTypeDef]
    platformAvailable: bool
    trainServices: list[TrainServiceTypeDef]
