"""Builds the candidate pool from pool/candidates.json: checks every quote, scores with the frozen rules, writes the tables.

    python pool/build.py

1. Every value in pool/candidates.json carries evidence ({source, quote}). Each quote must be found word for word in
   the saved page (evidence-check, tools/vendor/check_evidence.py), every number in the value must be in its quotes,
   and the quote must contain the words that make it evidence for that value (a Shopee store needs "shopee", a
   certification statement needs SIRIM, MCMC or Energy Commission, ...). Any failure stops the build.
2. Scores follow pool/SCORING.md v2; the build stops if that file is not the frozen version (SHA-256 below).
   Demand signals from public third-party estimates come from pool/demand_sources.csv: a vendor-share source
   counts on a line that names the brand and gives a share; a shop ranking counts on a row that carries the
   brand's name; a trending-products source counts when a product word of the sub-category is in a product row.
   A content-commerce shop counts when the merchant's own page, its own release, or a news report of its own
   announcement or of the platform's announcement names or links it.
3. Writes pool/candidates.csv, pool/scores.csv, pool/PRIORITY.md (the first rows with reasons and links),
   pool/claims.json (every checked value, re-checkable with evidence-check), pool/merchant_pool.xlsx, pool/pool.duckdb.
"""
from __future__ import annotations

import csv
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools" / "vendor"))
import check_evidence as ce  # noqa: E402

FROZEN = "9499691aa3dc6db1874e2ea3d522631ff9a2009d61b96d261c7441b677b0f993"
NF = "not found in public sources"
WEIGHTS = {"demand": 0.30, "gap": 0.30, "readiness": 0.25, "content": 0.15}
PRESENCE = ["Malaysian brand", "global brand with a Malaysian company", "sold through a named Malaysian distributor",
            "Malaysian distributor or retailer", "sold to Malaysia from abroad only", NF]
LOCAL = {"Malaysian brand", "global brand with a Malaysian company", "sold through a named Malaysian distributor",
         "Malaysian distributor or retailer"}
GUARDS = {
    "Shopee": [r"shopee"], "Lazada": [r"lazada", r"lazmall"], "Zalora": [r"zalora"], "PG Mall": [r"pgmall|pg mall"],
    "own e-store": [r"store|shop|buy|cart|order|purchase|website|kedai|beli"],
    "content shop": [r"tiktok\s*shop|shop\.tiktok|tiktokshop|tik\s*tik\s*shop|(flagship|official) store.{0,40}tiktok|e-?commerce partners?.{0,40}tiktok"],
    "short video": [r"tiktok"], "YouTube": [r"youtube|youtu\.be"], "Instagram": [r"instagram"],
    "Facebook": [r"facebook|fb\.com"], "X": [r"twitter\.com|x\.com"],
    "Malaysia-specific": [r"malaysia|_my\b|\.my\b|\bmy\b|/my|my/|my\b"], "global only": [r"."],
    "Malaysian brand": [r"malaysia"], "global brand with a Malaysian company": [r"sdn\.?\s*bhd|malaysia"],
    "sold through a named Malaysian distributor": [r"distribut|authori[sz]ed|dealer|pengedar|sdn\.?\s*bhd"],
    "Malaysian distributor or retailer": [r"sdn\.?\s*bhd|berhad|malaysia|distribut|retail|store|outlet|cawangan"],
    "sold to Malaysia from abroad only": [r"ship|deliver|overseas|china|abroad"],
    "certification stated": [r"sirim|mcmc|suruhanjaya tenaga|energy commission|\bst\b|certif|pensijilan|kelulusan"],
    "public register entry found": [r"."],
    "contact": [r"contact|enquir|inquir|@|hubungi|partner|business|sales|career"],
    "filing-or-award": [r"."], "retail-network": [r"store|outlet|branch|dealer|partner|reseller|cawangan|kedai|showroom"],
}
PRODUCT_WORDS = {
    "Phones & tablets": [r"smartphone", r"telefon pintar", r"\bphone\b(?! ?(holder|case|stand|charger|cable))", r"\btablet\b(?! ?stand)"],
    "Charging & phone accessories": [r"power ?bank", r"charger", r"charging", r"cable", r"adapter", r"phone case", r"phone holder"],
    "Audio": [r"earbud", r"headphone", r"headset", r"speaker", r"\btws\b", r"soundbar"],
    "Wearables": [r"smart ?watch", r"fitness tracker", r"smart ring"],
    "Cameras & drones": [r"camera", r"dash ?cam", r"\bdrone", r"action cam", r"gimbal"],
    "Smart home & networking": [r"router", r"wi-?fi", r"mesh", r"cctv", r"ip camera", r"smart plug", r"security camera"],
    "Computer & gaming accessories": [r"keyboard", r"\bmouse\b", r"gaming", r"monitor", r"controller"],
    "Home appliances": [r"blender", r"\bfan\b", r"rice cooker", r"air fryer", r"vacuum", r"kettle", r"\biron\b"],
    "Multi-category retail": [],   # retailers: demand comes from their own store network, not product words
}


