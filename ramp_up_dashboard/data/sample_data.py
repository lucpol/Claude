"""
Sample data generator matching the actual Amadeus Nexus ramp-up Excel format.

Excel columns: BU, Org Path Name, Region, Country, Location,
               Monthly columns (1/1/2026 .. 11/1/2026), Grand Total

Business Units: CFA, HOS, TRU, TSI
Regions: Americas, APAC, EMEA, TBD
"""

import pandas as pd
import numpy as np
from datetime import datetime

np.random.seed(42)

# ── Real structure based on screenshots ───────────────────────────────────────

ORGS = {
    "CFA": {
        "org_paths": ["CFA-CPO", "CFA-FOP", "CFA-GFC", "CFA-SFH", "CFA-SFT"],
        "weight": 13,
    },
    "HOS": {
        "org_paths": ["HOS-COM", "HOS-E8T", "HOS-MID", "HOS-MPC", "HOS-OPS", "HOS-PRD", "HOS-STT"],
        "weight": 52,
    },
    "TRU": {
        "org_paths": ["TRU-AIR", "TRU-AME", "TRU-AOP", "TRU-APC", "TRU-GIS", "TRU-RMS", "TRU-TRD"],
        "weight": 225,
    },
    "TSI": {
        "org_paths": ["TSI-COR", "TSI-DPS", "TSI-INF", "TSI-SEC"],
        "weight": 20,
    },
}

LOCATIONS_BY_REGION = {
    "Americas": ["Bogota", "San Jose", "Dallas", "Maitland", "USA"],
    "APAC": ["Bangalore", "Pune", "New Delhi", "Kuala Lumpur", "Bangkok", "Manila", "Tokyo", "Japan", "Sydney"],
    "EMEA": ["Madrid", "Barcelona", "Nice", "London", "Lisbon", "Warsaw", "Heathrow", "Berlin"],
    "TBD": ["TBD"],
}

COUNTRIES_BY_LOCATION = {
    "Bogota": "Colombia", "San Jose": "Costa Rica", "Dallas": "United States of America",
    "Maitland": "United States of America", "USA": "United States of America",
    "Bangalore": "India", "Pune": "India", "New Delhi": "India",
    "Kuala Lumpur": "Malaysia", "Bangkok": "Thailand", "Manila": "Philippines",
    "Tokyo": "Japan", "Japan": "Japan", "Sydney": "Australia",
    "Madrid": "Spain", "Barcelona": "Spain", "Nice": "France",
    "London": "United Kingdom", "Lisbon": "Portugal", "Warsaw": "Poland",
    "Heathrow": "United Kingdom", "Berlin": "Germany", "TBD": "TBD",
}

MONTHS = [
    "1/1/2026", "2/1/2026", "3/1/2026", "4/1/2026", "5/1/2026",
    "6/1/2026", "7/1/2026", "8/1/2026", "9/1/2026", "10/1/2026", "11/1/2026",
]

# Pipeline stage names from the PPT
PIPELINE_STAGES = ["Review", "Manager Review", "Screen", "Assessment", "Interview", "Offer", "Ready for Hire"]

# Statuses
STATUSES = ["Open", "Future Fill", "Filled"]

# ── Weekly tracking data from the PPT chart ───────────────────────────────────

WEEKLY_DATA = [
    {"Week": "2025-11-25", "Label": "25th November", "Job Reqs Open": 146, "Job Reqs Filled": 3},
    {"Week": "2025-12-02", "Label": "2nd December", "Job Reqs Open": 148, "Job Reqs Filled": 3},
    {"Week": "2025-12-09", "Label": "9th December", "Job Reqs Open": 153, "Job Reqs Filled": 8},
    {"Week": "2025-12-16", "Label": "16th December", "Job Reqs Open": 146, "Job Reqs Filled": 16},
    {"Week": "2026-01-14", "Label": "14th January", "Job Reqs Open": 124, "Job Reqs Filled": 46},
    {"Week": "2026-01-20", "Label": "20th January", "Job Reqs Open": 246, "Job Reqs Filled": 54},
    {"Week": "2026-01-27", "Label": "27th January", "Job Reqs Open": 282, "Job Reqs Filled": 55},
    {"Week": "2026-02-03", "Label": "3rd February", "Job Reqs Open": 261, "Job Reqs Filled": 119},
    {"Week": "2026-02-10", "Label": "10th February", "Job Reqs Open": 262, "Job Reqs Filled": 127},
    {"Week": "2026-02-17", "Label": "17th February", "Job Reqs Open": 261, "Job Reqs Filled": 142},
    {"Week": "2026-02-24", "Label": "24th February", "Job Reqs Open": 241, "Job Reqs Filled": 167},
    {"Week": "2026-03-03", "Label": "3rd March", "Job Reqs Open": 228, "Job Reqs Filled": 219},
]

