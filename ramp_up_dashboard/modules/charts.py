"""Charts module — all chart builder functions for the Amadeus Ramp-Up Dashboard."""

import plotly.graph_objects as go
import pandas as pd
import numpy as np
from ..theme import (
    CHART_COLORS, PLOTLY_LAYOUT,
    AMADEUS_NAVY, AMADEUS_CYAN, AMADEUS_GREEN, AMADEUS_ORANGE,
    AMADEUS_RED, AMADEUS_LIGHT_BLUE, AMADEUS_GRAY_300, AMADEUS_DARK_BLUE,
    AMADEUS_PURPLE, AMADEUS_SKY, AMADEUS_WHITE, AMADEUS_GRAY_500,
    BU_COLORS,
)

MONTH_COLUMNS = [
    "1/1/2026", "2/1/2026", "3/1/2026", "4/1/2026", "5/1/2026",
    "6/1/2026", "7/1/2026", "8/1/2026", "9/1/2026", "10/1/2026", "11/1/2026",
]
MONTH_LABELS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov"]


def _apply_layout(fig, title=None, height=400):
    fig.update_layout(**PLOTLY_LAYOUT, height=height)
    if title:
        fig.update_layout(title_text=title)
    return fig


# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 — EXECUTIVE OVERVIEW
# ══════════════════════════════════════════════════════════════════════════════

def chart_status_donut(df):
    """Open / Future Fill / Filled donut."""
    counts = df["Status"].value_counts().reset_index()
    counts.columns = ["Status", "Count"]
    color_map = {"Open": AMADEUS_NAVY, "Future Fill": AMADEUS_ORANGE, "Filled": AMADEUS_GREEN}
    colors = [color_map.get(s, AMADEUS_GRAY_500) for s in counts["Status"]]

    fig = go.Figure(go.Pie(
        labels=counts["Status"], values=counts["Count"],
        hole=0.58,
        marker=dict(colors=colors, line=dict(color=AMADEUS_WHITE, width=2)),
        textinfo="label+value", textfont=dict(size=13),
        hovertemplate="<b>%{label}</b><br>Count: %{value}<br>%{percent}<extra></extra>",
    ))
    total = counts["Count"].sum()
    fig.add_annotation(text=f"<b>{total}</b><br><span style='font-size:12px'>Total Reqs</span>",
                       x=0.5, y=0.5, font_size=22, showarrow=False, font_color=AMADEUS_DARK_BLUE)
    return _apply_layout(fig, "Requisition Status", 380)


def chart_bu_breakdown(df):
    """Horizontal stacked bar: positions by BU and status."""
    cross = pd.crosstab(df["BU"], df["Status"])
    for s in ["Open", "Future Fill", "Filled"]:
        if s not in cross.columns:
            cross[s] = 0
    cross = cross[["Open", "Future Fill", "Filled"]].sort_values("Open", ascending=True)

    color_map = {"Open": AMADEUS_NAVY, "Future Fill": AMADEUS_ORANGE, "Filled": AMADEUS_GREEN}
    fig = go.Figure()
    for status in ["Filled", "Future Fill", "Open"]:
        fig.add_trace(go.Bar(
            y=cross.index, x=cross[status], name=status, orientation="h",
            marker_color=color_map[status],
            text=cross[status], textposition="inside",
        ))
    fig.update_layout(barmode="stack")
    return _apply_layout(fig, "Positions by Business Unit", 350)


def chart_region_breakdown(df):
    """Bar chart by region."""
    counts = df.groupby(["Region", "Status"]).size().reset_index(name="Count")
    color_map = {"Open": AMADEUS_NAVY, "Future Fill": AMADEUS_ORANGE, "Filled": AMADEUS_GREEN}
    fig = go.Figure()
    for status in ["Filled", "Future Fill", "Open"]:
        subset = counts[counts["Status"] == status]
        fig.add_trace(go.Bar(
            x=subset["Region"], y=subset["Count"], name=status,
            marker_color=color_map.get(status, AMADEUS_GRAY_500),
            text=subset["Count"], textposition="outside",
        ))
    fig.update_layout(barmode="group")
    return _apply_layout(fig, "Positions by Region", 380)