class BuildError(Exception):
    pass


def guard_ok(key: str, quote: str) -> bool:
    pats = GUARDS.get(key)
    return True if pats is None else any(re.search(p, quote, re.I) for p in pats)


class Evidence:
    def __init__(self, roots=None):
        roots = roots or [ROOT / "sources" / "snapshots"]
        self.sources = ce.load_sources([str(r) for r in roots])
        stems = [Path(s).stem for s in self.sources]
        dup = sorted({s for s in stems if stems.count(s) > 1})
        if dup:
            raise BuildError(f"page ids used in two groups: {dup}")
        self.claims: list[dict] = []

    def group_of(self, sid: str) -> str:
        for k in self.sources:
            if Path(k).stem == sid:
                return Path(k).parent.as_posix()
        return ""

    def need(self, who: str, field: str, text: str, evidence: list[dict], guard: str | None = None) -> list[dict]:
        if not evidence:
            raise BuildError(f"{who}: {field} = {text!r} has no evidence")
        # 1. every quote must be in its page, and the quotes together must hold every number of the value
        r = ce.check_claim({"id": "x", "text": text, "evidence": evidence}, self.sources)
        if r["status"] != "supported":
            raise BuildError(f"{who}: {field} = {text!r}: {r['status']} (missing numbers {r['missing_numbers']})")
        ok = evidence
        # 2. the quotes must contain the words that make them evidence for this value; keep only the quotes that do,
        #    as long as they still hold the numbers (a fact split over two lines may need both)
        if guard:
            fitting = [e for e in evidence if guard_ok(guard, e["quote"])]
            if fitting and ce.check_claim({"id": "x", "text": text, "evidence": fitting}, self.sources)["status"] == "supported":
                ok = fitting
            elif not guard_ok(guard, " ".join(e["quote"] for e in evidence)):
                raise BuildError(f"{who}: {field} = {text!r}: no quote has the words that make it evidence ({guard})")
        self.claims.append({"id": f"{who}|{field}", "text": f"{field}: {text}", "evidence": ok})
        return ok


def check_frozen() -> None:
    h = hashlib.sha256((ROOT / "pool" / "SCORING.md").read_bytes()).hexdigest()
    if h != FROZEN:
        raise BuildError(f"pool/SCORING.md changed (sha256 {h}); the frozen rules are {FROZEN}")


def read_csv(p: Path) -> list[dict]:
    with p.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def manifests() -> dict[str, dict]:
    out = {}
    for m in sorted((ROOT / "sources" / "manifests").glob("*.csv")):
        for r in read_csv(m):
            out[r["id"]] = r
    return out


def snapshot(sid: str) -> str:
    hits = list((ROOT / "sources" / "snapshots").rglob(f"{sid}.txt"))
    if len(hits) != 1:
        raise BuildError(f"snapshot {sid}: {len(hits)} files")
    return hits[0].read_text("utf-8")


