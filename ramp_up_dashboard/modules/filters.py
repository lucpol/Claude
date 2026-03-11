"""Filter panel component."""

from dash import html, dcc
import dash_bootstrap_components as dbc


def build_filter_panel(positions_df):
    """Build the global filter panel."""
    bus = sorted(positions_df["BU"].dropna().unique())
    regions = sorted(positions_df["Region"].dropna().unique())
    countries = sorted(positions_df["Country"].dropna().unique())
    locations = sorted(positions_df["Location"].dropna().unique())
    org_paths = sorted(positions_df["Org Path Name"].dropna().unique())
    statuses = sorted(positions_df["Status"].dropna().unique())

    return html.Div([
        dbc.Row([
            dbc.Col([
                html.Label("Business Unit"),
                dcc.Dropdown(
                    id="filter-bu", options=[{"label": b, "value": b} for b in bus],
                    multi=True, placeholder="All BUs",
                    style={"fontSize": "13px"},
                ),
            ], xs=12, sm=6, md=4, lg=2),
            dbc.Col([
                html.Label("Region"),
                dcc.Dropdown(
                    id="filter-region", options=[{"label": r, "value": r} for r in regions],
                    multi=True, placeholder="All Regions",
                    style={"fontSize": "13px"},
                ),
            ], xs=12, sm=6, md=4, lg=2),
            dbc.Col([
                html.Label("Country"),
                dcc.Dropdown(
                    id="filter-country", options=[{"label": c, "value": c} for c in countries],
                    multi=True, placeholder="All Countries",
                    style={"fontSize": "13px"},
                ),
            ], xs=12, sm=6, md=4, lg=2),
            dbc.Col([
                html.Label("Location"),
                dcc.Dropdown(
                    id="filter-location", options=[{"label": l, "value": l} for l in locations],
                    multi=True, placeholder="All Locations",
                    style={"fontSize": "13px"},
                ),
            ], xs=12, sm=6, md=4, lg=2),
            dbc.Col([
                html.Label("Org Path"),
                dcc.Dropdown(
                    id="filter-org", options=[{"label": o, "value": o} for o in org_paths],
                    multi=True, placeholder="All Org Paths",
                    style={"fontSize": "13px"},
                ),
            ], xs=12, sm=6, md=4, lg=2),
            dbc.Col([
                html.Label("Status"),
                dcc.Dropdown(
                    id="filter-status", options=[{"label": s, "value": s} for s in statuses],
                    multi=True, placeholder="All Statuses",
                    style={"fontSize": "13px"},
                ),
            ], xs=12, sm=6, md=4, lg=2),
        ], className="g-2"),
    ], className="filter-panel")
