# Malaysia Electronics Merchant Sourcing Pack

A first-week recruiting pack for Malaysian online consumer electronics: what the market looks like, which brands, distributors and retailers to contact first and why, which approvals each product needs, how to track onboarding dates, what to watch in a new shop's first 30 days, and what to write. Every fact links to a public page and is checked word for word against the saved text of that page.

[中文说明](README.zh-CN.md) · [Who to contact first](pool/PRIORITY.md) · [Market insight](insight/INSIGHTS.md) · [Approvals checklist](onboarding/CHECKLIST.md)

## Who uses what

| Part | Who uses it, for what | Files |
|---|---|---|
| Market insight | a category manager: which sub-categories and kinds of merchant to recruit, and the arguments to use | [insight/INSIGHTS.md](insight/INSIGHTS.md) |
| Candidate pool and priority | a recruiter: who to call first, the reasons with their sources, the public contact route and the next step | [pool/PRIORITY.md](pool/PRIORITY.md), [pool/merchant_pool.xlsx](pool/merchant_pool.xlsx), [pool/queries.sql](pool/queries.sql) |
| Approvals checklist | the merchant, sent after the first call: what to register, test, label and show on the listing | [onboarding/CHECKLIST.md](onboarding/CHECKLIST.md) |
| Onboarding tracker | the recruiter: one sheet per merchant, due dates from one first-contact date, reminders for overdue and due-soon steps | [onboarding/tracker_template.xlsx](onboarding/tracker_template.xlsx) |
| First 30 days | the person who grows new shops: weekly numbers, milestones and flags | [coldstart/](coldstart/) |
| Outreach templates | the recruiter: first message, follow-up, document request, kickoff, week-1 check-in; English, with a short Malay opening | [outreach/TEMPLATES.md](outreach/TEMPLATES.md) |

## What is in it

- 183 public pages saved, 130 of them quoted: 42 official pages, 44 market pages, 96 brand pages and 1 full shop ranking. <!-- c:S01 -->
- A pool of 42 merchants (33 brands, 1 distributor, 8 retailers) across 9 sub-categories; 23 have a Malaysian company or a named Malaysian distributor. <!-- c:S02 -->
- 303 values in the pool, each with a quote found in its saved page. <!-- c:S03 -->
- Priority by rules written before scoring: 14 merchants in tier A, 20 in B, 8 in C; 17 to help open a first content-commerce shop, 18 to help activate a shop that is not yet large. <!-- c:S04 -->

## Who to contact first

| Rank | Merchant | Why (each reason is a quoted public source) |
|---|---|---|
| 1 | Khind, Malaysian appliance brand | its annual report puts e-commerce at 4.2% of revenue in 2025, with direct-to-consumer sales up from RM27.2 million to RM49.3 million; already on content commerce but not yet large; products already approved by the Energy Commission and SIRIM <!-- c:S05 --> |
| 2 | VSTECS, Malaysian ICT distributor | runs official online stores for brand principals and a network of over 4,000 partners; checks that brands are SIRIM and MCMC certified; no content-commerce shop found <!-- c:S06 --> |
| 3, 4 | CompAsia and Machines, Malaysian retail chains | around 70 and more than 50 stores; Malaysian short-video accounts already running; no content-commerce shop found <!-- c:S07 --> |

The full list, with the next step and the public contact route for each, is in [pool/PRIORITY.md](pool/PRIORITY.md). "No content-commerce shop found" means none was found in the public pages read; check the platform's own seller list before the first call.

## Three findings that shape the list

- Shoppers are already there: 62% of Malaysian online shoppers used TikTok Shop in 2026, up from 52% in 2025 and 43% in 2024 (Ipsos). <!-- c:S08 -->
- The electronics leaders there by units are accessory sellers, such as Baseus Malaysia (14th) and UgreenOfficialShop (15th) in FindNiche's ranking of 100 shops by units sold, so brands that sell higher-value electronics elsewhere are the thinner supply. <!-- c:S09 -->
- Local sellers have a tailwind: a 10% sales tax on imported goods of RM500 or less raised RM817 juta (million) in 2025, up from RM476 juta in 2024. <!-- c:S10 -->

## How it was built

1. **Existing tools first.** Shop-ranking tools (Kalodata, FastMoss, EchoTik, FindNiche) rank merchants already on a platform; a platform's seller-centre tools need a seller login. Neither answers which merchants that are not yet there, or not yet large, to bring in first. This pack fills that gap from public sources and uses the existing tools' public pages as inputs.
2. **Reading pages.** Single public pages only, after checking robots.txt (including the rules a site writes for AI assistants), at least 8 seconds apart on the same site, with no sign-in; no marketplace product, shop or search pages. A site that asks assistants not to read it is not read. The page texts stay with their publishers: [sources/manifests/](sources/manifests/) lists each URL, the reading time and a SHA-256 of the saved text, and [tools/refetch.py](tools/refetch.py) saves them again.
3. **Approvals from regulators only:** the Energy Commission, MCMC, SIRIM QAS, KPDN, Royal Malaysian Customs and SSM. A new Energy Commission approval takes five working days if the documents are complete, and MCMC asks for the certification to be shown on the product page. <!-- c:S11 -->
4. **Scores by fixed rules.** [pool/SCORING.md](pool/SCORING.md) was written before any candidate row was filled; [pool/build.py](pool/build.py) refuses to score if it changes. Its change log records that v2 replaced v1 before any row was scored. <!-- c:S12 -->
5. **Every value checked.** `pool/build.py` stops if a quote is not in its page, a number is not in its quote, or the quote lacks the words that make it evidence (a Shopee store needs "shopee", a certification needs SIRIM, MCMC or the Energy Commission). [tools/check_all.py](tools/check_all.py) checks every tagged line of the insight, the checklist and both READMEs the same way. The checker is [evidence-check](https://github.com/llia0031-dotcom/evidence-check).

## Run it

Python 3.10 or later.

```bash
pip install -r requirements.txt
python tools/refetch.py          # save the public pages again from the manifests (slow on purpose)
python pool/build.py             # check every value, score, write the tables, the Excel file and the DuckDB file
python pool/run_queries.py       # answer the questions in pool/queries.sql into pool/QUERIES.md
python tools/check_all.py        # check the insight, the checklist and the READMEs against their sources
python coldstart/run.py          # first-30-days views on the synthetic example
python -m unittest discover -s tests
```

## Limits

- "Not found in public sources" is not a judgement of any merchant, and does not mean a shop or an approval does not exist.
- Sales figures from research firms and data tools are their estimates; the shop ranking comes from one dataset and ranks by units.
- Home appliances are included next to Phones & Electronics because local appliance brands are among the strongest local candidates.
- No merchant has been contacted, and the outreach templates have not been sent.
- The data in `coldstart/example/` is synthetic and exists only to test the SQL.

## Where this fits

Part of a set of projects built on one idea: every claim should show its evidence. [evidence-check](https://github.com/llia0031-dotcom/evidence-check) is the checker used here; [Grounded Business Review](https://github.com/llia0031-dotcom/grounded-business-review) is the weekly-metrics method the first-30-days SQL follows.

Code: MIT. The facts and short quotes come from the publishers named in the manifests. Independent research from public sources, not affiliated with any platform, brand or retailer named here.
