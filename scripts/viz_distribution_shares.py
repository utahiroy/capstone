#!/usr/bin/env python3
"""
Distribution-Share Choropleth Maps
===================================
Generates 12 standalone HTML maps: IN_SHARE and OUT_SHARE for 5 age groups
plus all-ages.

Usage:
    python -m scripts.viz_distribution_shares

Outputs:
    outputs/figures/distribution_shares/map_IN_SHARE_*.html  (6 files)
    outputs/figures/distribution_shares/map_OUT_SHARE_*.html (6 files)
"""

from pathlib import Path

import pandas as pd
import plotly.graph_objects as go

PROJECT = Path(__file__).resolve().parent.parent
DATA_PATH = PROJECT / "data_processed" / "analysis_ready_distribution_shares.csv"
FIG_DIR = PROJECT / "outputs" / "figures" / "distribution_shares"

AGE_GROUPS = ["18_24", "25_34", "35_54", "55_64", "65_PLUS", "ALL_AGES"]
AGE_LABELS = {
    "18_24": "18\u201324", "25_34": "25\u201334", "35_54": "35\u201354",
    "55_64": "55\u201364", "65_PLUS": "65+", "ALL_AGES": "All Ages",
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

# Sequential blue scale for shares (all values >= 0)
SEQ_SCALE = [
    [0.0, "#f7fbff"], [0.25, "#c6dbef"], [0.5, "#6baed6"],
    [0.75, "#2171b5"], [1.0, "#08306b"],
]


def make_map(
    df: pd.DataFrame,
    col: str,
    pct_col: str,
    title: str,
    outpath: Path,
):
    """Generate a single choropleth map and save as standalone HTML."""
    hover_texts = []
    for _, r in df.iterrows():
        hover_texts.append(
            f"<b>{r['state_name']}</b><br>"
            f"{col}: {r[col]:.4f} ({r[pct_col]:.2f}%)"
        )

    fig = go.Figure()
    fig.add_trace(
        go.Choropleth(
            locations=df["abbrev"],
            z=df[pct_col],
            locationmode="USA-states",
            colorscale=SEQ_SCALE,
            zmin=0,
            colorbar=dict(title=dict(text="Share (%)"), thickness=12, len=0.6),
            text=hover_texts,
            hovertemplate="%{text}<extra></extra>",
        )
    )
    fig.update_layout(
        title=dict(text=title, x=0.5, font=dict(size=16)),
        geo=dict(scope="usa", bgcolor="rgba(0,0,0,0)"),
        margin=dict(l=0, r=0, t=50, b=30),
        paper_bgcolor="white",
        annotations=[
            dict(
                text=(
                    "Share = state gross flow / national total for the age group. "
                    "Reflects state size and migration volume, not population-normalized rate."
                ),
                xref="paper", yref="paper", x=0.5, y=-0.02,
                showarrow=False, font=dict(size=10, color="#888"),
            )
        ],
    )
    fig.write_html(str(outpath), include_plotlyjs="cdn")


def main():
    FIG_DIR.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(DATA_PATH, dtype={"state": str})
    df["state"] = df["state"].str.zfill(2)
    df["abbrev"] = df["state"].map(FIPS_TO_ABBREV)

    count = 0
    for direction in ["IN", "OUT"]:
        dir_label = "Inflow" if direction == "IN" else "Outflow"
        for ag in AGE_GROUPS:
            col = f"{direction}_SHARE_{ag}"
            pct_col = f"{direction}_SHARE_PCT_{ag}"
            if col not in df.columns or pct_col not in df.columns:
                print(f"  SKIP (missing column): {col}")
                continue
            title = (
                f"{dir_label} Share \u2014 {AGE_LABELS[ag]}"
            )
            outpath = FIG_DIR / f"map_{col}.html"
            make_map(df, col, pct_col, title, outpath)
            count += 1
            print(f"  [{count:2d}/12] {outpath.name}")

    print(f"\nGenerated {count} maps in {FIG_DIR.relative_to(PROJECT)}")


if __name__ == "__main__":
    main()