# ── Candidate pipeline data from PPT ─────────────────────────────────────────

PIPELINE_DATA = [
    {"BU": "CFA", "Job Requisitions": 2, "Review": 17, "Manager Review": 10, "Screen": 7, "Assessment": 0, "Interview": 6, "Offer": 1, "Ready for Hire": 0},
    {"BU": "HOS", "Job Requisitions": 25, "Review": 55, "Manager Review": 75, "Screen": 34, "Assessment": 6, "Interview": 26, "Offer": 6, "Ready for Hire": 5},
    {"BU": "TRU", "Job Requisitions": 170, "Review": 1429, "Manager Review": 174, "Screen": 177, "Assessment": 20, "Interview": 181, "Offer": 27, "Ready for Hire": 40},
    {"BU": "TSI", "Job Requisitions": 31, "Review": 546, "Manager Review": 11, "Screen": 23, "Assessment": 2, "Interview": 37, "Offer": 4, "Ready for Hire": 6},
]

# ── Nexus replacement monthly targets from PPT ───────────────────────────────

NEXUS_MONTHLY = {
    "CFA": {"Americas": {"March": 5, "October": 0}, "APAC": {"March": 1}, "EMEA": {"March": 6, "October": 1}},
    "HOS": {"Americas": {"January": 1, "April": 11, "July": 1}, "APAC": {"January": 5, "April": 13, "October": 5}, "EMEA": {"January": 2, "April": 10, "July": 4}},
    "TRU": {"Americas": {"January": 34, "February": 3, "March": 1, "April": 1, "June": 3, "July": 6},
             "APAC": {"January": 35, "February": 3, "March": 4, "April": 30, "May": 2, "June": 19, "July": 24, "September": 1, "October": 2, "November": 1},
             "EMEA": {"January": 19, "March": 1, "April": 2, "May": 1, "June": 8, "July": 24},
             "TBD": {"March": 1}},
    "TSI": {"Americas": {"January": 1, "February": 1, "March": 4}, "APAC": {"January": 2, "March": 1, "April": 1, "May": 3, "June": 6, "October": 1}},
}


