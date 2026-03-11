"""
Amadeus Global Ramp-Up Analysis Dashboard
==========================================
Main application file. Run with: python -m ramp_up_dashboard.app
"""

import base64
import io
from datetime import datetime

import dash
from dash import html, dcc, Input, Output, State, dash_table, callback_context
import dash_bootstrap_components as dbc
import pandas as pd

from .data.data_loader import load_data
from .theme import CUSTOM_CSS, AMADEUS_NAVY, AMADEUS_DARK_BLUE, AMADEUS_WHITE, BG_PAGE
from .modules.kpi_cards import build_kpi_row
from .modules.filters import build_filter_panel
from .modules import charts
from .modules.export import export_to_excel, generate_pdf_html

# ── Load data ─────────────────────────────────────────────────────────────────
positions_df, weekly_df, pipeline_df, nexus_df, locations_df = load_data()

MONTH_COLUMNS = [
    "1/1/2026", "2/1/2026", "3/1/2026", "4/1/2026", "5/1/2026",
    "6/1/2026", "7/1/2026", "8/1/2026", "9/1/2026", "10/1/2026", "11/1/2026",
]

# ── App setup ─────────────────────────────────────────────────────────────────
app = dash.Dash(
    __name__,
    external_stylesheets=[
        dbc.themes.BOOTSTRAP,
        "https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap",
    ],
    suppress_callback_exceptions=True,
    title="Amadeus Ramp-Up Dashboard",
)

app.index_string = '''<!DOCTYPE html>
<html>
<head>
{%metas%}
<title>{%title%}</title>
{%favicon%}
{%css%}
<style>''' + CUSTOM_CSS + '''</style>
</head>
<body>
{%app_entry%}
<footer>
{%config%}
{%scripts%}
{%renderer%}
</footer>
</body>
</html>'''


# ══════════════════════════════════════════════════════════════════════════════
# LAYOUT
# ══════════════════════════════════════════════════════════════════════════════

def build_header():
    return html.Div([
        dbc.Row([
            dbc.Col([
                html.H1("Global Ramp-Ups | Talent Acquisition Dashboard"),
                html.P("Amadeus — Nexus Replacements — Real-time ramp-up tracking and analytics"),
            ], width=8),
            dbc.Col([
                html.Div([
                    html.Div(datetime.now().strftime("%d %B %Y"), style={
                        "fontSize": "18px", "fontWeight": "600", "textAlign": "right"
                    }),
                    html.Div([
                        dbc.Button("Export Excel", id="btn-export-excel", className="me-2",
                                   size="sm", color="light", outline=True,
                                   style={"fontWeight": "600"}),
                        dbc.Button("Export PDF", id="btn-export-pdf",
                                   size="sm", color="light", outline=True,
                                   style={"fontWeight": "600"}),
                    ], className="mt-2", style={"textAlign": "right"}),
                ]),
            ], width=4),
        ]),
        dcc.Download(id="download-excel"),
        dcc.Download(id="download-pdf"),
    ], className="main-header")


def build_tab_overview(df):
    return html.Div([
        dbc.Row([
            dbc.Col(html.Div([dcc.Graph(figure=charts.chart_status_donut(df))], className="chart-card"), md=4),
            dbc.Col(html.Div([dcc.Graph(figure=charts.chart_bu_breakdown(df))], className="chart-card"), md=4),
            dbc.Col(html.Div([dcc.Graph(figure=charts.chart_region_breakdown(df))], className="chart-card"), md=4),
        ]),
        dbc.Row([
            dbc.Col(html.Div([dcc.Graph(figure=charts.chart_location_bars(df))], className="chart-card"), md=6),
            dbc.Col(html.Div([dcc.Graph(figure=charts.chart_country_treemap(df))], className="chart-card"), md=6),
        ]),
        dbc.Row([
            dbc.Col(html.Div([dcc.Graph(figure=charts.chart_org_path_heatmap(df))], className="chart-card"), md=12),
        ]),
    ])