def chart_location_bars(df):
    """Top locations bar chart."""
    top = df["Location"].value_counts().head(15).reset_index()
    top.columns = ["Location", "Count"]
    top = top.sort_values("Count", ascending=True)
    fig = go.Figure(go.Bar(
        y=top["Location"], x=top["Count"], orientation="h",
        marker_color=AMADEUS_NAVY,
        text=top["Count"], textposition="outside",
        marker_line_color=AMADEUS_DARK_BLUE, marker_line_width=0.5,
    ))
    return _apply_layout(fig, "Top 15 Locations", 480)


def chart_country_treemap(df):
    """Treemap by country."""
    counts = df.groupby(["Region", "Country"]).size().reset_index(name="Count")
    labels = list(counts["Country"]) + list(counts["Region"].unique()) + ["Global"]
    parents = list(counts["Region"]) + ["Global"] * len(counts["Region"].unique()) + [""]
    values = list(counts["Count"]) + [0] * len(counts["Region"].unique()) + [0]

    fig = go.Figure(go.Treemap(
        labels=labels, parents=parents, values=values,
        branchvalues="total",
        marker=dict(
            colorscale=[[0, AMADEUS_SKY], [1, AMADEUS_DARK_BLUE]],
            line=dict(color=AMADEUS_WHITE, width=1),
        ),
        textinfo="label+value",
        hovertemplate="<b>%{label}</b><br>Positions: %{value}<extra></extra>",
    ))
    return _apply_layout(fig, "Positions by Country & Region", 450)


def chart_org_path_heatmap(df):
    """Heatmap: Org Path vs Month."""
    # Top 20 org paths by total
    top_orgs = df.groupby("Org Path Name")["Grand Total"].sum().nlargest(20).index
    subset = df[df["Org Path Name"].isin(top_orgs)]
    pivot = subset.groupby("Org Path Name")[MONTH_COLUMNS].sum()
    pivot.columns = MONTH_LABELS

    fig = go.Figure(go.Heatmap(
        z=pivot.values, x=pivot.columns.tolist(), y=pivot.index.tolist(),
        colorscale=[[0, AMADEUS_WHITE], [0.3, AMADEUS_SKY], [0.7, AMADEUS_LIGHT_BLUE], [1, AMADEUS_DARK_BLUE]],
        text=pivot.values, texttemplate="%{text}",
        hovertemplate="Org: %{y}<br>Month: %{x}<br>Headcount: %{z}<extra></extra>",
    ))
    return _apply_layout(fig, "Monthly Headcount by Org Path (Top 20)", 520)


# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 — WEEKLY TRACKING
# ══════════════════════════════════════════════════════════════════════════════

def chart_weekly_open_vs_filled(weekly_df):
    """Bar + line: Job Reqs Open (bars) vs Filled (line) — matching PPT style."""
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=weekly_df["Label"], y=weekly_df["Job Reqs Open"],
        name="Job Reqs Open",
        marker_color=AMADEUS_DARK_BLUE,
        text=weekly_df["Job Reqs Open"], textposition="outside",
        textfont=dict(size=11, color=AMADEUS_WHITE),
    ))
    fig.add_trace(go.Scatter(
        x=weekly_df["Label"], y=weekly_df["Job Reqs Filled"],
        name="Job Reqs Filled", mode="lines+markers+text",
        line=dict(color=AMADEUS_SKY, width=3),
        marker=dict(size=8, color=AMADEUS_SKY),
        text=weekly_df["Job Reqs Filled"], textposition="top center",
        textfont=dict(size=11, color=AMADEUS_LIGHT_BLUE),
    ))
    fig.update_layout(
        yaxis2=dict(overlaying="y", side="right", showgrid=False,
                    range=[0, max(weekly_df["Job Reqs Filled"].max() * 1.2, 300)]),
    )
    return _apply_layout(fig, "Job Requisitions Open vs Filled by Week", 450)


def chart_weekly_velocity(weekly_df):
    """Weekly new openings and fills."""
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=weekly_df["Label"], y=weekly_df["New Opened This Week"],
        name="New Opened", marker_color=AMADEUS_NAVY,
    ))
    fig.add_trace(go.Bar(
        x=weekly_df["Label"], y=weekly_df["New Filled This Week"],
        name="New Filled", marker_color=AMADEUS_GREEN,
    ))
    fig.update_layout(barmode="group")
    return _apply_layout(fig, "Weekly Velocity: New Opens vs Fills", 380)


