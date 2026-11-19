# Malaysia Electronics Merchant Sourcing Pack

A recruiting playbook for Malaysian online consumer electronics: which merchants to bring in first and why, what approvals their products need, and how to run their first 30 days. Every fact links to a public page and is checked against the saved text of that page.

[中文说明](README.zh-CN.md) · [Who to contact first](pool/PRIORITY.md) · [Deep dive: chargers and power banks](insight/DEEP_DIVE_CHARGING.md) · [Approvals checklist](onboarding/CHECKLIST.md) · [Inside a category team](pool/INSIDE_THE_TEAM.md)

## What it found

**Who to contact first**

| Rank | Merchant | Why (each reason is a quoted public source) |
|---|---|---|
| 1 | Khind, Malaysian appliance brand | its annual report puts e-commerce at 4.2% of revenue in 2025, with direct-to-consumer sales up from RM27.2 million to RM49.3 million; already on content commerce but not yet large; products already approved by the Energy Commission and SIRIM <!-- c:S05 --> |
| 2 | VSTECS, Malaysian ICT distributor | runs official online stores for brand principals and a network of over 4,000 partners; checks that brands are SIRIM and MCMC certified; no content-commerce shop found <!-- c:S06 --> |
| 3, 4 | CompAsia and Machines, Malaysian retail chains | around 70 and more than 50 stores; Malaysian short-video accounts already running; no content-commerce shop found <!-- c:S07 --> |

The full list, with the next step and the public contact route for each, is in [pool/PRIORITY.md](pool/PRIORITY.md). "No content-commerce shop found" means none was found in the public pages read; check the platform's own seller list before the first call.

**Why local merchants first**

- Shoppers are already there: 62% of Malaysian online shoppers used TikTok Shop in 2026, up from 52% in 2025 and 43% in 2024 (Ipsos). <!-- c:S08 -->
- The electronics leaders there by units are accessory sellers, such as Baseus Malaysia (14th) and UgreenOfficialShop (15th) in FindNiche's ranking of 100 shops by units sold, so brands that sell higher-value electronics elsewhere are the thinner supply. <!-- c:S09 -->
- Local sellers have a tailwind: a 10% sales tax on imported goods of RM500 or less raised RM817 juta (million) in 2025, up from RM476 juta in 2024. <!-- c:S10 -->

**One sub-category in depth: chargers and power banks.** The unit leaders cost between RM0.19 and RM16.29 while branded chargers start at MYR 69, and the Energy Commission approval is held by a Malaysian importer, so the brand's local distributor is the first call. [Deep dive](insight/DEEP_DIVE_CHARGING.md). <!-- c:S13 -->

## Who uses what

| Part | Who uses it, for what | Files |
|---|---|---|
| Market insight and deep dive | a category manager: which sub-categories and kinds of merchant to recruit, and the arguments to use | [insight/](insight/) |
| Candidate pool and priority | a recruiter: who to call first, the reasons with their sources, the public contact route and the next step | [pool/PRIORITY.md](pool/PRIORITY.md), [pool/merchant_pool.xlsx](pool/merchant_pool.xlsx), [pool/queries.sql](pool/queries.sql) |
| Approvals checklist | the merchant, sent after the first call: what to register, test, label and show on the listing | [onboarding/CHECKLIST.md](onboarding/CHECKLIST.md) |
| Onboarding tracker | the recruiter: one sheet per merchant, due dates from one first-contact date, reminders for overdue and due-soon steps | [onboarding/tracker_template.xlsx](onboarding/tracker_template.xlsx) |
| First 30 days | the person who grows new shops: weekly numbers, milestones and flags | [coldstart/](coldstart/) |
| Outreach templates | the recruiter: first message, follow-up, document request, kickoff, week-1 check-in; English, with a short Malay opening | [outreach/TEMPLATES.md](outreach/TEMPLATES.md) |

## Inside a category team

- The weakest fields come from public pages and are the first to replace with the platform's own data: whether a shop already exists, product-level search demand, and qualification records per SKU. [pool/INSIDE_THE_TEAM.md](pool/INSIDE_THE_TEAM.md) lists each one and what it changes.
- The weights are a starting assumption. After the first batch of merchants, [pool/calibration.sql](pool/calibration.sql) compares tiers and each dimension with who onboarded and how much they sold in week 4, and any new weights are frozen before the next batch is scored.

## How it was built

- **Existing tools first.** Shop-ranking tools rank merchants already on a platform; seller-centre tools need a seller login. This pack covers merchants not yet there, or not yet large, and uses the public pages of the existing tools as inputs.
- **Public pages only,** read one at a time after checking robots.txt (including the rules a site writes for AI assistants), at least eight seconds apart on a site, with no sign-in and no marketplace product, shop or search pages. The page texts stay with their publishers; [sources/manifests/](sources/manifests/) lists each URL, reading time and fingerprint, and [tools/refetch.py](tools/refetch.py) saves them again.
- **Approvals from regulators only:** the Energy Commission, MCMC, SIRIM QAS, KPDN, Royal Malaysian Customs and SSM. A new Energy Commission approval takes five working days if the documents are complete, and MCMC asks for the certification to be shown on the product page. <!-- c:S11 -->
- **Scores by rules fixed before scoring.** [pool/SCORING.md](pool/SCORING.md) records that v2 replaced v1 before any row was scored; [pool/build.py](pool/build.py) refuses to score if the rules change. <!-- c:S12 -->
- **Every fact checked** against its saved page with [evidence-check](https://github.com/llia0031-dotcom/evidence-check), by [pool/build.py](pool/build.py) for the pool and [tools/check_all.py](tools/check_all.py) for the documents.

Scale: 183 public pages saved and 131 quoted; 42 merchants (33 brands, 1 distributor, 8 retailers) across 9 sub-categories, 23 of them with a Malaysian company or a named Malaysian distributor; 303 values in the pool, each with a quote found in its page; tiers A 14, B 20, C 8; 17 merchants to help open a first content-commerce shop and 18 to help grow one. <!-- c:S14 -->

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
