"""Runs the three checks of pool/calibration.sql on the pool's scores and a CSV of results.

    python pool/calibrate.py outcomes.csv

outcomes.csv columns: brand, contacted_on, onboarded (true/false), week4_gmv_per_day_rm (empty if not onboarded).
No results ship with this pack: no merchant has been contacted.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]


def run_checks(con: duckdb.DuckDBPyConnection) -> dict[str, list[tuple]]:
    """Runs every statement of calibration.sql; `scores` and `outcomes` must exist (CREATE ... IF NOT EXISTS is kept)."""
    out = {}
    for part in (ROOT / "pool" / "calibration.sql").read_text("utf-8").split(";"):
        body = "\n".join(ln for ln in part.splitlines() if not ln.strip().startswith("--")).strip()
        if not body:
            continue
        if body.upper().startswith("CREATE"):
            con.execute(body)
            continue
        m = re.search(r"--\s*(C\d)\.", part)
        out[m.group(1) if m else f"Q{len(out) + 1}"] = con.execute(body).fetchall()
    return out


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__)
        return 2
    con = duckdb.connect()
    con.execute("CREATE TABLE scores AS SELECT * FROM read_csv_auto(?, header=true)", [str(ROOT / "pool" / "scores.csv")])
    con.execute("CREATE TABLE outcomes AS SELECT * FROM read_csv_auto(?, header=true)", [sys.argv[1]])
    for name, rows in run_checks(con).items():
        print(name)
        for r in rows:
            print("   ", r)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
