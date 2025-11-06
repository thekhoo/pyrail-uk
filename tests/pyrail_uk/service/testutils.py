class MockCallingPoint:

    def __init__(self, crs: str, et: str):
        self.event = {
            "crs": crs,
            "et": et,
        }

    def set_crs(self, crs: str):
        self.event["crs"] = crs
        return self

    def set_et(self, et: str):
        self.event["et"] = et
        return self

    def build(self):
        return self.event


class MockTrainServiceData:
    """
    Not cancelled, delayed and has no subsequent calling points
    by default.
    """

    def __init__(self):
        self.event = {
            "serviceID": "12345678",
            "isReverseFormation": False,
            "detachFront": False,
            "length": 0,
            "serviceType": "train",
            "filterLocationCancelled": False,
            "isCancelled": False,
            "isCircularRoute": False,
            # operator information
            "operatorCode": "GW",
            "operator": "Great Western Railway",
            # platform
            "platform": None,
            "etd": "On time",
            "std": "14:39",
            "rsid": "GW1234",
            # bogus
            "futureCancellation": False,
            "futureDelay": False,
            # train information
            "platform": "3",
            "origin": [{"crs": "OXF", "locationName": "Oxford"}],
            "destination": [{"crs": "PAD", "locationName": "London Paddington"}],
            "currentDestinations": [{"crs": "RDG", "locationName": "Reading"}],
        }

    def build(self):
        return self.event

    def set_cancelled(self):
        self.event["isCancelled"] = True
        return self

    def set_cancel_reason(self, reason: str):
        self.event["cancelReason"] = reason
        return self

    def set_delay_reason(self, reason: str):
        self.event["delayReason"] = reason
        return self

    def set_etd(self, etd: str):
        self.event["etd"] = etd
        return self

    def set_std(self, std: str):
        self.event["std"] = std
        return self

    def set_delay_reason(self, reason: str):
        self.event["delayReason"] = reason
        return self

    def set_subsequent_calling_points(self, calling_points: list[MockCallingPoint]):
        self.event["subsequentCallingPoints"] = [
            {
                "callingPoint": [cp.build() for cp in calling_points],
                "serviceType": "train",
                "serviceChangeRequired": False,
                "assocIsCancelled": False,
            }
        ]
        return self

    def clear_subsequent_calling_points(self):
        if "subsequentCallingPoints" in self.event:
            del self.event["subsequentCallingPoints"]
        return self

    def set_filter_location_cancelled(self):
        self.event["filterLocationCancelled"] = True
        return self


class MockDepartureData:

    def __init__(self):
        self.event = {
            "areServicesAvailable": True,
            "Xmlns": {"Count": 5},
            "crs": "RDG",
            "locationName": "Reading",
            "filtercrs": "OXF",
            "filterLocationName": "Oxford",
            "platformAvailable": True,
            "trainServices": [],
        }

    def set_count(self, count: int):
        self.event["Xmlns"] = {"Count": count}
        return self

    def set_train_services(self, train_services: list[dict]):
        self.event["trainServices"] = train_services
        return self

    def set_service_available(self):
        self.event["areServicesAvailable"] = True
        return self

    def set_service_not_available(self):
        self.event["areServicesAvailable"] = False
        return self

    def set_nrcc_messages(self, messages: list[str]):
        self.event["nrccMessages"] = [{"Value": message} for message in messages]
        return self

    def build(self):
        return self.event
