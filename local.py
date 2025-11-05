import json
import os
from pprint import pprint

import boto3
from dotenv import load_dotenv

from pyrail.NationalRail import NationalRailClient

load_dotenv()


def get_national_rail_token():
    return os.environ.get("NATIONAL_RAIL_TOKEN")


def main():
    token = get_national_rail_token()
    client = NationalRailClient(token)
    departures = client.get_trains(dep_crs="RDG", arr_crs="PAD")

    pprint(departures)

    with open("depBoard.json", "w") as f:
        json.dump(departures, f, indent=4)


if __name__ == "__main__":
    main()
