"""
dashboard/app.py
----------------
PharmaPulse — Interactive Streamlit Dashboard

Run with:
    streamlit run dashboard/app.py
"""

import os
import sys

# Allow imports from project root
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from scripts.analyze import (
    kpi_summary,
    top_drugs_by_revenue,
    market_share_by_manufacturer,
    yoy_growth_by_category,
    monthly_trend,
    regional_performance,
    lifecycle_summary,
    price_volume_correlation,
    get_conn,
)

# ── Page config ───────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="PharmaPulse Analytics",
    page_icon="💊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────

st.markdown("""
<style>
    .metric-card {
        background: #1e2130;
        border-radius: 10px;
        padding: 1rem 1.4rem;
        border-left: 4px solid #4f8ef7;
    }
    .metric-label { color: #8b93a7; font-size: 0.78rem; text-transform: uppercase; letter-spacing: 0.05em; }
    .metric-value { color: #ffffff; font-size: 1.6rem; font-weight: 700; margin-top: 4px; }
    .metric-sub   { color: #4f8ef7; font-size: 0.82rem; margin-top: 2px; }
    section[data-testid="stSidebar"] { background-color: #141622; }
</style>
""", unsafe_allow_html=True)

# ── Sidebar filters ───────────────────────────────────────────────────────────

with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/pill.png", width=60)
    st.title("PharmaPulse")
    st.caption("Drug Sales & Market Analytics")
    st.divider()

    years_available = [2020, 2021, 2022, 2023, 2024]
    selected_years = st.multiselect("Filter by Year", years_available, default=years_available)

    all_categories = ["Cardiovascular", "Diabetes", "CNS", "Oncology",
                      "Gastroenterology", "Respiratory", "Endocrinology",
                      "Infectious", "Immunology"]
    selected_cats = st.multiselect("Therapeutic Category", all_categories, default=all_categories)

    all_regions = ["North America", "Europe", "Asia Pacific",
                   "Latin America", "Middle East & Africa"]
    selected_region = st.selectbox("Region (trend chart)", ["All Regions"] + all_regions)

    st.divider()
    st.caption("Data: Synthetic pharma sales dataset\nBuilt by Aditya Yadav")


# ── Filtered data helper ──────────────────────────────────────────────────────

@st.cache_data
def load_filtered(years, categories):
    conn = get_conn()
    y_placeholder = ",".join(str(y) for y in years)
    c_placeholder = ",".join(f"'{c}'" for c in categories)
    query = f"""
        SELECT * FROM sales
        WHERE year IN ({y_placeholder})
          AND category IN ({c_placeholder})
    """
    df = pd.read_sql_query(query, conn)
    df["date"] = pd.to_datetime(df["date"])
    return df


df = load_filtered(tuple(selected_years), tuple(selected_cats))

# ── KPI cards ─────────────────────────────────────────────────────────────────

st.markdown("## 💊 PharmaPulse — Market Performance Dashboard")
st.caption("Analysing pharmaceutical sales across 20 drugs, 5 regions, 2020–2024")
st.divider()

kpis = kpi_summary()

c1, c2, c3, c4, c5 = st.columns(5)

