"""Writes results/SUMMARY.md: the counts the READMEs quote, computed from the result files.

    python tools/summary.py
"""
from __future__ import annotations

import csv
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NF = "not found in public sources"


def rows(p: str) -> list[dict]:
    with (ROOT / p).open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def main() -> int:
    cands, scores = rows("pool/candidates.csv"), rows("pool/scores.csv")
    manifests = []
    for m in sorted((ROOT / "sources" / "manifests").glob("*.csv")):
        manifests += [r | {"_group": m.stem} for r in rows(m.relative_to(ROOT).as_posix()) if r.get("sha256")]
    by_group = Counter(r["_group"] for r in manifests)
    subs = Counter(r["subcategory"] for r in cands)
    tiers = Counter(r["tier"] for r in scores)
    segs = Counter(r["segment"] for r in scores)
    supply = Counter(r["supply_type"] for r in cands)
    cc = sum(r["content_commerce_shop_linked"] != NF for r in cands)
    sv = sum(r["short_video_account_linked"] == "yes" for r in cands)
    claims = json.loads((ROOT / "pool" / "claims.json").read_text("utf-8"))["claims"]
    quoted = {e["source"] for c in claims for e in c["evidence"]}
    for f in ("insight/evidence.json", "onboarding/evidence.json"):
        quoted |= {e["source"] for ev in json.loads((ROOT / f).read_text("utf-8")).values() for e in ev}
    quoted &= {r["id"] for r in manifests}   # saved public pages only, not the pack's own result files
    lines = ["# Summary of results", "", "Counts computed by `tools/summary.py` from the result files.", "",
             f"- public pages saved: {len(manifests)} ({by_group.get('official', 0)} official, "
             f"{by_group.get('market', 0)} market, {by_group.get('brands', 0)} brand pages, "
             f"{by_group.get('rankings', 0)} full ranking)",
             f"- pages quoted in the insight, the checklist and the pool: {len(quoted)}",
             f"- merchants in the candidate pool: {len(cands)} (" + ", ".join(f"{k} {v}" for k, v in sorted(Counter(r['kind'] for r in cands).items())) + ")",
             f"- local merchants (Malaysian company or distributor): {sum(r['supply_type'] == 'local' for r in cands)}",
             f"- sub-categories covered: {len(subs)}",
             f"- checked values (each with a quote found in the saved page): {len(claims)}",
             f"- merchants with a content-commerce shop found in public sources: {cc}",
             f"- merchants whose own pages link a Malaysian short-video account: {sv}",
             "- tiers: " + ", ".join(f"{t} {tiers.get(t, 0)}" for t in "ABC"),
             "- segments: " + ", ".join(f"{k} {v}" for k, v in sorted(segs.items())),
             "- Malaysian company or distributor found: " + str(supply.get("local", 0)) + "; not found in public sources: " + str(sum(v for k, v in supply.items() if k != "local"))]
    (ROOT / "results" / "SUMMARY.md").write_text("\n".join(lines) + "\n", "utf-8")
    print("\n".join(lines))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