def chart_fill_rate_trend(weekly_df):
    """Fill rate % over time."""
    fig = go.Figure(go.Scatter(
        x=weekly_df["Label"], y=weekly_df["Fill Rate (%)"],
        mode="lines+markers+text",
        line=dict(color=AMADEUS_CYAN, width=3),
        marker=dict(size=8),
        text=[f"{v}%" for v in weekly_df["Fill Rate (%)"]],
        textposition="top center",
        fill="tozeroy", fillcolor="rgba(0,178,169,0.08)",
    ))
    fig.add_hline(y=50, line_dash="dash", line_color=AMADEUS_GRAY_300,
                  annotation_text="50% Milestone")
    return _apply_layout(fig, "Fill Rate Over Time (%)", 350)


def chart_cumulative_trend(weekly_df):
    """Cumulative total reqs and filled."""
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=weekly_df["Label"], y=weekly_df["Total Reqs (Cumulative)"],
        name="Total Reqs (Open + Filled)", mode="lines+markers",
        line=dict(color=AMADEUS_NAVY, width=3),
        fill="tozeroy", fillcolor="rgba(0,94,184,0.06)",
    ))
    fig.add_trace(go.Scatter(
        x=weekly_df["Label"], y=weekly_df["Job Reqs Filled"],
        name="Filled (Cumulative)", mode="lines+markers",
        line=dict(color=AMADEUS_GREEN, width=3),
        fill="tozeroy", fillcolor="rgba(0,166,81,0.06)",
    ))
    fig.add_trace(go.Scatter(
        x=weekly_df["Label"], y=weekly_df["Job Reqs Open"],
        name="Still Open", mode="lines+markers",
        line=dict(color=AMADEUS_ORANGE, width=2, dash="dash"),
    ))
    return _apply_layout(fig, "Cumulative Ramp-Up Progress", 400)


# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 — CANDIDATE PIPELINE
# ══════════════════════════════════════════════════════════════════════════════

def chart_pipeline_funnel(pipeline_df):
    """Funnel chart of candidate pipeline stages."""
    stages = ["Review", "Manager Review", "Screen", "Assessment", "Interview", "Offer", "Ready for Hire"]
    totals = [pipeline_df[s].sum() for s in stages]

    fig = go.Figure(go.Funnel(
        y=stages, x=totals,
        textinfo="value+percent initial",
        marker=dict(color=[
            AMADEUS_NAVY, AMADEUS_LIGHT_BLUE, AMADEUS_CYAN,
            AMADEUS_PURPLE, AMADEUS_ORANGE, AMADEUS_GREEN, "#00A651",
        ]),
        connector=dict(line=dict(color=AMADEUS_GRAY_300)),
    ))
    return _apply_layout(fig, "Candidate Pipeline Funnel (All BUs)", 450)


def chart_pipeline_by_bu(pipeline_df):
    """Grouped bar of pipeline stages per BU."""
    stages = ["Review", "Manager Review", "Screen", "Assessment", "Interview", "Offer", "Ready for Hire"]
    colors = [AMADEUS_NAVY, AMADEUS_LIGHT_BLUE, AMADEUS_CYAN,
              AMADEUS_PURPLE, AMADEUS_ORANGE, AMADEUS_GREEN, "#00A651"]

    fig = go.Figure()
    for i, stage in enumerate(stages):
        fig.add_trace(go.Bar(
            x=pipeline_df["BU"], y=pipeline_df[stage],
            name=stage, marker_color=colors[i],
            text=pipeline_df[stage], textposition="outside",
        ))
    fig.update_layout(barmode="group")
    return _apply_layout(fig, "Pipeline Stages by Business Unit", 420)


def chart_pipeline_stacked(pipeline_df):
    """100% stacked bar showing conversion ratios per BU."""
    stages = ["Review", "Manager Review", "Screen", "Assessment", "Interview", "Offer", "Ready for Hire"]
    colors = [AMADEUS_NAVY, AMADEUS_LIGHT_BLUE, AMADEUS_CYAN,
              AMADEUS_PURPLE, AMADEUS_ORANGE, AMADEUS_GREEN, "#00A651"]

    fig = go.Figure()
    for i, stage in enumerate(stages):
        fig.add_trace(go.Bar(
            x=pipeline_df["BU"], y=pipeline_df[stage],
            name=stage, marker_color=colors[i],
        ))
    fig.update_layout(barmode="stack")
    return _apply_layout(fig, "Pipeline Composition by BU (Stacked)", 400)