def generate_positions():
    """Generate position-level data matching the Excel format."""
    rows = []
    pos_id = 0

    for bu, info in ORGS.items():
        target = info["weight"]
        org_paths = info["org_paths"]

        # Distribute across org paths
        per_org = max(1, target // len(org_paths))
        remainder = target - per_org * len(org_paths)

        for oi, org_path in enumerate(org_paths):
            count = per_org + (1 if oi < remainder else 0)
            if count <= 0:
                count = 1

            for _ in range(count):
                pos_id += 1
                # Pick region weighted by real data
                if bu == "TRU":
                    region = np.random.choice(
                        ["Americas", "APAC", "EMEA", "TBD"],
                        p=[0.21, 0.54, 0.24, 0.01]
                    )
                elif bu == "HOS":
                    region = np.random.choice(
                        ["Americas", "APAC", "EMEA"],
                        p=[0.25, 0.44, 0.31]
                    )
                elif bu == "CFA":
                    region = np.random.choice(
                        ["Americas", "APAC", "EMEA"],
                        p=[0.38, 0.08, 0.54]
                    )
                else:
                    region = np.random.choice(
                        ["Americas", "APAC"],
                        p=[0.30, 0.70]
                    )

                location = np.random.choice(LOCATIONS_BY_REGION[region])
                country = COUNTRIES_BY_LOCATION[location]

                # Monthly distribution — most hires in Jan, Apr, Jul
                monthly = {m: 0 for m in MONTHS}
                # Pick 1-3 months with hires
                n_months = np.random.choice([1, 2, 3], p=[0.6, 0.3, 0.1])
                # Weight towards Jan, Apr, Jul
                month_weights = [25, 3, 8, 22, 2, 12, 19, 0, 1, 3, 1]
                month_probs = np.array(month_weights, dtype=float)
                month_probs /= month_probs.sum()
                chosen_months = np.random.choice(
                    range(len(MONTHS)), size=int(n_months), replace=False, p=month_probs
                )
                grand_total = np.random.choice([1, 2, 3, 4, 5, 6, 8, 10, 12, 15, 20, 30, 35, 36],
                                                p=[0.25, 0.20, 0.10, 0.10, 0.05, 0.05, 0.05, 0.04, 0.04, 0.03, 0.03, 0.03, 0.02, 0.01])
                # Spread grand_total across chosen months
                remaining = grand_total
                for idx, mi in enumerate(chosen_months):
                    if idx == len(chosen_months) - 1:
                        monthly[MONTHS[mi]] = remaining
                    else:
                        alloc = max(1, np.random.randint(1, max(2, remaining)))
                        monthly[MONTHS[mi]] = alloc
                        remaining -= alloc
                        if remaining <= 0:
                            break

                # Determine status based on current month (March 2026)
                # Positions with hires in Jan-Feb are likely filled, Apr+ are open/future
                filled_months = sum(monthly[m] for m in MONTHS[:2])  # Jan, Feb
                current_month = monthly[MONTHS[2]]  # March
                future_months = sum(monthly[m] for m in MONTHS[3:])  # Apr+

                if filled_months > 0 and future_months == 0 and current_month == 0:
                    status = "Filled"
                elif future_months > 0 and filled_months == 0:
                    status = "Future Fill" if np.random.random() < 0.3 else "Open"
                else:
                    status = np.random.choice(["Open", "Filled", "Future Fill"], p=[0.46, 0.45, 0.09])

                row = {
                    "BU": bu,
                    "Org Path Name": org_path,
                    "Region": region,
                    "Country": country,
                    "Location": location,
                    "Status": status,
                }
                for m in MONTHS:
                    row[m] = monthly[m]
                row["Grand Total"] = grand_total

                rows.append(row)

    return pd.DataFrame(rows)


def generate_weekly_tracking():
    """Weekly tracking data from the PPT chart."""
    df = pd.DataFrame(WEEKLY_DATA)
    df["Week"] = pd.to_datetime(df["Week"])
    df["New Filled This Week"] = df["Job Reqs Filled"].diff().fillna(df["Job Reqs Filled"]).astype(int)
    df["New Opened This Week"] = df["Job Reqs Open"].diff().fillna(df["Job Reqs Open"]).astype(int)
    df["Fill Rate (%)"] = (df["Job Reqs Filled"] / (df["Job Reqs Open"] + df["Job Reqs Filled"]) * 100).round(1)
    df["Total Reqs (Cumulative)"] = df["Job Reqs Open"] + df["Job Reqs Filled"]
    return df


def generate_pipeline_data():
    """Candidate pipeline data by BU."""
    return pd.DataFrame(PIPELINE_DATA)


def generate_nexus_monthly():
    """Nexus replacement monthly targets by BU and region."""
    month_names = ["January", "February", "March", "April", "May", "June",
                   "July", "August", "September", "October", "November"]
    rows = []
    for bu, regions in NEXUS_MONTHLY.items():
        for region, months in regions.items():
            row = {"BU": bu, "Region": region}
            total = 0
            for m in month_names:
                val = months.get(m, 0)
                row[m] = val
                total += val
            row["Total"] = total
            rows.append(row)
    return pd.DataFrame(rows)


def generate_location_summary():
    """Open and Filled job requisitions by key location (from PPT)."""
    return pd.DataFrame([
        {"Location": "Bangalore", "Open": 72, "Open Delta": -7, "Filled": 36, "Filled Delta": 7},
        {"Location": "Barcelona", "Open": 2, "Open Delta": 0, "Filled": 26, "Filled Delta": 2},
        {"Location": "Bogota", "Open": 48, "Open Delta": -9, "Filled": 48, "Filled Delta": 12},
        {"Location": "Lisbon", "Open": 11, "Open Delta": -1, "Filled": 9, "Filled Delta": 3},
        {"Location": "Makati", "Open": 34, "Open Delta": -1, "Filled": 30, "Filled Delta": 13},
        {"Location": "San Jose", "Open": 14, "Open Delta": 3, "Filled": 28, "Filled Delta": 3},
    ])


def load_data():
    """Main entry point — returns all datasets."""
    positions = generate_positions()
    weekly = generate_weekly_tracking()
    pipeline = generate_pipeline_data()
    nexus = generate_nexus_monthly()
    locations = generate_location_summary()
    return positions, weekly, pipeline, nexus, locations
