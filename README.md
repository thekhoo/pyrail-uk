# PyRail

PyRail is a Python SDK for the National Rail APIs on the
[Rail Data Marketplace](https://raildata.org.uk). It needs Python 3.11 or later.

## Supported APIs

| Client | API | Use it to |
|--------|-----|-----------|
| `DepartureBoardClient` | [Departure Board with Details](https://raildata.org.uk/dashboard/dataProduct/P-9a01dd96-7211-4912-bcbb-c1b5d2e35609/overview) | Get the live departures from a station |
| `ReferenceDataClient` | [Reference Data (Stations Only)](https://raildata.org.uk/dashboard/dataProduct/P-c73f0d2a-c233-497d-846b-8354e2cac326/overview) | Convert between station names and CRS codes |
| `HistoricServiceClient` | Historical Service Performance (HSP) | Find past journeys and see how late they ran |

## Install

```bash
pip install pyrail-uk
```

## Get an API token

Each API on the Rail Data Marketplace has its own token. Subscribe to the API on the
Marketplace, then copy the token. Give each client the token for its own API.

Do not put a token in your code. Read it from an environment variable.

```python
import os

from pyrail_uk import DepartureBoardClient

client = DepartureBoardClient(token=os.environ["NATIONAL_RAIL_TOKEN"])
```

## Station codes

The APIs identify a station by its three-letter CRS code. For example, `EUS` is London
Euston and `MAN` is Manchester Piccadilly. Use `ReferenceDataClient` to find a code.

```python
from pyrail_uk import ReferenceDataClient

reference = ReferenceDataClient(token=os.environ["REFERENCE_DATA_TOKEN"])

reference.get_crs_by_station_name("London Euston")  # "EUS"
reference.get_station_name_by_crs("eus")  # "London Euston" (case does not matter)
```

`get_crs_by_station_name` ignores case but needs the full station name. It raises
`StationNotFoundException` when no station matches. `get_station_name_by_crs` raises
`CRSNotFoundException` when no station has that code. Both exceptions are in
`pyrail_uk.core.exceptions`. The client caches the station list for 5 minutes.

## Get live departures

```python
from pyrail_uk import DepartureBoardClient

board = DepartureBoardClient(token=os.environ["NATIONAL_RAIL_TOKEN"])

result = board.get_trains("EUS", "MAN")
for train in result.services:
    print(train.std, train.train_destination, train.status, train.departure_mins_delayed)
```

`get_trains(dep_crs, arr_crs=None, timeoffset_mins=0, timewindow_mins=120)` returns a
`DepartureServiceResponse`.

- `dep_crs` is the station the trains leave from.
- `arr_crs` is optional. If you set it, the board shows only trains that call at that station.
- `timeoffset_mins` moves the start of the window away from now. Valid values are
  between -120 and 120.
- `timewindow_mins` is the length of the window.

Each item in `result.services` is a `TrainService`. It has the scheduled, estimated and actual
times (`std`, `etd`, `atd`, `sta`, `eta`), the `platform`, the operator, the delay in minutes,
and a `status`. The status is one of `ON_TIME`, `DELAYED`, `CANCELLED`, `DEPARTED` or
`DELAYED_DEPARTED`. Fields such as `platform` are `None` when the API gives no value.

To get the unchanged API response as a dictionary, call `get_trains_raw` with the same arguments.

## Find historic journeys

`HistoricServiceClient.find_journeys` finds the trains that ran between two stations in a
window of time. It shows when each train was due and when it really ran.

```python
from datetime import datetime

from pyrail_uk import HistoricServiceClient

history = HistoricServiceClient(token=os.environ["HISTORIC_SERVICE_TOKEN"])

journeys = history.find_journeys(
    "EUS", "MAN", datetime(2026, 8, 28, 8, 0), datetime(2026, 8, 31, 12, 0)
)
for journey in journeys:
    if journey.cancelled:
        print(journey.scheduled_departure, "cancelled", journey.reason_code)
    else:
        print(journey.scheduled_departure, f"{journey.arrival_delay_mins} min late")
```

### Arguments

| Argument | Meaning |
|----------|---------|
| `origin`, `destination` | CRS codes of the first and last station |
| `start_dt`, `end_dt` | Start and end of the window. The window includes both ends. It applies to the **scheduled** departure from `origin`. Use datetimes without a time zone. They must be UK local time |
| `use_threads` | Default `False`. Set it to `True` to get the train details in a thread pool |
| `max_workers` | Size of the thread pool when `use_threads` is `True`. Default `5` |

`find_journeys` raises `ValueError` when `start_dt` is after `end_dt`.

### Result

The method returns a list of `HistoricJourney`, sorted by scheduled departure.

| Field | Meaning |
|-------|---------|
| `rid` | The ID of the train service |
| `toc_code` | The code of the train operator |
| `origin`, `destination` | The CRS codes you asked for |
| `scheduled_departure`, `scheduled_arrival` | The timetable times, as datetimes |
| `actual_departure`, `actual_arrival` | The times the train really ran. `None` for a cancelled train |
| `departure_delay_mins`, `arrival_delay_mins` | The difference between actual and scheduled, in minutes. `None` for a cancelled train |
| `cancelled` | `True` when the train has no actual times |
| `reason_code` | The code for the delay or cancellation reason. `None` when there is none |

### How it works, and its limits

1. The method asks the `serviceMetrics` endpoint for the trains that match. A window that covers
   several days becomes up to 5 requests. The API accepts only one day type for each request.
   The day types are weekday, Saturday and Sunday.
2. The method then asks the `serviceDetails` endpoint **once for each train**. This is the only
   way to get the real date and the actual times. A wide window can need hundreds of requests.
3. The method keeps the trains with a scheduled departure inside your window.

The API uses the calendar weekday, so a bank holiday Monday counts as a weekday.

A thread pool did not help in live tests. It was slower than one request at a time.
Keep `use_threads` off unless you measure a gain.

The method skips a train that does not call at both stations, and it writes a warning to the log.

### Lower-level methods

`HistoricServiceClient` also has the two API calls that `find_journeys` uses.

- `get_service_metrics(dep, arr, start_dt, end_dt, day_type)` returns a `ServiceMetricsResponse`.
  The `day_type` is a `HistoricServiceDayType`. The times in `start_dt` and `end_dt` set a daily
  window. The dates set the date range.
- `get_service_details(rid)` returns a `ServiceDetailsResponse`. Times are `datetime.time`
  objects. A blank value from the API becomes `None`.

## Retries, timeouts and logging

All clients share one HTTP layer, `BaseRequestClient` in `pyrail_uk.utils.request`.

- It retries a request up to 3 times when the API replies 429, 500, 502, 503 or 504.
  Each retry waits longer than the one before.
- The Departure Board and Reference Data clients stop a request after 5 minutes. The Historic
  client waits with no limit by default, because the API can be slow. Set `timeout` (in
  seconds) when you create `HistoricServiceClient` to change this.
- A reply with another error status, such as 401 or 404, raises `requests.HTTPError`.
  The client does not retry it.
- The SDK writes to the standard `logging` module, in loggers named `pyrail_uk.*`. Set the level
  to `INFO` to see the main steps and to `DEBUG` to see each request.

## Deprecated

Use `DepartureBoardClient` and `ReferenceDataClient` instead of `NationalRailClient` in
`pyrail_uk.NationalRail`. The old class shows a deprecation warning.

## Development

```bash
uv sync
uv run pytest
uv run ruff check pyrail_uk
uv run pyrefly check
```

## Releasing

Releases use [release-please](https://github.com/googleapis/release-please). Use
conventional commits (`feat:`, `fix:`, `ci:`, ...) on `main`.

| Workflow | Starts on | Does |
|----------|-----------|------|
| `ci.yml` | pull request | commit-message check, then `checks.yml` |
| `release.yml` | push to `main` | `checks.yml` (the same checks as CI), then `github-tag-release` (release-please, from `github-actions-shared`). It skips the checks for the release PR's own merge commit and only tags the release |
| `pypi-release.yml` | a GitHub Release is published | uses the `python-pypi-publish` action (from `github-actions-shared`) to build the tag and publish it to PyPI |

1. Each push to `main` updates a release PR that bumps the version in
   `pyproject.toml` and writes `CHANGELOG.md`.
2. The release PR turns on auto-merge, so it merges once its required checks and review
   rules are met. release-please then tags the release and creates the GitHub Release.
   (To release by hand instead, remove `auto-merge: true` from `release.yml`.)
3. `pypi-release.yml` starts from that release. To publish a tag again, run `PyPI Release` by
   hand and enter the tag.

The PyPI trusted publisher must name the workflow `pypi-release.yml` and the environment
`production`.

The workflows sign in as the `thekhoo-actions-writer-agent` GitHub App, using the
secret `RELEASE_APP_PRIVATE_KEY` and the variable `RELEASE_APP_ID`. See
`docs/release-app-setup.md` in `thekhoo/github-actions-shared`.
