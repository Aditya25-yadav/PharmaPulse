"""
ingest.py
---------
Generates a synthetic pharmaceutical sales dataset and loads it into
a local SQLite database. Run this first before anything else.

Usage:
    python scripts/ingest.py
"""

import os
import sqlite3
import numpy as np
import pandas as pd

# ── Config ──────────────────────────────────────────────────────────────────

RAW_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "raw", "pharma_sales.csv")
DB_PATH  = os.path.join(os.path.dirname(__file__), "..", "data", "processed", "pharmapulse.db")

os.makedirs(os.path.dirname(RAW_PATH), exist_ok=True)
os.makedirs(os.path.dirname(DB_PATH),  exist_ok=True)

# ── Synthetic data definition ────────────────────────────────────────────────

DRUGS = [
    ("Atorvastatin",    "Cardiovascular",   "Pfizer",        12.50),
    ("Metformin",       "Diabetes",         "Teva",           4.20),
    ("Lisinopril",      "Cardiovascular",   "Merck",          8.75),
    ("Omeprazole",      "Gastroenterology", "AstraZeneca",    9.30),
    ("Amlodipine",      "Cardiovascular",   "Pfizer",        11.00),
    ("Levothyroxine",   "Endocrinology",    "Abbott",        15.60),
    ("Sertraline",      "CNS",              "Pfizer",        22.40),
    ("Azithromycin",    "Infectious",       "Teva",           6.80),
    ("Montelukast",     "Respiratory",      "Merck",         18.90),
    ("Gabapentin",      "CNS",              "Pfizer",        14.20),
    ("Pantoprazole",    "Gastroenterology", "AstraZeneca",   10.10),
    ("Rosuvastatin",    "Cardiovascular",   "AstraZeneca",   19.80),
    ("Escitalopram",    "CNS",              "Abbott",        25.60),
    ("Dapagliflozin",   "Diabetes",         "AstraZeneca",   45.30),
    ("Apixaban",        "Cardiovascular",   "Pfizer",        52.10),
    ("Semaglutide",     "Diabetes",         "Novo Nordisk",  380.00),
    ("Dupilumab",       "Immunology",       "Sanofi",        720.00),
    ("Pembrolizumab",   "Oncology",         "Merck",        1200.00),
    ("Trastuzumab",     "Oncology",         "Roche",         980.00),
    ("Ibrutinib",       "Oncology",         "AbbVie",        860.00),
]

REGIONS = ["North America", "Europe", "Asia Pacific", "Latin America", "Middle East & Africa"]

YEARS  = [2020, 2021, 2022, 2023, 2024]
MONTHS = list(range(1, 13))

# ── Generator ────────────────────────────────────────────────────────────────

def generate_dataset(seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    rows = []

    # Lifecycle phase by drug index (0-4 = mature, 5-14 = growth, 15-19 = launch)
    def lifecycle(drug_idx: int) -> str:
        if drug_idx < 5:
            return "Maturity"
        elif drug_idx < 15:
            return "Growth"
        else:
            return "Launch"

    # Base volume per region (North America dominates)
    region_weights = {
        "North America":       0.42,
        "Europe":              0.28,
        "Asia Pacific":        0.18,
        "Latin America":       0.07,
        "Middle East & Africa":0.05,
    }

    for drug_idx, (drug, category, manufacturer, base_price) in enumerate(DRUGS):
        phase = lifecycle(drug_idx)

        # Yearly growth rate depends on lifecycle
        growth_rates = {
            "Maturity": rng.uniform(0.01, 0.04, size=len(YEARS)),
            "Growth":   rng.uniform(0.08, 0.20, size=len(YEARS)),
            "Launch":   rng.uniform(0.25, 0.60, size=len(YEARS)),
        }[phase]

        base_units = rng.integers(50_000, 500_000)

        for y_idx, year in enumerate(YEARS):
            year_units = int(base_units * np.prod(1 + growth_rates[:y_idx + 1]))

            # Slight price drift year-on-year
            price = round(base_price * (1 + rng.uniform(-0.02, 0.05) * y_idx), 2)

            for region in REGIONS:
                region_units = int(year_units * region_weights[region])

                for month in MONTHS:
                    # Add monthly seasonality noise
                    seasonal = 1 + 0.08 * np.sin(2 * np.pi * (month - 3) / 12)
                    monthly_units = max(1, int(region_units / 12 * seasonal * rng.uniform(0.9, 1.1)))
                    revenue = round(monthly_units * price, 2)

                    rows.append({
                        "drug_name":     drug,
                        "category":      category,
                        "manufacturer":  manufacturer,
                        "region":        region,
                        "year":          year,
                        "month":         month,
                        "units_sold":    monthly_units,
                        "price_per_unit":price,
                        "revenue":       revenue,
                        "lifecycle":     phase,
                    })

    df = pd.DataFrame(rows)
    return df


# ── Clean ────────────────────────────────────────────────────────────────────

def clean(df: pd.DataFrame) -> pd.DataFrame:
    """Basic cleaning steps — mirrors what you'd do on a real messy dataset."""
    df = df.copy()

    # Create a proper date column
    df["date"] = pd.to_datetime(df[["year", "month"]].assign(day=1))

    # Ensure correct dtypes
    df["units_sold"]     = df["units_sold"].astype(int)
    df["price_per_unit"] = df["price_per_unit"].astype(float)
    df["revenue"]        = df["revenue"].astype(float)

    # Drop any accidental duplicates
    df = df.drop_duplicates()

    # Sort
    df = df.sort_values(["drug_name", "region", "date"]).reset_index(drop=True)

    return df


# ── Load to SQLite ───────────────────────────────────────────────────────────

def load_to_db(df: pd.DataFrame, db_path: str) -> None:
    conn = sqlite3.connect(db_path)
    df.to_sql("sales", conn, if_exists="replace", index=False)

    # Create useful indexes for faster query performance
    conn.execute("CREATE INDEX IF NOT EXISTS idx_drug     ON sales(drug_name)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_category ON sales(category)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_region   ON sales(region)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_year     ON sales(year)")
    conn.commit()
    conn.close()
    print(f"✅ Loaded {len(df):,} rows into {db_path}")


# ── Main ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("🔄 Generating synthetic pharma sales dataset...")
    df = generate_dataset()
    df = clean(df)

    print(f"   Shape : {df.shape}")
    print(f"   Years : {sorted(df['year'].unique())}")
    print(f"   Drugs : {df['drug_name'].nunique()}")
    print(f"   Regions: {df['region'].nunique()}")

    # Save raw CSV
    df.to_csv(RAW_PATH, index=False)
    print(f"✅ Saved CSV → {RAW_PATH}")

    # Load to DB
    load_to_db(df, DB_PATH)
