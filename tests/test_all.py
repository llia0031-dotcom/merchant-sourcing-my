"""Offline tests: no network.

    python -m unittest discover -s tests
"""
from __future__ import annotations

import csv
import sys
import tempfile
import unittest
import urllib.robotparser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for p in ("tools", "pool", "coldstart", "tools/vendor"):
    sys.path.insert(0, str(ROOT / p))

import build  # noqa: E402
import check_evidence as ce  # noqa: E402
import save_page  # noqa: E402

NF = "not found in public sources"


class SavePageTests(unittest.TestCase):
    def test_text_and_store_links(self):
        html = b"""<html><head><title>Brand MY</title><script>var x=1</script></head><body>
        <h1>Brand Malaysia</h1><p>Brand Electronics (Malaysia) Sdn Bhd</p>
        <footer><a href="https://shopee.com.my/brand.os"><img alt=""></a>
        <a href="https://www.tiktok.com/@brand.my" aria-label="TikTok"></a>
        <a href="/about">About</a></footer></body></html>"""
        title, text = save_page.html_to_text(html, "utf-8")
        self.assertEqual(title, "Brand MY")
        self.assertIn("Brand Electronics (Malaysia) Sdn Bhd", text)
        self.assertNotIn("var x", text)
        self.assertIn("link: (icon) -> https://shopee.com.my/brand.os", text)
        self.assertIn("link: TikTok -> https://www.tiktok.com/@brand.my", text)
        self.assertNotIn("/about", text)

    def test_robots_rules_for_assistant_agents(self):
        rp = urllib.robotparser.RobotFileParser()
        rp.parse(["User-agent: Claude-User", "Disallow: /", "", "User-agent: *", "Allow: /"])
        save_page._robots["https://example.test"] = rp
        self.assertEqual(save_page.robots_allows("https://example.test/page"), "robots-disallow")
        rp2 = urllib.robotparser.RobotFileParser()
        rp2.parse(["User-agent: *", "Disallow: /private/"])
        save_page._robots["https://ok.test"] = rp2
        self.assertEqual(save_page.robots_allows("https://ok.test/page"), "allowed")
        self.assertEqual(save_page.robots_allows("https://ok.test/private/x"), "robots-disallow")


PAGE = ("Acme Electronics (Malaysia) Sdn Bhd\nAll products come with SIRIM certification.\n"
        "Acme 20W charger RM 49.90\nOnline sales grew 35% in FY2025.\nContact us: sales@acme.example\n"
        "Links on this page to online stores and social accounts:\n"
        "link: (icon) -> https://shopee.com.my/acme.os\nlink: (icon) -> https://www.facebook.com/AcmeMalaysia\n")


def acme(**kw):
    c = {"brand": "Acme", "kind": "brand", "subcategory": "Audio",
         "presence": {"value": "global brand with a Malaysian company", "entity": "Acme Electronics (Malaysia) Sdn Bhd",
                      "evidence": [{"source": "acme-home", "quote": "Acme Electronics (Malaysia) Sdn Bhd"}]},
         "stores": {"value": ["Shopee"], "evidence": [{"source": "acme-home", "quote": "link: (icon) -> https://shopee.com.my/acme.os"}]},
         "accounts": {"short_video": False, "others": ["Facebook"], "scope": "Malaysia-specific",
                      "evidence": [{"source": "acme-home", "quote": "link: (icon) -> https://www.facebook.com/AcmeMalaysia"}]},
         "certification": {"value": "certification stated", "detail": "SIRIM certification stated on its page",
                           "evidence": [{"source": "acme-home", "quote": "All products come with SIRIM certification."}]},
         "sells_well": {"value": "Online sales grew 35% in FY2025", "level": "filing-or-award",
                        "evidence": [{"source": "acme-home", "quote": "Online sales grew 35% in FY2025."}]},
         "contact": {"value": "sales@acme.example", "evidence": [{"source": "acme-home", "quote": "Contact us: sales@acme.example"}]}}
    c.update(kw)
    return c


class BuildTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        d = Path(self.tmp.name) / "brands"
        d.mkdir()
        (d / "acme-home.txt").write_text(PAGE, "utf-8")
        self.E = build.Evidence([Path(self.tmp.name)])

    def tearDown(self):
        self.tmp.cleanup()

    def test_checked_row_and_score(self):
        row = build.check_row(acme(), self.E)
        self.assertEqual(row["supply_type"], "local")
        self.assertEqual(row["official_stores_elsewhere"], "Shopee")
        s = build.score(row, acme(), [])
        self.assertEqual((s["demand"], s["gap"], s["readiness"], s["content"]), (3, 3, 3, 2))
        self.assertEqual(s["total"], round(100 * (0.3 * 3 + 0.3 * 3 + 0.25 * 3 + 0.15 * 2) / 3, 1))
        self.assertEqual((s["tier"], s["segment"]), ("A", "open a shop"))

    def test_invented_store_stops_the_build(self):
        c = acme(stores={"value": ["Shopee", "Lazada"], "evidence": [
            {"source": "acme-home", "quote": "link: (icon) -> https://shopee.com.my/acme.os"},
            {"source": "acme-home", "quote": "link: (icon) -> https://www.lazada.com.my/shop/acme"}]})
        with self.assertRaises(build.BuildError):
            build.check_row(c, self.E)

    def test_wrong_number_stops_the_build(self):
        c = acme(sells_well={"value": "Online sales grew 45% in FY2025", "level": "filing-or-award",
                             "evidence": [{"source": "acme-home", "quote": "Online sales grew 35% in FY2025."}]})
        with self.assertRaises(build.BuildError):
            build.check_row(c, self.E)

    def test_quote_must_fit_the_value(self):
        c = acme(certification={"value": "certification stated", "detail": "certification",
                                "evidence": [{"source": "acme-home", "quote": "Acme 20W charger RM 49.90"}]})
        with self.assertRaises(build.BuildError):
            build.check_row(c, self.E)

    def test_levels_without_evidence(self):
        c = acme(presence={"value": NF, "evidence": []}, stores={"value": [], "evidence": []},
                 accounts={"short_video": False, "others": [], "scope": NF, "evidence": []},
                 certification={"value": NF}, sells_well=None, contact=None)
        c.pop("sells_well")
        c.pop("contact")
        row = build.check_row(c, self.E)
        s = build.score(row, c, [])
        self.assertEqual((s["demand"], s["gap"], s["readiness"], s["content"], s["segment"]), (0, 0, 0, 0, "check first"))

    def test_frozen_rules_unchanged(self):
        build.check_frozen()


class ColdstartTests(unittest.TestCase):
    def test_weekly_numbers_match_the_csv(self):
        import run as coldstart_run

        con = coldstart_run.connect(ROOT / "coldstart" / "example")
        with (ROOT / "coldstart" / "example" / "daily_shop.csv").open(encoding="utf-8") as f:
            rows = [r for r in csv.DictReader(f) if r["merchant_id"] == "EX-001"][:7]
        visitors = sum(int(r["visitors"]) for r in rows)
        orders = sum(int(r["orders"]) for r in rows)
        got = con.execute("SELECT visitors, orders, conversion_rate, days_in_week FROM coldstart_weekly "
                          "WHERE merchant_id='EX-001' AND week=1").fetchone()
        self.assertEqual(got[0], visitors)
        self.assertEqual(got[1], orders)
        self.assertAlmostEqual(got[2], round(orders / visitors, 4))
        self.assertEqual(got[3], 7)
        weeks = con.execute("SELECT list(days_in_week ORDER BY week) FROM coldstart_weekly WHERE merchant_id='EX-001'").fetchone()[0]
        self.assertEqual(weeks, [7, 7, 7, 7, 2])

    def test_reminders(self):
        import run as coldstart_run

        con = coldstart_run.connect(ROOT / "coldstart" / "example")
        states = {r[0] for r in con.execute("SELECT reminder FROM milestone_reminders").fetchall()}
        self.assertTrue(states <= {"done", "overdue", "due within 3 days", "scheduled"})
        self.assertIn("done", states)


if __name__ == "__main__":
    unittest.main()