def chart_reqs_vs_pipeline(pipeline_df):
    """Scatter: Job Requisitions vs total pipeline size."""
    pipeline_df = pipeline_df.copy()
    stages = ["Review", "Manager Review", "Screen", "Assessment", "Interview", "Offer", "Ready for Hire"]
    pipeline_df["Total Pipeline"] = pipeline_df[stages].sum(axis=1)

    fig = go.Figure()
    for i, row in pipeline_df.iterrows():
        fig.add_trace(go.Scatter(
            x=[row["Job Requisitions"]], y=[row["Total Pipeline"]],
            mode="markers+text", text=[row["BU"]],
            textposition="top center",
            marker=dict(size=max(20, row["Total Pipeline"] / 30),
                        color=list(BU_COLORS.values())[i % len(BU_COLORS)],
                        opacity=0.8, line=dict(color=AMADEUS_DARK_BLUE, width=1)),
            name=row["BU"],
            hovertemplate=f"<b>{row['BU']}</b><br>Reqs: {row['Job Requisitions']}<br>Pipeline: {row['Total Pipeline']}<extra></extra>",
        ))
    fig.update_layout(showlegend=False,
                      xaxis_title="Open Job Requisitions",
                      yaxis_title="Total Candidates in Pipeline")
    return _apply_layout(fig, "Requisitions vs Pipeline Size", 400)


# ══════════════════════════════════════════════════════════════════════════════
# TAB 4 — NEXUS MONTHLY RAMP-UP
# ══════════════════════════════════════════════════════════════════════════════

def chart_nexus_monthly_by_bu(nexus_df):
    """Stacked bar: monthly Nexus replacements by BU."""
    month_names = ["January", "February", "March", "April", "May", "June",
                   "July", "August", "September", "October", "November"]
    bu_totals = nexus_df.groupby("BU")[month_names].sum()

    fig = go.Figure()
    for i, bu in enumerate(bu_totals.index):
        fig.add_trace(go.Bar(
            x=month_names, y=bu_totals.loc[bu],
            name=bu,
            marker_color=list(BU_COLORS.values())[i % len(BU_COLORS)],
            text=bu_totals.loc[bu], textposition="inside",
        ))
    fig.update_layout(barmode="stack")
    return _apply_layout(fig, "2026 Nexus Ramp-Up by Month & BU", 420)


def chart_nexus_monthly_by_region(nexus_df):
    """Monthly by region."""
    month_names = ["January", "February", "March", "April", "May", "June",
                   "July", "August", "September", "October", "November"]
    region_totals = nexus_df.groupby("Region")[month_names].sum()
    region_colors = {"Americas": AMADEUS_NAVY, "APAC": AMADEUS_CYAN, "EMEA": AMADEUS_ORANGE, "TBD": AMADEUS_GRAY_500}

    fig = go.Figure()
    for region in region_totals.index:
        fig.add_trace(go.Bar(
            x=month_names, y=region_totals.loc[region],
            name=region,
            marker_color=region_colors.get(region, AMADEUS_PURPLE),
        ))
    fig.update_layout(barmode="stack")
    return _apply_layout(fig, "2026 Nexus Ramp-Up by Month & Region", 420)


def chart_nexus_cumulative(nexus_df):
    """Cumulative Nexus replacements over months."""
    month_names = ["January", "February", "March", "April", "May", "June",
                   "July", "August", "September", "October", "November"]
    monthly_totals = nexus_df[month_names].sum()
    cumulative = monthly_totals.cumsum()

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=month_names, y=monthly_totals.values,
        name="Monthly", marker_color=AMADEUS_LIGHT_BLUE,
        text=monthly_totals.values.astype(int), textposition="outside",
    ))
    fig.add_trace(go.Scatter(
        x=month_names, y=cumulative.values,
        name="Cumulative", mode="lines+markers+text",
        line=dict(color=AMADEUS_DARK_BLUE, width=3),
        text=cumulative.values.astype(int), textposition="top center",
    ))
    total = int(cumulative.values[-1])
    fig.add_hline(y=total, line_dash="dot", line_color=AMADEUS_GREEN,
                  annotation_text=f"Total: {total}")
    return _apply_layout(fig, "Nexus Ramp-Up: Monthly & Cumulative", 420)


