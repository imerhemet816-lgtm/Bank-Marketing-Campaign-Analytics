"""Segment-level response rates from the cleaned dataset.

Writes one CSV per breakdown to outputs/tables/ and prints a summary.
Run after 01_clean_data.py:  python src/02_eda.py
"""
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
df = pd.read_csv(ROOT / "data" / "processed" / "bank_clean.csv")
TABLES = ROOT / "outputs" / "tables"
TABLES.mkdir(parents=True, exist_ok=True)

MONTH_ORDER = ["jan", "feb", "mar", "apr", "may", "jun",
               "jul", "aug", "sep", "oct", "nov", "dec"]


def wilson_interval(successes, n, z=1.96):
    """95% Wilson interval for a proportion (better than normal approx for small n)."""
    p = successes / n
    centre = (p + z**2 / (2 * n)) / (1 + z**2 / n)
    half = z * np.sqrt(p * (1 - p) / n + z**2 / (4 * n**2)) / (1 + z**2 / n)
    return centre - half, centre + half


def response_by(col, order=None):
    g = df.groupby(col).agg(
        customers=("record_id", "count"),
        subscribers=("subscribed_flag", "sum"),
        avg_contacts=("campaign", "mean"),
    )
    g["response_rate_pct"] = (g["subscribers"] / g["customers"] * 100).round(2)
    ci = [wilson_interval(s, n) for s, n in zip(g["subscribers"], g["customers"])]
    g["ci_low_pct"] = [round(c[0] * 100, 1) for c in ci]
    g["ci_high_pct"] = [round(c[1] * 100, 1) for c in ci]
    g["avg_contacts"] = g["avg_contacts"].round(2)
    if order is not None:
        g = g.reindex(order)
    else:
        g = g.sort_values("response_rate_pct", ascending=False)
    g.to_csv(TABLES / f"response_by_{col}.csv")
    return g


def main():
    total = len(df)
    yes = int(df["subscribed_flag"].sum())
    lo, hi = wilson_interval(yes, total)
    print(f"Records: {total} | Subscribed: {yes} | Rate: {yes/total*100:.2f}% "
          f"(95% CI {lo*100:.1f}-{hi*100:.1f}%)")
    print(f"Total contacts this campaign: {int(df['campaign'].sum())} | "
          f"Avg age: {df['age'].mean():.1f} | Median balance: {df['balance'].median():.0f}")
    print(f"Contacts per subscription: {df['campaign'].sum()/yes:.1f}")

    breakdowns = {
        "age_group": ["<25", "25-34", "35-44", "45-54", "55-64", "65+"],
        "job": None, "education": None, "marital": None,
        "contact": None, "poutcome": None,
        "campaign_band": ["1", "2", "3", "4-5", "6+"],
        "balance_band": ["Negative", "Zero", "1-500", "501-1,500", "1,501-5,000", "5,000+"],
        "month": MONTH_ORDER, "housing": None, "loan": None,
        "credit_default": None, "previously_contacted": None,
    }
    for col, order in breakdowns.items():
        print(f"\n--- {col} ---")
        print(response_by(col, order).to_string())

    # Duration is only known after the call ends, so it is described but not
    # treated as a targeting variable.
    print("\n--- duration (seconds) ---")
    print(df.groupby("subscribed")["duration"].describe().round(1).to_string())

    # Job x education combos with enough volume to compare
    combo = response_by_combo()
    print("\n--- Top/bottom job x education (n >= 100) ---")
    print(combo.head(5).to_string()); print(combo.tail(3).to_string())

    # Correlation of numeric fields with the outcome (descriptive only)
    num = ["age", "balance", "day", "duration", "campaign", "pdays", "previous"]
    corr = df[num + ["subscribed_flag"]].corr()["subscribed_flag"].drop("subscribed_flag")
    corr.round(3).to_csv(TABLES / "numeric_correlation_with_outcome.csv")
    print("\n--- correlation with subscribed_flag ---")
    print(corr.round(3).to_string())


def response_by_combo():
    g = df.groupby(["job", "education"]).agg(
        customers=("record_id", "count"), subscribers=("subscribed_flag", "sum"))
    g = g[g["customers"] >= 100].copy()
    g["response_rate_pct"] = (g["subscribers"] / g["customers"] * 100).round(2)
    g = g.sort_values("response_rate_pct", ascending=False)
    g.to_csv(TABLES / "response_by_job_education.csv")
    return g


if __name__ == "__main__":
    main()
