#!/usr/bin/env python3
"""
Specialization / Deviation Visualization Package
=================================================
Generates:
  - 10 REL_IN/REL_OUT maps (specialization ratios, diverging at 1.0)
  - 10 DIFF_IN/DIFF_OUT maps (difference from baseline, diverging at 0)
  - 5 SHARE_GAP maps (diverging at 0)
  - State specialization profile charts for exemplar states
  - Rank-shift summary table (HTML)

Usage:
    python -m scripts.viz_specialization
"""

from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

PROJECT = Path(__file__).resolve().parent.parent
DATA_PATH = PROJECT / "data_processed" / "analysis_ready_specialization.csv"
RANK_PATH = PROJECT / "outputs" / "tables" / "specialization" / "rank_shifts.csv"
FIG_DIR = PROJECT / "outputs" / "figures" / "specialization"
FIG_DIR.mkdir(parents=True, exist_ok=True)

AGE_GROUPS = ["18_24", "25_34", "35_54", "55_64", "65_PLUS"]
AGE_LABELS = {
    "18_24": "18\u201324", "25_34": "25\u201334", "35_54": "35\u201354",
    "55_64": "55\u201364", "65_PLUS": "65+",
}

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

# Diverging scales
DIV_ZERO = [  # centered at 0: red-white-blue
    [0.0, "#b2182b"], [0.25, "#ef8a62"], [0.5, "#f7f7f7"],
    [0.75, "#67a9cf"], [1.0, "#2166ac"],
]
DIV_ONE = [  # centered at 1: orange-white-teal for specialization ratios
    [0.0, "#d95f02"], [0.25, "#fdb863"], [0.5, "#f7f7f7"],
    [0.75, "#80cdc1"], [1.0, "#1b7837"],
]


def load_data():
    df = pd.read_csv(DATA_PATH, dtype={"state": str})
    df["state"] = df["state"].str.zfill(2)
    if "abbrev" not in df.columns:
        df["abbrev"] = df["state"].map(FIPS_TO_ABBREV)
    return df


def make_choropleth(df, col, title, colorscale, zmid, outpath, footnote=""):
    vals = df[col]
    abs_dev = max(abs(vals.min() - zmid), abs(vals.max() - zmid)) or 0.1

    hover = []
    for _, r in df.iterrows():
        hover.append(f"<b>{r['state_name']}</b><br>{col}: {r[col]:.4f}")

    fig = go.Figure()
    fig.add_trace(go.Choropleth(
        locations=df["abbrev"], z=vals, locationmode="USA-states",
        colorscale=colorscale, zmin=zmid - abs_dev, zmax=zmid + abs_dev,
        colorbar=dict(title=dict(text=col.split("_")[0] + " " + col.split("_")[1]),
                      thickness=12, len=0.6),
        text=hover, hovertemplate="%{text}<extra></extra>",
    ))
    annotations = []
    if footnote:
        annotations.append(dict(
            text=footnote, xref="paper", yref="paper", x=0.5, y=-0.02,
            showarrow=False, font=dict(size=9, color="#888"),
        ))
    fig.update_layout(
        title=dict(text=title, x=0.5, font=dict(size=15)),
        geo=dict(scope="usa", bgcolor="rgba(0,0,0,0)"),
        margin=dict(l=0, r=0, t=50, b=30),
        paper_bgcolor="white",
        annotations=annotations,
    )
    fig.write_html(str(outpath), include_plotlyjs="cdn")


def make_profile_chart(df, state_abbrev, outpath):
    """Bar chart showing REL_IN and REL_OUT across all 5 age groups for one state."""
    row = df[df["abbrev"] == state_abbrev]
    if row.empty:
        return
    row = row.iloc[0]
    state_name = row["state_name"]

    ages = list(AGE_LABELS.values())
    rel_in = [row[f"REL_IN_{ag}"] for ag in AGE_GROUPS]
    rel_out = [row[f"REL_OUT_{ag}"] for ag in AGE_GROUPS]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        y=ages, x=rel_in, orientation="h", name="Inflow specialization",
        marker_color="#2166ac", text=[f"{v:.2f}" for v in rel_in],
        textposition="outside",
    ))
    fig.add_trace(go.Bar(
        y=ages, x=rel_out, orientation="h", name="Outflow specialization",
        marker_color="#b2182b", text=[f"{v:.2f}" for v in rel_out],
        textposition="outside",
    ))
    fig.add_vline(x=1.0, line_color="#999", line_dash="dash", line_width=1.5,
                  annotation_text="1.0 = proportional", annotation_position="top")
    fig.update_layout(
        title=dict(text=f"{state_name} ({state_abbrev}) \u2014 Age-Group Specialization", x=0.5),
        barmode="group",
        xaxis_title="Specialization ratio (>1 = over-represented)",
        yaxis=dict(autorange="reversed"),
        margin=dict(l=60, r=80, t=50, b=50),
        legend=dict(orientation="h", y=-0.15),
        paper_bgcolor="white", plot_bgcolor="#fafafa",
    )
    fig.write_html(str(outpath), include_plotlyjs="cdn")