def build_tab_weekly():
    return html.Div([
        dbc.Row([
            dbc.Col(html.Div([dcc.Graph(figure=charts.chart_weekly_open_vs_filled(weekly_df))], className="chart-card"), md=12),
        ]),
        dbc.Row([
            dbc.Col(html.Div([dcc.Graph(figure=charts.chart_weekly_velocity(weekly_df))], className="chart-card"), md=6),
            dbc.Col(html.Div([dcc.Graph(figure=charts.chart_fill_rate_trend(weekly_df))], className="chart-card"), md=6),
        ]),
        dbc.Row([
            dbc.Col(html.Div([dcc.Graph(figure=charts.chart_cumulative_trend(weekly_df))], className="chart-card"), md=12),
        ]),
    ])


def build_tab_pipeline():
    return html.Div([
        dbc.Row([
            dbc.Col(html.Div([dcc.Graph(figure=charts.chart_pipeline_funnel(pipeline_df))], className="chart-card"), md=6),
            dbc.Col(html.Div([dcc.Graph(figure=charts.chart_reqs_vs_pipeline(pipeline_df))], className="chart-card"), md=6),
        ]),
        dbc.Row([
            dbc.Col(html.Div([dcc.Graph(figure=charts.chart_pipeline_by_bu(pipeline_df))], className="chart-card"), md=6),
            dbc.Col(html.Div([dcc.Graph(figure=charts.chart_pipeline_stacked(pipeline_df))], className="chart-card"), md=6),
        ]),
        # Pipeline data table
        dbc.Row([
            dbc.Col(html.Div([
                html.H3("Candidate Pipeline Detail", style={"color": "#003B73", "marginBottom": "12px"}),
                dash_table.DataTable(
                    data=pipeline_df.to_dict("records"),
                    columns=[{"name": c, "id": c} for c in pipeline_df.columns],
                    style_header={
                        "backgroundColor": "#005EB8", "color": "white", "fontWeight": "bold",
                        "textAlign": "center", "fontSize": "13px",
                    },
                    style_cell={
                        "textAlign": "center", "padding": "10px", "fontSize": "13px",
                        "fontFamily": "Inter, sans-serif",
                    },
                    style_data_conditional=[
                        {"if": {"row_index": "odd"}, "backgroundColor": "#F5F7FA"},
                    ],
                ),
            ], className="chart-card"), md=12),
        ]),
    ])


def build_tab_nexus():
    return html.Div([
        dbc.Row([
            dbc.Col(html.Div([dcc.Graph(figure=charts.chart_nexus_monthly_by_bu(nexus_df))], className="chart-card"), md=6),
            dbc.Col(html.Div([dcc.Graph(figure=charts.chart_nexus_bu_totals(nexus_df))], className="chart-card"), md=6),
        ]),
        dbc.Row([
            dbc.Col(html.Div([dcc.Graph(figure=charts.chart_nexus_monthly_by_region(nexus_df))], className="chart-card"), md=6),
            dbc.Col(html.Div([dcc.Graph(figure=charts.chart_nexus_cumulative(nexus_df))], className="chart-card"), md=6),
        ]),
        # Nexus data table
        dbc.Row([
            dbc.Col(html.Div([
                html.H3("2026 Nexus Monthly Plan", style={"color": "#003B73", "marginBottom": "12px"}),
                dash_table.DataTable(
                    data=nexus_df.to_dict("records"),
                    columns=[{"name": c, "id": c} for c in nexus_df.columns],
                    style_header={
                        "backgroundColor": "#005EB8", "color": "white", "fontWeight": "bold",
                        "textAlign": "center", "fontSize": "13px",
                    },
                    style_cell={
                        "textAlign": "center", "padding": "10px", "fontSize": "13px",
                        "fontFamily": "Inter, sans-serif",
                    },
                    style_data_conditional=[
                        {"if": {"row_index": "odd"}, "backgroundColor": "#F5F7FA"},
                    ],
                ),
            ], className="chart-card"), md=12),
        ]),
    ])