def window(line: str, a: int, b: int, width: int = 110) -> str:
    if len(line) <= 2 * width + (b - a):
        return line.strip()
    s = max(0, a - width)
    e = min(len(line), b + width)
    s = line.rfind(" ", 0, s) + 1 if s > 0 else 0
    sp = line.find(" ", e)
    return line[s: sp if sp != -1 else len(line)].strip()


def name_pattern(c: dict) -> re.Pattern:
    names = [c["brand"]] + c.get("aliases", [])
    return re.compile(r"(?<![A-Za-z0-9])(" + "|".join(re.escape(n) for n in names) + r")(?![A-Za-z0-9])", re.I)


def third_party(c: dict, demand_sources: list[dict]) -> tuple[int, list[dict], bool]:
    """(demand level from public estimates, evidence, a shop with the name is in a content-commerce top-shop ranking)."""
    best, ev, ranked = 0, [], False
    pat = name_pattern(c)
    for s in demand_sources:
        kind = s["type"]
        if kind == "vendor-share" and s["subcategory"] not in ("", c["subcategory"]):
            continue
        for line in snapshot(s["source_id"]).splitlines():
            if len(line) > 400 or re.search(r"Select a category|^(Top|Compare) 100|^Links on this page|^link:", line):
                continue  # filter menus, headings and link lists, not ranking rows
            if kind == "vendor-share" and not re.search(r"%|per ?cent", line, re.I):
                continue  # a vendor-share source counts only on a line that gives a share
            if kind in ("vendor-share", "shop-ranking"):
                m = pat.search(line)
                if m:
                    if best < 3:
                        best, ev = 3, []
                    if not any(e["source"] == s["source_id"] for e in ev):
                        ev.append({"source": s["source_id"], "quote": window(line, m.start(), m.end()), "_kind": kind})
                    if kind == "shop-ranking" and s.get("content_commerce") == "yes":
                        ranked = True
            elif kind == "trending-products" and best < 2:
                for w in PRODUCT_WORDS.get(c["subcategory"], []):
                    m = re.search(w, line, re.I)
                    if m:
                        best, ev = 2, [{"source": s["source_id"], "quote": window(line, m.start(), m.end()), "_kind": kind}]
                        break
    return best, ev, ranked


def check_row(c: dict, E: Evidence) -> dict:
    """Checks every value of one candidate; returns the flat row."""
    who = c["brand"]
    p = c["presence"]
    if p["value"] not in PRESENCE:
        raise BuildError(f"{who}: presence {p['value']!r} not one of {PRESENCE}")
    if p["value"] != NF:
        E.need(who, "presence", p["value"], p["evidence"], p["value"])
        if p.get("entity"):
            E.need(who, "Malaysian company or distributor", p["entity"],
                   [e for e in p["evidence"] if p["entity"].lower() in e["quote"].lower()] or p["evidence"])
    if c.get("origin", {}).get("value"):
        o = c["origin"]
        E.need(who, "origin", o["value"], [e for e in o["evidence"] if o["value"].lower() in e["quote"].lower()])
    stores = c.get("stores", {}).get("value", [])
    labels = c.get("stores", {}).get("labels", {})
    for s in stores:
        E.need(who, "official store", labels.get(s, s), c["stores"]["evidence"], s)
    shown = [labels.get(s, s) for s in stores]
    content_shop = bool(c.get("content_shop", {}).get("value"))
    if content_shop:
        E.need(who, "content-commerce shop linked", "yes", c["content_shop"]["evidence"], "content shop")
    acc = c.get("accounts", {"short_video": False, "others": [], "scope": NF, "evidence": []})
    if acc.get("short_video"):
        E.need(who, "short-video account linked", "yes", acc["evidence"], "short video")
    for a in acc.get("others", []):
        E.need(who, "account linked", a, acc["evidence"], a)
    scope = acc.get("scope", NF)
    if scope != NF:
        E.need(who, "accounts scope", scope, acc["evidence"], scope)
    cert = c.get("certification", {"value": NF})
    if cert["value"] != NF:
        ev = E.need(who, "certification", cert.get("detail", cert["value"]), cert["evidence"], cert["value"])
        if cert["value"] == "public register entry found" and not all(E.group_of(e["source"]) in ("official", "registers") for e in ev):
            raise BuildError(f"{who}: a register entry must be quoted from an official register page")
    sw = c.get("sells_well")
    if sw:
        E.need(who, "sells well elsewhere", sw["value"], sw["evidence"], sw["level"])
    if c.get("contact"):
        E.need(who, "public contact route", c["contact"]["value"], c["contact"]["evidence"], "contact")
    if c.get("price"):
        E.need(who, "example price", c["price"]["value"], c["price"]["evidence"])
    return {
        "brand": who, "kind": c["kind"], "subcategory": c["subcategory"], "presence": p["value"],
        "malaysian_company_or_distributor": p.get("entity", ""),
        "supply_type": "local" if p["value"] in LOCAL else ("cross-border" if p["value"] == "sold to Malaysia from abroad only" else NF),
        "official_stores_elsewhere": "; ".join(shown) or NF,
        "content_commerce_shop_linked": "yes" if content_shop else NF,
        "short_video_account_linked": "yes" if acc.get("short_video") else NF,
        "other_accounts_linked": "; ".join(acc.get("others", [])) or NF,
        "accounts_scope": scope,
        "certification_evidence": cert.get("detail", cert["value"]) if cert["value"] != NF else NF,
        "sells_well_elsewhere": sw["value"] if sw else NF,
        "public_contact_route": c["contact"]["value"] if c.get("contact") else NF,
        "example_price": c["price"]["value"] if c.get("price") else "",
        "_sells_level": sw["level"] if sw else "",
    }


