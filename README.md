# Trackview — Lockview Dashboard

An internal analytics dashboard for parsing and visualizing Lockview vehicle lock/unlock event data. Built for logistics and fleet operations teams who need to query lock status history, filter by vehicle or center, and export records.

Lockview exports raw CSV data with inconsistent status strings and edge cases (including typos baked into the tracking system itself). This tool normalizes that data, converts it to a queryable JSON format, and serves it through a lightweight Flask dashboard.

## Features

- Upload Lockview CSV exports and convert them to structured JSON
- Filter by vehicle ID, center, and date ranges (supports dual date range comparison)
- Lock/unlock status detection from 7 key event types
- CSV export of filtered results
- Handles known data quirks — including `"Shackle Opned"` (typo in source system, not a bug here)

## Lock status logic

The system maps Lockview event strings to binary lock/unlock states:

**Locked** — `Close Shackle Auto Seal`, `Shackle Closed`

**Unlocked** — `Shackle Opened`, `Dynamic Password Unseal`, `Platform Unseal`, `Auto Unseal`, `Bluetooth Unseal`

Full reference in [`KEY_REMARKS_REFERENCE.md`](./KEY_REMARKS_REFERENCE.md).

## Stack

| | |
|---|---|
| Backend | Flask, Python |
| Data layer | `lockview_converter.py` — CSV → JSON normalization |
| Frontend | Single-file HTML dashboard (`lockview_dashboard_json.html`) |
| Deployment | Heroku (Procfile included) |

## Running locally

```bash
pip install -r requirements.txt
python server.py
```

Upload a Lockview CSV via the dashboard at `http://localhost:5000`. Converted data is written to `lockview_data.json` and queried on the fly.

## Deployment

Includes a `Procfile` for Heroku:

```
web: python server.py
```
