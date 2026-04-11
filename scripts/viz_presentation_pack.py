#!/usr/bin/env python3
"""
Presentation Pack - Main Deck (Part 1)
========================================
Curated, presentation-ready figures for an 8-12 minute capstone talk on
life-stage migration patterns. Main deck only: 10 polished figures.

Usage:
    python -m scripts.viz_presentation_pack
"""

from pathlib import Path
import numpy as np
import pandas as pd
from scipy import stats
import statsmodels.api as sm
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# --- Paths --------------------------------------------------------------
PROJECT = Path(__file__).resolve().parent.parent
DATA = PROJECT / "data_processed" / "analysis_ready_specialization.csv"
FIG_DIR = PROJECT / "outputs" / "figures" / "presentation_pack"
FIG_DIR.mkdir(parents=True, exist_ok=True)

# --- Design tokens ------------------------------------------------------
FONT = "system-ui, -apple-system, 'Segoe UI', sans-serif"

AGES = ["18_24", "25_34", "35_54", "55_64", "65_PLUS"]
AGE_LBL = {"18_24": "18-24", "25_34": "25-34", "35_54": "35-54",
           "55_64": "55-64", "65_PLUS": "65+"}
AGE_NAME = {"18_24": "College-Age", "25_34": "Young Professionals",
            "35_54": "Mid-Career", "55_64": "Pre-Retirees",
            "65_PLUS": "Retirees"}
AGE_CLR = {"18_24": "#e67e22", "25_34": "#2980b9", "35_54": "#27ae60",
           "55_64": "#8e44ad", "65_PLUS": "#c0392b"}

IV_LABELS = {
    "POP": "State Population Size",
    "LAND_AREA": "State Land Area",
    "POP_DENS": "Population Density",
    "GDP": "State Economic Size (GDP)",
    "RPP": "Cost of Living Level",
    "REAL_PCPI": "Real Income per Person",
    "UNEMP": "Unemployment Rate",
    "PRIV_EMP": "Private-Sector Employment",
    "PRIV_ESTAB": "Number of Private Businesses",
    "PRIV_AVG_PAY": "Average Private-Sector Pay",
    "PERMITS": "New Housing Permits",
    "MED_RENT": "Median Rent",
    "MED_HOMEVAL": "Median Home Price",
    "COST_BURDEN_ALL": "Households Under Housing Cost Pressure",
    "VACANCY_RATE": "Rental Vacancy Rate",
    "COMMUTE_MED": "Median Commute Time",
    "TRANSIT_SHARE": "Public Transit Commuting Share",
    "BA_PLUS": "College-Educated Share",
    "UNINSURED": "Uninsured Share",
    "ELEC_PRICE_TOT": "Average Electricity Price",
    "CRIME_VIOLENT_RATE": "Violent Crime Rate",
    "NRI_RISK_INDEX": "Overall Natural Disaster Risk",
}

DIV_ONE = [[0.0, "#d95f02"], [0.25, "#fdb863"], [0.5, "#f7f7f7"],
           [0.75, "#80cdc1"], [1.0, "#1b7837"]]

LOCAL = {"WI", "MN"}

FIPS_TO_ABBREV = {
    "01": "AL", "02": "AK", "04": "AZ", "05": "AR", "06": "CA",
    "08": "CO", "09": "CT", "10": "DE", "12": "FL", "13": "GA",
    "15": "HI", "16": "ID", "17": "IL", "18": "IN", "19": "IA",
    "20": "KS", "21": "KY", "22": "LA", "23": "ME", "24": "MD",
    "25": "MA", "26": "MI", "27": "MN", "28": "MS", "29": "MO",
    "30": "MT", "31": "NE", "32": "NV", "33": "NH", "34": "NJ",
    "35": "NM", "36": "NY", "37": "NC", "38": "ND", "39": "OH",
    "40": "OK", "41": "OR", "42": "PA", "44": "RI", "45": "SC",
    "46": "SD", "47": "TN", "48": "TX", "49": "UT", "50": "VT",
    "51": "VA", "53": "WA", "54": "WV", "55": "WI", "56": "WY",
}

# --- Helpers ------------------------------------------------------------

def load():
    df = pd.read_csv(DATA, dtype={"state": str})
    df["state"] = df["state"].str.zfill(2)
    if "abbrev" not in df.columns:
        df["abbrev"] = df["state"].map(FIPS_TO_ABBREV)
    return df


