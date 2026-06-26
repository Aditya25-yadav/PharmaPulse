"""
analyze.py
----------
Core analysis functions used by both the notebook and the dashboard.
All functions read from the SQLite DB for consistency.

Usage (standalone):
    python scripts/analyze.py
"""

import os
import sqlite3
import pandas as pd
import numpy as np

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "processed", "pharmapulse.db")


def get_conn() -> sqlite3.Connection:
    return sqlite3.connect(DB_PATH)


# ── 1. Top drugs by total revenue ────────────────────────────────────────────

def top_drugs_by_revenue(n: int = 10) -> pd.DataFrame:
    """Return top N drugs ranked by total revenue across all years and regions."""
    query = """
        SELECT
            drug_name,
            manufacturer,
            category,
            lifecycle,
            ROUND(SUM(revenue) / 1e6, 2)   AS total_revenue_m,
            SUM(units_sold)                 AS total_units
        FROM sales
        GROUP BY drug_name, manufacturer, category, lifecycle
        ORDER BY total_revenue_m DESC
        LIMIT :n
    """
    return pd.read_sql_query(query, get_conn(), params={"n": n})


# ── 2. Year-over-year growth by category ─────────────────────────────────────

def yoy_growth_by_category() -> pd.DataFrame:
    """
    Compute year-over-year revenue growth % for each therapeutic category.
    Returns a wide DataFrame: rows = categories, columns = years.
    """
    query = """
        SELECT
            category,
            year,
            ROUND(SUM(revenue) / 1e6, 2) AS revenue_m
        FROM sales
        GROUP BY category, year
        ORDER BY category, year
    """
    df = pd.read_sql_query(query, get_conn())

    # Pivot to wide
    wide = df.pivot(index="category", columns="year", values="revenue_m").fillna(0)

    # Calculate YoY growth % for each consecutive year pair
    years = sorted(df["year"].unique())
    growth_cols = {}
    for i in range(1, len(years)):
        prev, curr = years[i - 1], years[i]
        col = f"YoY {prev}→{curr} (%)"
        growth_cols[col] = ((wide[curr] - wide[prev]) / wide[prev] * 100).round(1)

    result = pd.concat([wide, pd.DataFrame(growth_cols)], axis=1).reset_index()
    return result


# ── 3. Market share by manufacturer ─────────────────────────────────────────

def market_share_by_manufacturer(year: int = None) -> pd.DataFrame:
    """Return revenue share % for each manufacturer. Optionally filter by year."""
    where = f"WHERE year = {year}" if year else ""
    query = f"""
        SELECT
            manufacturer,
            ROUND(SUM(revenue) / 1e6, 2) AS revenue_m
        FROM sales
        {where}
        GROUP BY manufacturer
        ORDER BY revenue_m DESC
    """
    df = pd.read_sql_query(query, get_conn())
    df["share_pct"] = (df["revenue_m"] / df["revenue_m"].sum() * 100).round(1)
    return df


# ── 4. Price vs volume correlation ───────────────────────────────────────────

def price_volume_correlation() -> pd.DataFrame:
    """
    Aggregate avg price and total units per drug.
    Returns DataFrame ready for a scatter plot + Pearson correlation.
    """
    query = """
        SELECT
            drug_name,
            category,
            lifecycle,
            ROUND(AVG(price_per_unit), 2)  AS avg_price,
            SUM(units_sold)                AS total_units,
            ROUND(SUM(revenue) / 1e6, 2)  AS total_revenue_m
        FROM sales
        GROUP BY drug_name, category, lifecycle
    """
    df = pd.read_sql_query(query, get_conn())
    corr = df["avg_price"].corr(df["total_units"])
    print(f"  Pearson correlation (price vs units): {corr:.3f}")
    return df


# ── 5. Monthly revenue trend (all drugs or one) ──────────────────────────────

