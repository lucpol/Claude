"""
Launch the Amadeus Ramp-Up Dashboard.

Usage:
    python run.py                              # Uses sample data
    RAMPUP_EXCEL_PATH=data.xlsx python run.py  # Uses your Excel file

Open http://localhost:8050 in your browser.
"""

from ramp_up_dashboard.app import app

if __name__ == "__main__":
    print()
    print("=" * 60)
    print("  Amadeus Global Ramp-Up Dashboard")
    print("  Open: http://localhost:8050")
    print("=" * 60)
    print()
    app.run(debug=True, host="0.0.0.0", port=8050)