def make_rank_shift_dumbbell(rank_df, direction, ag, outpath):
    """Dumbbell plot: all-ages rank vs age-specific rank for top/bottom shifters."""
    sub = rank_df[(rank_df["direction"] == direction) & (rank_df["age_group"] == ag)]
    sub = sub.sort_values("rank_shift", ascending=False)
    # Top 8 upward + top 8 downward shifters
    top = sub.head(8)
    bottom = sub.tail(8)
    show = pd.concat([top, bottom]).drop_duplicates(subset=["abbrev"])
    show = show.sort_values("rank_shift", ascending=True)

    fig = go.Figure()
    for _, r in show.iterrows():
        color = "#2166ac" if r["rank_shift"] > 0 else "#b2182b"
        fig.add_trace(go.Scatter(
            x=[r["rank_all_ages"], r["rank_age_specific"]],
            y=[r["abbrev"], r["abbrev"]],
            mode="lines+markers",
            marker=dict(size=8, color=color),
            line=dict(color=color, width=2),
            showlegend=False,
            hovertemplate=(
                f"<b>{r['state_name']}</b><br>"
                f"All-ages rank: {r['rank_all_ages']}<br>"
                f"{AGE_LABELS[ag]} rank: {r['rank_age_specific']}<br>"
                f"Shift: {r['rank_shift']:+d}<extra></extra>"
            ),
        ))
    dir_label = "Inflow" if direction == "IN" else "Outflow"
    fig.update_layout(
        title=dict(
            text=f"Rank Shift: {dir_label} {AGE_LABELS[ag]} vs All-Ages",
            x=0.5, font=dict(size=14),
        ),
        xaxis_title="Rank (1 = highest share)",
        xaxis=dict(autorange="reversed"),
        margin=dict(l=50, r=20, t=50, b=40),
        paper_bgcolor="white", plot_bgcolor="#fafafa",
        height=max(400, len(show) * 28 + 100),
    )
    fig.write_html(str(outpath), include_plotlyjs="cdn")


def main():
    df = load_data()
    rank_df = pd.read_csv(RANK_PATH)
    count = 0

    # --- REL maps (specialization ratios, centered at 1.0) ---
    print("Generating REL maps (specialization ratios)...")
    for direction, dir_label in [("IN", "Inflow"), ("OUT", "Outflow")]:
        for ag in AGE_GROUPS:
            col = f"REL_{direction}_{ag}"
            title = f"{dir_label} Specialization \u2014 {AGE_LABELS[ag]}"
            footnote = f"REL_{direction} > 1 = state over-represented vs all-ages baseline. REL_{direction} < 1 = under-represented."
            outpath = FIG_DIR / f"map_{col}.html"
            make_choropleth(df, col, title, DIV_ONE, 1.0, outpath, footnote)
            count += 1
            print(f"  [{count:2d}] {outpath.name}")

    # --- DIFF maps (difference from baseline, centered at 0) ---
    print("Generating DIFF maps (difference from baseline)...")
    for direction, dir_label in [("IN", "Inflow"), ("OUT", "Outflow")]:
        for ag in AGE_GROUPS:
            col = f"DIFF_{direction}_{ag}"
            title = f"{dir_label} Deviation from Total \u2014 {AGE_LABELS[ag]}"
            footnote = f"DIFF > 0 = age-specific share above all-ages share. DIFF < 0 = below."
            outpath = FIG_DIR / f"map_{col}.html"
            make_choropleth(df, col, title, DIV_ZERO, 0.0, outpath, footnote)
            count += 1
            print(f"  [{count:2d}] {outpath.name}")

    # --- SHARE_GAP maps (centered at 0) ---
    print("Generating SHARE_GAP maps...")
    for ag in AGE_GROUPS:
        col = f"SHARE_GAP_{ag}"
        title = f"Inflow\u2013Outflow Share Gap \u2014 {AGE_LABELS[ag]}"
        footnote = "Gap > 0 = state captures more inflow than outflow for this age group. Gap < 0 = opposite."
        outpath = FIG_DIR / f"map_{col}.html"
        make_choropleth(df, col, title, DIV_ZERO, 0.0, outpath, footnote)
        count += 1
        print(f"  [{count:2d}] {outpath.name}")

    # --- State profiles ---
    print("Generating state specialization profiles...")
    exemplars = ["FL", "CA", "TX", "NY", "AZ", "NV", "ND", "ME", "HI"]
    for abbr in exemplars:
        outpath = FIG_DIR / f"profile_{abbr}.html"
        make_profile_chart(df, abbr, outpath)
        count += 1
        print(f"  [{count:2d}] {outpath.name}")

    # --- Rank-shift dumbbells ---
    print("Generating rank-shift dumbbell plots...")
    for direction in ["IN", "OUT"]:
        for ag in AGE_GROUPS:
            outpath = FIG_DIR / f"rankshift_{direction}_{ag}.html"
            make_rank_shift_dumbbell(rank_df, direction, ag, outpath)
            count += 1
            print(f"  [{count:2d}] {outpath.name}")

    print(f"\nGenerated {count} visualizations in {FIG_DIR.relative_to(PROJECT)}")


if __name__ == "__main__":
    main()
