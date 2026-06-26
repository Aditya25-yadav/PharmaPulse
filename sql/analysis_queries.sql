-- ============================================================
-- PharmaPulse — SQL Analysis Queries
-- Database: data/processed/pharmapulse.db
-- Table: sales
-- ============================================================
-- Columns: drug_name, category, manufacturer, region,
--          year, month, date, units_sold, price_per_unit,
--          revenue, lifecycle
-- ============================================================


-- ── 1. Top 10 drugs by total revenue ────────────────────────
SELECT
    drug_name,
    manufacturer,
    category,
    ROUND(SUM(revenue) / 1e6, 2)  AS total_revenue_m,
    SUM(units_sold)                AS total_units
FROM sales
GROUP BY drug_name, manufacturer, category
ORDER BY total_revenue_m DESC
LIMIT 10;


-- ── 2. Revenue by therapeutic category per year ─────────────
SELECT
    category,
    year,
    ROUND(SUM(revenue) / 1e6, 2) AS revenue_m,
    SUM(units_sold)               AS units_sold
FROM sales
GROUP BY category, year
ORDER BY category, year;


-- ── 3. Market share by manufacturer (all years) ─────────────
SELECT
    manufacturer,
    ROUND(SUM(revenue) / 1e6, 2)                           AS revenue_m,
    ROUND(SUM(revenue) * 100.0 / SUM(SUM(revenue)) OVER(), 1) AS share_pct
FROM sales
GROUP BY manufacturer
ORDER BY revenue_m DESC;


-- ── 4. Year-over-year revenue growth per category ───────────
-- Uses a self-join to get the prior year's revenue.
SELECT
    curr.category,
    curr.year,
    ROUND(curr.revenue_m, 2)                                     AS revenue_m,
    ROUND((curr.revenue_m - prev.revenue_m) / prev.revenue_m * 100, 1) AS yoy_growth_pct
FROM (
    SELECT category, year, SUM(revenue) / 1e6 AS revenue_m
    FROM sales
    GROUP BY category, year
) curr
LEFT JOIN (
    SELECT category, year, SUM(revenue) / 1e6 AS revenue_m
    FROM sales
    GROUP BY category, year
) prev
  ON curr.category = prev.category
 AND curr.year     = prev.year + 1
ORDER BY curr.category, curr.year;


-- ── 5. Regional performance ranked ──────────────────────────
SELECT
    region,
    ROUND(SUM(revenue) / 1e6, 2)  AS revenue_m,
    SUM(units_sold)                AS total_units,
    ROUND(AVG(price_per_unit), 2)  AS avg_price
FROM sales
GROUP BY region
ORDER BY revenue_m DESC;


-- ── 6. Average price per drug and its revenue rank ──────────
SELECT
    drug_name,
    category,
    lifecycle,
    ROUND(AVG(price_per_unit), 2)  AS avg_price,
    SUM(units_sold)                AS total_units,
    ROUND(SUM(revenue) / 1e6, 2)  AS total_revenue_m,
    RANK() OVER (ORDER BY SUM(revenue) DESC) AS revenue_rank
FROM sales
GROUP BY drug_name, category, lifecycle
ORDER BY revenue_rank;


-- ── 7. Monthly revenue trend (all drugs) ────────────────────
SELECT
    year,
    month,
    date,
    ROUND(SUM(revenue) / 1e6, 4)  AS revenue_m,
    SUM(units_sold)                AS units_sold
FROM sales
GROUP BY year, month, date
ORDER BY date;


-- ── 8. Drugs underperforming vs. category average ───────────
-- Identifies drugs whose revenue is below their category mean.
WITH drug_revenue AS (
    SELECT
        drug_name,
        category,
        SUM(revenue) / 1e6 AS drug_revenue_m
    FROM sales
    GROUP BY drug_name, category
),
cat_avg AS (
    SELECT
        category,
        AVG(drug_revenue_m) AS avg_revenue_m
    FROM drug_revenue
    GROUP BY category
)
SELECT
    d.drug_name,
    d.category,
    ROUND(d.drug_revenue_m, 2)  AS drug_revenue_m,
    ROUND(c.avg_revenue_m, 2)   AS category_avg_m,
    ROUND((d.drug_revenue_m - c.avg_revenue_m) / c.avg_revenue_m * 100, 1) AS pct_vs_avg
FROM drug_revenue d
JOIN cat_avg c ON d.category = c.category
WHERE d.drug_revenue_m < c.avg_revenue_m
ORDER BY pct_vs_avg ASC;


-- ── 9. Lifecycle stage revenue breakdown ────────────────────
SELECT
    lifecycle,
    COUNT(DISTINCT drug_name)       AS num_drugs,
    ROUND(SUM(revenue) / 1e6, 2)   AS total_revenue_m,
    ROUND(AVG(price_per_unit), 2)   AS avg_price,
    ROUND(SUM(revenue) * 100.0 / SUM(SUM(revenue)) OVER(), 1) AS portfolio_share_pct
FROM sales
GROUP BY lifecycle
ORDER BY total_revenue_m DESC;


-- ── 10. Top drug per region in 2024 ─────────────────────────
SELECT
    region,
    drug_name,
    ROUND(SUM(revenue) / 1e6, 2) AS revenue_m
FROM sales
WHERE year = 2024
GROUP BY region, drug_name
QUALIFY RANK() OVER (PARTITION BY region ORDER BY SUM(revenue) DESC) = 1
ORDER BY region;
-- Note: QUALIFY is SQLite 3.45+; if it fails use a subquery approach.