def score(row: dict, c: dict, demand_sources: list[dict]) -> dict:
    tp_level, tp_ev, ranked = third_party(c, demand_sources)
    stores = row["official_stores_elsewhere"] != NF
    shop = row["content_commerce_shop_linked"] == "yes"
    lv = row["_sells_level"]
    demand = max(3 if lv == "filing-or-award" else 2 if lv == "retail-network" else 0, tp_level, 1 if (stores or shop) else 0)
    gap = 1 if ranked else 3 if (stores and not shop) else 2 if shop else 0
    local = row["supply_type"] == "local"
    readiness = 3 if local and row["certification_evidence"] != NF else 2 if local else 1 if row["supply_type"] == "cross-border" else 0
    sv, others, scope = row["short_video_account_linked"] == "yes", row["other_accounts_linked"] != NF, row["accounts_scope"]
    content = (3 if sv and others else 2 if (sv or others) else 0) if scope == "Malaysia-specific" else \
              (1 if scope == "global only" and (sv or others) else 0)
    total = round(100 * (WEIGHTS["demand"] * demand + WEIGHTS["gap"] * gap + WEIGHTS["readiness"] * readiness
                         + WEIGHTS["content"] * content) / 3, 1)
    return {"brand": row["brand"], "kind": row["kind"], "subcategory": row["subcategory"], "supply_type": row["supply_type"],
            "demand": demand, "gap": gap, "readiness": readiness, "content": content, "total": total,
            "tier": "A" if total >= 70 else "B" if total >= 50 else "C",
            "segment": {3: "open a shop", 2: "activate", 1: "grow", 0: "check first"}[gap],
            "next_action": {3: "Share the category document list; confirm certificate numbers for the first SKUs",
                            2: "Ask which SKUs carry SIRIM / MCMC / Energy Commission approval, and who holds the certificates",
                            1: "Point to the cross-border seller route; check which SKUs are regulated in Malaysia",
                            0: "Find the Malaysian contact first"}[readiness],
            "public_contact_route": row["public_contact_route"],
            "_tp_ev": tp_ev, "_ranked": ranked}