def save(fig, name):
    fig.write_html(str(FIG_DIR / name), include_plotlyjs="cdn")


def title(text, sub=""):
    if sub:
        return (f"<b>{text}</b><br>"
                f"<span style='font-size:13px;color:#7f8c8d;font-weight:400'>{sub}</span>")
    return f"<b>{text}</b>"


def base_layout(fig, ttl, sub="", w=900, h=550, foot=""):
    anns = list(fig.layout.annotations or [])
    if foot:
        anns.append(dict(
            text=foot, xref="paper", yref="paper", x=0, y=-0.17,
            showarrow=False, xanchor="left",
            font=dict(size=9, color="#bdc3c7", family=FONT),
        ))
    fig.update_layout(
        title=dict(
            text=title(ttl, sub),
            font=dict(size=19, family=FONT, color="#2c3e50"),
            x=0.5, xanchor="center", y=0.96,
        ),
        width=w, height=h,
        plot_bgcolor="#fafafa", paper_bgcolor="#ffffff",
        font=dict(family=FONT, color="#2c3e50", size=12),
        margin=dict(l=70, r=50, t=110, b=80),
        annotations=anns,
    )


def ols_fit(x, y):
    X = sm.add_constant(x)
    m = sm.OLS(y, X).fit()
    xp = np.linspace(np.nanmin(x), np.nanmax(x), 100)
    pred = m.get_prediction(sm.add_constant(xp))
    return xp, pred.predicted_mean, pred.conf_int(alpha=0.05), m


# ========================================================================
# P01 - Raw Share Intro
# ========================================================================
def p01_volume(df):
    col = "IN_SHARE_ALL_AGES"
    top = df.nlargest(15, col).sort_values(col)
    clr = ["#d35400" if a in LOCAL else "#3498db" for a in top["abbrev"]]
    fig = go.Figure(go.Bar(
        x=top[col] * 100, y=top["state_name"], orientation="h",
        marker_color=clr,
        text=[f"{v:.1f}%" for v in top[col] * 100],
        textposition="outside", textfont=dict(size=11, color="#2c3e50"),
        hovertemplate="<b>%{y}</b><br>Share: %{x:.1f}%<extra></extra>",
    ))
    base_layout(fig,
                "Large States Dominate U.S. Migration Volume",
                "Top 15 states by share of all interstate moves (all ages combined)",
                w=870, h=560,
                foot="Source: 2024 ACS state-to-state migration flows - 50 states")
    fig.update_xaxes(title="Share of National Interstate Inflow (%)",
                     showgrid=True, gridcolor="#ecf0f1", zeroline=False,
                     range=[0, top[col].max() * 100 * 1.15])
    fig.update_yaxes(title="", showgrid=False)
    save(fig, "P01_volume_leaders.html")
    print("  [1/10] P01 volume leaders")


# ========================================================================
# P02 - Specialization Concept
# ========================================================================
def p02_concept(df):
    """Paired ranking: volume vs 25-34 concentration."""
    fig = make_subplots(
        1, 2, horizontal_spacing=0.22,
        subplot_titles=[
            "<b>Top 10 by Volume</b>",
            "<b>Top 10 by 25-34 Concentration</b>",
        ],
    )
    vol = df.nlargest(10, "IN_SHARE_ALL_AGES").sort_values("IN_SHARE_ALL_AGES")
    fig.add_trace(go.Bar(
        x=vol["IN_SHARE_ALL_AGES"] * 100, y=vol["state_name"],
        orientation="h", marker_color="#95a5a6", showlegend=False,
        text=[f"{v:.1f}%" for v in vol["IN_SHARE_ALL_AGES"] * 100],
        textposition="outside", textfont=dict(size=11),
    ), 1, 1)

    spec = df.nlargest(10, "REL_IN_25_34").sort_values("REL_IN_25_34")
    fig.add_trace(go.Bar(
        x=spec["REL_IN_25_34"], y=spec["state_name"],
        orientation="h", marker_color="#2980b9", showlegend=False,
        text=[f"{v:.2f}" for v in spec["REL_IN_25_34"]],
        textposition="outside", textfont=dict(size=11),
    ), 1, 2)
    fig.add_vline(x=1.0, row=1, col=2, line_dash="dot",
                  line_color="#e74c3c", line_width=1.5)

    base_layout(fig,
                "Volume and Concentration Tell Different Stories",
                "The biggest migration destinations are not the most concentrated for 25-34 movers",
                w=1050, h=520,
                foot="Concentration = age-specific inflow share divided by all-ages inflow share. "
                     "Ratio > 1 = state attracts more 25-34 movers than its overall size would predict.")
    fig.update_xaxes(title="Inflow Share (%)", row=1, col=1,
                     showgrid=True, gridcolor="#ecf0f1")
    fig.update_xaxes(title="Concentration Ratio", row=1, col=2,
                     showgrid=True, gridcolor="#ecf0f1")
    fig.update_yaxes(showgrid=False)
    save(fig, "P02_concept_volume_vs_concentration.html")
    print("  [2/10] P02 concept")


