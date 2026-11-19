-- Testing the scoring rules against results (see INSIDE_THE_TEAM.md). DuckDB.
-- Inputs: `scores` (written by pool/build.py) and `outcomes`, one row per merchant contacted.

CREATE TABLE IF NOT EXISTS outcomes (
    brand                 VARCHAR PRIMARY KEY,   -- as in scores.brand
    contacted_on          DATE,
    onboarded             BOOLEAN NOT NULL,      -- shop approved within the tracking window
    week4_gmv_per_day_rm  DOUBLE                 -- coldstart_weekly.gmv_per_day_rm for week 4, NULL if not onboarded
);

-- C1. Did the tiers sort merchants the way the results did?
SELECT s.tier,
       count(*)                                   AS contacted,
       round(avg(CAST(o.onboarded AS INTEGER)), 2) AS onboard_rate,
       round(median(o.week4_gmv_per_day_rm), 2)   AS median_week4_gmv_per_day_rm
FROM scores s JOIN outcomes o USING (brand)
GROUP BY s.tier
ORDER BY s.tier;

-- C2. For each dimension, how results change with its score level.
WITH long AS (
    UNPIVOT (SELECT brand, demand, gap, readiness, content FROM scores)
    ON demand, gap, readiness, content INTO NAME dimension VALUE level
)
SELECT dimension, level,
       count(*)                                   AS contacted,
       round(avg(CAST(o.onboarded AS INTEGER)), 2) AS onboard_rate,
       round(median(o.week4_gmv_per_day_rm), 2)   AS median_week4_gmv_per_day_rm
FROM long JOIN outcomes o USING (brand)
GROUP BY ALL
ORDER BY dimension, level;

-- C3. One number per dimension: rank correlation of score level with week-4 GMV per day (onboarded merchants).
WITH long AS (
    UNPIVOT (SELECT brand, demand, gap, readiness, content FROM scores)
    ON demand, gap, readiness, content INTO NAME dimension VALUE level
),
ranked AS (
    SELECT dimension,
           percent_rank() OVER (PARTITION BY dimension ORDER BY level)                  AS level_rank,
           percent_rank() OVER (PARTITION BY dimension ORDER BY o.week4_gmv_per_day_rm) AS result_rank
    FROM long JOIN outcomes o USING (brand)
    WHERE o.onboarded AND o.week4_gmv_per_day_rm IS NOT NULL
)
SELECT dimension, count(*) AS merchants, round(corr(level_rank, result_rank), 2) AS rank_correlation
FROM ranked
GROUP BY dimension
ORDER BY rank_correlation DESC NULLS LAST;