def reasons(row: dict, s: dict) -> list[str]:
    out = []
    if row["sells_well_elsewhere"] != NF:
        out.append(f"Sells well elsewhere: {row['sells_well_elsewhere']}")
    def q(e):
        t = e["quote"]
        return f"“{t if len(t) <= 140 else t[:140].rsplit(' ', 1)[0] + ' …'}” ({e['source']})"
    named = [e for e in s["_tp_ev"] if e.get("_kind") in ("vendor-share", "shop-ranking")]
    typed = [e for e in s["_tp_ev"] if e.get("_kind") == "trending-products"]
    if named:
        out.append("Named in a public third-party estimate: " + "; ".join(q(e) for e in named[:2]))
    elif typed:
        out.append("Its product type is in a public best-seller list: " + "; ".join(q(e) for e in typed[:1]))
    if row["official_stores_elsewhere"] != NF:
        out.append(f"Official online stores on other channels: {row['official_stores_elsewhere']}")
    if s["gap"] == 3:
        out.append("No content-commerce shop found on its own pages or in the public top-shop rankings used here")
    elif s["gap"] == 2:
        out.append("Links a content-commerce shop; not in the public top-shop rankings used here")
    if row["malaysian_company_or_distributor"]:
        out.append(f"Malaysian company or distributor: {row['malaysian_company_or_distributor']}")
    if row["certification_evidence"] != NF:
        out.append(f"Certification evidence: {row['certification_evidence']}")
    return out


def write_xlsx(path: Path, sheets: dict[str, list[dict]], notes: list[str]) -> None:
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Font, PatternFill
    from openpyxl.utils import get_column_letter

    wb = Workbook()
    ws = wb.active
    ws.title = "README"
    for i, n in enumerate(notes, 1):
        ws.cell(row=i, column=1, value=n).alignment = Alignment(wrap_text=True, vertical="top")
    ws.column_dimensions["A"].width = 120
    for name, rows in sheets.items():
        ws = wb.create_sheet(name)
        if not rows:
            continue
        cols = [k for k in rows[0] if not k.startswith("_")]
        ws.append(cols)
        for cell in ws[1]:
            cell.font = Font(bold=True, color="FFFFFF")
            cell.fill = PatternFill("solid", fgColor="1F2937")
        for r in rows:
            ws.append([r.get(k, "") for k in cols])
        for i, k in enumerate(cols, 1):
            w = max([len(str(k))] + [min(len(str(r.get(k, ""))), 70) for r in rows]) + 2
            ws.column_dimensions[get_column_letter(i)].width = min(w, 72)
        ws.freeze_panes = "B2"
        ws.auto_filter.ref = ws.dimensions
    wb.save(path)


