"""KPI cards module matching the PPT summary format."""

from dash import html
import dash_bootstrap_components as dbc
from ..theme import AMADEUS_NAVY, AMADEUS_GREEN, AMADEUS_ORANGE, AMADEUS_RED, AMADEUS_CYAN, AMADEUS_PURPLE


def compute_kpis(positions_df, weekly_df, pipeline_df):
    """Compute KPIs from all data sources."""
    total_rows = len(positions_df)
    total_headcount = int(positions_df["Grand Total"].sum())

    by_status = positions_df["Status"].value_counts()
    open_count = int(by_status.get("Open", 0))
    filled_count = int(by_status.get("Filled", 0))
    future_fill = int(by_status.get("Future Fill", 0))

    open_hc = int(positions_df[positions_df["Status"] == "Open"]["Grand Total"].sum())
    filled_hc = int(positions_df[positions_df["Status"] == "Filled"]["Grand Total"].sum())

    # Pipeline totals
    total_pipeline = int(pipeline_df[["Review", "Manager Review", "Screen", "Assessment", "Interview", "Offer", "Ready for Hire"]].sum().sum())
    total_offers = int(pipeline_df["Offer"].sum())
    ready_to_hire = int(pipeline_df["Ready for Hire"].sum())

    # Weekly deltas (latest vs previous)
    if len(weekly_df) >= 2:
        latest = weekly_df.iloc[-1]
        prev = weekly_df.iloc[-2]
        open_delta = int(latest["Job Reqs Open"] - prev["Job Reqs Open"])
        filled_delta = int(latest["Job Reqs Filled"] - prev["Job Reqs Filled"])
    else:
        open_delta = 0
        filled_delta = 0

    fill_rate = round(filled_hc / total_headcount * 100, 1) if total_headcount > 0 else 0

    return {
        "total_headcount": total_headcount,
        "open_reqs": open_count,
        "open_hc": open_hc,
        "open_delta": open_delta,
        "filled_reqs": filled_count,
        "filled_hc": filled_hc,
        "filled_delta": filled_delta,
        "future_fill": future_fill,
        "fill_rate": fill_rate,
        "total_pipeline": total_pipeline,
        "total_offers": total_offers,
        "ready_to_hire": ready_to_hire,
        "num_bus": positions_df["BU"].nunique(),
        "num_locations": positions_df["Location"].nunique(),
    }


def _card(value, label, border_color=AMADEUS_NAVY, delta=None, delta_type="neutral", prefix="", suffix=""):
    delta_el = None
    if delta is not None:
        cls = f"kpi-delta {'positive' if delta_type == 'positive' else 'negative' if delta_type == 'negative' else 'neutral'}"
        arrow = "+" if delta_type == "positive" else "" if delta_type == "negative" else ""
        delta_el = html.Div(f"{arrow}{delta}", className=cls)

    return html.Div([
        html.Div(f"{prefix}{value}{suffix}", className="kpi-value"),
        html.Div(label, className="kpi-label"),
        delta_el,
    ], className="kpi-card", style={"borderLeftColor": border_color})


def build_kpi_row(positions_df, weekly_df, pipeline_df):
    """Build the KPI summary row."""
    k = compute_kpis(positions_df, weekly_df, pipeline_df)

    return dbc.Row([
        dbc.Col(_card(k["open_hc"], "Open Requisitions", AMADEUS_NAVY,
                       delta=f"{k['open_delta']:+d} WoW",
                       delta_type="negative" if k["open_delta"] < 0 else "neutral"),
                xs=6, sm=4, md=3, lg=2),
        dbc.Col(_card(k["future_fill"], "Future Fill", AMADEUS_ORANGE),
                xs=6, sm=4, md=3, lg=2),
        dbc.Col(_card(k["filled_hc"], "Filled Requisitions", AMADEUS_GREEN,
                       delta=f"+{k['filled_delta']} WoW",
                       delta_type="positive"),
                xs=6, sm=4, md=3, lg=2),
        dbc.Col(_card(f"{k['fill_rate']}%", "Fill Rate", AMADEUS_CYAN),
                xs=6, sm=4, md=3, lg=2),
        dbc.Col(_card(f"{k['total_pipeline']:,}", "Candidates in Pipeline", AMADEUS_PURPLE,
                       delta=f"{k['total_offers']} offers, {k['ready_to_hire']} ready",
                       delta_type="neutral"),
                xs=6, sm=4, md=3, lg=2),
        dbc.Col(_card(k["num_locations"], "Locations", "#4A4A68",
                       delta=f"{k['num_bus']} Business Units",
                       delta_type="neutral"),
                xs=6, sm=4, md=3, lg=2),
    ], className="g-3 mb-4")
