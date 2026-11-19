"""Writes the onboarding follow-up tracker template: CSV (imports into a spreadsheet or a multi-dimensional table)
and Excel with live date reminders.

    python onboarding/make_tracker.py   # -> onboarding/tracker_template.csv, onboarding/tracker_template.xlsx

Every milestone's due date is an offset from the first-contact date, so a new brand needs one date typed in.
The offsets are a starting plan to adjust per brand, not platform deadlines. The milestone names match
coldstart/schema.sql (table `milestones`) so the same rows feed the first-30-days reminders.
"""
from __future__ import annotations

import csv
from pathlib import Path

HERE = Path(__file__).resolve().parent

# (milestone, owner, offset in days from first contact, what "done" means)
MILESTONES = [
    ("First contact", "category team", 0, "first message sent (outreach template 1)"),
    ("Needs call", "category team + brand", 7, "call held; products, goals and help needed written down (template 3)"),
    ("Documents requested", "category team", 8, "category checklist and document list sent"),
    ("Documents received", "brand", 15, "business registration, bank details and brand authorisation received"),
    ("Certificate numbers for regulated SKUs", "brand", 15, "CoA / MCMC certificate numbers listed per regulated SKU"),
    ("Account submitted", "brand", 17, "seller application submitted"),
    ("Account approved", "platform", 20, "account approved (template 4 sent)"),
    ("First 10 SKUs live", "brand", 27, "ten SKUs live with prices, photos and certificate numbers where needed"),
    ("First live stream", "brand + creators", 34, "first live stream or first creator video published"),
    ("Week-1 check-in", "category team + brand", 34, "week-1 numbers shared (template 5)"),
    ("Day-30 review", "category team + brand", 57, "coldstart/metrics.sql weekly table reviewed together"),
]
COLUMNS = ["brand", "subcategory", "supply_type", "milestone", "owner", "offset_days", "first_contact_date",
           "due_date", "done_date", "days_left", "reminder", "done_means", "documents_or_numbers", "notes"]


def main() -> None:
    with (HERE / "tracker_template.csv").open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(COLUMNS)
        for m, owner, off, done in MILESTONES:
            w.writerow(["{brand}", "{subcategory}", "{local or cross-border}", m, owner, off, "", "", "", "", "", done, "", ""])

    from openpyxl import Workbook
    from openpyxl.formatting.rule import FormulaRule
    from openpyxl.styles import Alignment, Font, PatternFill
    from openpyxl.utils import get_column_letter
    from openpyxl.worksheet.datavalidation import DataValidation

    wb = Workbook()
    ws = wb.active
    ws.title = "tracker"
    ws.append(COLUMNS)
    for c in ws[1]:
        c.font = Font(bold=True, color="FFFFFF")
        c.fill = PatternFill("solid", fgColor="1F2937")
    col = {name: get_column_letter(i) for i, name in enumerate(COLUMNS, 1)}
    first = 2
    for i, (m, owner, off, done) in enumerate(MILESTONES):
        r = first + i
        fc = f"{col['first_contact_date']}{r}" if i == 0 else f"{col['first_contact_date']}${first}"
        ws.append(["Example brand (type the real one)", "", "", m, owner, off,
                   "" if i == 0 else f"={col['first_contact_date']}${first}",
                   f'=IF({fc}="","",{fc}+{col["offset_days"]}{r})', "",
                   f'=IF({col["due_date"]}{r}="","",{col["due_date"]}{r}-TODAY())',
                   f'=IF({col["done_date"]}{r}<>"","done",IF({col["due_date"]}{r}="","",'
                   f'IF({col["days_left"]}{r}<0,"overdue",IF({col["days_left"]}{r}<=3,"due within 3 days","scheduled"))))',
                   done, "", ""])
        for k in ("first_contact_date", "due_date", "done_date"):
            ws[f"{col[k]}{r}"].number_format = "yyyy-mm-dd"
    last = first + len(MILESTONES) - 1
    rng = f"A{first}:{col['notes']}{last}"
    ws.conditional_formatting.add(rng, FormulaRule(formula=[f'${col["reminder"]}{first}="overdue"'],
                                                   fill=PatternFill("solid", fgColor="FDE2E1")))
    ws.conditional_formatting.add(rng, FormulaRule(formula=[f'${col["reminder"]}{first}="due within 3 days"'],
                                                   fill=PatternFill("solid", fgColor="FEF3C7")))
    ws.conditional_formatting.add(rng, FormulaRule(formula=[f'${col["reminder"]}{first}="done"'],
                                                   font=Font(color="6B7280")))
    dv = DataValidation(type="list", formula1='"local,cross-border"', allow_blank=True)
    ws.add_data_validation(dv)
    dv.add(f"{col['supply_type']}{first}:{col['supply_type']}{last}")
    widths = {"brand": 30, "subcategory": 22, "supply_type": 14, "milestone": 36, "owner": 22, "offset_days": 11,
              "first_contact_date": 17, "due_date": 12, "done_date": 12, "days_left": 10, "reminder": 18,
              "done_means": 60, "documents_or_numbers": 30, "notes": 30}
    for k, v in widths.items():
        ws.column_dimensions[col[k]].width = v
    for row in ws.iter_rows(min_row=first, max_row=last):
        for c in row:
            c.alignment = Alignment(vertical="top", wrap_text=c.column_letter == col["done_means"])
    ws.freeze_panes = "E2"

    how = wb.create_sheet("how to use")
    for line in [
        "1. Type the brand, sub-category and supply type on the first row, and the first-contact date in G2.",
        "2. Every other due date follows from G2 and the offset in column F; change an offset to re-plan one step.",
        "3. Type the done date when a step is complete. Column K shows done / overdue / due within 3 days / scheduled, "
        "from today's date, and colours the row.",
        "4. Offsets are a starting plan, not platform deadlines. Copy the sheet once per brand.",
        "5. The category document list is in CHECKLIST.md (official sources only); the outreach templates are in "
        "outreach/TEMPLATES.md.",
    ]:
        how.append([line])
    how.column_dimensions["A"].width = 120
    wb.save(HERE / "tracker_template.xlsx")
    print("wrote onboarding/tracker_template.csv and .xlsx")


if __name__ == "__main__":
    main()
