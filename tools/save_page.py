"""Saves public web pages as plain text so every claim can be checked against the exact words of its source.

    python tools/save_page.py URL --id st-regulated-list --group official --publisher "Energy Commission" --kind official
    python tools/save_page.py --list urls.csv          # columns: id,url,group,publisher,kind[,note]

Rules it keeps, so access stays at the level of a person reading pages:
- robots.txt is read first; a page it disallows for this reader, for any user agent (*), or for assistant agents
  (Claude-User, ClaudeBot, anthropic-ai) is not fetched (recorded as "robots-disallow").
- At most one request to the same host every 8 seconds (state kept in sources/.last_access.json).
- No sign-in, no cookies, no query loops, no crawling: only the URLs given.

Each page becomes sources/snapshots/<group>/<id>.txt (visible text only; HTML or PDF; links to online stores and
social accounts are listed after the text). A page that shows its text only with JavaScript can be read in a browser
without signing in and passed with --from-text FILE; robots.txt is checked the same way. The snapshot holds the page
text and nothing else, so dates in it are the page's own. URL, retrieval time, status and a SHA-256 of the text go
to sources/manifests/<group>.csv (one file per group, so separate runs never write the same file). Snapshots are not redistributed; the manifest and the quotes are.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
import sys
import time
import urllib.error
import urllib.request
import urllib.robotparser
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
SOURCES = ROOT / "sources"
STATE = SOURCES / ".last_access.json"
UA = "Mozilla/5.0 (compatible; public-source-reader/0.1)"
DELAY = 8.0
FIELDS = ["id", "url", "final_url", "title", "publisher", "kind", "group", "retrieved_at", "status", "robots",
          "content_type", "chars", "sha256", "note"]
_robots: dict[str, urllib.robotparser.RobotFileParser | None] = {}
LINK_RE = re.compile(r"(shopee\.|lazada\.|tiktok\.com|zalora\.|pgmall\.|amazon\.|facebook\.com|instagram\.com|"
                     r"youtube\.com|/store|/shop|where-to-buy|wheretobuy|official-store)", re.I)


def now_myt() -> str:
    # The machine clock is Malaysia time (UTC+08:00).
    return datetime.now().astimezone().strftime("%Y-%m-%d %H:%M %z")


def _wait(host: str) -> None:
    state = json.loads(STATE.read_text("utf-8")) if STATE.exists() else {}
    last = state.get(host, 0.0)
    gap = time.time() - last
    if gap < DELAY:
        time.sleep(DELAY - gap)
    state[host] = time.time()
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(state), "utf-8")


def _open(url: str, timeout: int = 40):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "en-MY,en;q=0.9"})
    return urllib.request.urlopen(req, timeout=timeout)


def robots_allows(url: str) -> str:
    p = urlparse(url)
    base = f"{p.scheme}://{p.netloc}"
    if base not in _robots:
        rp = urllib.robotparser.RobotFileParser()
        try:
            _wait(p.netloc)
            with _open(base + "/robots.txt", timeout=20) as r:
                body = r.read().decode("utf-8", "replace")
            rp.parse(body.splitlines())
            _robots[base] = rp
        except urllib.error.HTTPError as e:
            # 404/410: no robots.txt, everything allowed. 401/403: treat as disallowed (robotparser's own rule).
            _robots[base] = None if e.code in (404, 410) else False
        except Exception:
            _robots[base] = None
    rp = _robots[base]
    if rp is None:
        return "no-robots"
    if rp is False:
        return "robots-unreadable-disallow"
    # The pages are read for a person by an assistant, so the rules a site writes for assistant agents apply too.
    agents = [UA, "*", "Claude-User", "ClaudeBot", "anthropic-ai"]
    return "allowed" if all(rp.can_fetch(a, url) for a in agents) else "robots-disallow"


def html_to_text(raw: bytes, charset: str | None) -> tuple[str, str]:
    from bs4 import BeautifulSoup

    html = raw.decode(charset or "utf-8", "replace")
    soup = BeautifulSoup(html, "html.parser")
    title = (soup.title.get_text(" ", strip=True) if soup.title else "")[:200]
    for t in soup(["script", "style", "noscript", "svg", "iframe", "template"]):
        t.decompose()
    blocks = []
    for el in soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6", "p", "li", "td", "th", "caption", "dt", "dd",
                             "blockquote", "figcaption", "pre", "summary", "label"]):
        if el.find(["p", "li", "td", "h1", "h2", "h3", "h4", "table"]):
            continue  # a container; its children are taken on their own
        s = re.sub(r"\s+", " ", el.get_text(" ", strip=True)).strip()
        if s:
            blocks.append(s)
    if len(" ".join(blocks)) < 400:  # pages built from divs only
        body = soup.body or soup
        blocks = [re.sub(r"[ \t]+", " ", ln).strip() for ln in body.get_text("\n").splitlines()]
        blocks = [b for b in blocks if b]
    out, seen = [], set()
    for b in blocks:
        if b in seen and len(b) < 60:
            continue  # repeated menu items
        seen.add(b)
        out.append(b)
    # Store and social links are often icons with no text, so their addresses are listed after the text.
    links, seen_links = [], set()
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if not LINK_RE.search(href) or href in seen_links:
            continue
        seen_links.add(href)
        label = re.sub(r"\s+", " ", a.get_text(" ", strip=True) or a.get("aria-label", "") or a.get("title", "")).strip()
        links.append(f"link: {label[:80] or '(icon)'} -> {href[:300]}")
    if links:
        out.append("Links on this page to online stores and social accounts:")
        out.extend(links[:80])
    return title, "\n".join(out) + "\n"


def pdf_to_text(raw: bytes) -> tuple[str, str]:
    from pypdf import PdfReader

    reader = PdfReader(io.BytesIO(raw))
    pages = []
    for i, page in enumerate(reader.pages, 1):
        t = page.extract_text() or ""
        t = re.sub(r"[ \t]+", " ", t)
        pages.append(f"[page {i}]\n{t.strip()}")
    title = ""
    try:
        title = (reader.metadata.title or "") if reader.metadata else ""
    except Exception:
        pass
    return title[:200], "\n".join(pages) + "\n"


def manifest_path(group: str) -> Path:
    return SOURCES / "manifests" / f"{group}.csv"


def load_manifest(group: str) -> dict[str, dict]:
    m = manifest_path(group)
    if not m.exists():
        return {}
    with m.open(encoding="utf-8", newline="") as f:
        return {r["id"]: r for r in csv.DictReader(f)}


def save_manifest(group: str, rows: dict[str, dict]) -> None:
    m = manifest_path(group)
    m.parent.mkdir(parents=True, exist_ok=True)
    with m.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        for k in sorted(rows):
            w.writerow({c: rows[k].get(c, "") for c in FIELDS})


def fetch_one(sid: str, url: str, group: str, publisher: str, kind: str, note: str = "", force: bool = False,
              from_text: str | None = None) -> dict:
    if not re.fullmatch(r"[a-z0-9][a-z0-9-]{1,80}", sid):
        raise SystemExit(f"bad id {sid!r}: lower-case letters, digits and hyphens")
    rows = load_manifest(group)
    out = SOURCES / "snapshots" / group / f"{sid}.txt"
    if sid in rows and out.exists() and not force:
        print(f"skip {sid}: already saved ({rows[sid]['retrieved_at']})")
        return rows[sid]
    row = {"id": sid, "url": url, "group": group, "publisher": publisher, "kind": kind, "note": note,
           "retrieved_at": now_myt()}
    verdict = robots_allows(url)
    row["robots"] = verdict
    if verdict.startswith("robots"):
        row["status"] = "not-fetched"
        print(f"{sid}: {verdict}, not fetched")
    elif from_text:
        # A page that needs a browser to show its text: the text was read in a browser (no sign-in) and saved to a
        # file; robots.txt was still checked above.
        text = Path(from_text).read_text("utf-8")
        text = "\n".join(ln.rstrip() for ln in text.splitlines() if ln.strip()) + "\n"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(text, "utf-8")
        row.update(final_url=url, status="browser-rendered", content_type="text/plain", chars=str(len(text)),
                   sha256=hashlib.sha256(text.encode("utf-8")).hexdigest())
        print(f"{sid}: browser-rendered text {len(text)} chars -> {out.relative_to(ROOT)}")
    else:
        host = urlparse(url).netloc
        _wait(host)
        try:
            with _open(url) as r:
                raw = r.read()
                ctype = r.headers.get("Content-Type", "")
                row["final_url"] = r.geturl()
                row["status"] = str(r.status)
                charset = r.headers.get_content_charset()
        except urllib.error.HTTPError as e:
            row["status"] = str(e.code)
            row["note"] = (note + f" HTTP {e.code}").strip()
            raw, ctype, charset = b"", "", None
        except Exception as e:  # network or TLS problems: record, do not retry in a loop
            row["status"] = "error"
            row["note"] = (note + f" {type(e).__name__}: {e}"[:200]).strip()
            raw, ctype, charset = b"", "", None
        row["content_type"] = ctype.split(";")[0]
        if raw:
            if "pdf" in ctype or raw[:5] == b"%PDF-":
                title, text = pdf_to_text(raw)
            else:
                title, text = html_to_text(raw, charset)
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(text, "utf-8")
            row["title"] = title
            row["chars"] = str(len(text))
            row["sha256"] = hashlib.sha256(text.encode("utf-8")).hexdigest()
            print(f"{sid}: {row['status']} {row['content_type']} {len(text)} chars -> {out.relative_to(ROOT)}")
        else:
            print(f"{sid}: {row['status']} {row.get('note','')}")
    rows = load_manifest(group)
    rows[sid] = row
    save_manifest(group, rows)
    return row


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("url", nargs="?")
    ap.add_argument("--id")
    ap.add_argument("--group", default="misc")
    ap.add_argument("--publisher", default="")
    ap.add_argument("--kind", default="", help="official | brand | news | third-party-estimate | platform-public")
    ap.add_argument("--note", default="")
    ap.add_argument("--list", help="CSV with id,url,group,publisher,kind[,note]")
    ap.add_argument("--force", action="store_true", help="fetch again even if saved")
    ap.add_argument("--from-text", help="text of the page read in a browser (for pages that need JavaScript)")
    a = ap.parse_args()
    if a.list:
        with open(a.list, encoding="utf-8", newline="") as f:
            for r in csv.DictReader(f):
                fetch_one(r["id"], r["url"], r.get("group") or "misc", r.get("publisher", ""), r.get("kind", ""),
                          r.get("note", ""), a.force)
        return 0
    if not (a.url and a.id):
        ap.error("give URL and --id, or --list")
    fetch_one(a.id, a.url, a.group, a.publisher, a.kind, a.note, a.force or bool(a.from_text), a.from_text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