# ========================================================================
# P03 - Life-Course Signatures (full 5-age overview)
# ========================================================================
def p03_lifecourse(df):
    """Lines showing how 7 states fare across all 5 age groups."""
    states = ["FL", "ND", "NY", "TX", "NV", "WI", "MN"]
    palette = {
        "FL": "#d62728", "ND": "#1f77b4", "NY": "#2ca02c",
        "TX": "#ff7f0e", "NV": "#9467bd",
        "WI": "#17becf", "MN": "#e377c2",
    }
    xlbl = [AGE_LBL[a] for a in AGES]

    fig = go.Figure()
    fig.add_hline(y=1.0, line_dash="dot", line_color="#bdc3c7", line_width=1.5)

    for st in states:
        row = df[df["abbrev"] == st].iloc[0]
        yv = [row[f"REL_IN_{a}"] for a in AGES]
        is_local = st in LOCAL
        fig.add_trace(go.Scatter(
            x=xlbl, y=yv, mode="lines+markers",
            name=f"{row['state_name']} ({st})",
            line=dict(color=palette[st], width=3.5 if is_local else 2.5,
                      dash="solid"),
            marker=dict(size=11 if is_local else 9,
                        line=dict(color="white", width=1.5)),
            hovertemplate=f"<b>{row['state_name']}</b><br>%{{x}}: %{{y:.2f}}<extra></extra>",
        ))

    # Key point annotations
    fl = df[df["abbrev"] == "FL"].iloc[0]
    nd = df[df["abbrev"] == "ND"].iloc[0]
    ny = df[df["abbrev"] == "NY"].iloc[0]
    fig.add_annotation(x=xlbl[4], y=fl["REL_IN_65_PLUS"],
                       text="FL: 1.83<br>(retirees)",
                       showarrow=True, arrowhead=2, ax=-40, ay=-30,
                       font=dict(size=10, color="#d62728"),
                       bgcolor="rgba(255,255,255,0.85)",
                       bordercolor="#d62728", borderwidth=1)
    fig.add_annotation(x=xlbl[0], y=nd["REL_IN_18_24"],
                       text="ND: 1.60<br>(college-age)",
                       showarrow=True, arrowhead=2, ax=40, ay=-30,
                       font=dict(size=10, color="#1f77b4"),
                       bgcolor="rgba(255,255,255,0.85)",
                       bordercolor="#1f77b4", borderwidth=1)
    fig.add_annotation(x=xlbl[1], y=ny["REL_IN_25_34"],
                       text="NY: 1.27<br>(young pros)",
                       showarrow=True, arrowhead=2, ax=40, ay=-35,
                       font=dict(size=10, color="#2ca02c"),
                       bgcolor="rgba(255,255,255,0.85)",
                       bordercolor="#2ca02c", borderwidth=1)

    base_layout(fig,
                "Each Generation Has Its Own Migration Fingerprint",
                "Inflow concentration across five age groups for selected states - ratio > 1 means stronger pull than expected",
                w=980, h=620,
                foot="Dotted line = proportional baseline. "
                     "Wisconsin and Minnesota shown with thicker markers.")
    fig.update_xaxes(title="Age Group", showgrid=False, tickfont=dict(size=13))
    fig.update_yaxes(title="Inflow Concentration Ratio",
                     showgrid=True, gridcolor="#ecf0f1",
                     range=[0.3, 2.0], tickfont=dict(size=12))
    fig.update_layout(legend=dict(
        orientation="h", yanchor="bottom", y=-0.32,
        xanchor="center", x=0.5, font=dict(size=11),
    ))
    save(fig, "P03_lifecourse_signatures.html")
    print("  [3/10] P03 life-course signatures")


