-- Weekly first-30-days view per merchant. Day 1 = shop_live_date. Week 1 = days 1-7, ... week 4 = days 22-28,
-- week 5 = days 29-30 (two days, shown so the 30 days are complete). Run after schema.sql and loading data.

-- 1. One row per merchant and week.
CREATE OR REPLACE VIEW coldstart_weekly AS
WITH d AS (
    SELECT s.*, m.brand, m.subcategory, m.supply_type,
           CAST(date_diff('day', m.shop_live_date, s.day) AS INTEGER) + 1 AS day_n
    FROM daily_shop s JOIN merchants m USING (merchant_id)
    WHERE m.shop_live_date IS NOT NULL
),
w AS (
    SELECT merchant_id, brand, subcategory, supply_type,
           CAST(ceil(day_n / 7.0) AS INTEGER) AS week,
           count(*)                         AS days_in_week,
           sum(product_page_views)          AS page_views,
           sum(visitors)                    AS visitors,
           sum(orders)                      AS orders,
           sum(units)                       AS units,
           sum(gmv_rm)                      AS gmv_rm,
           sum(content_gmv_rm)              AS content_gmv_rm,
           sum(refunds_rm)                  AS refunds_rm,
           sum(cancelled_orders)            AS cancelled_orders,
           sum(shipped_orders)              AS shipped_orders,
           sum(shipped_on_time)             AS shipped_on_time,
           sum(live_minutes)                AS live_minutes,
           sum(short_videos_posted)         AS short_videos,
           max(active_creators)             AS peak_active_creators,
           sum(chats_received)              AS chats_received,
           sum(chats_answered_in_time)      AS chats_answered_in_time
    FROM d WHERE day_n BETWEEN 1 AND 30
    GROUP BY ALL
),
live_skus AS (   -- SKUs live by the last day of each week
    SELECT w.merchant_id, w.week,
           count(l.sku_id) FILTER (WHERE l.status = 'live')                                    AS live_skus,
           count(l.sku_id) FILTER (WHERE l.status = 'live' AND l.regulated)                   AS live_regulated_skus,
           count(l.sku_id) FILTER (WHERE l.status = 'live' AND l.regulated AND l.certificate_ref IS NOT NULL)
                                                                                                AS live_regulated_with_ref
    FROM w JOIN merchants m USING (merchant_id)
    LEFT JOIN listings l ON l.merchant_id = w.merchant_id
        AND l.listed_date <= m.shop_live_date + (LEAST(w.week * 7, 30) - 1) * INTERVAL 1 DAY
    GROUP BY ALL
)
SELECT w.*, s.live_skus, s.live_regulated_skus, s.live_regulated_with_ref,
       round(w.orders / nullif(w.visitors, 0), 4)                   AS conversion_rate,
       round(w.gmv_rm / nullif(w.orders, 0), 2)                     AS avg_order_value_rm,
       round(w.content_gmv_rm / nullif(w.gmv_rm, 0), 4)             AS content_share_of_gmv,
       round(w.refunds_rm / nullif(w.gmv_rm, 0), 4)                 AS refund_rate,
       round(w.cancelled_orders / nullif(w.orders, 0), 4)           AS cancellation_rate,
       round(w.shipped_on_time / nullif(w.shipped_orders, 0), 4)    AS on_time_ship_rate,
       round(w.chats_answered_in_time / nullif(w.chats_received, 0), 4) AS chat_response_rate,
       round(w.gmv_rm / w.days_in_week, 2)                          AS gmv_per_day_rm,
       -- growth of GMV per day, so the two-day week 5 compares fairly with the full weeks
       round((w.gmv_rm / w.days_in_week)
             / nullif(lag(w.gmv_rm / w.days_in_week) OVER (PARTITION BY w.merchant_id ORDER BY w.week), 0) - 1, 4)
                                                                    AS gmv_per_day_wow_growth
FROM w JOIN live_skus s USING (merchant_id, week)
ORDER BY w.merchant_id, w.week;

-- 2. Milestones of the first 30 days per merchant.
CREATE OR REPLACE VIEW coldstart_milestones AS
WITH first_order AS (
    SELECT s.merchant_id, min(s.day) AS first_order_day
    FROM daily_shop s WHERE s.orders > 0 GROUP BY 1
),
first_live AS (
    SELECT merchant_id, min(day) AS first_live_day FROM daily_shop WHERE live_minutes > 0 GROUP BY 1
)
SELECT m.merchant_id, m.brand, m.onboard_date, m.shop_live_date,
       date_diff('day', m.onboard_date, m.shop_live_date)          AS days_onboard_to_live,
       date_diff('day', m.shop_live_date, f.first_order_day) + 1   AS first_order_on_day,
       date_diff('day', m.shop_live_date, l.first_live_day) + 1    AS first_live_stream_on_day
FROM merchants m
LEFT JOIN first_order f USING (merchant_id)
LEFT JOIN first_live l USING (merchant_id);

-- 3. Flags: each weekly number compared with the team's own thresholds.
CREATE OR REPLACE VIEW coldstart_flags AS
WITH long AS (
    UNPIVOT (SELECT merchant_id, brand, week, conversion_rate, refund_rate, cancellation_rate,
                    on_time_ship_rate, chat_response_rate, content_share_of_gmv FROM coldstart_weekly)
    ON conversion_rate, refund_rate, cancellation_rate, on_time_ship_rate, chat_response_rate, content_share_of_gmv
    INTO NAME metric VALUE value
)
SELECT l.merchant_id, l.brand, l.week, l.metric, l.value, t.comparison, t.value AS threshold, t.note
FROM long l JOIN thresholds t USING (metric)
WHERE (t.comparison = 'min' AND l.value < t.value)
   OR (t.comparison = 'max' AND l.value > t.value)
ORDER BY l.merchant_id, l.week, l.metric;

-- 4. Onboarding milestones that are late or due within 3 days (the date reminder).
CREATE OR REPLACE VIEW milestone_reminders AS
SELECT merchant_id, milestone, due_date, done_date,
       CASE WHEN done_date IS NOT NULL THEN 'done'
            WHEN due_date < current_date THEN 'overdue'
            WHEN due_date <= current_date + INTERVAL 3 DAY THEN 'due within 3 days'
            ELSE 'scheduled' END AS reminder
FROM milestones
ORDER BY CASE WHEN done_date IS NULL THEN 0 ELSE 1 END, due_date;
