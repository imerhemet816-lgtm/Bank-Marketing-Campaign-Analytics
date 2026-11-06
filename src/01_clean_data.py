"""Load the raw bank marketing file, check quality, and write a cleaned CSV.

Run from the repository root:  python src/01_clean_data.py
"""
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW_PATH = ROOT / "data" / "raw" / "bank.csv"
CLEAN_PATH = ROOT / "data" / "processed" / "bank_clean.csv"

MONTHS = ["jan", "feb", "mar", "apr", "may", "jun",
          "jul", "aug", "sep", "oct", "nov", "dec"]


def main():
    # The file is semicolon-separated with quoted text fields
    df = pd.read_csv(RAW_PATH, sep=";")
    print(f"Raw shape: {df.shape}")

    # Quality checks (reported, not silently fixed)
    print("Missing values:", int(df.isna().sum().sum()))
    print("Exact duplicate rows:", int(df.duplicated().sum()))

    text_cols = df.select_dtypes(include=["object", "string"]).columns
    for col in text_cols:
        df[col] = df[col].str.strip().str.lower()

    # `default` is a reserved word in SQL and `y` says nothing, so rename
    df = df.rename(columns={"default": "credit_default", "y": "subscribed"})

    df["subscribed_flag"] = (df["subscribed"] == "yes").astype(int)

    # pdays = -1 means "never contacted before". Averaging it with real day
    # counts would be wrong, so the cleaned column is NaN for those clients.
    df["previously_contacted"] = (df["pdays"] != -1).astype(int)
    df["days_since_prev_contact"] = df["pdays"].where(df["pdays"] != -1)

    df["age_group"] = pd.cut(
        df["age"], bins=[0, 24, 34, 44, 54, 64, 120],
        labels=["<25", "25-34", "35-44", "45-54", "55-64", "65+"],
    ).astype(str)
    df["balance_band"] = pd.cut(
        df["balance"], bins=[-np.inf, -1, 0, 500, 1500, 5000, np.inf],
        labels=["Negative", "Zero", "1-500", "501-1,500", "1,501-5,000", "5,000+"],
    ).astype(str)
    df["campaign_band"] = pd.cut(
        df["campaign"], bins=[0, 1, 2, 3, 5, np.inf],
        labels=["1", "2", "3", "4-5", "6+"],
    ).astype(str)
    df["month_num"] = df["month"].map({m: i + 1 for i, m in enumerate(MONTHS)})

    # Validation: stop if something unexpected appears
    assert df["month_num"].notna().all(), "Unexpected month value"
    assert df["age"].between(18, 100).all(), "Age outside 18-100"
    assert df["duration"].ge(0).all()
    assert set(df["subscribed"]) == {"yes", "no"}
    never = df["previously_contacted"] == 0
    assert (df.loc[never, "previous"] == 0).all()

    df.insert(0, "record_id", np.arange(1, len(df) + 1))
    df.to_csv(CLEAN_PATH, index=False)
    print(f"Cleaned shape: {df.shape} -> {CLEAN_PATH.relative_to(ROOT)}")
    print("Negative balances kept:", int((df["balance"] < 0).sum()))
    print("'unknown' kept as category - job:", int((df["job"] == "unknown").sum()),
          "| education:", int((df["education"] == "unknown").sum()),
          "| contact:", int((df["contact"] == "unknown").sum()))


if __name__ == "__main__":
    main()