def chart_nexus_bu_totals(nexus_df):
    """BU total Nexus replacements donut."""
    bu_totals = nexus_df.groupby("BU")["Total"].sum().reset_index()
    fig = go.Figure(go.Pie(
        labels=bu_totals["BU"], values=bu_totals["Total"],
        hole=0.55,
        marker=dict(colors=[BU_COLORS.get(bu, AMADEUS_NAVY) for bu in bu_totals["BU"]],
                    line=dict(color=AMADEUS_WHITE, width=2)),
        textinfo="label+value+percent",
    ))
    total = bu_totals["Total"].sum()
    fig.add_annotation(text=f"<b>{total}</b><br>Total", x=0.5, y=0.5,
                       font_size=20, showarrow=False, font_color=AMADEUS_DARK_BLUE)
    return _apply_layout(fig, "Nexus Replacements by BU", 380)


# ══════════════════════════════════════════════════════════════════════════════
# TAB 5 — KEY LOCATIONS
# ══════════════════════════════════════════════════════════════════════════════

def chart_location_open_vs_filled(loc_df):
    """Grouped bar: open vs filled by key location."""
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=loc_df["Location"], y=loc_df["Open"],
        name="Open", marker_color=AMADEUS_NAVY,
        text=loc_df["Open"], textposition="outside",
    ))
    fig.add_trace(go.Bar(
        x=loc_df["Location"], y=loc_df["Filled"],
        name="Filled", marker_color=AMADEUS_GREEN,
        text=loc_df["Filled"], textposition="outside",
    ))
    fig.update_layout(barmode="group")
    return _apply_layout(fig, "Key Locations: Open vs Filled", 400)


def chart_location_deltas(loc_df):
    """Week-over-week delta by location."""
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=loc_df["Location"], y=loc_df["Open Delta"],
        name="Open WoW Change", marker_color=AMADEUS_ORANGE,
        text=loc_df["Open Delta"], textposition="outside",
    ))
    fig.add_trace(go.Bar(
        x=loc_df["Location"], y=loc_df["Filled Delta"],
        name="Filled WoW Change", marker_color=AMADEUS_GREEN,
        text=loc_df["Filled Delta"], textposition="outside",
    ))
    fig.update_layout(barmode="group")
    return _apply_layout(fig, "Weekly Changes by Location", 380)


def chart_location_fill_rate(loc_df):
    """Fill rate gauge per location."""
    loc_df = loc_df.copy()
    loc_df["Total"] = loc_df["Open"] + loc_df["Filled"]
    loc_df["Fill Rate"] = (loc_df["Filled"] / loc_df["Total"] * 100).round(1)
    loc_df = loc_df.sort_values("Fill Rate", ascending=True)

    fig = go.Figure(go.Bar(
        y=loc_df["Location"], x=loc_df["Fill Rate"],
        orientation="h",
        marker_color=[AMADEUS_GREEN if r >= 50 else AMADEUS_ORANGE if r >= 30 else AMADEUS_RED
                      for r in loc_df["Fill Rate"]],
        text=[f"{v}%" for v in loc_df["Fill Rate"]], textposition="outside",
    ))
    fig.add_vline(x=50, line_dash="dash", line_color=AMADEUS_GRAY_300,
                  annotation_text="50%")
    return _apply_layout(fig, "Fill Rate by Key Location (%)", 350)


# ══════════════════════════════════════════════════════════════════════════════
# TAB 6 — ANALYTICS / DEEP DIVE
# ══════════════════════════════════════════════════════════════════════════════

def chart_monthly_headcount_plan(df):
    """Area chart of planned monthly headcount additions."""
    monthly = df[MONTH_COLUMNS].sum()
    monthly.index = MONTH_LABELS

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=MONTH_LABELS, y=monthly.values,
        mode="lines+markers+text",
        fill="tozeroy", fillcolor="rgba(0,94,184,0.1)",
        line=dict(color=AMADEUS_NAVY, width=3),
        text=monthly.values.astype(int), textposition="top center",
    ))
    return _apply_layout(fig, "Planned Headcount Additions by Month", 380)