def build_tab_locations():
    return html.Div([
        dbc.Row([
            dbc.Col(html.Div([dcc.Graph(figure=charts.chart_location_open_vs_filled(locations_df))], className="chart-card"), md=4),
            dbc.Col(html.Div([dcc.Graph(figure=charts.chart_location_deltas(locations_df))], className="chart-card"), md=4),
            dbc.Col(html.Div([dcc.Graph(figure=charts.chart_location_fill_rate(locations_df))], className="chart-card"), md=4),
        ]),
        # Locations data table
        dbc.Row([
            dbc.Col(html.Div([
                html.H3("Key Locations Summary", style={"color": "#003B73", "marginBottom": "12px"}),
                dash_table.DataTable(
                    data=locations_df.to_dict("records"),
                    columns=[{"name": c, "id": c} for c in locations_df.columns],
                    style_header={
                        "backgroundColor": "#005EB8", "color": "white", "fontWeight": "bold",
                        "textAlign": "center", "fontSize": "13px",
                    },
                    style_cell={
                        "textAlign": "center", "padding": "10px", "fontSize": "13px",
                        "fontFamily": "Inter, sans-serif",
                    },
                    style_data_conditional=[
                        {"if": {"row_index": "odd"}, "backgroundColor": "#F5F7FA"},
                        {"if": {"filter_query": "{Filled Delta} > 0", "column_id": "Filled Delta"},
                         "color": "#00A651", "fontWeight": "bold"},
                        {"if": {"filter_query": "{Open Delta} < 0", "column_id": "Open Delta"},
                         "color": "#E74C3C"},
                    ],
                ),
            ], className="chart-card"), md=12),
        ]),
    ])


def build_tab_analytics(df):
    return html.Div([
        dbc.Row([
            dbc.Col(html.Div([dcc.Graph(figure=charts.chart_completion_gauge(df, 310))], className="chart-card"), md=4),
            dbc.Col(html.Div([dcc.Graph(figure=charts.chart_monthly_headcount_plan(df))], className="chart-card"), md=8),
        ]),
        dbc.Row([
            dbc.Col(html.Div([dcc.Graph(figure=charts.chart_bu_monthly_stacked(df))], className="chart-card"), md=6),
            dbc.Col(html.Div([dcc.Graph(figure=charts.chart_bu_region_heatmap(df))], className="chart-card"), md=6),
        ]),
        dbc.Row([
            dbc.Col(html.Div([dcc.Graph(figure=charts.chart_grand_total_distribution(df))], className="chart-card"), md=6),
            dbc.Col(html.Div([dcc.Graph(figure=charts.chart_top_countries(df))], className="chart-card"), md=6),
        ]),
    ])


def build_tab_data(df):
    """Full data table with search and sort."""
    display_cols = ["BU", "Org Path Name", "Region", "Country", "Location", "Status"] + MONTH_COLUMNS + ["Grand Total"]
    available_cols = [c for c in display_cols if c in df.columns]

    return html.Div([
        dbc.Row([
            dbc.Col([
                html.Div([
                    html.H3("Position Data Table", style={"color": "#003B73", "marginBottom": "12px"}),
                    html.P(f"Showing {len(df)} rows", style={"color": "#8E8EA0", "fontSize": "13px"}),
                    dash_table.DataTable(
                        id="main-data-table",
                        data=df.to_dict("records"),
                        columns=[{"name": c, "id": c, "selectable": True} for c in available_cols],
                        filter_action="native",
                        sort_action="native",
                        sort_mode="multi",
                        page_size=25,
                        page_action="native",
                        style_header={
                            "backgroundColor": "#005EB8", "color": "white", "fontWeight": "bold",
                            "textAlign": "center", "fontSize": "12px", "whiteSpace": "normal",
                        },
                        style_cell={
                            "textAlign": "center", "padding": "8px 10px", "fontSize": "12px",
                            "fontFamily": "Inter, sans-serif", "minWidth": "80px",
                            "maxWidth": "200px", "overflow": "hidden", "textOverflow": "ellipsis",
                        },
                        style_data_conditional=[
                            {"if": {"row_index": "odd"}, "backgroundColor": "#F5F7FA"},
                            {"if": {"filter_query": '{Status} = "Filled"', "column_id": "Status"},
                             "backgroundColor": "#D5F5E3", "fontWeight": "bold"},
                            {"if": {"filter_query": '{Status} = "Open"', "column_id": "Status"},
                             "backgroundColor": "#D6EAF8", "fontWeight": "bold"},
                            {"if": {"filter_query": '{Status} = "Future Fill"', "column_id": "Status"},
                             "backgroundColor": "#FDEBD0", "fontWeight": "bold"},
                        ],
                        style_table={"overflowX": "auto"},
                        export_format="csv",
                    ),
                ], className="chart-card"),
            ], md=12),
        ]),
    ])


