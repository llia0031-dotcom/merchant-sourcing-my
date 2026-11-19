"""Saves every page in sources/manifests/ again and reports whether its text changed since it was first read.

    python tools/refetch.py [--group official]

The page texts are not part of this repository (they belong to their publishers). This script rebuilds
sources/snapshots/ from the listed URLs with the same polite fetcher (robots.txt first, 8 seconds per site), then
compares each new text's SHA-256 with the one recorded at first reading. After it, tools/check_all.py can re-check
every quote. Pages that changed are listed; their quotes may no longer be found, which is expected for live pages.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import save_page as fetch  # noqa: E402


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--group")
    a = ap.parse_args()
    same = changed = failed = 0
    for m in sorted((ROOT / "sources" / "manifests").glob("*.csv")):
        if a.group and m.stem != a.group:
            continue
        with m.open(encoding="utf-8", newline="") as f:
            rows = list(csv.DictReader(f))
        for r in rows:
            if not r.get("sha256") or r.get("status") == "browser-rendered":
                continue  # never saved, or read in a browser: cannot be refetched the same way
            out = ROOT / "sources" / "snapshots" / r["group"] / f"{r['id']}.txt"
            if out.exists():
                h = hashlib.sha256(out.read_text("utf-8").encode("utf-8")).hexdigest()
                same += h == r["sha256"]
                changed += h != r["sha256"]
                continue
            # fetch into a scratch group so the published manifest keeps the first-reading record
            row = fetch.fetch_one(r["id"], r["url"], "_refetch", r["publisher"], r["kind"], force=True)
            tmp = ROOT / "sources" / "snapshots" / "_refetch" / f"{r['id']}.txt"
            if not tmp.exists():
                failed += 1
                continue
            out.parent.mkdir(parents=True, exist_ok=True)
            tmp.replace(out)
            if row.get("sha256") == r["sha256"]:
                same += 1
            else:
                changed += 1
                print(f"changed since first reading: {r['id']} ({r['url']})")
    print(f"same text: {same}; changed: {changed}; could not fetch: {failed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
