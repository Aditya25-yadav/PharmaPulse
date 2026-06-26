# 💊 PharmaPulse — Drug Sales & Market Performance Analytics

An end-to-end analytics project analyzing pharmaceutical sales data to uncover market trends, segment performance, and growth opportunities — built with Python, SQL, and an interactive Streamlit dashboard.

---

## 📌 Project Overview

PharmaPulse simulates the analytics workflow at a pharma consulting firm:
- Ingest and clean raw drug sales data
- Store and query using SQL (SQLite)
- Perform exploratory and trend analysis with Pandas
- Visualize insights in an interactive Streamlit dashboard

---

## 🗂️ Project Structure

```
pharmapulse/
│
├── data/
│   ├── raw/                  # Raw CSV datasets
│   └── processed/            # Cleaned data outputs
│
├── sql/
│   └── analysis_queries.sql  # All SQL queries used for analysis
│
├── scripts/
│   ├── ingest.py             # Data loading and DB setup
│   └── analyze.py            # Core analysis functions
│
├── notebooks/
│   └── eda.ipynb             # Exploratory Data Analysis notebook
│
├── dashboard/
│   └── app.py                # Streamlit dashboard
│
├── requirements.txt
└── README.md
```

---

## 📊 Key Insights Delivered

- Top 10 drugs by total revenue across all regions
- Year-over-year sales growth by therapeutic category
- Market share breakdown by manufacturer
- Price vs. volume correlation analysis
- Drug lifecycle segmentation (Launch / Growth / Maturity / Decline)
- Regional performance heatmap

---

## 🛠️ Tech Stack

| Tool | Purpose |
|------|---------|
| Python 3.10+ | Core analysis language |
| Pandas | Data cleaning & transformation |
| SQLite + sqlite3 | SQL-based analysis layer |
| Matplotlib / Seaborn | Static charts for EDA |
| Plotly | Interactive charts |
| Streamlit | Dashboard UI |
| Jupyter | Exploratory notebook |

---

## 🚀 Getting Started

### 1. Clone the repo
```bash
git clone https://github.com/YOUR_USERNAME/pharmapulse.git
cd pharmapulse
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Generate & load data
```bash
python scripts/ingest.py
```

### 4. Run the dashboard
```bash
streamlit run dashboard/app.py
```

### 5. (Optional) Open the EDA notebook
```bash
jupyter notebook notebooks/eda.ipynb
```

---

## 📁 Dataset

This project uses a **synthetically generated** pharmaceutical sales dataset modeled after real-world industry structure (drug names, therapeutic areas, regional sales, pricing). Generated via `scripts/ingest.py` — no external download required.

To use a real dataset, replace `data/raw/pharma_sales.csv` with any Kaggle pharma sales CSV and re-run `ingest.py`.

---

## 📈 Dashboard Preview

The Streamlit dashboard includes:
- KPI cards: Total Revenue, Top Drug, Best Region, Avg Growth Rate
- Sales trend line chart (filterable by year and category)
- Market share donut chart
- Top 10 drugs bar chart
- Price vs. Volume scatter plot
- Lifecycle segmentation table

---

## 🙋 Author

**Aditya Yadav**  
B.Tech CSE, MITWPU Pune  
[GitHub](https://github.com/Aditya25-yadav) • [LinkedIn](https://linkedin.com/in/) • adi2507yadav@gmail.com