def chart_bu_monthly_stacked(df):
    """Stacked area: monthly headcount by BU."""
    bu_monthly = df.groupby("BU")[MONTH_COLUMNS].sum()
    bu_monthly.columns = MONTH_LABELS

    fig = go.Figure()
    for i, bu in enumerate(bu_monthly.index):
        fig.add_trace(go.Scatter(
            x=MONTH_LABELS, y=bu_monthly.loc[bu].values,
            name=bu, mode="lines",
            stackgroup="one",
            line=dict(color=list(BU_COLORS.values())[i % len(BU_COLORS)]),
        ))
    return _apply_layout(fig, "Monthly Headcount Plan by BU", 400)


def chart_grand_total_distribution(df):
    """Histogram of Grand Total per position row."""
    fig = go.Figure(go.Histogram(
        x=df["Grand Total"], nbinsx=25,
        marker_color=AMADEUS_NAVY,
        marker_line_color=AMADEUS_DARK_BLUE, marker_line_width=1,
    ))
    avg = df["Grand Total"].mean()
    fig.add_vline(x=avg, line_dash="dash", line_color=AMADEUS_RED,
                  annotation_text=f"Avg: {avg:.1f}")
    return _apply_layout(fig, "Distribution of Headcount per Requisition", 350)


def chart_bu_region_heatmap(df):
    """Heatmap: BU x Region."""
    cross = pd.crosstab(df["BU"], df["Region"])
    fig = go.Figure(go.Heatmap(
        z=cross.values, x=cross.columns.tolist(), y=cross.index.tolist(),
        colorscale=[[0, AMADEUS_WHITE], [0.5, AMADEUS_SKY], [1, AMADEUS_DARK_BLUE]],
        text=cross.values, texttemplate="%{text}",
        hovertemplate="BU: %{y}<br>Region: %{x}<br>Count: %{z}<extra></extra>",
    ))
    return _apply_layout(fig, "BU x Region Matrix", 320)


def chart_top_countries(df):
    """Top 15 countries by total headcount."""
    country_totals = df.groupby("Country")["Grand Total"].sum().nlargest(15).reset_index()
    country_totals = country_totals.sort_values("Grand Total", ascending=True)
    fig = go.Figure(go.Bar(
        y=country_totals["Country"], x=country_totals["Grand Total"],
        orientation="h", marker_color=AMADEUS_CYAN,
        text=country_totals["Grand Total"], textposition="outside",
    ))
    return _apply_layout(fig, "Top 15 Countries by Headcount", 450)


def chart_completion_gauge(df, total_target=310):
    """Overall completion gauge (310 = total from Nexus PPT)."""
    filled = len(df[df["Status"] == "Filled"]) if "Status" in df.columns else 0
    # Use Grand Total sum of filled rows
    filled_total = df[df["Status"] == "Filled"]["Grand Total"].sum() if "Status" in df.columns else 0
    pct = round(filled_total / total_target * 100, 1) if total_target > 0 else 0

    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=pct,
        number=dict(suffix="%", font=dict(size=48, color=AMADEUS_DARK_BLUE)),
        delta=dict(reference=100, suffix="%"),
        gauge=dict(
            axis=dict(range=[0, 100], tickcolor=AMADEUS_GRAY_300),
            bar=dict(color=AMADEUS_GREEN if pct >= 75 else AMADEUS_ORANGE if pct >= 50 else AMADEUS_RED),
            bgcolor=AMADEUS_SKY,
            steps=[
                dict(range=[0, 50], color="#FDEBD0"),
                dict(range=[50, 75], color="#D5F5E3"),
                dict(range=[75, 100], color="#ABEBC6"),
            ],
            threshold=dict(line=dict(color=AMADEUS_RED, width=4), thickness=0.8, value=100),
        ),
        title=dict(text=f"Filled: {int(filled_total)} / Target: {total_target}", font=dict(size=14)),
    ))
    return _apply_layout(fig, "Ramp-Up Completion", 350)
