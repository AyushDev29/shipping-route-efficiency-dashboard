# Nassau Candy — Shipping Route Efficiency Dashboard

## How to run

1. Install Python 3.9+ if you don't have it.
2. Open a terminal in this folder and install the dependencies:

   pip install -r requirements.txt

3. Run the app:

   streamlit run app.py

4. It opens automatically in your browser at http://localhost:8501

## What's inside

- `app.py` — the full dashboard (all 4 modules + filters)
- `data/cleaned_data.csv` — your cleaned dataset (exported from the Excel workbook)
- `requirements.txt` — Python packages needed

## Modules

1. Route Efficiency Overview — leaderboard + Top 10 fastest/slowest routes (toggle State/Region)
2. Geographic Shipping Map — US choropleth colored by average lead time, bottleneck table
3. Ship Mode Comparison — lead time & delay frequency by ship mode
4. Route Drill-Down — pick a state, see factory/ship-mode breakdown + order-level timeline

## Filters (apply to all modules)

- Order Date range
- Region / State selector
- Ship Mode filter
- Delay threshold slider (redefine what counts as "delayed" — updates Delay Frequency everywhere live)
- Minimum shipment volume for a route to appear in Top 10 rankings

## Deploying it live (optional, for your submission link)

Easiest free option: push this folder to a GitHub repo, then deploy on
https://share.streamlit.io (Streamlit Community Cloud) — point it at `app.py`.
