# Inside a category team: what changes

This pack is built from public pages only. Inside a category team, the weakest fields are replaced by the platform's own data in the first week, and the scoring rules are tested against real results after the first batch of merchants.

## Fields to replace first

| Field now (public pages) | Replace with | What it changes |
|---|---|---|
| Content-commerce shop found or not | The platform's own seller list: shop exists, start date, GMV band | The gap score becomes exact. "Open a shop" and "activate" are split by a GMV line, not by what a news page mentioned. Merchants already served by another team drop out |
| Demand: filings, store network, vendor share, best-seller lists | Search demand with too few sellers, by product (the supply-gap data a category team sees), and the merchant's sales on other channels where the team has a data tool | Demand moves from "is the brand known" to "which of its products are searched for and missing". The first SKUs come from here |
| Readiness: Malaysian company found, certification statement | Category qualification records, and each model checked in SIRIM's eComM enquiry or the SIRIM app | Readiness is known per SKU before the first call, so the call asks only for what is missing |
| Content: social links on the brand's site | The brand's short-video and live results where it already sells | Separates brands with an account from brands whose content sells |
| Public contact route | The CRM record and the owner on the team | No duplicate outreach |

## Testing the scoring rules with results

The weights in [SCORING.md](SCORING.md) are a starting assumption. After the first batch they are checked against what happened, with [calibration.sql](calibration.sql):

1. **Contact a mixed first batch.** Most calls go to tiers A and B, plus a few tier-C merchants, so the comparison has a contrast. Record each one in the onboarding tracker.
2. **Record the result for each merchant** in an `outcomes` table: date contacted, onboarded or not, and GMV per day in week 4 from `coldstart/metrics.sql`.
3. **Run the three checks** (`python pool/calibrate.py outcomes.csv`):
   - C1: do higher tiers onboard more often and sell more in week 4?
   - C2: for each dimension, how do results change with its score level?
   - C3: one rank correlation per dimension between score level and week-4 GMV per day.
4. **Change a weight only when a dimension clearly fails to track results** across enough merchants, and write the new weights as the next version of SCORING.md before scoring the next batch, the same freeze rule as v1 and v2.
5. **Keep what the score is for.** It orders calls; it does not decide whether a merchant is good. A merchant with a low score and a strong reason to call still gets called.
