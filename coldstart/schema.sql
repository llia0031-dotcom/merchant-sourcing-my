-- First-30-days tracking for a newly onboarded merchant: table structure (DuckDB; plain SQL, ports to other engines).
-- One row per merchant, per SKU, per merchant-day and per onboarding milestone. Field names follow the numbers a
-- seller dashboard usually exports; map them to the real export once one is available.

CREATE TABLE IF NOT EXISTS merchants (
    merchant_id      VARCHAR PRIMARY KEY,
    brand            VARCHAR NOT NULL,
    subcategory      VARCHAR NOT NULL,      -- e.g. 'Charging & accessories'
    supply_type      VARCHAR NOT NULL,      -- 'local' | 'cross-border'
    onboard_date     DATE    NOT NULL,      -- account approved
    shop_live_date   DATE                   -- first SKU live; day 1 of the 30 days
);

CREATE TABLE IF NOT EXISTS listings (
    merchant_id      VARCHAR NOT NULL,
    sku_id           VARCHAR NOT NULL,
    listed_date      DATE    NOT NULL,
    price_rm         DECIMAL(10, 2) NOT NULL,
    regulated        BOOLEAN NOT NULL,      -- needs an Energy Commission CoA or MCMC certification (see onboarding/)
    certificate_ref  VARCHAR,               -- CoA or certificate number given by the merchant; NULL if not yet given
    status           VARCHAR NOT NULL,      -- 'live' | 'in review' | 'rejected' | 'delisted'
    PRIMARY KEY (merchant_id, sku_id)
);

CREATE TABLE IF NOT EXISTS daily_shop (
    merchant_id              VARCHAR NOT NULL,
    day                      DATE    NOT NULL,
    product_page_views       INTEGER NOT NULL DEFAULT 0,
    visitors                 INTEGER NOT NULL DEFAULT 0,
    orders                   INTEGER NOT NULL DEFAULT 0,
    units                    INTEGER NOT NULL DEFAULT 0,
    gmv_rm                   DECIMAL(12, 2) NOT NULL DEFAULT 0,
    content_gmv_rm           DECIMAL(12, 2) NOT NULL DEFAULT 0,   -- from live streams, short videos and creators
    refunds_rm               DECIMAL(12, 2) NOT NULL DEFAULT 0,
    cancelled_orders         INTEGER NOT NULL DEFAULT 0,
    shipped_orders           INTEGER NOT NULL DEFAULT 0,
    shipped_on_time          INTEGER NOT NULL DEFAULT 0,          -- shipped within the promised handling time
    live_minutes             INTEGER NOT NULL DEFAULT 0,
    short_videos_posted      INTEGER NOT NULL DEFAULT 0,
    active_creators          INTEGER NOT NULL DEFAULT 0,          -- creators who posted or streamed the shop's products
    chats_received           INTEGER NOT NULL DEFAULT 0,
    chats_answered_in_time   INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (merchant_id, day)
);

CREATE TABLE IF NOT EXISTS milestones (
    merchant_id      VARCHAR NOT NULL,
    milestone        VARCHAR NOT NULL,      -- names as in onboarding/tracker_template.csv
    due_date         DATE    NOT NULL,
    done_date        DATE,
    PRIMARY KEY (merchant_id, milestone)
);

-- Thresholds a team sets for itself; the values in example data are examples, not platform rules.
CREATE TABLE IF NOT EXISTS thresholds (
    metric           VARCHAR PRIMARY KEY,
    comparison       VARCHAR NOT NULL,      -- 'min' (flag when below) | 'max' (flag when above)
    value            DOUBLE  NOT NULL,
    note             VARCHAR
);
