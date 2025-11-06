import os

from dotenv import load_dotenv

from pyrail_uk.NationalRail import NationalRailClient

load_dotenv()


def get_national_rail_token():
    return os.environ.get("NATIONAL_RAIL_TOKEN")


def get_reference_data_token():
    return os.environ.get("REFERENCE_DATA_TOKEN")


def main():
    token = get_national_rail_token()
    ref_data_token = get_reference_data_token()
    client = NationalRailClient(departure_board_token=token, reference_data_token=ref_data_token)

    station_name = client.get_station_name_by_crs("rdg")
    crs = client.get_crs_by_station_name("OXFORD")

    print(station_name)
    print(crs)


if __name__ == "__main__":
    main()