# ========================================================================
# P04 - 25-34 Map
# ========================================================================
def _map(df, col, ttl, sub, name):
    vals = df[col]
    zmid = 1.0
    dev = max(abs(vals.min() - zmid), abs(vals.max() - zmid)) or 0.1
    hover = [f"<b>{r['state_name']}</b><br>Ratio: {r[col]:.3f}"
             for _, r in df.iterrows()]
    fig = go.Figure(go.Choropleth(
        locations=df["abbrev"], z=vals, locationmode="USA-states",
        colorscale=DIV_ONE, zmin=zmid - dev, zmax=zmid + dev,
        colorbar=dict(title="Ratio", thickness=14, len=0.6,
                      tickfont=dict(size=11)),
        text=hover, hovertemplate="%{text}<extra></extra>",
        marker_line_color="white", marker_line_width=0.5,
    ))
    base_layout(fig, ttl, sub, w=920, h=560,
                foot="Ratio > 1 (green) = more concentrated than expected. "
                     "Ratio < 1 (orange) = less concentrated. Source: 2024 ACS.")
    fig.update_geos(scope="usa", showlakes=False, bgcolor="#fafafa",
                    lakecolor="#fafafa", landcolor="#ffffff")
    save(fig, name)


def p04_map_25_34(df):
    _map(df, "REL_IN_25_34",
         "Where Do Young Professionals Move?",
         "Inflow concentration for ages 25-34 - Northeast corridor and Alaska lead",
         "P04_map_25_34.html")
    print("  [4/10] P04 map 25-34")


def p06_map_18_24(df):
    _map(df, "REL_IN_18_24",
         "Where Do College-Age Adults Move?",
         "Inflow concentration for ages 18-24 - Upper Midwest and New England lead",
         "P06_map_18_24.html")
    print("  [6/10] P06 map 18-24")


# ========================================================================
# P05 & P07 - Scatter with OLS trend
# ========================================================================
def _scatter(df, iv, dv, dv_label, ttl, sub, labels, name, xtickprefix=""):
    x, y = df[iv].values, df[dv].values
    xp, yp, ci, m = ols_fit(x, y)

    fig = go.Figure()
    # CI band
    fig.add_trace(go.Scatter(
        x=np.concatenate([xp, xp[::-1]]),
        y=np.concatenate([ci[:, 0], ci[:, 1][::-1]]),
        fill="toself", fillcolor="rgba(192,57,43,0.1)",
        line=dict(width=0), showlegend=False, hoverinfo="skip",
    ))
    # Trend
    fig.add_trace(go.Scatter(
        x=xp, y=yp, mode="lines",
        line=dict(color="#c0392b", width=2.5, dash="dash"),
        showlegend=False, hoverinfo="skip",
    ))
    # Points
    clr = ["#d35400" if a in LOCAL else "#2980b9" for a in df["abbrev"]]
    sz = [11 if a in LOCAL else 8 for a in df["abbrev"]]
    fig.add_trace(go.Scatter(
        x=x, y=y, mode="markers",
        marker=dict(color=clr, size=sz,
                    line=dict(color="white", width=1.2)),
        text=df["abbrev"], showlegend=False,
        hovertemplate=(f"<b>%{{text}}</b><br>"
                       f"{IV_LABELS[iv]}: %{{x}}<br>"
                       f"{dv_label}: %{{y:.3f}}<extra></extra>"),
    ))
    # Labels
    for _, r in df[df["abbrev"].isin(labels)].iterrows():
        fig.add_annotation(
            x=r[iv], y=r[dv], text=r["abbrev"], showarrow=False,
            yshift=14, font=dict(size=11, color="#2c3e50", family=FONT),
        )
    # R^2 badge
    fig.add_annotation(
        text=f"Adj R^2 = {m.rsquared_adj:.2f}",
        xref="paper", yref="paper", x=0.03, y=0.97,
        showarrow=False, xanchor="left",
        font=dict(size=12, color="#2c3e50"),
        bgcolor="rgba(255,255,255,0.9)",
        bordercolor="#ecf0f1", borderwidth=1, borderpad=6,
    )
    base_layout(fig, ttl, sub, w=870, h=560,
                foot=f"Each dot = one state. Orange dots = Wisconsin and Minnesota. "
                     f"Red dashed line = best-fit trend with 95% confidence band.")
    fig.update_xaxes(title=IV_LABELS[iv],
                     showgrid=True, gridcolor="#ecf0f1",
                     tickprefix=xtickprefix)
    fig.update_yaxes(title=dv_label,
                     showgrid=True, gridcolor="#ecf0f1")
    save(fig, name)


