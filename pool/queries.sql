-- Questions a category team asks of the pool. Run in DuckDB:
--   duckdb pool/pool.duckdb < pool/queries.sql        (or python pool/run_queries.py)
-- Tables: candidates (one row per brand, from public pages), scores (frozen rules in pool/SCORING.md).

-- Q1. Who to contact first: tier A and B merchants with no content-commerce shop yet, or a shop not yet large.
SELECT rank, brand, kind, subcategory, supply_type, total, tier, segment, next_action, public_contact_route
FROM scores
WHERE segment IN ('open a shop', 'activate') AND tier IN ('A', 'B')
ORDER BY rank;

-- Q2. The best two brands per sub-category, so every sub-category gets supply, not only the top scorers.
SELECT subcategory, brand, total, tier, segment
FROM (SELECT *, row_number() OVER (PARTITION BY subcategory ORDER BY total DESC, readiness DESC, brand) AS n FROM scores)
WHERE n <= 2
ORDER BY subcategory, n;

-- Q3. Mix of local and cross-border supply, and of brands, distributors and retailers, by tier.
SELECT tier, supply_type, kind, count(*) AS merchants
FROM scores
GROUP BY ALL
ORDER BY tier, merchants DESC;

-- Q4. Where each brand already sells, and where content commerce would be new.
SELECT c.brand, c.subcategory, c.official_stores_elsewhere, c.content_commerce_shop_linked,
       c.short_video_account_linked, s.segment
FROM candidates c JOIN scores s USING (brand)
ORDER BY s.segment, s.rank;

-- Q5. Document requests to prepare: brands whose readiness is below 3, with the next action.
SELECT brand, subcategory, readiness, c.presence, c.certification_evidence, next_action
FROM scores s JOIN candidates c USING (brand, subcategory)
WHERE readiness < 3
ORDER BY readiness DESC, rank;

-- Q6. Score breakdown: how much each dimension adds to the total of the top ten.
SELECT rank, brand,
       round(100 * 0.30 * demand / 3, 1)    AS from_demand,
       round(100 * 0.30 * gap / 3, 1)       AS from_gap,
       round(100 * 0.25 * readiness / 3, 1) AS from_readiness,
       round(100 * 0.15 * content / 3, 1)   AS from_content,
       total
FROM scores
WHERE rank <= 10
ORDER BY rank;
