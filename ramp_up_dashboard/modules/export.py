"""Export module — PDF and Excel exports."""

import io
import base64
from datetime import datetime
import pandas as pd


MONTH_COLUMNS = [
    "1/1/2026", "2/1/2026", "3/1/2026", "4/1/2026", "5/1/2026",
    "6/1/2026", "7/1/2026", "8/1/2026", "9/1/2026", "10/1/2026", "11/1/2026",
]
MONTH_LABELS = ["Jan 2026", "Feb 2026", "Mar 2026", "Apr 2026", "May 2026",
                "Jun 2026", "Jul 2026", "Aug 2026", "Sep 2026", "Oct 2026", "Nov 2026"]


def export_to_excel(positions_df, weekly_df, pipeline_df, nexus_df, locations_df):
    """Export all data to a multi-sheet Excel file. Returns bytes."""
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        workbook = writer.book

        # ── Formats ───────────────────────────────────────────────────────
        header_fmt = workbook.add_format({
            "bold": True, "bg_color": "#005EB8", "font_color": "white",
            "border": 1, "text_wrap": True, "align": "center", "valign": "vcenter",
            "font_name": "Calibri", "font_size": 11,
        })
        data_fmt = workbook.add_format({
            "border": 1, "font_name": "Calibri", "font_size": 10,
            "align": "center", "valign": "vcenter",
        })
        num_fmt = workbook.add_format({
            "border": 1, "font_name": "Calibri", "font_size": 10,
            "align": "center", "num_format": "#,##0",
        })
        title_fmt = workbook.add_format({
            "bold": True, "font_size": 16, "font_color": "#003B73",
            "font_name": "Calibri",
        })
        subtitle_fmt = workbook.add_format({
            "bold": True, "font_size": 12, "font_color": "#005EB8",
            "font_name": "Calibri",
        })
        green_fmt = workbook.add_format({
            "border": 1, "font_name": "Calibri", "font_size": 10,
            "align": "center", "bg_color": "#D5F5E3",
        })
        orange_fmt = workbook.add_format({
            "border": 1, "font_name": "Calibri", "font_size": 10,
            "align": "center", "bg_color": "#FDEBD0",
        })
        blue_fmt = workbook.add_format({
            "border": 1, "font_name": "Calibri", "font_size": 10,
            "align": "center", "bg_color": "#D6EAF8",
        })

        # ── Sheet 1: Positions ────────────────────────────────────────────
        positions_df.to_excel(writer, sheet_name="Positions", index=False, startrow=2)
        ws1 = writer.sheets["Positions"]
        ws1.write(0, 0, "Amadeus Global Ramp-Up — Position Data", title_fmt)
        ws1.write(1, 0, f"Exported: {datetime.now().strftime('%d %B %Y %H:%M')}", subtitle_fmt)
        for col_idx, col in enumerate(positions_df.columns):
            ws1.write(2, col_idx, col, header_fmt)
            ws1.set_column(col_idx, col_idx, max(12, len(str(col)) + 4))
        # Conditional formatting on Status
        for row_idx in range(len(positions_df)):
            status = positions_df.iloc[row_idx].get("Status", "")
            fmt = green_fmt if status == "Filled" else orange_fmt if status == "Future Fill" else blue_fmt
            status_col = list(positions_df.columns).index("Status") if "Status" in positions_df.columns else None
            if status_col is not None:
                ws1.write(row_idx + 3, status_col, status, fmt)
        ws1.autofilter(2, 0, len(positions_df) + 2, len(positions_df.columns) - 1)
        ws1.freeze_panes(3, 0)

        # ── Sheet 2: Summary by BU ───────────────────────────────────────
        summary = positions_df.groupby("BU").agg(
            Rows=("BU", "count"),
            Total_Headcount=("Grand Total", "sum"),
            Open=("Status", lambda x: (x == "Open").sum()),
            Filled=("Status", lambda x: (x == "Filled").sum()),
            Future_Fill=("Status", lambda x: (x == "Future Fill").sum()),
        ).reset_index()
        summary.columns = ["BU", "# Rows", "Total Headcount", "Open", "Filled", "Future Fill"]
        summary.to_excel(writer, sheet_name="Summary by BU", index=False, startrow=2)
        ws2 = writer.sheets["Summary by BU"]
        ws2.write(0, 0, "Summary by Business Unit", title_fmt)
        for col_idx, col in enumerate(summary.columns):
            ws2.write(2, col_idx, col, header_fmt)
            ws2.set_column(col_idx, col_idx, 18)

        # ── Sheet 3: Weekly Tracking ──────────────────────────────────────
        weekly_df.to_excel(writer, sheet_name="Weekly Tracking", index=False, startrow=2)
        ws3 = writer.sheets["Weekly Tracking"]
        ws3.write(0, 0, "Weekly Job Requisitions Tracking", title_fmt)
        for col_idx, col in enumerate(weekly_df.columns):
            ws3.write(2, col_idx, col, header_fmt)
            ws3.set_column(col_idx, col_idx, 18)
        # Add chart
        chart = workbook.add_chart({"type": "column"})
        chart.add_series({
            "name": "Job Reqs Open",
            "categories": ["Weekly Tracking", 3, 1, len(weekly_df) + 2, 1],
            "values": ["Weekly Tracking", 3, 2, len(weekly_df) + 2, 2],
            "fill": {"color": "#003B73"},
        })
        chart.add_series({
            "name": "Job Reqs Filled",
            "categories": ["Weekly Tracking", 3, 1, len(weekly_df) + 2, 1],
            "values": ["Weekly Tracking", 3, 3, len(weekly_df) + 2, 3],
            "fill": {"color": "#B3D4FC"},
            "line": {"color": "#B3D4FC"},
        })
        chart.set_title({"name": "Job Requisitions Open vs Filled"})
        chart.set_style(10)
        chart.set_size({"width": 900, "height": 400})
        ws3.insert_chart("A" + str(len(weekly_df) + 5), chart)

        # ── Sheet 4: Pipeline ─────────────────────────────────────────────
        pipeline_df.to_excel(writer, sheet_name="Candidate Pipeline", index=False, startrow=2)
        ws4 = writer.sheets["Candidate Pipeline"]
        ws4.write(0, 0, "Candidate Pipeline by Business Unit", title_fmt)
        for col_idx, col in enumerate(pipeline_df.columns):
            ws4.write(2, col_idx, col, header_fmt)
            ws4.set_column(col_idx, col_idx, 16)

        # ── Sheet 5: Nexus Monthly ────────────────────────────────────────
        nexus_df.to_excel(writer, sheet_name="Nexus Monthly", index=False, startrow=2)
        ws5 = writer.sheets["Nexus Monthly"]
        ws5.write(0, 0, "2026 Nexus Replacement Monthly Plan", title_fmt)
        for col_idx, col in enumerate(nexus_df.columns):
            ws5.write(2, col_idx, col, header_fmt)
            ws5.set_column(col_idx, col_idx, 14)

        # ── Sheet 6: Key Locations ────────────────────────────────────────
        locations_df.to_excel(writer, sheet_name="Key Locations", index=False, startrow=2)
        ws6 = writer.sheets["Key Locations"]
        ws6.write(0, 0, "Key Locations Summary", title_fmt)
        for col_idx, col in enumerate(locations_df.columns):
            ws6.write(2, col_idx, col, header_fmt)
            ws6.set_column(col_idx, col_idx, 16)

        # ── Sheet 7: By Region ────────────────────────────────────────────
        region_summary = positions_df.groupby(["BU", "Region"]).agg(
            Rows=("BU", "count"),
            Total_HC=("Grand Total", "sum"),
        ).reset_index()
        region_summary.to_excel(writer, sheet_name="By BU & Region", index=False, startrow=2)
        ws7 = writer.sheets["By BU & Region"]
        ws7.write(0, 0, "Headcount by BU & Region", title_fmt)
        for col_idx, col in enumerate(region_summary.columns):
            ws7.write(2, col_idx, col, header_fmt)

    output.seek(0)
    return output.getvalue()