def p05_pay(df):
    _scatter(df, "PRIV_AVG_PAY", "REL_IN_25_34",
             "25-34 Inflow Concentration",
             "Higher Pay, Stronger Pull for Young Professionals",
             "Average private-sector pay explains 39% of state-to-state variation",
             {"NY", "MD", "MA", "AK", "WV", "MS", "WI", "MN", "ND"},
             "P05_scatter_25_34_pay.html",
             xtickprefix="$")
    print("  [5/10] P05 scatter 25-34 pay")


def p07_commute(df):
    _scatter(df, "COMMUTE_MED", "REL_IN_18_24",
             "18-24 Inflow Concentration",
             "Shorter Commutes, Stronger Pull for College-Age Movers",
             "Median commute time explains 22% of state-to-state variation",
             {"ND", "IA", "VT", "NV", "FL", "WI", "MN", "NY"},
             "P07_scatter_18_24_commute.html")
    print("  [7/10] P07 scatter 18-24 commute")


# ========================================================================
# P08 - Bridge States (FL, ND, TX cross-age)
# ========================================================================
def p08_bridge_states(df):
    bridge = [("FL", "Florida",   "#d62728"),
              ("ND", "N. Dakota", "#1f77b4"),
              ("TX", "Texas",     "#ff7f0e")]
    x_lbls = [f"{AGE_LBL[a]}<br><span style='font-size:10px;color:#95a5a6'>{AGE_NAME[a]}</span>"
              for a in AGES]

    fig = go.Figure()
    fig.add_hline(y=1.0, line_dash="dot", line_color="#bdc3c7", line_width=1.5)

    for st, name, clr in bridge:
        row = df[df["abbrev"] == st].iloc[0]
        yv = [row[f"REL_IN_{a}"] for a in AGES]
        fig.add_trace(go.Bar(
            x=x_lbls, y=yv, name=name, marker_color=clr,
            text=[f"{v:.2f}" for v in yv], textposition="outside",
            textfont=dict(size=11, color="#2c3e50"),
            hovertemplate=f"<b>{name}</b><br>%{{x}}: %{{y:.2f}}<extra></extra>",
        ))

    base_layout(fig,
                "Three States, Five Ages: The Life-Course Made Concrete",
                "Florida chases retirees - North Dakota attracts college-age - Texas stays balanced",
                w=960, h=580,
                foot="Bar height = inflow concentration ratio. Dotted line = proportional baseline (1.0).")
    fig.update_xaxes(title="", showgrid=False, tickfont=dict(size=12))
    fig.update_yaxes(title="Inflow Concentration Ratio",
                     showgrid=True, gridcolor="#ecf0f1",
                     range=[0, 2.1], tickfont=dict(size=12))
    fig.update_layout(
        barmode="group", bargap=0.22, bargroupgap=0.08,
        legend=dict(orientation="h", yanchor="bottom", y=-0.28,
                    xanchor="center", x=0.5, font=dict(size=12)),
    )
    save(fig, "P08_bridge_states.html")
    print("  [8/10] P08 bridge states")


