import boto3

from pyrail.NationalRail import NationalRailClient


def get_national_rail_token():
    client = boto3.client("ssm")
    response = client.get_parameter(Name="/development/choo-choo-bot/app/darwin/departure-token", WithDecryption=True)
    return response["Parameter"]["Value"]


def main():
    token = get_national_rail_token()
    client = NationalRailClient(token)
    client.hello()


if __name__ == "__main__":
    main()