def kpi_card(col, label, value, sub=""):
    col.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">{label}</div>
        <div class="metric-value">{value}</div>
        <div class="metric-sub">{sub}</div>
    </div>
    """, unsafe_allow_html=True)

kpi_card(c1, "Total Revenue",    f"${kpis['total_revenue_b']}B",    "All years & regions")
kpi_card(c2, "Units Sold",       f"{kpis['total_units']:,}",         "Across all drugs")
kpi_card(c3, "Top Drug",         kpis['top_drug'],                   f"${kpis['top_drug_revenue']}M revenue")
kpi_card(c4, "Avg YoY Growth",   f"{kpis['avg_yoy_growth']}%",       "Across categories")
kpi_card(c5, "Markets Covered",  f"{kpis['total_regions']} Regions", "Global footprint")

st.markdown("<br>", unsafe_allow_html=True)

# ── Row 1: Revenue trend + Market share ───────────────────────────────────────

col_l, col_r = st.columns([3, 2])

with col_l:
    st.subheader("📈 Monthly Revenue Trend")
    region_filter = None if selected_region == "All Regions" else selected_region
    trend_df = monthly_trend(region=region_filter)
    # Filter to selected years
    trend_df = trend_df[trend_df["year"].isin(selected_years)]

    fig_trend = px.area(
        trend_df, x="date", y="revenue_m",
        labels={"revenue_m": "Revenue ($M)", "date": ""},
        color_discrete_sequence=["#4f8ef7"],
        template="plotly_dark",
    )
    fig_trend.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=0, r=0, t=10, b=0), height=300,
    )
    fig_trend.update_traces(fillcolor="rgba(79,142,247,0.15)", line_width=2)
    st.plotly_chart(fig_trend, use_container_width=True)

with col_r:
    st.subheader("🏭 Market Share by Manufacturer")
    ms_year = max(selected_years) if selected_years else 2024
    ms_df = market_share_by_manufacturer(ms_year)

    fig_pie = px.pie(
        ms_df, names="manufacturer", values="revenue_m",
        hole=0.5, template="plotly_dark",
        color_discrete_sequence=px.colors.qualitative.Set2,
    )
    fig_pie.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=0, r=0, t=10, b=0), height=300,
        legend=dict(font=dict(size=11)),
    )
    st.plotly_chart(fig_pie, use_container_width=True)

# ── Row 2: Top drugs + Regional performance ───────────────────────────────────

col_l2, col_r2 = st.columns([2, 3])

with col_l2:
    st.subheader("🏆 Top 10 Drugs by Revenue")
    top_df = top_drugs_by_revenue(10)
    fig_bar = px.bar(
        top_df.sort_values("total_revenue_m"),
        x="total_revenue_m", y="drug_name", orientation="h",
        color="category",
        labels={"total_revenue_m": "Revenue ($M)", "drug_name": ""},
        template="plotly_dark",
        color_discrete_sequence=px.colors.qualitative.Pastel,
    )
    fig_bar.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=0, r=0, t=10, b=0), height=380,
        showlegend=True, legend_title_text="Category",
    )
    st.plotly_chart(fig_bar, use_container_width=True)

with col_r2:
    st.subheader("🌍 Revenue by Category & Year")
    cat_year = (
        df.groupby(["category", "year"])["revenue"]
        .sum()
        .div(1e6)
        .round(2)
        .reset_index()
        .rename(columns={"revenue": "revenue_m"})
    )
    fig_cat = px.line(
        cat_year, x="year", y="revenue_m", color="category",
        markers=True, template="plotly_dark",
        labels={"revenue_m": "Revenue ($M)", "year": "Year"},
        color_discrete_sequence=px.colors.qualitative.Set1,
    )
    fig_cat.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=0, r=0, t=10, b=0), height=380,
    )
    st.plotly_chart(fig_cat, use_container_width=True)

# ── Row 3: Price vs Volume + Lifecycle ───────────────────────────────────────

col_l3, col_r3 = st.columns(2)

with col_l3:
    st.subheader("🔍 Price vs. Volume Correlation")
    pv_df = price_volume_correlation()
    fig_scatter = px.scatter(
        pv_df, x="avg_price", y="total_units",
        color="lifecycle", size="total_revenue_m",
        hover_name="drug_name",
        labels={"avg_price": "Avg Price (USD)", "total_units": "Total Units Sold"},
        template="plotly_dark",
        color_discrete_map={"Launch": "#f7c948", "Growth": "#4f8ef7", "Maturity": "#6fcf97"},
    )
    fig_scatter.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=0, r=0, t=10, b=0), height=340,
    )
    st.plotly_chart(fig_scatter, use_container_width=True)
    st.caption("Bubble size = total revenue. Hover over a drug for details.")

with col_r3:
    st.subheader("🔄 Drug Lifecycle Segmentation")
    lc_df = lifecycle_summary()
    fig_lc = px.bar(
        lc_df, x="lifecycle", y="total_revenue_m",
        color="lifecycle", text="num_drugs",
        labels={"total_revenue_m": "Total Revenue ($M)", "lifecycle": "Stage"},
        template="plotly_dark",
        color_discrete_map={"Launch": "#f7c948", "Growth": "#4f8ef7", "Maturity": "#6fcf97"},
    )
    fig_lc.update_traces(texttemplate="%{text} drugs", textposition="outside")
    fig_lc.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=0, r=0, t=30, b=0), height=340, showlegend=False,
    )
    st.plotly_chart(fig_lc, use_container_width=True)

# ── Row 4: Regional performance table ────────────────────────────────────────

st.subheader("🗺️ Regional Performance Breakdown")
reg_df = regional_performance()
reg_df.columns = ["Region", "Revenue ($M)", "Units Sold", "Drugs Tracked"]

st.dataframe(
    reg_df.style
        .background_gradient(subset=["Revenue ($M)"], cmap="Blues")
        .format({"Revenue ($M)": "{:.1f}", "Units Sold": "{:,}"}),
    use_container_width=True,
    hide_index=True,
)

st.divider()
st.caption("PharmaPulse | Synthetic dataset for analytics demonstration | Built by Aditya Yadav")