def generate_pdf_html(positions_df, weekly_df, pipeline_df, nexus_df, locations_df):
    """Generate HTML for PDF export."""
    # Compute summaries
    total_hc = int(positions_df["Grand Total"].sum())
    by_status = positions_df["Status"].value_counts()
    open_count = int(by_status.get("Open", 0))
    filled_count = int(by_status.get("Filled", 0))
    future_fill = int(by_status.get("Future Fill", 0))

    bu_summary = positions_df.groupby("BU").agg(
        Rows=("BU", "count"),
        Total=("Grand Total", "sum"),
        Open=("Status", lambda x: (x == "Open").sum()),
        Filled=("Status", lambda x: (x == "Filled").sum()),
    ).reset_index()

    region_summary = positions_df.groupby("Region")["Grand Total"].sum().reset_index()

    now = datetime.now().strftime("%d %B %Y")

    def make_table(df, max_rows=50):
        cols = df.columns.tolist()
        header = "".join(f"<th>{c}</th>" for c in cols)
        rows = ""
        for _, row in df.head(max_rows).iterrows():
            cells = "".join(f"<td>{row[c]}</td>" for c in cols)
            rows += f"<tr>{cells}</tr>"
        return f"<table><thead><tr>{header}</tr></thead><tbody>{rows}</tbody></table>"

    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
    @page {{ size: A4 landscape; margin: 15mm; }}
    body {{ font-family: 'Segoe UI', Calibri, Arial, sans-serif; color: #1A1A2E; font-size: 11px; }}
    .header {{ background: linear-gradient(135deg, #003B73, #005EB8); color: white; padding: 20px 30px; border-radius: 8px; margin-bottom: 20px; }}
    .header h1 {{ margin: 0; font-size: 24px; }}
    .header p {{ margin: 4px 0 0 0; opacity: 0.85; font-size: 12px; }}
    .section {{ margin-bottom: 24px; }}
    .section h2 {{ color: #003B73; font-size: 16px; border-bottom: 2px solid #005EB8; padding-bottom: 4px; }}
    .kpi-row {{ display: flex; gap: 16px; margin-bottom: 20px; }}
    .kpi-box {{ flex: 1; background: #F5F7FA; border-left: 4px solid #005EB8; padding: 12px 16px; border-radius: 6px; }}
    .kpi-box.green {{ border-left-color: #00A651; }}
    .kpi-box.orange {{ border-left-color: #F5A623; }}
    .kpi-box.cyan {{ border-left-color: #00B2A9; }}
    .kpi-val {{ font-size: 28px; font-weight: 700; color: #003B73; }}
    .kpi-label {{ font-size: 10px; text-transform: uppercase; color: #4A4A68; letter-spacing: 0.5px; }}
    table {{ border-collapse: collapse; width: 100%; font-size: 10px; }}
    th {{ background: #005EB8; color: white; padding: 8px 10px; text-align: center; }}
    td {{ padding: 6px 10px; border: 1px solid #D1D1DB; text-align: center; }}
    tr:nth-child(even) {{ background: #F5F7FA; }}
    .footer {{ text-align: center; color: #8E8EA0; font-size: 9px; margin-top: 30px; border-top: 1px solid #D1D1DB; padding-top: 8px; }}
    .page-break {{ page-break-before: always; }}
</style>
</head>
<body>
    <div class="header">
        <h1>Global Ramp-Ups | Talent Acquisition Report</h1>
        <p>Amadeus — Nexus Replacements | Report generated {now}</p>
    </div>

    <div class="kpi-row">
        <div class="kpi-box"><div class="kpi-val">{open_count}</div><div class="kpi-label">Open Requisitions</div></div>
        <div class="kpi-box orange"><div class="kpi-val">{future_fill}</div><div class="kpi-label">Future Fill</div></div>
        <div class="kpi-box green"><div class="kpi-val">{filled_count}</div><div class="kpi-label">Filled Requisitions</div></div>
        <div class="kpi-box cyan"><div class="kpi-val">{total_hc}</div><div class="kpi-label">Total Headcount</div></div>
    </div>

    <div class="section">
        <h2>Summary by Business Unit</h2>
        {make_table(bu_summary)}
    </div>

    <div class="section">
        <h2>Headcount by Region</h2>
        {make_table(region_summary)}
    </div>

    <div class="section">
        <h2>Key Locations</h2>
        {make_table(locations_df)}
    </div>

    <div class="page-break"></div>

    <div class="section">
        <h2>Candidate Pipeline by Business Unit</h2>
        {make_table(pipeline_df)}
    </div>

    <div class="section">
        <h2>Weekly Tracking</h2>
        {make_table(weekly_df)}
    </div>

    <div class="section">
        <h2>Nexus Monthly Ramp-Up Plan</h2>
        {make_table(nexus_df)}
    </div>

    <div class="page-break"></div>

    <div class="section">
        <h2>Detailed Positions (Top 50)</h2>
        {make_table(positions_df[["BU", "Org Path Name", "Region", "Country", "Location", "Status", "Grand Total"]].sort_values("Grand Total", ascending=False), 50)}
    </div>

    <div class="footer">
        Amadeus Global Ramp-Up Dashboard — Confidential — {now}
    </div>
</body>
</html>"""
    return html