def monthly_trend(drug_name: str = None, region: str = None) -> pd.DataFrame:
    """
    Return monthly aggregated revenue. Filter by drug and/or region if provided.
    """
    filters = []
    params  = {}
    if drug_name:
        filters.append("drug_name = :drug")
        params["drug"] = drug_name
    if region:
        filters.append("region = :region")
        params["region"] = region

    where = ("WHERE " + " AND ".join(filters)) if filters else ""

    query = f"""
        SELECT
            year,
            month,
            date,
            ROUND(SUM(revenue) / 1e6, 4) AS revenue_m,
            SUM(units_sold) AS units_sold
        FROM sales
        {where}
        GROUP BY year, month, date
        ORDER BY date
    """
    df = pd.read_sql_query(query, get_conn(), params=params)
    df["date"] = pd.to_datetime(df["date"])
    return df


# ── 6. Regional performance ───────────────────────────────────────────────────

def regional_performance(year: int = None) -> pd.DataFrame:
    """Revenue and units by region, optionally filtered by year."""
    where = f"WHERE year = {year}" if year else ""
    query = f"""
        SELECT
            region,
            ROUND(SUM(revenue) / 1e6, 2)   AS revenue_m,
            SUM(units_sold)                 AS units_sold,
            COUNT(DISTINCT drug_name)       AS drugs_sold
        FROM sales
        {where}
        GROUP BY region
        ORDER BY revenue_m DESC
    """
    return pd.read_sql_query(query, get_conn())


# ── 7. Lifecycle segmentation summary ────────────────────────────────────────

def lifecycle_summary() -> pd.DataFrame:
    """Summarise revenue and drug count per lifecycle stage."""
    query = """
        SELECT
            lifecycle,
            COUNT(DISTINCT drug_name)       AS num_drugs,
            ROUND(SUM(revenue) / 1e6, 2)   AS total_revenue_m,
            ROUND(AVG(price_per_unit), 2)   AS avg_price
        FROM sales
        GROUP BY lifecycle
        ORDER BY total_revenue_m DESC
    """
    return pd.read_sql_query(query, get_conn())


# ── 8. KPI summary ────────────────────────────────────────────────────────────

def kpi_summary() -> dict:
    """Top-level KPIs for the dashboard header cards."""
    query = """
        SELECT
            ROUND(SUM(revenue) / 1e9, 2)           AS total_revenue_b,
            SUM(units_sold)                         AS total_units,
            COUNT(DISTINCT drug_name)               AS total_drugs,
            COUNT(DISTINCT region)                  AS total_regions
        FROM sales
    """
    row = pd.read_sql_query(query, get_conn()).iloc[0]

    # Best-performing drug
    top_drug = top_drugs_by_revenue(1).iloc[0]

    # Avg YoY growth across all categories (last year pair)
    yoy = yoy_growth_by_category()
    last_growth_col = [c for c in yoy.columns if isinstance(c, str) and "YoY" in c][-1]
    avg_growth = yoy[last_growth_col].mean()

    return {
        "total_revenue_b":  row["total_revenue_b"],
        "total_units":      int(row["total_units"]),
        "total_drugs":      int(row["total_drugs"]),
        "total_regions":    int(row["total_regions"]),
        "top_drug":         top_drug["drug_name"],
        "top_drug_revenue": top_drug["total_revenue_m"],
        "avg_yoy_growth":   round(avg_growth, 1),
    }


# ── CLI runner ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("\n=== Top 5 Drugs by Revenue ===")
    print(top_drugs_by_revenue(5).to_string(index=False))

    print("\n=== Market Share by Manufacturer (2024) ===")
    print(market_share_by_manufacturer(2024).to_string(index=False))

    print("\n=== Lifecycle Summary ===")
    print(lifecycle_summary().to_string(index=False))

    print("\n=== Price vs Volume Correlation ===")
    price_volume_correlation()

    print("\n=== KPI Summary ===")
    for k, v in kpi_summary().items():
        print(f"  {k}: {v}")