# ── Main layout ───────────────────────────────────────────────────────────────
app.layout = html.Div([
    build_header(),
    dbc.Container([
        # KPI row
        html.Div(id="kpi-row-container"),
        # Filters
        build_filter_panel(positions_df),
        html.Div(style={"height": "12px"}),
        # Tabs
        dcc.Tabs(id="main-tabs", value="overview", className="custom-tabs", children=[
            dcc.Tab(label="Executive Overview", value="overview", className="tab"),
            dcc.Tab(label="Weekly Tracking", value="weekly", className="tab"),
            dcc.Tab(label="Candidate Pipeline", value="pipeline", className="tab"),
            dcc.Tab(label="Nexus Monthly", value="nexus", className="tab"),
            dcc.Tab(label="Key Locations", value="locations", className="tab"),
            dcc.Tab(label="Analytics", value="analytics", className="tab"),
            dcc.Tab(label="Data Table", value="datatable", className="tab"),
        ]),
        html.Div(id="tab-content", className="mt-3"),
    ], fluid=True, style={"padding": "0 20px"}),
    # Footer
    html.Div([
        html.Hr(style={"borderColor": "#D1D1DB"}),
        html.P([
            "Amadeus Global Ramp-Up Dashboard",
            html.Span(" | ", style={"color": "#D1D1DB"}),
            "Talent Acquisition",
            html.Span(" | ", style={"color": "#D1D1DB"}),
            html.Span(f"Data as of {datetime.now().strftime('%d %B %Y')}", style={"color": "#8E8EA0"}),
        ], style={"textAlign": "center", "color": "#4A4A68", "fontSize": "12px"}),
    ], style={"padding": "10px 30px 20px"}),
], style={"backgroundColor": BG_PAGE, "minHeight": "100vh"})


# ══════════════════════════════════════════════════════════════════════════════
# CALLBACKS
# ══════════════════════════════════════════════════════════════════════════════

def apply_filters(df, bu, region, country, location, org, status):
    """Apply dropdown filters to the positions dataframe."""
    filtered = df.copy()
    if bu:
        filtered = filtered[filtered["BU"].isin(bu)]
    if region:
        filtered = filtered[filtered["Region"].isin(region)]
    if country:
        filtered = filtered[filtered["Country"].isin(country)]
    if location:
        filtered = filtered[filtered["Location"].isin(location)]
    if org:
        filtered = filtered[filtered["Org Path Name"].isin(org)]
    if status:
        filtered = filtered[filtered["Status"].isin(status)]
    return filtered


@app.callback(
    [Output("tab-content", "children"),
     Output("kpi-row-container", "children")],
    [Input("main-tabs", "value"),
     Input("filter-bu", "value"),
     Input("filter-region", "value"),
     Input("filter-country", "value"),
     Input("filter-location", "value"),
     Input("filter-org", "value"),
     Input("filter-status", "value")],
)
def update_tab(tab, bu, region, country, location, org, status):
    filtered = apply_filters(positions_df, bu, region, country, location, org, status)

    # KPI row always shows
    kpi_row = build_kpi_row(filtered, weekly_df, pipeline_df)

    if tab == "overview":
        return build_tab_overview(filtered), kpi_row
    elif tab == "weekly":
        return build_tab_weekly(), kpi_row
    elif tab == "pipeline":
        return build_tab_pipeline(), kpi_row
    elif tab == "nexus":
        return build_tab_nexus(), kpi_row
    elif tab == "locations":
        return build_tab_locations(), kpi_row
    elif tab == "analytics":
        return build_tab_analytics(filtered), kpi_row
    elif tab == "datatable":
        return build_tab_data(filtered), kpi_row
    return html.Div("Select a tab"), kpi_row


