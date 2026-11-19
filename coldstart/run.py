"""Loads coldstart CSVs into DuckDB, creates the views and prints the weekly table.

    python coldstart/run.py                       # uses coldstart/example/ (synthetic)
    python coldstart/run.py --data path/to/csvs   # the same five CSV files exported from a real tracker
"""
from __future__ import annotations

import argparse
from pathlib import Path

import duckdb

HERE = Path(__file__).resolve().parent
TABLES = ["merchants", "listings", "daily_shop", "milestones", "thresholds"]


def connect(data: Path, db: str = ":memory:") -> duckdb.DuckDBPyConnection:
    con = duckdb.connect(db)
    con.execute((HERE / "schema.sql").read_text("utf-8"))
    for t in TABLES:
        f = data / f"{t}.csv"
        if f.exists():
            con.execute(f"INSERT INTO {t} SELECT * FROM read_csv_auto(?, header=true, nullstr='')", [str(f)])
    con.execute((HERE / "metrics.sql").read_text("utf-8"))
    return con


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", default=str(HERE / "example"))
    a = ap.parse_args()
    con = connect(Path(a.data))
    print(con.sql("""SELECT merchant_id, week, days_in_week, live_skus, visitors, orders, gmv_rm, conversion_rate,
                     avg_order_value_rm, content_share_of_gmv, on_time_ship_rate, gmv_per_day_wow_growth
                     FROM coldstart_weekly"""))
    print(con.sql("SELECT * FROM coldstart_milestones"))
    print(con.sql("SELECT merchant_id, week, metric, value, threshold FROM coldstart_flags"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
