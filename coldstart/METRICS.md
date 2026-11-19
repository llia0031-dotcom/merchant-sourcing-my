# First 30 days of a new merchant: what to look at each week

Day 1 is the day the first SKU goes live. The SQL is in `schema.sql` (tables) and `metrics.sql` (views); `run.py`
loads five CSV files and prints the weekly table. The files in `example/` are **synthetic** (two invented brands,
fixed random seed): they exist only so the SQL can be run and tested. They describe no real merchant or result.

## Weekly focus

| Week | Main question | Numbers that answer it |
|---|---|---|
| 1 (days 1–7) | Is the shop complete and can it take orders? | live SKUs; regulated SKUs live with a certificate reference; day of first order; on-time ship rate on the first orders |
| 2 (days 8–14) | Are shoppers finding the products? | product page views; visitors; conversion rate |
| 3 (days 15–21) | Is content starting to sell? | live minutes; short videos posted; active creators; content share of GMV |
| 4 (days 22–28) | Is the shop healthy enough to scale? | refund rate; cancellation rate; chat response rate; GMV per day, week on week |
| 5 (days 29–30) | Hand-over to the regular review | the whole table, plus the flags |

## Definitions (all per merchant and week)

| Metric | Formula | Why it matters early |
|---|---|---|
| Live SKUs | SKUs with status `live` and listed by the week's last day | An incomplete range limits traffic and conversion |
| Regulated SKUs live with a reference | live regulated SKUs that have a CoA or certificate number recorded | Keeps listings in the categories that need approval from being taken down later |
| Conversion rate | orders ÷ visitors | Whether product pages and prices work |
| Average order value | GMV ÷ orders | Bundles and price band |
| Content share of GMV | GMV from live streams, short videos and creators ÷ GMV | How much the content channel is carrying |
| GMV per day, week on week | (GMV ÷ days in the week) ÷ the same for the week before − 1 | Growth, fair to the two-day week 5 |
| On-time ship rate | orders shipped within the promised handling time ÷ orders shipped | Early delays hurt ratings and repeat orders |
| Cancellation rate | cancelled orders ÷ orders | Stock and price accuracy |
| Refund rate | refunds (RM) ÷ GMV | Product and description accuracy |
| Chat response rate | chats answered in time ÷ chats received | Pre-sale questions are common for electronics (compatibility, warranty) |
| Day of first order, day of first live stream | from `coldstart_milestones` | Time to first result |

## Flags and reminders

- `coldstart_flags` lists every weekly value that crosses a threshold in the `thresholds` table. The thresholds are
  the team's own choice; the example values (for example on-time ship rate below 95%) are examples, not platform rules.
- `milestone_reminders` marks onboarding milestones as overdue, due within 3 days, scheduled or done, by today's
  date. The milestone names match `onboarding/tracker_template.csv`.
