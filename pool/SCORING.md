# Scoring rules for the candidate pool

Written and frozen before any candidate was scored. The SHA-256 of this file is recorded with the scores, and
`pool/build.py` refuses to score if the file has changed. A change to the rules means a new version of this file
and a full re-score, both recorded in the change log at the end.

## What the score is for

To decide which brands, distributors and retailers a category team should contact first, so that the platform gains
supply it lacks and the merchant gets a smooth start. It ranks by public evidence only. It says nothing about a
merchant's quality; a low score means "less evidence, or less to gain right now", never a judgement of the merchant.

## Inputs

Each candidate row is filled from saved public pages only (`sources/manifests/`). Every filled field carries the
source id and a verbatim quote, and the quote is checked against the saved page text by evidence-check. A field
without a checked quote counts as **not found in public sources** and scores as such.

## Four dimensions (each scored 0–3; take the highest level whose condition holds)

### 1. Demand signal (weight 30%)
Evidence that the merchant already sells well to Malaysian shoppers through other channels.

| Score | Condition |
|---|---|
| 3 | Its own filing or annual report, or a public award or ranking announcement, states its Malaysian online sales, online growth or an online-sales award; or it is named in a public, dated third-party estimate of Malaysian sales (a vendor-share release for its product type, or a public ranking of Malaysian shops) |
| 2 | It states a nationwide physical retail or dealer network in Malaysia (a number of stores or dealers), or its product type is named among best-selling or trending electronics in a public Malaysian source |
| 1 | It lists at least one official Malaysian online store (any channel) |
| 0 | None of the above found |

### 2. Content-commerce gap (weight 30%)
How much a guided start on content commerce would add.

| Score | Condition |
|---|---|
| 3 | Official Malaysian online store(s) on other channels found; no content-commerce shop found on its own pages, and no shop with its name in the public top-shop rankings of content-commerce shops used in this pack |
| 2 | Its own pages link a content-commerce shop, but no shop with its name is in those public top-shop rankings (started, not yet large) |
| 1 | A shop with its name is in those public top-shop rankings (already large; a growth conversation, not entry) |
| 0 | No official Malaysian online store found on any channel |

### 3. Qualification readiness (weight 25%)
How quickly it could list regulated electronics in Malaysia.

| Score | Condition |
|---|---|
| 3 | A Malaysian company or a named Malaysian distributor is found, and either a public register entry (MCMC, SIRIM QAS or Energy Commission) for at least one of its products or a statement of Malaysian certification on its own pages is found |
| 2 | A Malaysian company or a named Malaysian distributor is found; no certification evidence found |
| 1 | It is found selling to Malaysia from abroad only |
| 0 | Nothing found |

A merchant that a page calls Malaysian counts as a Malaysian company.

### 4. Content capability (weight 15%)
Whether it already makes social or video content for Malaysian shoppers.

| Score | Condition |
|---|---|
| 3 | Its own pages link a Malaysian short-video account and at least one other Malaysian social or video account |
| 2 | Its own pages link Malaysian social or video accounts (but not both kinds above) |
| 1 | Only global (not Malaysia-specific) social or video accounts are linked |
| 0 | None found |

## Total, tiers and order

- Total = 100 × (0.30 × demand + 0.30 × gap + 0.25 × readiness + 0.15 × content) / 3, rounded to one decimal.
- Tier A: total ≥ 70. Tier B: 50 ≤ total < 70. Tier C: total < 50.
- Order: total, then readiness, then demand, then local merchants (Malaysian company or distributor) before
  cross-border ones, then name.
- Segment: **open a shop** when gap = 3, **activate** when gap = 2, **grow** when gap = 1, **check first** when gap = 0.

## Next action (rule, not judgement)

| Condition | Next action written in the row |
|---|---|
| readiness = 3 | Share the category document list; confirm certificate numbers for the first SKUs |
| readiness = 2 | Ask which SKUs carry SIRIM / MCMC / Energy Commission approval, and who holds the certificates |
| readiness = 1 | Point to the cross-border seller route; check which SKUs are regulated in Malaysia |
| readiness = 0 | Find the Malaysian contact first |

## Change log

- v1 (2026-11-19 19:04): first version. Replaced before any candidate row was filled or scored.
- v2 (2026-11-19, before any candidate row was filled or scored): the pack's focus moved to Malaysian brands,
  distributors and retailers that already sell well elsewhere but are not yet large on content commerce. Demand now
  counts a merchant's own filings and public awards, and a stated retail network; the gap separates "no shop" from
  "a shop that is not yet large"; readiness counts public register entries and no longer counts warranty statements;
  content capability's middle level is reworded so every case has a level; local merchants come first on ties.
