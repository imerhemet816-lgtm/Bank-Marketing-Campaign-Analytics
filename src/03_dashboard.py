"""Build the one-page dashboard image and individual chart files.

Run after 01_clean_data.py:  python src/03_dashboard.py
All numbers are computed from data/processed/bank_clean.csv.
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
df = pd.read_csv(ROOT / "data" / "processed" / "bank_clean.csv")
CHARTS = ROOT / "outputs" / "charts"
CHARTS.mkdir(parents=True, exist_ok=True)

NAVY, TEAL, GOLD, GREY, LIGHT, RED = "#0B2545", "#1B7F8C", "#C9A227", "#8A94A6", "#DCE3EA", "#B5483A"
MONTHS = ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]
overall = df["subscribed_flag"].mean() * 100

plt.rcParams.update({
    "font.family": "DejaVu Sans", "axes.spines.top": False, "axes.spines.right": False,
    "axes.edgecolor": LIGHT, "axes.titleweight": "bold", "axes.titlesize": 12,
    "axes.titlecolor": NAVY, "xtick.color": "#333", "ytick.color": "#333",
})


def rate_table(col, order=None):
    g = df.groupby(col).agg(n=("record_id", "count"), yes=("subscribed_flag", "sum"))
    g["rate"] = g["yes"] / g["n"] * 100
    return g.reindex(order) if order else g.sort_values("rate", ascending=False)


def bar_rates(ax, g, title, horizontal=False, min_n=100):
    """Bars coloured teal; segments with fewer than min_n records are greyed out."""
    colors = [TEAL if n >= min_n else GREY for n in g["n"]]
    labels = [str(i) for i in g.index]
    if horizontal:
        g = g.iloc[::-1]; colors = colors[::-1]; labels = labels[::-1]
        ax.barh(labels, g["rate"], color=colors)
        for y, (r, n) in enumerate(zip(g["rate"], g["n"])):
            ax.text(r + 0.4, y, f"{r:.1f}%  (n={n:,})", va="center", fontsize=8)
        ax.set_xlim(0, g["rate"].max() * 1.45)
        ax.xaxis.set_visible(False)
        ax.axvline(overall, color=GOLD, ls="--", lw=1.2)
    else:
        ax.bar(range(len(labels)), g["rate"], color=colors)
        ax.set_xticks(range(len(labels)))
        ax.set_xticklabels([f"{l}\nn={n:,}" for l, n in zip(labels, g["n"])], fontsize=8 if len(labels) < 8 else 6.5)
        for x, r in enumerate(g["rate"]):
            ax.text(x, r + 0.8, f"{r:.1f}%", ha="center", fontsize=8.5, fontweight="bold")
        ax.set_ylim(0, g["rate"].max() * 1.2)
        ax.yaxis.set_visible(False)
        ax.spines["left"].set_visible(False)
        ax.axhline(overall, color=GOLD, ls="--", lw=1.2)
    ax.set_title(title, loc="left")


def donut(ax):
    yes = int(df["subscribed_flag"].sum()); no = len(df) - yes
    ax.pie([yes, no], colors=[TEAL, LIGHT], startangle=90, counterclock=False,
           wedgeprops=dict(width=0.35, edgecolor="white"))
    ax.text(0, 0.05, f"{overall:.1f}%", ha="center", va="center", fontsize=22, fontweight="bold", color=NAVY)
    ax.text(0, -0.22, "subscribed", ha="center", fontsize=9, color=GREY)
    ax.set_title("Campaign response overview", loc="left")
    ax.text(0, -1.3, f"{yes:,} yes  |  {no:,} no", ha="center", fontsize=9)


def effort_chart(ax):
    g = df.groupby("campaign_band").agg(contacts=("campaign", "sum"), subs=("subscribed_flag", "sum"))
    order = ["1", "2", "3", "4-5", "6+"]
    g = g.reindex(order)
    share_contacts = g["contacts"] / g["contacts"].sum() * 100
    share_subs = g["subs"] / g["subs"].sum() * 100
    x = range(len(order)); w = 0.38
    ax.bar([i - w / 2 for i in x], share_contacts, w, color=NAVY, label="% of all contacts")
    ax.bar([i + w / 2 for i in x], share_subs, w, color=GOLD, label="% of subscriptions")
    ax.set_xticks(list(x)); ax.set_xticklabels(order)
    ax.set_xlabel("Contacts made to the client in this campaign", fontsize=8)
    ax.yaxis.set_visible(False); ax.spines["left"].set_visible(False)
    for i, (a, b) in enumerate(zip(share_contacts, share_subs)):
        ax.text(i - w / 2, a + 0.8, f"{a:.0f}%", ha="center", fontsize=8)
        ax.text(i + w / 2, b + 0.8, f"{b:.0f}%", ha="center", fontsize=8)
    ax.legend(frameon=False, fontsize=8, loc="upper center")
    ax.set_title("Contact effort vs. results", loc="left")


def build_panels(axes_by_name):
    donut(axes_by_name["overview"])
    bar_rates(axes_by_name["age"], rate_table("age_group", ["<25", "25-34", "35-44", "45-54", "55-64", "65+"]),
              "Response rate by age group")
    bar_rates(axes_by_name["job"], rate_table("job"), "Response rate by job category", horizontal=True)
    contact = rate_table("contact").rename(index={"unknown": "unknown (not recorded)"})
    bar_rates(axes_by_name["contact"], contact, "Response rate by contact channel")
    bar_rates(axes_by_name["month"], rate_table("month", MONTHS), "Response rate by month (2008-2010 combined)", min_n=100)
    bar_rates(axes_by_name["poutcome"], rate_table("poutcome", ["success", "other", "failure", "unknown"]),
              "Response rate by previous campaign outcome")
    effort_chart(axes_by_name["effort"])


def main():
    # Individual chart files (one panel each)
    names = ["overview", "age", "job", "contact", "month", "poutcome", "effort", "balance"]
    for name in names:
        fig, ax = plt.subplots(figsize=(7.5, 4.4), dpi=130)
        dispatch = {
            "overview": donut, "effort": effort_chart,
        }
        if name in dispatch:
            dispatch[name](ax)
        else:
            specs = {
                "age": (rate_table("age_group", ["<25", "25-34", "35-44", "45-54", "55-64", "65+"]), "Response rate by age group", False, 100),
                "job": (rate_table("job"), "Response rate by job category", True, 100),
                "contact": (rate_table("contact"), "Response rate by contact channel", False, 100),
                "month": (rate_table("month", MONTHS), "Response rate by month (2008-2010 combined)", False, 100),
                "poutcome": (rate_table("poutcome", ["success", "other", "failure", "unknown"]), "Response rate by previous campaign outcome", False, 100),
                "balance": (rate_table("balance_band", ["Negative", "Zero", "1-500", "501-1,500", "1,501-5,000", "5,000+"]), "Response rate by yearly balance (EUR)", False, 100),
            }
            g, title, horiz, min_n = specs[name]
            bar_rates(ax, g, title, horizontal=horiz, min_n=min_n)
        fig.tight_layout()
        fig.savefig(CHARTS / f"{name}.png")
        plt.close(fig)

    # One-page dashboard
    fig = plt.figure(figsize=(24, 14), dpi=100, facecolor="white")
    fig.patches.append(plt.Rectangle((0, 0.925), 1, 0.075, transform=fig.transFigure, color=NAVY))
    fig.text(0.025, 0.962, "Bank Marketing Campaign Performance", color="white", fontsize=22, fontweight="bold", va="center")
    fig.text(0.025, 0.937, "Portuguese bank, phone campaign for term deposits  |  4,521-record random sample (bank.csv)",
             color="#C8D3E0", fontsize=11, va="center")

    kpis = [
        ("Campaign records", f"{len(df):,}"),
        ("Subscribed", f"{int(df['subscribed_flag'].sum()):,}"),
        ("Response rate", f"{overall:.1f}%"),
        ("Total contacts made", f"{int(df['campaign'].sum()):,}"),
        ("Avg. customer age", f"{df['age'].mean():.1f}"),
        ("Contacts per subscription", f"{df['campaign'].sum() / df['subscribed_flag'].sum():.1f}"),
    ]
    for i, (label, value) in enumerate(kpis):
        x0 = 0.025 + i * 0.1605
        fig.patches.append(plt.Rectangle((x0, 0.835), 0.15, 0.075, transform=fig.transFigure,
                                         facecolor="#F3F6F9", edgecolor=LIGHT))
        fig.patches.append(plt.Rectangle((x0, 0.835), 0.004, 0.075, transform=fig.transFigure, color=GOLD))
        fig.text(x0 + 0.014, 0.887, label.upper(), fontsize=8.5, color=GREY, fontweight="bold")
        fig.text(x0 + 0.014, 0.850, value, fontsize=21, color=NAVY, fontweight="bold")

    gs = fig.add_gridspec(2, 4, left=0.04, right=0.985, top=0.80, bottom=0.075, hspace=0.34, wspace=0.18)
    axes = {
        "overview": fig.add_subplot(gs[0, 0]), "age": fig.add_subplot(gs[0, 1]),
        "job": fig.add_subplot(gs[0, 2:4]),
        "contact": fig.add_subplot(gs[1, 0]), "month": fig.add_subplot(gs[1, 1]),
        "poutcome": fig.add_subplot(gs[1, 2]), "effort": fig.add_subplot(gs[1, 3]),
    }
    build_panels(axes)
    fig.text(0.025, 0.028,
             f"Dashed gold line = overall response rate ({overall:.1f}%). Grey bars = fewer than 100 records, treat with caution. "
             "Month has no year in the source data, so 2008-2010 are combined.\n"
             "Source: Moro, Laureano & Cortez (2011), UCI Bank Marketing dataset. Descriptive results only; differences between segments are not causal.",
             fontsize=9, color=GREY, va="center")
    fig.savefig(CHARTS / "dashboard.png")
    plt.close(fig)
    print("Saved charts to", CHARTS.relative_to(ROOT))


if __name__ == "__main__":
    main()
