"""
Amadeus color palette and theme configuration.
Light background with Amadeus corporate colors.
"""

# ── Amadeus Corporate Colors ──────────────────────────────────────────────────
AMADEUS_NAVY = "#005EB8"
AMADEUS_DARK_BLUE = "#003B73"
AMADEUS_LIGHT_BLUE = "#4A90D9"
AMADEUS_SKY = "#B3D4FC"
AMADEUS_CYAN = "#00B2A9"
AMADEUS_GREEN = "#00A651"
AMADEUS_ORANGE = "#F5A623"
AMADEUS_RED = "#E74C3C"
AMADEUS_PURPLE = "#7B61FF"
AMADEUS_GRAY_900 = "#1A1A2E"
AMADEUS_GRAY_700 = "#4A4A68"
AMADEUS_GRAY_500 = "#8E8EA0"
AMADEUS_GRAY_300 = "#D1D1DB"
AMADEUS_GRAY_100 = "#F0F0F5"
AMADEUS_WHITE = "#FFFFFF"

BG_PAGE = "#F5F7FA"
BG_CARD = "#FFFFFF"
BG_SIDEBAR = "#003B73"
BG_HEADER = "#005EB8"

# ── BU-specific colors ────────────────────────────────────────────────────────
BU_COLORS = {
    "CFA": "#005EB8",
    "HOS": "#00B2A9",
    "TRU": "#F5A623",
    "TSI": "#7B61FF",
}

# ── Chart color sequences ─────────────────────────────────────────────────────
CHART_COLORS = [
    AMADEUS_NAVY, AMADEUS_CYAN, AMADEUS_ORANGE, AMADEUS_GREEN,
    AMADEUS_RED, AMADEUS_PURPLE, AMADEUS_LIGHT_BLUE, "#F39C12",
    "#2ECC71", "#E67E22", "#9B59B6", "#1ABC9C",
]

# ── Plotly layout template ────────────────────────────────────────────────────
PLOTLY_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter, Segoe UI, Helvetica, Arial, sans-serif", color=AMADEUS_GRAY_900, size=12),
    title_font=dict(size=16, color=AMADEUS_DARK_BLUE),
    margin=dict(l=40, r=20, t=50, b=40),
    legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=11)),
    xaxis=dict(gridcolor=AMADEUS_GRAY_300, gridwidth=0.5, zerolinecolor=AMADEUS_GRAY_300),
    yaxis=dict(gridcolor=AMADEUS_GRAY_300, gridwidth=0.5, zerolinecolor=AMADEUS_GRAY_300),
    colorway=CHART_COLORS,
    hoverlabel=dict(bgcolor=AMADEUS_WHITE, font_size=12, font_family="Inter, sans-serif"),
)

# ── CSS ───────────────────────────────────────────────────────────────────────
CUSTOM_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

body {
    font-family: 'Inter', 'Segoe UI', sans-serif;
    background-color: #F5F7FA;
    color: #1A1A2E;
    margin: 0;
}

.main-header {
    background: linear-gradient(135deg, #003B73 0%, #005EB8 100%);
    color: white;
    padding: 20px 30px;
    margin-bottom: 20px;
    border-radius: 0 0 12px 12px;
    box-shadow: 0 4px 20px rgba(0,94,184,0.15);
}
.main-header h1 { margin: 0; font-weight: 700; font-size: 28px; letter-spacing: -0.5px; }
.main-header p { margin: 4px 0 0 0; opacity: 0.85; font-size: 14px; font-weight: 300; }

.kpi-card {
    background: white;
    border-radius: 12px;
    padding: 20px 24px;
    box-shadow: 0 2px 12px rgba(0,0,0,0.06);
    border-left: 4px solid #005EB8;
    transition: transform 0.2s ease, box-shadow 0.2s ease;
    height: 100%;
}
.kpi-card:hover { transform: translateY(-2px); box-shadow: 0 6px 20px rgba(0,0,0,0.1); }
.kpi-value { font-size: 36px; font-weight: 700; color: #003B73; line-height: 1.1; margin-bottom: 4px; }
.kpi-label { font-size: 13px; color: #4A4A68; font-weight: 500; text-transform: uppercase; letter-spacing: 0.5px; }
.kpi-delta { font-size: 12px; margin-top: 6px; font-weight: 600; }
.kpi-delta.positive { color: #00A651; }
.kpi-delta.negative { color: #E74C3C; }
.kpi-delta.neutral { color: #8E8EA0; }

.chart-card {
    background: white;
    border-radius: 12px;
    padding: 20px;
    box-shadow: 0 2px 12px rgba(0,0,0,0.06);
    margin-bottom: 20px;
}
.chart-card h3 { margin: 0 0 16px 0; font-size: 16px; font-weight: 600; color: #003B73; }

.filter-panel {
    background: white;
    border-radius: 12px;
    padding: 16px 20px;
    box-shadow: 0 2px 12px rgba(0,0,0,0.06);
    margin-bottom: 20px;
    border-top: 3px solid #005EB8;
}
.filter-panel label {
    font-weight: 600; font-size: 11px; text-transform: uppercase;
    letter-spacing: 0.5px; color: #4A4A68; margin-bottom: 4px;
}

.custom-tabs .tab {
    border: none !important; border-bottom: 3px solid transparent !important;
    background: transparent !important; color: #4A4A68 !important;
    font-weight: 500 !important; padding: 12px 20px !important; font-size: 14px !important;
}
.custom-tabs .tab--selected {
    border-bottom: 3px solid #005EB8 !important; color: #005EB8 !important; font-weight: 600 !important;
}

::-webkit-scrollbar { width: 8px; }
::-webkit-scrollbar-track { background: #F0F0F5; }
::-webkit-scrollbar-thumb { background: #B3D4FC; border-radius: 4px; }
::-webkit-scrollbar-thumb:hover { background: #005EB8; }
"""
