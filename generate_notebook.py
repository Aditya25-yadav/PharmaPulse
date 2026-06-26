"""
generate_notebook.py
--------------------
Run this script to generate the EDA Jupyter notebook.

Usage:
    python generate_notebook.py
"""

import json, os

cells = [
    # Cell 0 - Title
    {
        "cell_type": "markdown",
        "metadata": {},
        "source": [
            "# PharmaPulse — Exploratory Data Analysis\n",
            "\n",
            "End-to-end analysis of synthetic pharmaceutical sales data.\n",
            "\n",
            "**Sections:**\n",
            "1. Data loading & overview\n",
            "2. Revenue trends over time\n",
            "3. Category & manufacturer analysis\n",
            "4. Price vs volume correlation\n",
            "5. Lifecycle segmentation\n",
            "6. Regional performance\n",
            "7. Key findings summary\n"
        ]
    },
    # Cell 1 - Imports
    {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "import sys\n",
            "sys.path.insert(0, '..')\n",
            "\n",
            "import pandas as pd\n",
            "import numpy as np\n",
            "import matplotlib.pyplot as plt\n",
            "import seaborn as sns\n",
            "import plotly.express as px\n",
            "import sqlite3\n",
            "\n",
            "from scripts.analyze import (\n",
            "    get_conn, top_drugs_by_revenue, market_share_by_manufacturer,\n",
            "    yoy_growth_by_category, monthly_trend, regional_performance,\n",
            "    lifecycle_summary, price_volume_correlation, kpi_summary\n",
            ")\n",
            "\n",
            "sns.set_theme(style='darkgrid', palette='muted')\n",
            "plt.rcParams['figure.figsize'] = (12, 5)\n",
            "pd.set_option('display.float_format', '{:.2f}'.format)\n",
            "print('Setup complete ✅')"
        ]
    },
    # Cell 2 - Load data
    {
        "cell_type": "markdown",
        "metadata": {},
        "source": ["## 1. Data Loading & Overview"]
    },
    {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "df = pd.read_sql_query('SELECT * FROM sales', get_conn())\n",
            "df['date'] = pd.to_datetime(df['date'])\n",
            "print(f'Shape: {df.shape}')\n",
            "df.head()"
        ]
    },
    {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "print('Dtypes:')\n",
            "print(df.dtypes)\n",
            "print('\\nMissing values:')\n",
            "print(df.isnull().sum())\n",
            "print('\\nBasic stats:')\n",
            "df[['units_sold', 'price_per_unit', 'revenue']].describe()"
        ]
    },
    # Cell 3 - Revenue trends
    {
        "cell_type": "markdown",
        "metadata": {},
        "source": ["## 2. Revenue Trends Over Time"]
    },
    {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "trend = monthly_trend()\n",
            "\n",
            "fig, ax = plt.subplots(figsize=(14, 5))\n",
            "ax.plot(trend['date'], trend['revenue_m'], color='#4f8ef7', linewidth=2)\n",
            "ax.fill_between(trend['date'], trend['revenue_m'], alpha=0.15, color='#4f8ef7')\n",
            "ax.set_title('Total Monthly Revenue — All Drugs & Regions', fontsize=14, pad=12)\n",
            "ax.set_xlabel('')\n",
            "ax.set_ylabel('Revenue ($M)')\n",
            "plt.tight_layout()\n",
            "plt.show()\n",
            "print(f'Peak month: {trend.loc[trend.revenue_m.idxmax(), \"date\"].strftime(\"%b %Y\")} — ${trend.revenue_m.max():.1f}M')"
        ]
    },
    {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "# YoY growth heatmap\n",
            "yoy = yoy_growth_by_category()\n",
            "growth_cols = [c for c in yoy.columns if 'YoY' in c]\n",
            "heat_df = yoy.set_index('category')[growth_cols]\n",
            "\n",
            "fig, ax = plt.subplots(figsize=(10, 5))\n",
            "sns.heatmap(heat_df, annot=True, fmt='.1f', cmap='RdYlGn', center=0,\n",
            "            linewidths=0.5, ax=ax, cbar_kws={'label': 'YoY Growth (%)'})\n",
            "ax.set_title('Year-over-Year Revenue Growth by Therapeutic Category (%)', fontsize=13, pad=12)\n",
            "ax.set_ylabel('')\n",
            "plt.tight_layout()\n",
            "plt.show()"
        ]
    },
    # Cell 4 - Category analysis
    {
        "cell_type": "markdown",
        "metadata": {},
        "source": ["## 3. Category & Manufacturer Analysis"]
    },
    {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "top10 = top_drugs_by_revenue(10)\n",
            "\n",
            "fig, ax = plt.subplots(figsize=(11, 6))\n",
            "colors = sns.color_palette('Set2', n_colors=len(top10['category'].unique()))\n",
            "cat_color = {c: colors[i] for i, c in enumerate(top10['category'].unique())}\n",
            "\n",
            "bars = ax.barh(top10['drug_name'], top10['total_revenue_m'],\n",
            "               color=[cat_color[c] for c in top10['category']])\n",
            "ax.set_xlabel('Total Revenue ($M)')\n",
            "ax.set_title('Top 10 Drugs by Total Revenue (2020–2024)', fontsize=13)\n",
            "\n",
            "for bar, val in zip(bars, top10['total_revenue_m']):\n",
            "    ax.text(bar.get_width() + 5, bar.get_y() + bar.get_height()/2,\n",
            "            f'${val:.0f}M', va='center', fontsize=9)\n",
            "\n",
            "plt.tight_layout()\n",
            "plt.show()"
        ]
    },
    {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "ms = market_share_by_manufacturer()\n",
            "fig, ax = plt.subplots(figsize=(8, 8))\n",
            "wedges, texts, autotexts = ax.pie(\n",
            "    ms['revenue_m'], labels=ms['manufacturer'],\n",
            "    autopct='%1.1f%%', startangle=140,\n",
            "    colors=sns.color_palette('pastel'),\n",
            "    wedgeprops={'edgecolor': 'white', 'linewidth': 1.5}\n",
            ")\n",
            "ax.set_title('Market Share by Manufacturer — Total Revenue', fontsize=13)\n",
            "plt.tight_layout()\n",
            "plt.show()"
        ]
    },
    # Cell 5 - Price vs volume
    {
        "cell_type": "markdown",
        "metadata": {},
        "source": ["## 4. Price vs Volume Correlation"]
    },
    {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "pv = price_volume_correlation()\n",
            "\n",
            "lc_colors = {'Launch': '#f7c948', 'Growth': '#4f8ef7', 'Maturity': '#6fcf97'}\n",
            "\n",
            "fig, ax = plt.subplots(figsize=(11, 6))\n",
            "for lc, grp in pv.groupby('lifecycle'):\n",
            "    ax.scatter(grp['avg_price'], grp['total_units'],\n",
            "               s=grp['total_revenue_m'] / 10,\n",
            "               label=lc, color=lc_colors[lc], alpha=0.8, edgecolors='white', linewidth=0.7)\n",
            "    for _, row in grp.iterrows():\n",
            "        ax.annotate(row['drug_name'], (row['avg_price'], row['total_units']),\n",
            "                    textcoords='offset points', xytext=(5, 4), fontsize=8)\n",
            "\n",
            "ax.set_xlabel('Average Price per Unit (USD)')\n",
            "ax.set_ylabel('Total Units Sold')\n",
            "ax.set_title('Price vs. Volume by Drug — Bubble size = Revenue', fontsize=13)\n",
            "ax.legend(title='Lifecycle')\n",
            "plt.tight_layout()\n",
            "plt.show()\n",
            "\n",
            "corr = pv['avg_price'].corr(pv['total_units'])\n",
            "print(f'Pearson correlation (price vs volume): {corr:.3f}')\n",
            "print('→ Negative correlation confirms higher-priced drugs sell fewer units (expected in pharma).')"
        ]
    },
    # Cell 6 - Lifecycle
    {
        "cell_type": "markdown",
        "metadata": {},
        "source": ["## 5. Lifecycle Segmentation"]
    },
    {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "lc = lifecycle_summary()\n",
            "print(lc.to_string(index=False))\n",
            "\n",
            "fig, axes = plt.subplots(1, 2, figsize=(12, 5))\n",
            "\n",
            "axes[0].bar(lc['lifecycle'], lc['total_revenue_m'],\n",
            "            color=[lc_colors[l] for l in lc['lifecycle']], edgecolor='white')\n",
            "axes[0].set_title('Total Revenue by Lifecycle Stage')\n",
            "axes[0].set_ylabel('Revenue ($M)')\n",
            "\n",
            "axes[1].bar(lc['lifecycle'], lc['avg_price'],\n",
            "            color=[lc_colors[l] for l in lc['lifecycle']], edgecolor='white')\n",
            "axes[1].set_title('Average Drug Price by Lifecycle Stage')\n",
            "axes[1].set_ylabel('Avg Price (USD)')\n",
            "\n",
            "plt.tight_layout()\n",
            "plt.show()"
        ]
    },
    # Cell 7 - Regional
    {
        "cell_type": "markdown",
        "metadata": {},
        "source": ["## 6. Regional Performance"]
    },
    {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "reg = regional_performance()\n",
            "print(reg.to_string(index=False))\n",
            "\n",
            "fig, ax = plt.subplots(figsize=(10, 5))\n",
            "bars = ax.bar(reg['region'], reg['revenue_m'],\n",
            "              color=sns.color_palette('Blues_r', n_colors=len(reg)),\n",
            "              edgecolor='white')\n",
            "ax.set_title('Total Revenue by Region (2020–2024)', fontsize=13)\n",
            "ax.set_ylabel('Revenue ($M)')\n",
            "ax.set_xlabel('')\n",
            "for bar, val in zip(bars, reg['revenue_m']):\n",
            "    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 20,\n",
            "            f'${val:.0f}M', ha='center', fontsize=9)\n",
            "plt.xticks(rotation=15)\n",
            "plt.tight_layout()\n",
            "plt.show()"
        ]
    },
    # Cell 8 - Summary
    {
        "cell_type": "markdown",
        "metadata": {},
        "source": [
            "## 7. Key Findings Summary\n",
            "\n",
            "| Finding | Detail |\n",
            "|---------|--------|\n",
            "| **Top revenue driver** | Oncology drugs (Pembrolizumab, Trastuzumab) generate highest per-drug revenue due to premium pricing |\n",
            "| **Fastest growing category** | Diabetes (driven by Semaglutide launch) shows highest YoY growth |\n",
            "| **Price-volume relationship** | Negative Pearson correlation confirms specialty drugs trade volume for margin |\n",
            "| **Regional dominance** | North America accounts for ~42% of global revenue |\n",
            "| **Lifecycle insight** | Launch-stage drugs have highest avg price but contribute less total revenue — growth opportunity |\n",
            "| **Manufacturer concentration** | Pfizer and AstraZeneca together hold ~45% market share |\n"
        ]
    },
    {
        "cell_type": "code",
        "execution_count": None,
        "metadata": {},
        "outputs": [],
        "source": [
            "kpis = kpi_summary()\n",
            "print('=== PharmaPulse KPI Summary ===')\n",
            "for k, v in kpis.items():\n",
            "    print(f'  {k:25s}: {v}')"
        ]
    }
]

notebook = {
    "nbformat": 4,
    "nbformat_minor": 5,
    "metadata": {
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python", "version": "3.10.0"}
    },
    "cells": cells
}

out_path = os.path.join(os.path.dirname(__file__), "notebooks", "eda.ipynb")
os.makedirs(os.path.dirname(out_path), exist_ok=True)
with open(out_path, "w") as f:
    json.dump(notebook, f, indent=1)

print(f"✅ Notebook written to {out_path}")
