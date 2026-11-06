"""Recalculate the headline KPIs from the raw file and compare them with the
cleaned dataset and with the figures quoted in the README.

Uses only the standard library for the raw-file calculation so it does not
share any code with the cleaning script.
Run from the repository root:  python src/validate_kpis.py
"""
import csv
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]

with open(ROOT / "data" / "raw" / "bank.csv", newline="", encoding="utf-8") as f:
    rows = list(csv.DictReader(f, delimiter=";"))

raw = {
    "records": len(rows),
    "subscribed": sum(r["y"] == "yes" for r in rows),
    "contacts": sum(int(r["campaign"]) for r in rows),
    "avg_age": sum(int(r["age"]) for r in rows) / len(rows),
}
raw["response_rate_pct"] = raw["subscribed"] / raw["records"] * 100
raw["contacts_per_sub"] = raw["contacts"] / raw["subscribed"]

clean = pd.read_csv(ROOT / "data" / "processed" / "bank_clean.csv")
cleaned = {
    "records": len(clean),
    "subscribed": int(clean["subscribed_flag"].sum()),
    "contacts": int(clean["campaign"].sum()),
    "avg_age": clean["age"].mean(),
    "response_rate_pct": clean["subscribed_flag"].mean() * 100,
}
cleaned["contacts_per_sub"] = cleaned["contacts"] / cleaned["subscribed"]

failures = []
for key, raw_value in raw.items():
    ok = abs(raw_value - cleaned[key]) < 1e-9
    print(f"{key:20s} raw={raw_value:<12.4f} clean={cleaned[key]:<12.4f} {'OK' if ok else 'MISMATCH'}")
    if not ok:
        failures.append(key)

# Figures quoted in the documentation must match the data
readme = (ROOT / "README.md").read_text(encoding="utf-8")
quoted = {
    "4,521": raw["records"], "12,630": raw["contacts"],
    "11.5%": round(raw["response_rate_pct"], 1), "24.2": round(raw["contacts_per_sub"], 1),
}
for text, value in quoted.items():
    found = text in readme
    if not found:
        failures.append(f"README missing {text}")
    print(f"README quotes {text:7s} (data value {value}) {'OK' if found else 'MISSING'}")

sys.exit(1 if failures else 0)
