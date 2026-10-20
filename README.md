# PyRail

An easier way to deal with the National Rail API

## Supported APIs

- [Departure Board with Details](https://raildata.org.uk/dashboard/dataProduct/P-9a01dd96-7211-4912-bcbb-c1b5d2e35609/overview)
- [Reference Data (Stations Only)](https://raildata.org.uk/dashboard/dataProduct/P-c73f0d2a-c233-497d-846b-8354e2cac326/overview)

## P.S.

- I'm sorry for not sticking to v0.X.X for alpha

## EXAMPLE HISTORIC SERVICE METRICS

```json
{
  "from_loc": "RDG",
  "to_loc": "PAD",
  "from_time": "0800",
  "to_time": "0900",
  "from_date": "2026-08-16",
  "to_date": "2026-08-31",
  "days": "WEEKDAY"
}
```

`HistoricServiceClient.get_service_metrics(...)` validates the response into a
`ServiceMetricsResponse` (pydantic), so times, counts and flags are typed.

## EXAMPLE HISTORIC SERVICE DETAILS

```json
{
    "rid": "XXXXX"
}
```

`HistoricServiceClient.get_service_details(rid)` returns a `ServiceDetailsResponse`.
Times are `datetime.time`; blank values from the API (e.g. no arrival at the origin,
or no actuals for a cancelled call) become `None`.

## Releasing

Releases use [release-please](https://github.com/googleapis/release-please). Use
conventional commits (`feat:`, `fix:`, `ci:`, ...) on `main`.

1. Each push to `main` updates a release PR that bumps the version in
   `pyproject.toml` and writes `CHANGELOG.md`.
2. Merge the release PR when you want to release. This tags the release and
   creates the GitHub Release.
3. The `Publish to PyPI` job then builds the tag and publishes it.

The workflow signs in as the `thekhoo-actions-writer-agent` GitHub App, using the
secret `RELEASE_APP_PRIVATE_KEY` and the variable `RELEASE_APP_ID`. See
`docs/release-app-setup.md` in `thekhoo/github-actions-shared`.

