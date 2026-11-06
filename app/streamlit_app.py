"""Interactive dashboard for the bank marketing campaign analysis.

Run from the repository root:  streamlit run app/streamlit_app.py
Reads data/processed/bank_clean.csv (created by src/01_clean_data.py).
"""
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "processed" / "bank_clean.csv"

NAVY, TEAL, GOLD, GREY, LIGHT = "#0B2545", "#1B7F8C", "#C9A227", "#8A94A6", "#DCE3EA"
MONTHS = ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]
AGE_ORDER = ["<25", "25-34", "35-44", "45-54", "55-64", "65+"]
BALANCE_ORDER = ["Negative", "Zero", "1-500", "501-1,500", "1,501-5,000", "5,000+"]
CAMPAIGN_ORDER = ["1", "2", "3", "4-5", "6+"]
EDU_ORDER = ["primary", "secondary", "tertiary", "unknown"]
POUTCOME_ORDER = ["success", "other", "failure", "unknown"]

st.set_page_config(page_title="Bank Marketing Campaign Analysis", layout="wide")

st.markdown(
    f"""
    <style>
    .block-container {{ padding-top: 3.2rem; max-width: 1300px; }}
    .app-header {{ background:{NAVY}; padding:18px 24px; border-radius:6px; margin-bottom:14px; }}
    .app-header h1 {{ color:white; font-size:1.6rem; margin:0; padding:0; }}
    .app-header p {{ color:#C8D3E0; margin:4px 0 0 0; font-size:0.9rem; }}
    .kpi {{ background:#F3F6F9; border:1px solid {LIGHT}; border-left:4px solid {GOLD};
            padding:12px 14px; border-radius:4px; height:100%; }}
    .kpi .label {{ color:{GREY}; font-size:0.72rem; font-weight:700; letter-spacing:0.04em; text-transform:uppercase; }}
    .kpi .value {{ color:{NAVY}; font-size:1.7rem; font-weight:700; line-height:1.3; }}
    .kpi .sub {{ color:{GREY}; font-size:0.75rem; }}
    h2, h3 {{ color:{NAVY}; }}
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data
def load_data():
    return pd.read_csv(DATA_PATH)


def wilson(successes, n, z=1.96):
    """95% Wilson interval for a proportion, as fractions."""
    p = successes / n
    centre = (p + z**2 / (2 * n)) / (1 + z**2 / n)
    half = z * np.sqrt(p * (1 - p) / n + z**2 / (4 * n**2)) / (1 + z**2 / n)
    return centre - half, centre + half


def segment_table(d, col, order=None):
    g = d.groupby(col, observed=True).agg(
        clients=("record_id", "count"),
        subscribers=("subscribed_flag", "sum"),
        contacts=("campaign", "sum"),
    )
    g = g[g["clients"] > 0]
    g["rate"] = g["subscribers"] / g["clients"] * 100
    bounds = [wilson(s, n) for s, n in zip(g["subscribers"], g["clients"])]
    g["ci_low"] = [b[0] * 100 for b in bounds]
    g["ci_high"] = [b[1] * 100 for b in bounds]
    if order:
        g = g.reindex([o for o in order if o in g.index])
    else:
        g = g.sort_values("rate", ascending=False)
    return g


def style_fig(fig, height=340, title=None):
    fig.update_layout(
        title=dict(text=title, x=0, font=dict(size=15, color=NAVY)) if title else None,
        height=height, margin=dict(l=10, r=10, t=45 if title else 15, b=10),
        paper_bgcolor="white", plot_bgcolor="white",
        font=dict(color="#333", size=12), showlegend=False,
    )
    fig.update_xaxes(showgrid=False, linecolor=LIGHT)
    fig.update_yaxes(gridcolor="#EEF1F5", zeroline=False)
    return fig


def rate_bar(g, title, benchmark, min_n, horizontal=False, height=340):
    """Bar chart of response rate; segments below min_n clients are grey."""
    colors = [TEAL if n >= min_n else GREY for n in g["clients"]]
    labels = [str(i) for i in g.index]
    hover = [
        f"<b>{lab}</b><br>Response rate: {r:.1f}%<br>95% interval: {lo:.1f}% to {hi:.1f}%"
        f"<br>Clients: {n:,}<br>Subscribers: {s:,}"
        for lab, r, lo, hi, n, s in zip(labels, g["rate"], g["ci_low"], g["ci_high"], g["clients"], g["subscribers"])
    ]
    text = [f"{r:.1f}%" for r in g["rate"]]
    if horizontal:
        fig = go.Figure(go.Bar(x=g["rate"], y=labels, orientation="h", marker_color=colors,
                               text=text, textposition="outside", hovertext=hover, hoverinfo="text"))
        fig.update_yaxes(autorange="reversed")
        fig.add_vline(x=benchmark, line_dash="dash", line_color=GOLD)
        fig.update_xaxes(visible=False, range=[0, max(g["rate"].max() * 1.2, benchmark * 1.2)])
    else:
        fig = go.Figure(go.Bar(x=labels, y=g["rate"], marker_color=colors, text=text,
                               textposition="outside", hovertext=hover, hoverinfo="text"))
        fig.add_hline(y=benchmark, line_dash="dash", line_color=GOLD)
        fig.update_yaxes(visible=False, range=[0, max(g["rate"].max() * 1.2, benchmark * 1.2)])
        fig.update_xaxes(type="category")
    return style_fig(fig, height, title)


def kpi(col, label, value, sub=""):
    col.markdown(
        f'<div class="kpi"><div class="label">{label}</div><div class="value">{value}</div>'
        f'<div class="sub">{sub}&nbsp;</div></div>',
        unsafe_allow_html=True,
    )


def pct(x, digits=1):
    return f"{x:.{digits}f}%"


# ---------------------------------------------------------------- data + filters
full = load_data()
overall_rate = full["subscribed_flag"].mean() * 100

st.sidebar.header("Filters")
st.sidebar.caption("Filters apply to the first three tabs. The Business Insights tab always uses the full sample.")


def multi(label, col, order=None):
    options = order or sorted(full[col].unique())
    return st.sidebar.multiselect(label, options, default=options)


f_age = multi("Age group", "age_group", AGE_ORDER)
f_job = multi("Job", "job")
f_edu = multi("Education", "education", EDU_ORDER)
f_contact = multi("Contact channel", "contact")
f_month = multi("Month", "month", MONTHS)
f_pout = multi("Previous outcome", "poutcome", POUTCOME_ORDER)
f_housing = multi("Housing loan", "housing")
f_loan = multi("Personal loan", "loan")
min_n = st.sidebar.slider("Grey out segments smaller than", 0, 300, 100, 10,
                          help="Segments below this many clients are drawn in grey because their rates are less reliable.")

df = full[
    full["age_group"].isin(f_age) & full["job"].isin(f_job) & full["education"].isin(f_edu)
    & full["contact"].isin(f_contact) & full["month"].isin(f_month) & full["poutcome"].isin(f_pout)
    & full["housing"].isin(f_housing) & full["loan"].isin(f_loan)
]

st.markdown(
    '<div class="app-header"><h1>Bank Marketing Campaign Performance</h1>'
    "<p>Phone campaign for term deposits at a Portuguese bank &nbsp;|&nbsp; 4,521-record random sample "
    "of the UCI Bank Marketing dataset (2008-2010) &nbsp;|&nbsp; descriptive analysis only</p></div>",
    unsafe_allow_html=True,
)

tab_exec, tab_cust, tab_camp, tab_ins = st.tabs(
    ["Executive Overview", "Customer Analytics", "Campaign Performance", "Business Insights"]
)

# ---------------------------------------------------------------- insights helpers
def rate_of(d):
    return d["subscribed_flag"].mean() * 100


if df.empty:
    for tab in (tab_exec, tab_cust, tab_camp):
        with tab:
            st.warning("No records match the current filters. Widen the selection in the sidebar.")
else:
    # ------------------------------------------------------------ Executive Overview
    with tab_exec:
        n_rec = len(df)
        n_yes = int(df["subscribed_flag"].sum())
        contacts = int(df["campaign"].sum())
        rate = n_yes / n_rec * 100
        c1, c2, c3, c4, c5 = st.columns(5)
        kpi(c1, "Campaign records", f"{n_rec:,}", f"{n_rec / len(full) * 100:.0f}% of full sample")
        kpi(c2, "Successful subscriptions", f"{n_yes:,}")
        diff = rate - overall_rate
        kpi(c3, "Response rate", pct(rate), f"{diff:+.1f} pts vs full sample ({pct(overall_rate)})")
        kpi(c4, "Total contact attempts", f"{contacts:,}")
        kpi(c5, "Contacts per subscription", f"{contacts / n_yes:.1f}" if n_yes else "n/a")

        if n_rec < 100:
            st.warning(f"Only {n_rec} records are selected, so rates below are not reliable.")

        left, right = st.columns([1, 2])
        with left:
            fig = go.Figure(go.Pie(labels=["Subscribed", "Did not subscribe"], values=[n_yes, n_rec - n_yes],
                                   hole=0.62, marker_colors=[TEAL, LIGHT], sort=False, textinfo="percent"))
            fig = style_fig(fig, 330, "Campaign response overview")
            fig.update_layout(showlegend=True, legend=dict(orientation="h", y=-0.05))
            st.plotly_chart(fig, width="stretch")
        with right:
            g = segment_table(df, "age_group", AGE_ORDER)
            st.plotly_chart(rate_bar(g, "Response rate by age group", overall_rate, min_n, height=330),
                            width="stretch")
        st.caption("Dashed gold line = response rate of the full sample. Grey bars have fewer clients than the "
                   "threshold set in the sidebar. Hover over a bar for client counts and the 95% interval.")

    # ------------------------------------------------------------ Customer Analytics
    with tab_cust:
        a, b = st.columns(2)
        with a:
            g = segment_table(df, "age_group", AGE_ORDER)
            st.plotly_chart(rate_bar(g, "Response rate by age group", overall_rate, min_n), width="stretch")
        with b:
            g = segment_table(df, "education", EDU_ORDER)
            st.plotly_chart(rate_bar(g, "Response rate by education level", overall_rate, min_n), width="stretch")

        g = segment_table(df, "job")
        st.plotly_chart(rate_bar(g, "Response rate by job category", overall_rate, min_n, horizontal=True, height=420),
                        width="stretch")

        st.subheader("Balance")
        a, b = st.columns(2)
        with a:
            g = segment_table(df, "balance_band", BALANCE_ORDER)
            st.plotly_chart(rate_bar(g, "Response rate by yearly balance (EUR)", overall_rate, min_n),
                            width="stretch")
        with b:
            lo, hi = -2000, 8000
            shown = df[df["balance"].between(lo, hi)]
            fig = go.Figure()
            for flag, name, color in [(0, "Did not subscribe", GREY), (1, "Subscribed", TEAL)]:
                sub = shown[shown["subscribed_flag"] == flag]
                if len(sub):
                    fig.add_trace(go.Histogram(x=sub["balance"], name=name, marker_color=color, opacity=0.75,
                                               xbins=dict(start=lo, end=hi, size=500), histnorm="percent"))
            fig = style_fig(fig, 340, "Balance distribution (% of each group)")
            fig.update_layout(barmode="overlay", showlegend=True, legend=dict(orientation="h", y=1.08, x=0.35))
            fig.update_xaxes(title="Average yearly balance (EUR)")
            st.plotly_chart(fig, width="stretch")
            outside = len(df) - len(shown)
            st.caption(f"Chart shows balances from {lo:,} to {hi:,} EUR; {outside} selected records outside this "
                       "range are left out of the histogram only (the maximum in the data is 71,188 EUR). "
                       "Each group is scaled to 100%, so the shapes can be compared directly.")

    # ------------------------------------------------------------ Campaign Performance
    with tab_camp:
        a, b = st.columns(2)
        with a:
            g = segment_table(df, "contact")
            g.index = [("unknown (not recorded)" if i == "unknown" else i) for i in g.index]
            st.plotly_chart(rate_bar(g, "Response rate by contact channel", overall_rate, min_n), width="stretch")
        with b:
            g = segment_table(df, "poutcome", POUTCOME_ORDER)
            st.plotly_chart(rate_bar(g, "Response rate by previous campaign outcome", overall_rate, min_n),
                            width="stretch")

        a, b = st.columns(2)
        with a:
            g = segment_table(df, "campaign_band", CAMPAIGN_ORDER)
            st.plotly_chart(rate_bar(g, "Response rate by contacts in this campaign", overall_rate, min_n),
                            width="stretch")
        with b:
            share = g.copy()
            share["pct_contacts"] = share["contacts"] / share["contacts"].sum() * 100
            share["pct_subs"] = share["subscribers"] / share["subscribers"].sum() * 100 if share["subscribers"].sum() else 0
            fig = go.Figure()
            fig.add_bar(x=list(share.index), y=share["pct_contacts"], name="% of contact attempts", marker_color=NAVY)
            fig.add_bar(x=list(share.index), y=share["pct_subs"], name="% of subscriptions", marker_color=GOLD)
            fig = style_fig(fig, 340, "Contact effort vs. results")
            fig.update_layout(barmode="group", showlegend=True, legend=dict(orientation="h", y=1.1, x=0.2))
            fig.update_yaxes(ticksuffix="%")
            fig.update_xaxes(type="category", title="Contacts made to the client in this campaign")
            st.plotly_chart(fig, width="stretch")

        g = segment_table(df, "month", MONTHS)
        fig = rate_bar(g, "Response rate by month (2008-2010 pooled)", overall_rate, min_n, height=360)
        fig.add_trace(go.Scatter(x=list(g.index), y=g["clients"], yaxis="y2", mode="lines+markers",
                                 name="Clients", line=dict(color=NAVY, width=1.5), marker=dict(size=5),
                                 hovertemplate="Clients: %{y:,}<extra></extra>"))
        fig.update_layout(yaxis2=dict(overlaying="y", side="right", showgrid=False, title="Clients (line)"))
        st.plotly_chart(fig, width="stretch")
        st.caption("The source data has a month and day but no year, so each month combines up to three years. "
                   "Small months can show very high rates; check the client counts (line) before reading anything into them.")

# ---------------------------------------------------------------- Business Insights
with tab_ins:
    d = full
    n, yes = len(d), int(d["subscribed_flag"].sum())
    contacts = int(d["campaign"].sum())

    ps = d[d["poutcome"] == "success"]
    new = d[d["previously_contacted"] == 0]
    prev = d[d["previously_contacted"] == 1]
    heavy = d[d["campaign"] >= 6]
    one = d[d["campaign"] == 1]
    unk = d[d["contact"] == "unknown"]
    known = d[d["contact"] != "unknown"]
    may, jun = d[d["month"] == "may"], d[d["month"] == "jun"]
    quiet = d[d["month"].isin(["mar", "sep", "oct", "dec"])]
    no_loans = d[(d["housing"] == "no") & (d["loan"] == "no")]
    seg = (d["housing"] == "no") & (d["loan"] == "no") & (d["balance"] > 0)
    mid_age = d[d["age"].between(35, 54)]
    over65 = d[d["age"] >= 65]
    retired = d[d["job"] == "retired"]
    blue = d[d["job"] == "blue-collar"]
    tert, prim = d[d["education"] == "tertiary"], d[d["education"] == "primary"]
    corr_dur = d["duration"].corr(d["subscribed_flag"])

    def sub(x): return int(x["subscribed_flag"].sum())

    st.markdown(
        f"**Baseline:** {sub(d):,} of {n:,} clients subscribed ({pct(rate_of(d), 2)}), using {contacts:,} contact "
        f"attempts, or {contacts / yes:.1f} per subscription. Figures on this tab are calculated from the full "
        "sample and do not change with the sidebar filters. They describe what happened; they do not show what "
        "would happen if the bank changed who it calls."
    )

    insights = [
        (
            "1. A successful previous campaign is the strongest signal",
            f"{sub(ps)} of {len(ps)} clients with a previous 'success' subscribed again ({pct(rate_of(ps))}), versus "
            f"{pct(rate_of(new))} for clients never contacted before ({sub(new)} of {len(new):,}). That group is "
            f"{len(ps) / n * 100:.1f}% of records but {sub(ps) / yes * 100:.1f}% of subscriptions. Any previously "
            f"contacted client converted at {pct(rate_of(prev))}.",
            "Call previously contacted clients, especially previous successes, before working through cold lists.",
            f"Only {len(ps)} records in the success group. These clients were already engaged, so the gap reflects who "
            "they are as well as the earlier contact.",
        ),
        (
            "2. Heavy repeat contact used a large share of effort for few subscriptions",
            f"Clients contacted 6+ times are {len(heavy)} records ({len(heavy) / n * 100:.1f}%), took "
            f"{heavy['campaign'].sum() / contacts * 100:.1f}% of all contact attempts and produced "
            f"{sub(heavy) / yes * 100:.1f}% of subscriptions. Their response rate is {pct(rate_of(heavy))} against "
            f"{pct(rate_of(one))} for clients contacted once.",
            "Pilot a cap of about five attempts per client and move call time to higher-response segments.",
            "Partly built into the variable: clients who agree early stop being called. The data cannot show whether "
            "a sixth call changes anyone's mind.",
        ),
        (
            "3. Records with an unrecorded contact channel convert far less",
            f"Contact = unknown: {pct(rate_of(unk))} ({len(unk):,} records) versus {pct(rate_of(known))} for recorded "
            f"channels. In May: {pct(rate_of(may[may['contact'] == 'unknown']))} vs "
            f"{pct(rate_of(may[may['contact'] != 'unknown']))}. In June: "
            f"{pct(rate_of(jun[jun['contact'] == 'unknown']))} vs {pct(rate_of(jun[jun['contact'] != 'unknown']))} "
            f"(only {len(jun[jun['contact'] != 'unknown'])} June records have a known channel).",
            "Find out what 'unknown' represents (a list, dialler or team) and make channel a required field.",
            "The file does not say what 'unknown' means, and it is concentrated in May and June, so channel and "
            "month are tangled together.",
        ),
        (
            "4. May has the most volume and the lowest response rate",
            f"May: {len(may):,} records ({len(may) / n * 100:.1f}% of the sample), {pct(rate_of(may))} response, "
            f"{sub(may) / yes * 100:.1f}% of subscriptions. March, September, October and December together have "
            f"{len(quiet)} records and {sub(quiet)} subscriptions ({pct(rate_of(quiet))}).",
            "Compare the client lists used in May with other months before treating this as seasonality.",
            "No year in the data, so 2008-2010 are pooled. The high-rate months are small (20 to 80 records each) "
            "and may reflect a targeted list.",
        ),
        (
            "5. Clients without loans respond about twice as often",
            f"No housing loan and no personal loan: {pct(rate_of(no_loans))} ({len(no_loans):,} clients). "
            f"'No loans and balance above zero': {pct(rate_of(d[seg]))} ({len(d[seg]):,}) versus "
            f"{pct(rate_of(d[~seg]))} for everyone else. Among clients aged 35-54, "
            f"{pct(rate_of(mid_age[mid_age['housing'] == 'no']))} without a housing loan subscribed versus "
            f"{pct(rate_of(mid_age[mid_age['housing'] == 'yes']))} with one.",
            "Use loan status and a positive balance as a first filter for call lists, and test it against a random "
            "control group.",
            "The reason is not in the data. The segment was defined after looking at the data, so expect it to look "
            "somewhat weaker on a new sample.",
        ),
        (
            "6. Retirees and the oldest clients respond most, but the groups are small",
            f"Retired: {pct(rate_of(retired))} ({len(retired)} clients). Age 65+: {pct(rate_of(over65))} "
            f"({len(over65)} clients). Blue-collar: {pct(rate_of(blue))} ({len(blue)}). Tertiary education: "
            f"{pct(rate_of(tert))} vs primary: {pct(rate_of(prim))}.",
            "Pilot a retiree-focused offer or script, and review whether the term-deposit pitch fits blue-collar "
            "clients with primary education (lowest combination in the data).",
            "Wide uncertainty for small groups (see the 95% interval in the chart hover). Age, job and education "
            "overlap, so these are not independent effects.",
        ),
        (
            "7. Call length tracks the outcome but cannot be used for targeting",
            f"Subscribers averaged {d[d['subscribed_flag'] == 1]['duration'].mean():.0f} seconds per call versus "
            f"{d[d['subscribed_flag'] == 0]['duration'].mean():.0f} for non-subscribers (correlation with the "
            f"outcome {corr_dur:.2f}).",
            "Do not use duration in call prioritisation. It is better suited to call-quality review.",
            "Duration is only known after the call, and calls run long when the client is interested, so the direction "
            "of cause is unclear.",
        ),
    ]
    for title, evidence, rec, limit in insights:
        with st.expander(title, expanded=False):
            st.markdown(f"**Evidence.** {evidence}")
            st.markdown(f"**Recommendation.** {rec}")
            st.markdown(f"**Limitation.** {limit}")

    st.subheader("Limitations of the analysis")
    st.markdown(
        "- The data is a 10% random sample of the full UCI file, so several segments are small.\n"
        "- There is no year, cost, revenue or deposit amount. The results are response rates, not profitability.\n"
        "- The bank chose whom to call, so segment differences are observational and not causal.\n"
        "- `contact = unknown` is a recording gap, not a real channel."
    )
    st.caption("Source: Moro, Laureano and Cortez (2011), UCI Bank Marketing dataset.")
