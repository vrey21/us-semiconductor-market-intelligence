from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st


# --------------------------------------------------
# 1. SET UP THE DASHBOARD PAGE
# --------------------------------------------------

st.set_page_config(
    page_title="U.S. Semiconductor Market Intelligence Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

DATA_FOLDER = Path("data")
TRADE_FILE = DATA_FOLDER / "us_semiconductor_trade_2025_2026.csv"
PRODUCTION_FILE = DATA_FOLDER / "us_semiconductor_production_index.csv"

PRODUCT_OPTIONS = {
    "All semiconductor products": None,
    "Semiconductor devices (HS 8541)": "8541",
    "Integrated circuits (HS 8542)": "8542",
}

PRODUCT_SHORT_NAMES = {
    "8541": "Semiconductor devices (HS 8541)",
    "8542": "Integrated circuits (HS 8542)",
}

FLOW_COLORS = {"Imports": "#2563EB", "Exports": "#F59E0B"}


st.markdown(
    """
    <style>
        .block-container {padding-top: 2rem; padding-bottom: 3rem;}
        [data-testid="stSidebar"] {background-color: #0F172A;}
        [data-testid="stSidebar"] * {color: #F8FAFC;}
        [data-testid="stMetric"] {
            background-color: #F8FAFC;
            border: 1px solid #E2E8F0;
            border-radius: 12px;
            padding: 16px;
        }
        h1, h2, h3 {color: #0F172A;}
    </style>
    """,
    unsafe_allow_html=True,
)


# --------------------------------------------------
# 2. LOAD THE SAVED DATA
# --------------------------------------------------

@st.cache_data
def load_data():
    trade_data = pd.read_csv(TRADE_FILE, parse_dates=["month"])
    production_data = pd.read_csv(PRODUCTION_FILE, parse_dates=["date"])

    # Keep HS codes as text labels so they match the dashboard filters.
    trade_data["hs_code"] = trade_data["hs_code"].astype(str)
    trade_data["trade_value_usd"] = pd.to_numeric(
        trade_data["trade_value_usd"], errors="coerce"
    )

        # Keep only individual countries with positive trade values.
    # A real Census country code is exactly four digits, such as 5700.
    # This removes regional groups and the "Total for All Countries" row.
    trade_data["CTY_CODE"] = trade_data["CTY_CODE"].astype(str)

    trade_data = trade_data[
        trade_data["CTY_CODE"].str.fullmatch(r"[1-9]\d{3}", na=False)
        & (trade_data["trade_value_usd"] > 0)
    ].copy()

    production_data["production_index"] = pd.to_numeric(
        production_data["production_index"], errors="coerce"
    )

    return trade_data, production_data


def format_money(value):
    """Turn a dollar amount into a short label such as $6.8B or $421.3M."""
    sign = "-" if value < 0 else ""
    value = abs(value)
    if value >= 1_000_000_000:
        return f"{sign}${value / 1_000_000_000:.2f}B"
    return f"{sign}${value / 1_000_000:.1f}M"


def make_partner_chart(data, flow_name, color):
    """Make a top-10 partner chart for either imports or exports."""
    partner_totals = (
        data[data["trade_flow"] == flow_name]
        .groupby("CTY_NAME", as_index=False)["trade_value_usd"]
        .sum()
        .nlargest(10, "trade_value_usd")
        .sort_values("trade_value_usd")
        .copy()
    )

    if partner_totals.empty:
        return None, None

    partner_totals["value_millions"] = (
        partner_totals["trade_value_usd"] / 1_000_000
    )

    fig = px.bar(
        partner_totals,
        x="value_millions",
        y="CTY_NAME",
        orientation="h",
        text="value_millions",
        color_discrete_sequence=[color],
        labels={
            "value_millions": "Trade value (millions of U.S. dollars)",
            "CTY_NAME": "",
        },
    )

    fig.update_traces(
        texttemplate="$%{text:.1f}M",
        textposition="outside",
	cliponaxis=False,
        hovertemplate="<b>%{y}</b><br>$%{x:.1f}M<extra></extra>",
    )
    fig.update_layout(
        height=420,
        showlegend=False,
        margin=dict(l=0, r=65, t=15, b=0),
        plot_bgcolor="white",
        paper_bgcolor="white",
    )
    fig.update_xaxes(
        showgrid=True,
        gridcolor="#E2E8F0",
        range=[0, partner_totals["value_millions"].max() * 1.18],
    )
    fig.update_yaxes(showgrid=False)

    return fig, partner_totals.iloc[-1]["CTY_NAME"]


# Stop with a clear message if someone opens app.py without the saved files.
if not TRADE_FILE.exists() or not PRODUCTION_FILE.exists():
    st.error("The saved CSV files were not found in the data folder.")
    st.info(
        "This dashboard needs data/us_semiconductor_trade_2025_2026.csv and "
        "data/us_semiconductor_production_index.csv."
    )
    st.stop()

trade_data, production_data = load_data()


# --------------------------------------------------
# 3. SIDEBAR CONTROLS
# --------------------------------------------------

month_options = sorted(trade_data["month"].dropna().unique())
latest_month = month_options[-1]

st.sidebar.title("Dashboard filters")
st.sidebar.caption(
    "Use the Product Category filter to update the KPI cards, monthly trends, "
    "trade balance, and partner charts."
)
selected_month = st.sidebar.select_slider(
    "Trade month",
    options=month_options,
    value=latest_month,
    format_func=lambda date: pd.Timestamp(date).strftime("%b %Y"),
)

selected_product_label = st.sidebar.radio(
    "Product category",
    options=list(PRODUCT_OPTIONS.keys()),
)
selected_hs_code = PRODUCT_OPTIONS[selected_product_label]

st.sidebar.divider()
st.sidebar.markdown("**Data period**")
st.sidebar.caption("Trade: Jan 2025–Aug 2026\n\nProduction index: 2016–Aug 2026")
st.sidebar.markdown("**Sources**")
st.sidebar.caption("U.S. Census International Trade data and FRED series IPG3344S")


# Apply the selected product filter. The selected month is only for snapshot views.
filtered_trade = trade_data.copy()
if selected_hs_code is not None:
    filtered_trade = filtered_trade[
        filtered_trade["hs_code"] == selected_hs_code
    ].copy()

selected_month_data = filtered_trade[
    filtered_trade["month"] == selected_month
].copy()

selected_month_label = pd.Timestamp(selected_month).strftime("%B %Y")

# Find the month right before the one selected in the sidebar
selected_month_position = month_options.index(selected_month)

previous_month = (
    month_options[selected_month_position - 1]
    if selected_month_position > 0
    else None
)

# Get the trade data from that previous month
previous_month_data = (
    filtered_trade[filtered_trade["month"] == previous_month].copy()
    if previous_month is not None
    else pd.DataFrame()
)


# --------------------------------------------------
# 4. PAGE HEADER AND KPI CARDS
# --------------------------------------------------

st.title("U.S. Semiconductor Market Intelligence")
st.write(
    "Explore U.S. semiconductor trade and manufacturing production over time. "
    "Use the sidebar to change the trade month or product category."
)
st.caption(
    "Trade values are reported in U.S. dollars. Trade balance = exports minus imports."
)

total_imports = selected_month_data.loc[
    selected_month_data["trade_flow"] == "Imports", "trade_value_usd"
].sum()
total_exports = selected_month_data.loc[
    selected_month_data["trade_flow"] == "Exports", "trade_value_usd"
].sum()
trade_balance = total_exports - total_imports

selected_production = production_data[
    production_data["date"] == selected_month
]["production_index"]
production_value = selected_production.iloc[0] if not selected_production.empty else None

# Get the KPI values for the previous month
if previous_month is not None:
    previous_imports = previous_month_data.loc[
        previous_month_data["trade_flow"] == "Imports",
        "trade_value_usd"
    ].sum()

    previous_exports = previous_month_data.loc[
        previous_month_data["trade_flow"] == "Exports",
        "trade_value_usd"
    ].sum()

    previous_trade_balance = previous_exports - previous_imports

    previous_production = production_data[
        production_data["date"] == previous_month
    ]["production_index"]

    previous_production_value = (
        previous_production.iloc[0]
        if not previous_production.empty
        else None
    )
else:
    previous_imports = None
    previous_exports = None
    previous_trade_balance = None
    previous_production_value = None


# Calculate how much each KPI changed from the prior month
import_change = (
    total_imports - previous_imports
    if previous_imports is not None
    else None
)

export_change = (
    total_exports - previous_exports
    if previous_exports is not None
    else None
)

balance_change = (
    trade_balance - previous_trade_balance
    if previous_trade_balance is not None
    else None
)

production_change = (
    production_value - previous_production_value
    if production_value is not None and previous_production_value is not None
    else None
)


# Turn a change into a label such as +$0.25B or -$0.40B
def format_change(value):
    if value is None:
        return None

    sign = "+" if value >= 0 else "-"
    return f"{sign}{format_money(abs(value))}"

st.subheader(f"Trade snapshot — {selected_month_label}")
metric_1, metric_2, metric_3, metric_4 = st.columns(4)


metric_1.metric(
    "Imports",
    format_money(total_imports),
    delta=format_change(import_change),
    delta_color="off",
)

metric_2.metric(
    "Exports",
    format_money(total_exports),
    delta=format_change(export_change),
    delta_color="off",
)

metric_3.metric(
    "Trade balance",
    format_money(trade_balance),
    delta=format_change(balance_change),
    delta_color="off",
)

metric_4.metric(
    "Production index",
    f"{production_value:.1f}" if production_value is not None else "Not available",
    delta=(
        f"{production_change:+.1f} points"
        if production_change is not None
        else None
    ),
    delta_color="off",
)

st.caption(
    "Small gray values under each card show the change from the previous month. "
    "Dollar amounts are rounded for display."
)

st.caption(
    "Production index: 2017 is the reference year (100). A value above 100 means "
    "broader U.S. semiconductor and electronic-component manufacturing activity was higher "
    "than its 2017 average. It is an activity score, not a count of individual chips."
)


# --------------------------------------------------
# 5. TRADE AND PRODUCTION TRENDS
# --------------------------------------------------

st.divider()
st.header("Trade over time")

# For "All semiconductor products," add HS 8541 and HS 8542 together.
# This keeps the chart readable: two lines (imports and exports), not four.
trend_data = (
    filtered_trade.groupby(["month", "trade_flow"], as_index=False)["trade_value_usd"]
    .sum()
)
trend_data["trade_value_billions"] = trend_data["trade_value_usd"] / 1_000_000_000

trend_fig = px.line(
    trend_data,
    x="month",
    y="trade_value_billions",
    color="trade_flow",
    markers=True,
    color_discrete_map=FLOW_COLORS,
    labels={
        "trade_value_billions": "Trade value (billions of U.S. dollars)",
        "month": "Month",
        "trade_flow": "Trade flow",
    },
)
trend_fig.update_layout(
    height=440,
    legend_title="",
    hovermode="x unified",
    plot_bgcolor="white",
    paper_bgcolor="white",
    margin=dict(l=0, r=10, t=20, b=35),
)
trend_fig.update_xaxes(
    rangeslider_visible=False,
    showgrid=False,
    tickformat="%b\n%Y",
    automargin=True,
)
trend_fig.update_yaxes(showgrid=True, gridcolor="#E2E8F0")
# Add a dotted vertical line for the month chosen in the sidebar
trend_fig.add_vline(
    x=pd.to_datetime(selected_month),
    line_dash="dot",
    line_color="#64748B",
    line_width=2,
)
st.plotly_chart(trend_fig, width="stretch")


# --------------------------------------------------
# MONTHLY TRADE BALANCE
# Green = surplus: exports were larger than imports.
# Red = deficit: imports were larger than exports.
# --------------------------------------------------

# Put the imports and exports for each month side by side
balance_data = (
    trend_data.pivot(
        index="month",
        columns="trade_flow",
        values="trade_value_usd"
    )
    .fillna(0)
    .reset_index()
)

# Trade balance = exports minus imports
# Change dollars to billions so the chart is easier to read
balance_data["trade_balance_billions"] = (
    balance_data["Exports"] - balance_data["Imports"]
) / 1_000_000_000

# Give each bar a label so Python knows which color to use
balance_data["balance_type"] = balance_data["trade_balance_billions"].apply(
    lambda value: "Surplus" if value >= 0 else "Deficit"
)

# Make one bar for every month
balance_fig = px.bar(
    balance_data,
    x="month",
    y="trade_balance_billions",
    color="balance_type",
    color_discrete_map={
        "Surplus": "#16A34A",  # green
        "Deficit": "#DC2626",  # red
    },
    labels={
        "month": "Month",
        "trade_balance_billions": "Trade balance (billions of U.S. dollars)",
        "balance_type": "",
    },
)

# Add the zero line: bars above it are surpluses; below it are deficits
balance_fig.add_hline(y=0, line_color="#64748B", line_width=1)

# Make the chart match the rest of your dashboard
balance_fig.update_layout(
    height=360,
    legend_title="",
    plot_bgcolor="white",
    paper_bgcolor="white",
    margin=dict(l=0, r=10, t=20, b=35),
)
balance_fig.update_xaxes(
    showgrid=False,
    tickformat="%b\n%Y",
    automargin=True,
)
balance_fig.update_yaxes(
    tickprefix="$",
    ticksuffix="B",
    showgrid=True,
    gridcolor="#E2E8F0",
)

st.subheader("Monthly trade balance")
st.caption("Green = the U.S. exported more than it imported. Red = the U.S. imported more than it exported.")
st.plotly_chart(balance_fig, width="stretch")

# --------------------------------------------------
# JANUARY-AUGUST TRADE COMPARISON BY PRODUCT CATEGORY
# This always shows both HS 8541 and HS 8542 side by side.
# --------------------------------------------------

# Keep January through August for both product categories
comparison_data = trade_data[
    (trade_data["hs_code"].isin(["8541", "8542"]))
    & (trade_data["month"].dt.month <= 8)
].copy()

# Create labels such as "Jan-Aug 2025"
comparison_data["comparison_period"] = (
    "Jan-Aug " + comparison_data["month"].dt.year.astype(str)
)

# Give each HS code a readable name for the two chart panels
comparison_data["product_category"] = comparison_data["hs_code"].map(
    PRODUCT_SHORT_NAMES
)

# Add up the trade values for each category, year period, and trade flow
comparison_summary = (
    comparison_data.groupby(
        ["product_category", "comparison_period", "trade_flow"],
        as_index=False,
    )["trade_value_usd"]
    .sum()
)

# Change dollars into billions for easier reading
comparison_summary["trade_value_billions"] = (
    comparison_summary["trade_value_usd"] / 1_000_000_000
)

# Make two side-by-side chart panels, like the Jupyter chart
comparison_fig = px.bar(
    comparison_summary,
    x="comparison_period",
    y="trade_value_billions",
    color="trade_flow",
    facet_col="product_category",
    barmode="group",
    text="trade_value_billions",
    color_discrete_map=FLOW_COLORS,
    category_orders={
        "product_category": [
            "Semiconductor devices (HS 8541)",
            "Integrated circuits (HS 8542)",
        ],
        "comparison_period": ["Jan-Aug 2025", "Jan-Aug 2026"],
        "trade_flow": ["Exports", "Imports"],
    },
    labels={
        "comparison_period": "",
        "trade_value_billions": "Trade value (billions of U.S. dollars)",
        "trade_flow": "Trade flow",
        "product_category": "",
    },
)

# Format dollar labels and hover information
comparison_fig.update_traces(
    texttemplate="$%{text:.2f}B",
    textposition="outside",
    cliponaxis=False,
    hovertemplate="<b>%{fullData.name}</b><br>%{x}<br>$%{y:.2f}B<extra></extra>",
)

# Make the chart match the dashboard style
comparison_fig.update_layout(
    height=460,
    legend_title="",
    plot_bgcolor="white",
    paper_bgcolor="white",
    margin=dict(l=0, r=20, t=55, b=35),
)

comparison_fig.update_xaxes(
    showgrid=False,
    title="",
)

# Let each product panel have its own scale, like the notebook chart
comparison_fig.update_yaxes(
    matches=None,
    showticklabels=True,
    tickprefix="$",
    ticksuffix="B",
    showgrid=True,
    gridcolor="#E2E8F0",
)

# Show the y-axis title on the left panel only
comparison_fig.update_yaxes(
    title_text="Trade value (billions of U.S. dollars)",
    row=1,

    col=1,
)
comparison_fig.update_yaxes(title_text="", row=1, col=2)

# Remove the extra "product_category=" text from panel headings
comparison_fig.for_each_annotation(
    lambda annotation: annotation.update(
        text=annotation.text.split("=", 1)[-1],
        font=dict(size=14, color="#0F172A"),
    )
)

st.subheader("January-August trade comparison by product category")
st.caption(
    "Both product categories are shown together so you can compare them. "
    "Each panel uses its own y-axis, so compare the dollar labels—not only bar height. "
    "September–December 2025 are intentionally not included."
)
st.plotly_chart(comparison_fig, width="stretch")


st.header("U.S. production trend")
production_recent = production_data[production_data["date"] >= "2016-01-01"].copy()

production_fig = px.line(
    production_recent,
    x="date",
    y="production_index",
    labels={"date": "Date", "production_index": "Production index (2017 = 100)"},
)
production_fig.update_traces(
    line_color="#0F766E",
    hovertemplate="%{x|%b %Y}<br>Index: %{y:.1f}<extra></extra>",
)
production_fig.add_hline(
    y=100,
    line_dash="dash",
    line_color="#64748B",
    annotation_text="2017 baseline (100)",
    annotation_position="top left",
)
production_fig.update_layout(
    height=400,
    plot_bgcolor="white",
    paper_bgcolor="white",
    margin=dict(l=0, r=10, t=20, b=0),
)
production_fig.update_xaxes(rangeslider_visible=True, showgrid=False)
production_fig.update_yaxes(showgrid=True, gridcolor="#E2E8F0")
st.plotly_chart(production_fig, width="stretch")


# --------------------------------------------------
# 6. TOP TRADING PARTNERS
# --------------------------------------------------

st.divider()
st.header(f"Major trading partners — {selected_month_label}")
st.caption(f"Showing the top 10 partners for: {selected_product_label}.")

import_chart, top_import_partner = make_partner_chart(
    selected_month_data, "Imports", "#2563EB"
)
export_chart, top_export_partner = make_partner_chart(
    selected_month_data, "Exports", "#F59E0B"
)

left_column, right_column = st.columns(2)
with left_column:
    st.subheader("Top U.S. import partners")
    if import_chart is not None:
        st.plotly_chart(import_chart, width="stretch")
    else:
        st.info("No import-partner data is available for this selection.")

with right_column:
    st.subheader("Top buyers of U.S. exports")
    if export_chart is not None:
        st.plotly_chart(export_chart, width="stretch")
    else:
        st.info("No export-partner data is available for this selection.")


# --------------------------------------------------
# 7. KEY TAKEAWAYS AND SOURCES
# --------------------------------------------------

st.divider()
st.header("Key takeaways for this selection")

if total_imports > total_exports:
    balance_sentence = "The U.S. imported more than it exported."
else:
    balance_sentence = "The U.S. exported more than it imported."

st.markdown(
    f"""
- In **{selected_month_label}**, {balance_sentence}
- The trade balance was **{format_money(trade_balance)}**.
- The largest import partner was **{top_import_partner or 'not available'}**.
- The largest export buyer was **{top_export_partner or 'not available'}**.
"""
)

with st.expander("Data notes and definitions"):
    st.markdown(
        """
        - **HS 8541**: semiconductor devices such as diodes, transistors, LEDs, and sensors.
        - **HS 8542**: integrated circuits, commonly called computer chips.
        - **Trade balance**: exports minus imports. A negative result means imports were larger.
        - **Production index**: an index of broader U.S. semiconductor and electronic-component manufacturing production, where 2017 = 100.
        """
    )

with st.expander("Sources"):
    st.markdown(
        """
        - [U.S. Census Bureau International Trade Data](https://www.census.gov/foreign-trade/statistics/country/index.html): monthly U.S. imports and exports by partner country and HS product code.
        - [Federal Reserve Economic Data (FRED), series IPG3344S](https://fred.stlouisfed.org/series/IPG3344S): monthly production index for semiconductor and other electronic-component manufacturing.
        - This dashboard uses downloaded CSV snapshots saved in the project `data` folder.
        """
    )