@app.callback(
    Output("download-excel", "data"),
    Input("btn-export-excel", "n_clicks"),
    [State("filter-bu", "value"),
     State("filter-region", "value"),
     State("filter-country", "value"),
     State("filter-location", "value"),
     State("filter-org", "value"),
     State("filter-status", "value")],
    prevent_initial_call=True,
)
def download_excel(n_clicks, bu, region, country, location, org, status):
    if not n_clicks:
        return dash.no_update
    filtered = apply_filters(positions_df, bu, region, country, location, org, status)
    excel_bytes = export_to_excel(filtered, weekly_df, pipeline_df, nexus_df, locations_df)
    now = datetime.now().strftime("%Y%m%d_%H%M")
    return dcc.send_bytes(excel_bytes, f"Amadeus_RampUp_Report_{now}.xlsx")


@app.callback(
    Output("download-pdf", "data"),
    Input("btn-export-pdf", "n_clicks"),
    [State("filter-bu", "value"),
     State("filter-region", "value"),
     State("filter-country", "value"),
     State("filter-location", "value"),
     State("filter-org", "value"),
     State("filter-status", "value")],
    prevent_initial_call=True,
)
def download_pdf(n_clicks, bu, region, country, location, org, status):
    if not n_clicks:
        return dash.no_update
    filtered = apply_filters(positions_df, bu, region, country, location, org, status)
    html_content = generate_pdf_html(filtered, weekly_df, pipeline_df, nexus_df, locations_df)
    try:
        from weasyprint import HTML
        pdf_bytes = HTML(string=html_content).write_pdf()
        now = datetime.now().strftime("%Y%m%d_%H%M")
        return dcc.send_bytes(pdf_bytes, f"Amadeus_RampUp_Report_{now}.pdf")
    except ImportError:
        # Fallback: export as HTML
        now = datetime.now().strftime("%Y%m%d_%H%M")
        return dcc.send_string(html_content, f"Amadeus_RampUp_Report_{now}.html")


# ── Cascading filter: update country options based on region ──────────────────
@app.callback(
    Output("filter-country", "options"),
    [Input("filter-region", "value"), Input("filter-bu", "value")],
)
def update_country_options(region, bu):
    filtered = positions_df.copy()
    if bu:
        filtered = filtered[filtered["BU"].isin(bu)]
    if region:
        filtered = filtered[filtered["Region"].isin(region)]
    countries = sorted(filtered["Country"].dropna().unique())
    return [{"label": c, "value": c} for c in countries]


@app.callback(
    Output("filter-location", "options"),
    [Input("filter-region", "value"), Input("filter-country", "value"), Input("filter-bu", "value")],
)
def update_location_options(region, country, bu):
    filtered = positions_df.copy()
    if bu:
        filtered = filtered[filtered["BU"].isin(bu)]
    if region:
        filtered = filtered[filtered["Region"].isin(region)]
    if country:
        filtered = filtered[filtered["Country"].isin(country)]
    locations = sorted(filtered["Location"].dropna().unique())
    return [{"label": l, "value": l} for l in locations]


@app.callback(
    Output("filter-org", "options"),
    [Input("filter-bu", "value")],
)
def update_org_options(bu):
    filtered = positions_df.copy()
    if bu:
        filtered = filtered[filtered["BU"].isin(bu)]
    orgs = sorted(filtered["Org Path Name"].dropna().unique())
    return [{"label": o, "value": o} for o in orgs]


# ══════════════════════════════════════════════════════════════════════════════
# RUN
# ══════════════════════════════════════════════════════════════════════════════

server = app.server

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8050)