# ========================================================================
# P09 - Later-Life Summary
# ========================================================================
def p09_later_life(df):
    """Top 5 states for each of 35-54, 55-64, 65+ with driver annotation."""
    later = [
        ("35_54", "Ages 35-54: Mid-Career",
         "Key driver: Uninsured Share (positive)"),
        ("55_64", "Ages 55-64: Pre-Retirees",
         "Key driver: Rental Vacancy Rate (positive)"),
        ("65_PLUS", "Ages 65+: Retirees",
         "Key driver: Rental Vacancy Rate (positive)"),
    ]

    subplot_titles = [
        f"<b>{t}</b>  -  <span style='font-size:11px;color:#7f8c8d'>{d}</span>"
        for _, t, d in later
    ]

    fig = make_subplots(3, 1, vertical_spacing=0.15,
                        subplot_titles=subplot_titles)

    for i, (age, _, _) in enumerate(later, 1):
        col = f"REL_IN_{age}"
        top5 = df.nlargest(5, col).sort_values(col)
        fig.add_trace(go.Bar(
            x=top5[col], y=top5["state_name"], orientation="h",
            marker_color=AGE_CLR[age], showlegend=False,
            text=[f"{v:.2f}" for v in top5[col]], textposition="outside",
            textfont=dict(size=11),
            hovertemplate="<b>%{y}</b><br>Ratio: %{x:.2f}<extra></extra>",
        ), i, 1)
        fig.add_vline(x=1.0, row=i, col=1, line_dash="dot",
                      line_color="#bdc3c7", line_width=1)

    base_layout(fig,
                "Later-Life Migration: Different Stages, Different Destinations",
                "Top 5 states by inflow concentration for each later-life age group",
                w=880, h=720,
                foot="Ratio > 1 = state attracts more of that age group than its overall size would predict.")
    for i in range(1, 4):
        fig.update_xaxes(title="Concentration Ratio" if i == 3 else "",
                         row=i, col=1, showgrid=True, gridcolor="#ecf0f1",
                         range=[0, 2.0])
        fig.update_yaxes(row=i, col=1, showgrid=False)
    save(fig, "P09_later_life_summary.html")
    print("  [9/10] P09 later-life summary")


# ========================================================================
# P10 - Takeaway Summary Table
# ========================================================================
def p10_takeaway(df):
    rows = [
        ["18-24", "College-Age",
         "Small, short-commute states",
         "Median Commute Time (-)", "ND, IA, VT", "0.22"],
        ["25-34", "Young Professionals",
         "High-pay metro states",
         "Avg. Private-Sector Pay (+)", "NY, AK, MD", "0.39"],
        ["35-54", "Mid-Career",
         "Sun Belt, affordable states",
         "Uninsured Share (+)", "NV, GA, LA", "0.26"],
        ["55-64", "Pre-Retirees",
         "Warm, housing-available",
         "Rental Vacancy Rate (+)", "FL, DE, AZ", "0.16"],
        ["65+", "Retirees",
         "Classic retirement states",
         "Rental Vacancy Rate (+)", "FL, AZ, ME", "0.07"],
    ]

    # Very light age-tinted row backgrounds
    tints = ["#fef5e7", "#eaf2f8", "#e8f8f0", "#f4ecf7", "#fdedec"]
    cell_fill = [tints] * 6  # one column list per column

    headers = ["Age Group", "Generation", "Where They Go",
               "Key Driver", "Top 3 States", "Signal (R^2)"]

    fig = go.Figure(go.Table(
        header=dict(
            values=[f"<b>{h}</b>" for h in headers],
            fill_color="#2c3e50",
            font=dict(color="white", size=13, family=FONT),
            align="center", height=42,
            line_color="#2c3e50",
        ),
        cells=dict(
            values=list(zip(*rows)),
            fill_color=cell_fill,
            font=dict(size=12, family=FONT, color="#2c3e50"),
            align=["center", "center", "left", "left", "center", "center"],
            height=38,
            line_color="#ecf0f1",
        ),
        columnwidth=[55, 85, 135, 130, 85, 60],
    ))

    base_layout(fig,
                "Life-Stage Migration at a Glance",
                "Each generation responds to different state characteristics",
                w=1020, h=420,
                foot="Signal column = single-variable adj R^2 (best predictor). "
                     "Multi-variable models achieve adj R^2 = 0.42 for both 18-24 and 25-34.")
    save(fig, "P10_takeaway_summary.html")
    print("  [10/10] P10 takeaway summary")


# ========================================================================
# Main
# ========================================================================
def main():
    print("Presentation Pack - Main Deck (Part 1)")
    print("=" * 50)
    df = load()
    p01_volume(df)
    p02_concept(df)
    p03_lifecourse(df)
    p04_map_25_34(df)
    p05_pay(df)
    p06_map_18_24(df)
    p07_commute(df)
    p08_bridge_states(df)
    p09_later_life(df)
    p10_takeaway(df)
    print("=" * 50)
    print(f"Generated 10 main-deck figures in {FIG_DIR}")


if __name__ == "__main__":
    main()
