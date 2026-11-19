"""Writes a small, clearly synthetic example for the first-30-days SQL, so the views can be run and tested.

    python coldstart/make_example.py      # -> coldstart/example/*.csv

The two merchants, their SKUs and every number are invented (fixed random seed). They describe no real brand,
shop or result, and the thresholds are examples a team would replace with its own.
"""
from __future__ import annotations

import csv
import random
from datetime import date, timedelta
from pathlib import Path

OUT = Path(__file__).resolve().parent / "example"


def main() -> None:
    rnd = random.Random(20261119)
    OUT.mkdir(exist_ok=True)
    merchants = [
        ("EX-001", "Example Brand A (synthetic)", "Charging & accessories", "local", date(2026, 1, 5), date(2026, 1, 12)),
        ("EX-002", "Example Brand B (synthetic)", "Audio", "cross-border", date(2026, 1, 7), date(2026, 1, 16)),
    ]
    with (OUT / "merchants.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["merchant_id", "brand", "subcategory", "supply_type", "onboard_date", "shop_live_date"])
        for m in merchants:
            w.writerow([m[0], m[1], m[2], m[3], m[4].isoformat(), m[5].isoformat()])

    with (OUT / "listings.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["merchant_id", "sku_id", "listed_date", "price_rm", "regulated", "certificate_ref", "status"])
        for mid, _, _, _, _, live in merchants:
            for i in range(12):
                listed = live + timedelta(days=rnd.choice([0, 0, 0, 3, 6, 10, 15]))
                regulated = i % 3 == 0
                ref = f"EXAMPLE-REF-{mid}-{i:02d}" if regulated and rnd.random() < 0.75 else ""
                status = "live" if rnd.random() < 0.9 else "in review"
                w.writerow([mid, f"{mid}-SKU{i:02d}", listed.isoformat(), f"{rnd.choice([19.9, 39.9, 59.0, 89.0, 129.0]):.2f}",
                            str(regulated).lower(), ref, status])

    with (OUT / "daily_shop.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["merchant_id", "day", "product_page_views", "visitors", "orders", "units", "gmv_rm", "content_gmv_rm",
                    "refunds_rm", "cancelled_orders", "shipped_orders", "shipped_on_time", "live_minutes",
                    "short_videos_posted", "active_creators", "chats_received", "chats_answered_in_time"])
        for k, (mid, _, _, _, _, live) in enumerate(merchants):
            for d in range(30):
                growth = 1 + d * (0.08 if k == 0 else 0.04)
                visitors = int(rnd.randint(40, 70) * growth)
                views = int(visitors * rnd.uniform(1.6, 2.4))
                orders = 0 if d < 2 + k else max(0, int(visitors * rnd.uniform(0.01, 0.035)))
                units = orders + rnd.randint(0, orders // 3 + 1) if orders else 0
                gmv = round(units * rnd.uniform(35, 75), 2)
                content = round(gmv * rnd.uniform(0.3, 0.7), 2)
                refunds = round(gmv * rnd.choice([0, 0, 0.02, 0.05]), 2)
                cancelled = rnd.choice([0, 0, 0, 1]) if orders else 0
                shipped = max(0, orders - cancelled)
                on_time = shipped - (1 if shipped and rnd.random() < (0.1 if k == 0 else 0.35) else 0)
                live_min = rnd.choice([0, 0, 60, 90]) if d >= 5 else 0
                chats = rnd.randint(2, 12)
                w.writerow([mid, (live + timedelta(days=d)).isoformat(), views, visitors, orders, units, f"{gmv:.2f}",
                            f"{content:.2f}", f"{refunds:.2f}", cancelled, shipped, on_time, live_min,
                            rnd.randint(0, 3), rnd.randint(0, 2 + d // 5), chats, chats - rnd.choice([0, 0, 1, 2])])

    with (OUT / "milestones.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["merchant_id", "milestone", "due_date", "done_date"])
        for mid, _, _, _, onboard, live in merchants:
            w.writerow([mid, "Account approved", onboard.isoformat(), onboard.isoformat()])
            w.writerow([mid, "First 10 SKUs live", (onboard + timedelta(days=7)).isoformat(), live.isoformat()])
            w.writerow([mid, "Certificate numbers for regulated SKUs", (onboard + timedelta(days=10)).isoformat(), ""])
            w.writerow([mid, "First live stream", (live + timedelta(days=7)).isoformat(), ""])

    with (OUT / "thresholds.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["metric", "comparison", "value", "note"])
        w.writerow(["on_time_ship_rate", "min", 0.95, "example threshold"])
        w.writerow(["cancellation_rate", "max", 0.05, "example threshold"])
        w.writerow(["refund_rate", "max", 0.05, "example threshold"])
        w.writerow(["chat_response_rate", "min", 0.80, "example threshold"])
        w.writerow(["conversion_rate", "min", 0.01, "example threshold"])
    print(f"wrote synthetic example to {OUT}")


if __name__ == "__main__":
    main()