def main() -> int:
    check_frozen()
    cands = json.loads((ROOT / "pool" / "candidates.json").read_text("utf-8"))["candidates"]
    demand_sources = read_csv(ROOT / "pool" / "demand_sources.csv")
    E = Evidence()
    errors, rows, scored = [], [], []
    for c in cands:
        try:
            row = check_row(c, E)
        except BuildError as e:
            errors.append(str(e))
            continue
        rows.append(row)
        scored.append(score(row, c, demand_sources))
    if errors:
        print("BUILD STOPPED: values whose quotes do not pass")
        print("\n".join("  " + e for e in errors))
        return 1
    for s in scored:
        for e in s["_tp_ev"]:
            label = "product type in a public best-seller list" if e["_kind"] == "trending-products" else "named in a public estimate"
            E.need(s["brand"], label, e["quote"], [{"source": e["source"], "quote": e["quote"]}])
    order = lambda s: (-s["total"], -s["readiness"], -s["demand"], 0 if s["supply_type"] == "local" else 1, s["brand"].lower())
    scored.sort(key=order)
    byname = {r["brand"]: r for r in rows}
    for i, s in enumerate(scored, 1):
        s["rank"] = i
        s["why"] = " · ".join(reasons(byname[s["brand"]], s))
    cols = ["rank", "brand", "kind", "subcategory", "supply_type", "demand", "gap", "readiness", "content", "total", "tier",
            "segment", "next_action", "public_contact_route", "why"]
    with (ROOT / "pool" / "scores.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows({k: s[k] for k in cols} for s in scored)
    ccols = [k for k in rows[0] if not k.startswith("_")]
    with (ROOT / "pool" / "candidates.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=ccols)
        w.writeheader()
        w.writerows({k: r[k] for k in ccols} for r in sorted(rows, key=lambda r: r["brand"].lower()))
    (ROOT / "pool" / "claims.json").write_text(json.dumps({"claims": E.claims}, ensure_ascii=False, indent=1), "utf-8")

    man = manifests()
    used = sorted({e["source"] for cl in E.claims for e in cl["evidence"]})
    src_rows = [{"id": i, "publisher": man[i]["publisher"], "url": man[i].get("final_url") or man[i]["url"],
                 "read_on": man[i]["retrieved_at"][:10], "sha256": man[i]["sha256"]} for i in used]
    write_priority(scored, byname, man)

    import duckdb
    db = ROOT / "pool" / "pool.duckdb"
    if db.exists():
        db.unlink()
    con = duckdb.connect(str(db))
    con.execute("CREATE TABLE candidates AS SELECT * FROM read_csv_auto(?, header=true, all_varchar=true)",
                [str(ROOT / "pool" / "candidates.csv")])
    con.execute("CREATE TABLE scores AS SELECT * FROM read_csv_auto(?, header=true)", [str(ROOT / "pool" / "scores.csv")])
    con.close()
    notes = ["Candidate pool: Malaysian online consumer electronics. Public sources only; no merchant has been contacted.",
             "Sheet 'priority': order by the frozen rules in pool/SCORING.md (demand 30%, content-commerce gap 30%, "
             "qualification readiness 25%, content capability 15%; each 0-3), with the reasons and a public contact route.",
             "Sheet 'candidates': every filled field is backed by a verbatim quote from a saved public page (pool/claims.json). "
             "'not found in public sources' means only that; it is not a judgement of the merchant.",
             "Sheet 'sources': every page quoted, with the date it was read. Third-party sales figures are estimates by the named source."]
    priority = [{k: s[k] for k in cols} for s in scored]   # rank first, the same columns as scores.csv
    write_xlsx(ROOT / "pool" / "merchant_pool.xlsx", {"priority": priority, "candidates": rows, "sources": src_rows}, notes)
    tiers = {t: sum(s["tier"] == t for s in scored) for t in "ABC"}
    print(f"built {len(rows)} candidates, {len(E.claims)} checked values; tiers {tiers}")
    for s in scored[:12]:
        print(f"{s['rank']:>2} {s['brand']:<22} {s['subcategory']:<30} {s['total']:>5} {s['tier']} {s['segment']}")
    return 0


def write_priority(scored: list[dict], byname: dict, man: dict) -> None:
    lines = ["# Who to contact first", "",
             "The first rows of the pool, ordered by the frozen rules in [SCORING.md](SCORING.md). Each reason is a "
             "checked quote from a public page (see [claims.json](claims.json)); the full table is "
             "[merchant_pool.xlsx](merchant_pool.xlsx). No merchant here has been contacted.", "",
             "Before the first call, check the platform's own seller list: \"no content-commerce shop found\" means none "
             "was found in the public pages read on 19 November 2026, not that none exists.", ""]
    for s in scored[:12]:
        r = byname[s["brand"]]
        lines += [f"## {s['rank']}. {s['brand']} ({s['subcategory']}, {s['supply_type']})", "",
                  f"Score {s['total']} (tier {s['tier']}, {s['segment']}): demand {s['demand']}, gap {s['gap']}, "
                  f"readiness {s['readiness']}, content {s['content']}.", ""]
        lines += [f"- {x}" for x in reasons(r, s)]
        lines += [f"- Next step: {s['next_action']}", f"- Public contact route: {s['public_contact_route']}", ""]
    (ROOT / "pool" / "PRIORITY.md").write_text("\n".join(lines), "utf-8")


if __name__ == "__main__":
    try:
        sys.exit(main())
    except BuildError as e:
        print(f"BUILD STOPPED: {e}")
        sys.exit(1)
