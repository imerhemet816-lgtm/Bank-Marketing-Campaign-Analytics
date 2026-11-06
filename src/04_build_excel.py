"""Build excel/bank_marketing_analysis.xlsx.

The Data sheet holds the cleaned records; the Summary and Segments sheets use
COUNTIFS formulas that point at it, so the numbers update if rows change.
Cached values are written too so the file also displays correctly in viewers
that do not recalculate.
"""
from pathlib import Path

import pandas as pd
import xlsxwriter

ROOT = Path(__file__).resolve().parents[1]
df = pd.read_csv(ROOT / "data" / "processed" / "bank_clean.csv")
OUT = ROOT / "excel" / "bank_marketing_analysis.xlsx"

wb = xlsxwriter.Workbook(OUT)
navy = "#0B2545"
head = wb.add_format({"bold": True, "font_color": "white", "bg_color": navy, "border": 1, "align": "center"})
txt = wb.add_format({"border": 1})
num = wb.add_format({"border": 1, "num_format": "#,##0"})
pct = wb.add_format({"border": 1, "num_format": "0.0%"})
dec = wb.add_format({"border": 1, "num_format": "0.0"})
title = wb.add_format({"bold": True, "font_size": 14, "font_color": navy})
note = wb.add_format({"italic": True, "font_color": "#666666"})

# ---- Data sheet ----
ws_data = wb.add_worksheet("Data")
cols = list(df.columns)
ws_data.add_table(0, 0, len(df), len(cols) - 1,
                  {"columns": [{"header": c} for c in cols], "style": "Table Style Light 1"})
for r, row in enumerate(df.itertuples(index=False), start=1):
    for c, v in enumerate(row):
        if pd.isna(v):
            continue
        ws_data.write(r, c, v)
ws_data.freeze_panes(1, 0)
ws_data.set_column(0, len(cols) - 1, 14)
last = len(df) + 1


def rng(col):
    i = cols.index(col)
    letter = xlsxwriter.utility.xl_col_to_name(i)
    return f"Data!${letter}$2:${letter}${last}"


# ---- Summary sheet ----
ws = wb.add_worksheet("Summary")
ws.write("A1", "Bank Marketing Campaign - Summary", title)
ws.write("A2", "Formulas reference the Data sheet. Source: UCI Bank Marketing (bank.csv, 4,521-row sample).", note)
kpis = [
    ("Campaign records", f"=COUNTA({rng('record_id')})", len(df), num),
    ("Subscribed", f"=SUM({rng('subscribed_flag')})", int(df.subscribed_flag.sum()), num),
    ("Response rate", "=B5/B4", df.subscribed_flag.mean(), pct),
    ("Total contacts (campaign)", f"=SUM({rng('campaign')})", int(df.campaign.sum()), num),
    ("Contacts per subscription", "=B7/B5", df.campaign.sum() / df.subscribed_flag.sum(), dec),
    ("Average age", f"=AVERAGE({rng('age')})", df.age.mean(), dec),
]
ws.write_row("A3", ["KPI", "Value"], head)
for i, (label, f, v, fmt) in enumerate(kpis):
    ws.write(3 + i, 0, label, txt)
    ws.write_formula(3 + i, 1, f, fmt, v)
ws.set_column("A:A", 30); ws.set_column("B:F", 16)

# ---- Segments sheet: one block per breakdown ----
seg = wb.add_worksheet("Segments")
seg.write("A1", "Response rate by segment (COUNTIFS on Data sheet)", title)
seg.set_column("A:A", 24); seg.set_column("B:E", 14)
blocks = [
    ("age_group", ["<25", "25-34", "35-44", "45-54", "55-64", "65+"]),
    ("job", list(df.groupby("job").subscribed_flag.mean().sort_values(ascending=False).index)),
    ("contact", ["cellular", "telephone", "unknown"]),
    ("poutcome", ["success", "other", "failure", "unknown"]),
    ("campaign_band", ["1", "2", "3", "4-5", "6+"]),
]
row = 2
chart_anchor_col = 6
for col, order in blocks:
    seg.write(row, 0, col, head)
    seg.write_row(row, 1, ["Clients", "Subscribers", "Response rate"], head)
    first = row + 1
    for k, val in enumerate(order, start=1):
        r = row + k
        sub = df[df[col].astype(str) == val]
        seg.write(r, 0, val, txt)
        # campaign_band is text like "1" in the data; use quotes so COUNTIFS matches text
        crit = f'"="&$A{r+1}'
        seg.write_formula(r, 1, f"=COUNTIFS({rng(col)},{crit})", num, len(sub))
        seg.write_formula(r, 2, f"=COUNTIFS({rng(col)},{crit},{rng('subscribed_flag')},1)", num, int(sub.subscribed_flag.sum()))
        seg.write_formula(r, 3, f"=C{r+1}/B{r+1}", pct, sub.subscribed_flag.mean())
    ch = wb.add_chart({"type": "column"})
    ch.add_series({"name": f"Response rate by {col}",
                   "categories": ["Segments", first, 0, row + len(order), 0],
                   "values": ["Segments", first, 3, row + len(order), 3],
                   "fill": {"color": "#1B7F8C"}, "data_labels": {"value": True, "num_format": "0%"}})
    ch.set_legend({"none": True}); ch.set_title({"name": f"Response rate by {col}"})
    ch.set_y_axis({"num_format": "0%", "major_gridlines": {"visible": False}})
    ch.set_size({"width": 440, "height": 250})
    seg.insert_chart(row, chart_anchor_col, ch)
    row += len(order) + 4

wb.close()
print("Wrote", OUT.relative_to(ROOT))
