"""
Data loader module.
Loads from Excel file if RAMPUP_EXCEL_PATH is set, otherwise uses sample data.

To use your own data:
  export RAMPUP_EXCEL_PATH=/path/to/your/rampup_file.xlsx
"""

import os
import pandas as pd
from .sample_data import load_data as load_sample_data


MONTH_COLUMNS = [
    "1/1/2026", "2/1/2026", "3/1/2026", "4/1/2026", "5/1/2026",
    "6/1/2026", "7/1/2026", "8/1/2026", "9/1/2026", "10/1/2026", "11/1/2026",
]


def load_from_excel(path):
    """Load the ramp-up Excel file."""
    df = pd.read_excel(path, engine="openpyxl")

    # Normalize column names — Excel dates may parse as datetime
    new_cols = {}
    for col in df.columns:
        if isinstance(col, pd.Timestamp):
            new_cols[col] = col.strftime("%-m/1/%Y")
        elif hasattr(col, "strftime"):
            new_cols[col] = col.strftime("%-m/1/%Y")
    if new_cols:
        df = df.rename(columns=new_cols)

    # Ensure month columns exist and fill NaN with 0
    for m in MONTH_COLUMNS:
        if m not in df.columns:
            df[m] = 0
        else:
            df[m] = pd.to_numeric(df[m], errors="coerce").fillna(0).astype(int)

    # Ensure Grand Total
    if "Grand Total" not in df.columns:
        df["Grand Total"] = df[MONTH_COLUMNS].sum(axis=1)

    # Derive Status if not present
    if "Status" not in df.columns:
        # Heuristic: filled = past months have values, open = current/future months
        def infer_status(row):
            past = row["1/1/2026"] + row["2/1/2026"]
            current = row["3/1/2026"]
            future = sum(row[m] for m in MONTH_COLUMNS[3:])
            if past > 0 and future == 0 and current == 0:
                return "Filled"
            elif future > 0 and past == 0 and current == 0:
                return "Future Fill"
            else:
                return "Open"
        df["Status"] = df.apply(infer_status, axis=1)

    return df


def load_data():
    """Main entry point."""
    excel_path = os.environ.get("RAMPUP_EXCEL_PATH")
    if excel_path and os.path.isfile(excel_path):
        print(f"[DATA] Loading from Excel: {excel_path}")
        positions = load_from_excel(excel_path)
        # Use sample data for weekly/pipeline/nexus (or load additional sheets)
        from .sample_data import (
            generate_weekly_tracking, generate_pipeline_data,
            generate_nexus_monthly, generate_location_summary,
        )
        weekly = generate_weekly_tracking()
        pipeline = generate_pipeline_data()
        nexus = generate_nexus_monthly()
        locations = generate_location_summary()
        return positions, weekly, pipeline, nexus, locations
    else:
        if excel_path:
            print(f"[DATA] File not found: {excel_path} — using sample data")
        else:
            print("[DATA] No RAMPUP_EXCEL_PATH set — using sample data")
            print("[DATA] Set it with: export RAMPUP_EXCEL_PATH=/path/to/file.xlsx")
        return load_sample_data()
