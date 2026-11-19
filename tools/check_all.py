"""Checks every claim in the published documents against the exact words of its sources, with evidence-check.

    python tools/check_all.py        # exit 0 when every claim is supported and no number is left unchecked

1. Documents with tagged lines: a line that ends with a tag such as `[I07]` (insight, checklist) or carries a hidden
   tag `<!-- c:S03 -->` (READMEs) is one claim. Its text is the line as published (tags, link targets and Markdown
   removed) and its evidence is the list under that tag in the document's evidence file. A line with a digit and no
   tag fails the check, so no number can be published without a source (headings, code blocks and the source list
   are exempt).
2. pool/claims.json (every value of every candidate row and every demand signal, written by pool/build.py) is
   checked as it is.

Sources are the saved page texts in sources/snapshots/ (not redistributed; tools/refetch.py rebuilds them) and the
result files of this repository. The checker is evidence-check's check_evidence.py (MIT), copied to tools/vendor/.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools" / "vendor"))
import check_evidence as ce  # noqa: E402

TAGGED = [  # document, evidence file
    ("insight/INSIGHTS.md", "insight/evidence.json"),
    ("insight/INSIGHTS.zh-CN.md", "insight/evidence.json"),
    ("insight/DEEP_DIVE_CHARGING.md", "insight/evidence.json"),
    ("insight/DEEP_DIVE_CHARGING.zh-CN.md", "insight/evidence.json"),
    ("onboarding/CHECKLIST.md", "onboarding/evidence.json"),
    ("README.md", "results/readme_evidence.json"),
    ("README.zh-CN.md", "results/readme_evidence.json"),
]
CLAIM_FILES = ["pool/claims.json"]
TAG = re.compile(r"\s*(?:\[([A-Z]\d{2,3})\]|<!--\s*c:([A-Z]\d{2,3})\s*-->)")


def clean(line: str) -> str:
    t = TAG.sub("", line)
    t = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", t)     # [text](link) -> text
    t = re.sub(r"[*_`>#]", "", t)
    t = t.strip().strip("|").strip()
    t = re.sub(r"^\s*[-•]\s*|^\d+\.\s+", "", t)
    return re.sub(r"\s*\|\s*", " | ", t).strip()


def tagged_claims(doc: Path, evidence: dict) -> tuple[list[dict], list[str]]:
    claims, problems, in_code, in_sources = [], [], False, False
    for n, line in enumerate(doc.read_text("utf-8").splitlines(), 1):
        if line.strip().startswith("```"):
            in_code = not in_code
            continue
        if in_code:
            continue
        if line.startswith("#"):
            in_sources = bool(re.match(r"#+\s*(Sources|出处|Source list|Change log)", line, re.I))
            continue
        tags = [a or b for a, b in TAG.findall(line)]
        if not tags:
            body = re.sub(r"\]\([^)]+\)|<!--.*?-->|https?://\S+", "", line)
            if doc.name.startswith("README"):
                # numbers that describe the pack itself, not facts from sources
                body = re.sub(r"^\s*\d+\.\s|Python 3\.\d+|SHA-256|(first |头 ?)30 ?(days|天)|30 days|first-30-days|\b8 (seconds|秒)|week-1|week 4|第 4 周", "", body)
            if not in_sources and re.search(r"\d", body) and not re.fullmatch(r"\s*\|?[-:| ]+\|?\s*", line):
                problems.append(f"{doc.relative_to(ROOT).as_posix()}:{n}: number without a source tag: {line.strip()[:90]}")
            continue
        for t in tags:
            if t not in evidence:
                problems.append(f"{doc.relative_to(ROOT).as_posix()}:{n}: tag {t} has no evidence entry")
                continue
            claims.append({"id": f"{doc.name}:{n}:{t}", "text": clean(line), "evidence": evidence[t]})
    return claims, problems


def main() -> int:
    roots = [ROOT / "sources" / "snapshots", ROOT / "results", ROOT / "pool", ROOT / "onboarding"]
    sources = ce.load_sources([str(r) for r in roots if r.exists()])
    all_claims, problems = [], []
    for doc, ev in TAGGED:
        d, e = ROOT / doc, ROOT / ev
        if not d.exists():
            continue
        evidence = json.loads(e.read_text("utf-8")) if e.exists() else {}
        c, p = tagged_claims(d, evidence)
        all_claims += c
        problems += p
    for f in CLAIM_FILES:
        p = ROOT / f
        if p.exists():
            all_claims += json.loads(p.read_text("utf-8"))["claims"]
    rep = ce.check(all_claims, sources)
    bad = [r for r in rep["claims"] if r["status"] != "supported"]
    lines = ["# Claim check", "",
             f"Every tagged line of the insight, the checklist and the READMEs, every field of the candidate rows and "
             f"every demand signal, checked with evidence-check {ce.__version__} against the saved page texts and the "
             f"result files.", "",
             f"- claims checked: {rep['summary']['claims']}",
             f"- supported: {rep['summary']['supported']}",
             f"- not supported: {rep['summary']['not_supported']}",
             f"- lines with a number but no source tag: {len(problems)}"]
    rounded = [r for r in rep["claims"] if r.get("rounded")]
    if rounded:
        lines += ["", "Numbers matched after rounding (read them):", ""]
        lines += [f"- {r['id']}: " + ", ".join(f"{x['claim']} for {x['quote']}" for x in r["rounded"]) for r in rounded]
    (ROOT / "results" / "CLAIM_CHECK.md").write_text("\n".join(lines) + "\n", "utf-8")
    print("\n".join(lines))
    for r in bad:
        print(f"NOT SUPPORTED {r['id']}: {r['status']} {r.get('missing_numbers')}\n   {r['text'][:140]}")
    for p in problems:
        print("UNTAGGED " + p)
    return 0 if not bad and not problems else 1


if __name__ == "__main__":
    raise SystemExit(main())
