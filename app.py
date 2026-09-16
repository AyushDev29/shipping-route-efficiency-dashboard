"""
Nassau Candy Distributor — Factory-to-Customer Shipping Route Efficiency Dashboard
Run with: streamlit run app.py
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from pathlib import Path

# ---------------------------------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Nassau Candy — Shipping Route Efficiency",
    page_icon="🍬",
    layout="wide",
)

DATA_PATH = Path(__file__).parent / "data" / "cleaned_data.csv"


# ---------------------------------------------------------------------------
# DATA LOADING
# ---------------------------------------------------------------------------
@st.cache_data
def load_data():
    df = pd.read_csv(DATA_PATH, parse_dates=["Order Date", "Ship Date"])
    return df


df_raw = load_data()

# ---------------------------------------------------------------------------
# SIDEBAR FILTERS  (apply to every module)
# ---------------------------------------------------------------------------
st.sidebar.title("🍬 Nassau Candy Dashboard")
st.sidebar.caption("Factory-to-Customer Shipping Route Efficiency Analysis")
st.sidebar.markdown("---")
st.sidebar.header("Filters")

# 1. Date range filter
min_date = df_raw["Order Date"].min().date()
max_date = df_raw["Order Date"].max().date()
date_range = st.sidebar.date_input(
    "Order Date range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date,
)
if isinstance(date_range, tuple) and len(date_range) == 2:
    start_date, end_date = date_range
else:
    start_date, end_date = min_date, max_date

# 2. Region / State selector
regions = sorted(df_raw["Region"].dropna().unique().tolist())
selected_regions = st.sidebar.multiselect("Region", regions, default=regions)

states_available = sorted(
    df_raw[df_raw["Region"].isin(selected_regions)]["State/Province"].dropna().unique().tolist()
)
selected_states = st.sidebar.multiselect(
    "State / Province", states_available, default=states_available
)

# 3. Ship mode filter
ship_modes = sorted(df_raw["Ship Mode"].dropna().unique().tolist())
selected_modes = st.sidebar.multiselect("Ship Mode", ship_modes, default=ship_modes)

# 4. Lead-time threshold slider (defines what counts as "delayed")
max_lead = int(df_raw["Shipping Lead Time"].max())
delay_threshold = st.sidebar.slider(
    "Delay threshold (days) — shipments above this are 'delayed'",
    min_value=0,
    max_value=max_lead,
    value=6,
)

st.sidebar.markdown("---")
min_volume = st.sidebar.number_input(
    "Minimum shipments for a route to appear in rankings",
    min_value=1,
    value=20,
    step=5,
    help="Prevents low-volume routes from distorting the fastest/slowest rankings.",
)

# ---------------------------------------------------------------------------
# APPLY FILTERS
# ---------------------------------------------------------------------------
mask = (
    (df_raw["Order Date"].dt.date >= start_date)
    & (df_raw["Order Date"].dt.date <= end_date)
    & (df_raw["Region"].isin(selected_regions))
    & (df_raw["State/Province"].isin(selected_states))
    & (df_raw["Ship Mode"].isin(selected_modes))
)
df = df_raw[mask].copy()

if df.empty:
    st.warning("No data matches the current filters. Widen your filter selection.")
    st.stop()

df["Delayed"] = df["Shipping Lead Time"] > delay_threshold


# ---------------------------------------------------------------------------
# HELPER: ROUTE AGGREGATION
# ---------------------------------------------------------------------------
def build_route_table(data: pd.DataFrame, route_col: str) -> pd.DataFrame:
    g = data.groupby(route_col)["Shipping Lead Time"].agg(
        Total_Shipments="count",
        Average_Lead_Time="mean",
        Std_Dev="std",
    ).reset_index()
    g["Std_Dev"] = g["Std_Dev"].fillna(0)
    delay_pct = data.groupby(route_col)["Delayed"].mean() * 100
    g["Delay_Frequency_%"] = g[route_col].map(delay_pct)

    max_avg, min_avg = g["Average_Lead_Time"].max(), g["Average_Lead_Time"].min()
    denom = (max_avg - min_avg) if max_avg != min_avg else 1
    g["Route_Efficiency_Score"] = round(1 - (g["Average_Lead_Time"] - min_avg) / denom, 3)

    g = g.rename(columns={route_col: "Route"})
    for c in ["Average_Lead_Time", "Std_Dev", "Delay_Frequency_%"]:
        g[c] = g[c].round(3)
    g = g.sort_values("Average_Lead_Time").reset_index(drop=True)
    g.insert(0, "Rank", g.index + 1)
    return g


# ---------------------------------------------------------------------------
# TOP KPI STRIP
# ---------------------------------------------------------------------------
st.title("Factory-to-Customer Shipping Route Efficiency")
st.caption("Nassau Candy Distributor — live analytics dashboard")

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Total Shipments", f"{len(df):,}")
k2.metric("Avg Lead Time", f"{df['Shipping Lead Time'].mean():.2f} days")
k3.metric("Std Dev", f"{df['Shipping Lead Time'].std():.2f} days")
k4.metric("Delay Frequency", f"{df['Delayed'].mean()*100:.1f}%")
k5.metric("Unique Routes", f"{df['Route_state'].nunique()}")

st.markdown("---")

# ---------------------------------------------------------------------------
# TABS = THE 4 DASHBOARD MODULES
# ---------------------------------------------------------------------------
tab1, tab2, tab3, tab4 = st.tabs(
    [
        "📊 Route Efficiency Overview",
        "🗺️ Geographic Shipping Map",
        "🚚 Ship Mode Comparison",
        "🔍 Route Drill-Down",
    ]
)

# ============================ MODULE 1 ============================
with tab1:
    st.subheader("Route Efficiency Overview")

    level = st.radio("Aggregate by:", ["Factory → State", "Factory → Region"], horizontal=True)
    route_col = "Route_state" if level == "Factory → State" else "Route_region"

    route_table = build_route_table(df, route_col)
    eligible = route_table[route_table["Total_Shipments"] >= min_volume]

    c1, c2 = st.columns(2)
    with c1:
        st.markdown(f"**Top 10 Fastest Routes** (min {min_volume} shipments)")
        top_fast = eligible.sort_values("Average_Lead_Time").head(10)
        fig = px.bar(
            top_fast, x="Average_Lead_Time", y="Route", orientation="h",
            color="Average_Lead_Time", color_continuous_scale="Greens_r",
            text="Average_Lead_Time",
        )
        fig.update_layout(yaxis=dict(autorange="reversed"), showlegend=False, height=400)
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        st.markdown(f"**Top 10 Slowest Routes** (min {min_volume} shipments)")
        top_slow = eligible.sort_values("Average_Lead_Time", ascending=False).head(10)
        fig = px.bar(
            top_slow, x="Average_Lead_Time", y="Route", orientation="h",
            color="Average_Lead_Time", color_continuous_scale="Reds",
            text="Average_Lead_Time",
        )
        fig.update_layout(yaxis=dict(autorange="reversed"), showlegend=False, height=400)
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("**Route Performance Leaderboard** (full table, sortable)")
    st.dataframe(
        route_table.style.background_gradient(subset=["Average_Lead_Time"], cmap="RdYlGn_r")
        .background_gradient(subset=["Route_Efficiency_Score"], cmap="RdYlGn"),
        use_container_width=True,
        height=400,
    )

# ============================ MODULE 2 ============================
with tab2:
    st.subheader("Geographic Shipping Map")

    us_df = df[df["Country/Region"] == "United States"]
    state_geo = us_df.groupby(["State/Province", "State_Abbrev"])["Shipping Lead Time"].agg(
        Total_Shipments="count", Average_Lead_Time="mean"
    ).reset_index()

    overall_avg = us_df["Shipping Lead Time"].mean()
    median_vol = state_geo["Total_Shipments"].median()
    state_geo["Bottleneck"] = np.where(
        (state_geo["Average_Lead_Time"] > overall_avg) & (state_geo["Total_Shipments"] > median_vol),
        "Bottleneck", "OK"
    )

    fig = px.choropleth(
        state_geo,
        locations="State_Abbrev",
        locationmode="USA-states",
        color="Average_Lead_Time",
        scope="usa",
        color_continuous_scale="RdYlGn_r",
        hover_name="State/Province",
        hover_data={"Total_Shipments": True, "Average_Lead_Time": ":.2f", "State_Abbrev": False},
        labels={"Average_Lead_Time": "Avg Lead Time (days)"},
    )
    fig.update_layout(height=520, margin=dict(l=0, r=0, t=20, b=0))
    st.plotly_chart(fig, use_container_width=True)

    st.markdown(
        f"**Bottleneck states** (above-average lead time *and* above-median volume): "
        f"{(state_geo['Bottleneck']=='Bottleneck').sum()} states flagged"
    )
    bottleneck_df = state_geo[state_geo["Bottleneck"] == "Bottleneck"].sort_values(
        "Total_Shipments", ascending=False
    )
    st.dataframe(bottleneck_df, use_container_width=True, height=300)

    if (df["Country/Region"] == "Canada").any():
        with st.expander("Canada routes (not shown on map)"):
            ca_geo = df[df["Country/Region"] == "Canada"].groupby("State/Province")[
                "Shipping Lead Time"
            ].agg(Total_Shipments="count", Average_Lead_Time="mean").reset_index()
            st.dataframe(ca_geo, use_container_width=True)

# ============================ MODULE 3 ============================
with tab3:
    st.subheader("Ship Mode Comparison")

    sm = df.groupby("Ship Mode")["Shipping Lead Time"].agg(
        Total_Shipments="count", Average_Lead_Time="mean", Std_Dev="std"
    ).reset_index()
    sm["Std_Dev"] = sm["Std_Dev"].fillna(0)
    delay_pct = df.groupby("Ship Mode")["Delayed"].mean() * 100
    sm["Delay_Frequency_%"] = sm["Ship Mode"].map(delay_pct)
    sm = sm.sort_values("Average_Lead_Time")

    c1, c2 = st.columns(2)
    with c1:
        fig = px.bar(
            sm, x="Ship Mode", y="Average_Lead_Time", color="Ship Mode",
            text_auto=".2f", title="Average Lead Time by Ship Mode (days)",
        )
        fig.update_layout(showlegend=False, height=400)
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        fig = px.bar(
            sm, x="Ship Mode", y="Delay_Frequency_%", color="Ship Mode",
            text_auto=".1f", title="Delay Frequency (%) by Ship Mode",
        )
        fig.update_layout(showlegend=False, height=400)
        st.plotly_chart(fig, use_container_width=True)

    st.dataframe(sm.round(3), use_container_width=True)

    slowest_mode = sm.iloc[-1]["Ship Mode"]
    st.info(
        f"**{slowest_mode}** has both the longest average lead time and the highest delay "
        f"frequency in the current filter selection — the clearest cost-time tradeoff in the data."
    )

# ============================ MODULE 4 ============================
with tab4:
    st.subheader("Route Drill-Down")

    drill_state = st.selectbox(
        "Select a State / Province to inspect",
        sorted(df["State/Province"].unique().tolist()),
    )
    state_df = df[df["State/Province"] == drill_state]

    c1, c2, c3 = st.columns(3)
    c1.metric("Shipments", f"{len(state_df):,}")
    c2.metric("Avg Lead Time", f"{state_df['Shipping Lead Time'].mean():.2f} days")
    c3.metric("Delay Frequency", f"{state_df['Delayed'].mean()*100:.1f}%")

    st.markdown(f"**Factories serving {drill_state}**")
    factory_break = state_df.groupby("Factory")["Shipping Lead Time"].agg(
        Total_Shipments="count", Average_Lead_Time="mean"
    ).reset_index().sort_values("Average_Lead_Time")
    st.dataframe(factory_break.round(3), use_container_width=True)

    st.markdown(f"**Ship Mode breakdown for {drill_state}**")
    mode_break = state_df.groupby("Ship Mode")["Shipping Lead Time"].agg(
        Total_Shipments="count", Average_Lead_Time="mean"
    ).reset_index().sort_values("Average_Lead_Time")
    st.dataframe(mode_break.round(3), use_container_width=True)

    st.markdown(f"**Order-level shipment timeline for {drill_state}**")
    fig = px.scatter(
        state_df.sort_values("Order Date"),
        x="Order Date", y="Shipping Lead Time",
        color="Ship Mode", hover_data=["Order ID", "Factory", "Product Name"],
        title=f"Shipping Lead Time over time — {drill_state}",
    )
    fig.add_hline(y=delay_threshold, line_dash="dash", line_color="red",
                  annotation_text="Delay threshold")
    fig.update_layout(height=450)
    st.plotly_chart(fig, use_container_width=True)

st.markdown("---")
st.caption("Nassau Candy Distributor · Shipping Route Efficiency Dashboard · Built with Streamlit")
