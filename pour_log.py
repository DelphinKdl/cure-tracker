"""Local JSON persistence for saved pour records, plus an Excel report builder.

Pours are stored in a flat JSON file next to the app so the log survives
across app restarts/refreshes during a demo day. No database, no network.
"""

from __future__ import annotations

import io
import json
from pathlib import Path

import pandas as pd

LOG_PATH = Path(__file__).parent / "pour_log.json"


def load_pours(path: Path = LOG_PATH) -> list[dict]:
    if not path.exists():
        return []
    with path.open("r") as f:
        return json.load(f)


def save_pour(pour: dict, readings: pd.DataFrame, path: Path = LOG_PATH) -> None:
    """Add or update one pour's record (metadata + its readings) in the JSON log."""
    pours = load_pours(path)
    record = {
        "pour_id": pour["pour_id"],
        "location": pour["location"],
        "target_psi": pour["target_psi"],
        "pour_datetime": pour["pour_datetime"].isoformat(),
        "readings": [
            {"timestamp": pd.Timestamp(row.timestamp).isoformat(), "temp_f": row.temp_f}
            for row in readings.itertuples()
        ],
    }
    pours = [p for p in pours if p["pour_id"] != record["pour_id"]] + [record]
    with path.open("w") as f:
        json.dump(pours, f, indent=2)


def next_pour_number(path: Path = LOG_PATH) -> int:
    """Next free numeric suffix for a "P-NNN" pour_id, based on what's already logged.

    Keeps new pours from colliding with (overwriting) already-saved ones,
    e.g. after seeding sample data or restarting the app mid-demo.
    """
    numbers = []
    for p in load_pours(path):
        try:
            numbers.append(int(p["pour_id"].split("-")[-1]))
        except (ValueError, IndexError):
            continue
    return max(numbers, default=0) + 1


def reset_log(path: Path = LOG_PATH) -> None:
    """Delete the pour log file, wiping the log back to empty."""
    if path.exists():
        path.unlink()


def build_excel_report(pour: dict, maturity_df: pd.DataFrame) -> bytes:
    """One-workbook report for a single pour: summary sheet + readings/maturity sheet."""
    summary = pd.DataFrame(
        [
            {
                "Pour ID": pour["pour_id"],
                "Location": pour["location"],
                "Target Strength (PSI)": pour["target_psi"],
                "Pour Date/Time": pour["pour_datetime"].strftime("%b %d, %Y %I:%M %p"),
            }
        ]
    )
    detail = maturity_df[["timestamp", "temp_f", "elapsed_hours", "maturity_degree_hours", "estimated_psi"]].copy()
    detail["timestamp"] = pd.to_datetime(detail["timestamp"]).dt.strftime("%b %d, %Y %I:%M %p")
    detail = detail.rename(
        columns={
            "timestamp": "Timestamp",
            "temp_f": "Temp (F)",
            "elapsed_hours": "Elapsed Hours",
            "maturity_degree_hours": "Maturity (degree-hours)",
            "estimated_psi": "Estimated Strength (PSI)",
        }
    )

    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        summary.to_excel(writer, sheet_name="Pour Summary", index=False)
        detail.to_excel(writer, sheet_name="Readings & Maturity", index=False)
    return buffer.getvalue()
