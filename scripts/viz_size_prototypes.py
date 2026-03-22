"""Phase A7b: Size-diagnostic visualization prototypes.

Generates two supplemental prototypes that pair rate, count, and
denominator context so that denominator-effect signals (especially
in 18–24 and 35–54) can be visually assessed.

Does NOT replace or modify any existing proto files.

Reads:
  data_processed/analysis_ready.csv
  outputs/tables/size_diag_state_age_long.csv

Writes:
  outputs/viz/proto5b_state_profiles_counts_and_flags.html
  outputs/viz/proto7_size_diagnostic_compare.html

Run:  python -m scripts.viz_size_prototypes
"""

import os
import sys

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

from src.constants import AGE_GROUPS
from src.fetch_crime import STATE_ABBR_TO_FIPS

# ── Setup ─────────────────────────────────────────────────────────

OUTDIR = "outputs/viz"
FIPS_TO_ABBR = {v: k for k, v in STATE_ABBR_TO_FIPS.items()}

AG_LABELS = {
    "18_24": "18–24", "25_34": "25–34", "35_54": "35–54",
    "55_64": "55–64", "65_PLUS": "65+",
}

# Age groups with statistically significant denominator-effect signal
DENOM_EFFECT_AGS = {"18_24", "35_54"}

FOOTER_NOTE = (
    "Rate = intensity (per 1,000 age-group pop). "
    "Count = volume (persons). "
    "POP_AGE = denominator context. "
    "Main DV remains NET_RATE. "
    "◆ = bottom-quintile POP_AGE (small-pop flag). "
    "50 states, 2024 cross-section, non-causal. "
    "* = provisional data source."
)

ANALYSIS_PATH = "data_processed/analysis_ready.csv"
DIAG_LONG_PATH = "outputs/tables/size_diag_state_age_long.csv"


def load_data():
    """Load wide analysis_ready and long diagnostic table."""
    for p in (ANALYSIS_PATH, DIAG_LONG_PATH):
        if not os.path.exists(p):
            print(f"ERROR: {p} not found.")
            sys.exit(1)

    df = pd.read_csv(ANALYSIS_PATH, dtype={"state": str})
    df["state"] = df["state"].str.zfill(2)
    df["abbr"] = df["state"].map(FIPS_TO_ABBR)

    diag = pd.read_csv(DIAG_LONG_PATH, dtype={"state": str})
    diag["state"] = diag["state"].str.zfill(2)
    diag["abbr"] = diag["state"].map(FIPS_TO_ABBR)

    return df, diag


def save_html(fig, filename):
    path = os.path.join(OUTDIR, filename)
    fig.write_html(path, include_plotlyjs="cdn")
    print(f"  Saved: {path}")


# ── Proto 5b: State profiles with counts, flags, and sort options ─

def proto5b_state_profiles(df, diag):
    """Enhanced state profiles: rate/count toggle, small-pop flag, 3 sort modes."""
    print("\n[5b] State profile: counts, flags, and sort options")

    # All metrics available for the bar chart
    metrics = {
        "NET_RATE":  {"label": "Net Rate (per 1,000)",   "unit": "per 1,000"},
        "IN_RATE":   {"label": "In Rate (per 1,000)",    "unit": "per 1,000"},
        "OUT_RATE":  {"label": "Out Rate (per 1,000)",   "unit": "per 1,000"},
        "NET_COUNT": {"label": "Net Count (persons)",    "unit": "persons"},
        "IN_COUNT":  {"label": "In Count (persons)",     "unit": "persons"},
        "OUT_COUNT": {"label": "Out Count (persons)",    "unit": "persons"},
    }

    sort_modes = {
        "by_metric": "By selected metric (avg across age groups)",
        "alpha":     "Alphabetical",
        "by_pop":    "By total population",
    }

    # Build a lookup for hover from the long diagnostic table
    # Key = (state, age_group) -> dict of hover fields
    hover_lookup = {}
    for _, row in diag.iterrows():
        key = (row["state"], row["age_group"])
        hover_lookup[key] = {
            "POP_AGE": f"{row['POP_AGE']:,.0f}",
            "IN_COUNT": f"{row['IN_COUNT']:,.0f}",
            "OUT_COUNT": f"{row['OUT_COUNT']:,.0f}",
            "NET_COUNT": f"{row['NET_COUNT']:,.0f}",
            "IN_RATE": f"{row['IN_RATE']:.2f}",
            "OUT_RATE": f"{row['OUT_RATE']:.2f}",
            "NET_RATE": f"{row['NET_RATE']:.2f}",
            "rank_net_rate": int(row["rank_net_rate"]),
            "rank_net_count": int(row["rank_net_count"]),
            "small_pop_flag": int(row["small_pop_flag"]),
        }

    # Precompute sort orders
    # by_pop: total POP ascending (so largest at top of horizontal bar)
    pop_order = df.sort_values("POP", ascending=True)["state_name"].tolist()
    alpha_order = sorted(df["state_name"].tolist(), reverse=True)

    # Small-pop flag lookup: state -> set of age groups where flagged
    small_states = {}
    for _, row in diag[diag["small_pop_flag"] == 1].iterrows():
        small_states.setdefault(row["state_name"], set()).add(row["age_group"])

    fig = go.Figure()
    traces_index = []  # (metric_key, sort_key, ag) for each trace
    colors = px.colors.qualitative.Set2

    for m_key, m_info in metrics.items():
        for s_key in sort_modes:
            # Compute sort order for this metric
            if s_key == "alpha":
                state_order = alpha_order
            elif s_key == "by_pop":
                state_order = pop_order
            else:  # by_metric
                # Average of this metric across age groups
                metric_cols = [f"{m_key}_{ag}" for ag in AGE_GROUPS]
                missing = [c for c in metric_cols if c not in df.columns]
                if missing:
                    # Fall back to NET_RATE for count metrics
                    avg = df[[f"NET_RATE_{ag}" for ag in AGE_GROUPS]].mean(axis=1)
                else:
                    avg = df[metric_cols].mean(axis=1)
                state_order = df.assign(_avg=avg).sort_values(
                    "_avg", ascending=True)["state_name"].tolist()

            for ai, ag in enumerate(AGE_GROUPS):
                col = f"{m_key}_{ag}"
                if col not in df.columns:
                    continue

                # Build per-state data in sort order
                ordered_df = df.set_index("state_name").loc[
                    [s for s in state_order if s in df["state_name"].values]
                ].reset_index()

                # Rich hover text
                hover_texts = []
                for _, r in ordered_df.iterrows():
                    hk = (r["state"], ag)
                    h = hover_lookup.get(hk, {})
                    flag_str = "YES" if h.get("small_pop_flag", 0) == 1 else "no"
                    denom_str = " ⚠ DENOM-EFFECT AGE GROUP" if ag in DENOM_EFFECT_AGS else ""
                    hover_texts.append(
                        f"<b>{r['state_name']}</b> ({r['abbr']}) — {AG_LABELS[ag]}{denom_str}<br>"
                        f"POP_AGE: {h.get('POP_AGE', '?')}<br>"
                        f"IN: {h.get('IN_COUNT', '?')} ({h.get('IN_RATE', '?')}/1k)<br>"
                        f"OUT: {h.get('OUT_COUNT', '?')} ({h.get('OUT_RATE', '?')}/1k)<br>"
                        f"NET: {h.get('NET_COUNT', '?')} ({h.get('NET_RATE', '?')}/1k)<br>"
                        f"Rank NET_RATE: {h.get('rank_net_rate', '?')} | "
                        f"Rank NET_COUNT: {h.get('rank_net_count', '?')}<br>"
                        f"Small-pop flag: {flag_str}"
                    )

                # Mark small-pop states with diamond pattern
                # Build marker pattern for each state
                patterns = []
                for _, r in ordered_df.iterrows():
                    hk = (r["state"], ag)
                    h = hover_lookup.get(hk, {})
                    if h.get("small_pop_flag", 0) == 1:
                        patterns.append("/")
                    else:
                        patterns.append("")

                # State labels: append ◆ for small-pop
                y_labels = []
                for _, r in ordered_df.iterrows():
                    sname = r["state_name"]
                    if sname in small_states and ag in small_states[sname]:
                        y_labels.append(f"◆ {sname}")
                    else:
                        y_labels.append(sname)

                traces_index.append((m_key, s_key, ag))
                fig.add_trace(go.Bar(
                    x=ordered_df[col],
                    y=y_labels,
                    orientation="h",
                    name=AG_LABELS[ag],
                    marker=dict(
                        color=colors[ai % len(colors)],
                        pattern_shape=patterns,
                        pattern_fillmode="overlay",
                    ),
                    visible=False,
                    hovertext=hover_texts,
                    hoverinfo="text",
                ))

    # Default visible: NET_RATE, by_metric sort, all 5 age groups
    n_ags = len(AGE_GROUPS)
    for k in range(n_ags):
        fig.data[k].visible = True

    # Build dropdown
    buttons = []
    trace_idx = 0
    for m_key, m_info in metrics.items():
        for s_key, s_label in sort_modes.items():
            col_check = f"{m_key}_{AGE_GROUPS[0]}"
            if col_check not in df.columns:
                continue
            vis = [False] * len(traces_index)
            for k in range(n_ags):
                vis[trace_idx + k] = True
            buttons.append(dict(
                label=f"{m_info['label']} / {s_label.split('(')[0].strip()}",
                method="update",
                args=[{"visible": vis},
                      {"title": (f"State Profiles: {m_info['label']} by Age Group (2024)<br>"
                                 f"<sup>{s_label}. ◆ = small-pop state for that age group.</sup>"),
                       "xaxis.title": f"{m_info['label']} ({m_info['unit']})"}],
            ))
            trace_idx += n_ags

    fig.update_layout(
        title=("State Profiles: Net Rate (per 1,000) by Age Group (2024)<br>"
               "<sup>By selected metric (avg across age groups). "
               "◆ = small-pop state for that age group.</sup>"),
        barmode="group",
        height=1500, width=1050,
        yaxis=dict(dtick=1),
        xaxis_title="Net Rate (per 1,000)",
        legend=dict(orientation="h", yanchor="bottom", y=1.01,
                    xanchor="center", x=0.5),
        updatemenus=[dict(
            type="dropdown", direction="down",
            x=0.01, y=0.99,
            buttons=buttons, showactive=True,
        )],
        annotations=[dict(
            text=FOOTER_NOTE,
            xref="paper", yref="paper", x=0.5, y=-0.015, showarrow=False,
            font=dict(size=9, color="gray"), align="center",
        )],
    )

    fig.add_vline(x=0, line_dash="dash", line_color="black", opacity=0.5)

    save_html(fig, "proto5b_state_profiles_counts_and_flags.html")


# ── Proto 7: Size diagnostic comparison ──────────────────────────

def proto7_size_diagnostic(df, diag):
    """Scatter: POP_AGE vs NET_RATE, point size ~ |NET_COUNT|, small-pop flagged."""
    print("\n[7] Size diagnostic comparison")

    fig = go.Figure()
    n_traces_per_ag = 2  # regular + small-pop
    trace_list = []

    for i, ag in enumerate(AGE_GROUPS):
        sub = diag[diag["age_group"] == ag].copy()
        denom_flag = ag in DENOM_EFFECT_AGS
        denom_note = " ⚠ denom-effect" if denom_flag else ""

        # Scale bubble size: map |NET_COUNT| to marker size 6–40
        abs_net = sub["NET_COUNT"].abs()
        if abs_net.max() > abs_net.min():
            size_scaled = 6 + 34 * (abs_net - abs_net.min()) / (abs_net.max() - abs_net.min())
        else:
            size_scaled = pd.Series(15, index=sub.index)

        # Split into regular and small-pop
        regular = sub[sub["small_pop_flag"] == 0]
        small = sub[sub["small_pop_flag"] == 1]

        for subset, is_small in [(regular, False), (small, True)]:
            if len(subset) == 0:
                trace_list.append((ag, is_small))
                fig.add_trace(go.Scatter(
                    x=[], y=[], mode="markers", visible=False,
                    name="(empty)",
                ))
                continue

            idx = subset.index
            marker_symbol = "diamond" if is_small else "circle"
            marker_color = "red" if is_small else "steelblue"
            edge_color = "darkred" if is_small else "navy"
            label = f"{AG_LABELS[ag]} — {'small-pop ◆' if is_small else 'regular'}"

            hover_texts = []
            for _, r in subset.iterrows():
                flag_str = "YES ◆" if r["small_pop_flag"] == 1 else "no"
                hover_texts.append(
                    f"<b>{r['state_name']}</b> ({r['abbr']}){denom_note}<br>"
                    f"POP_AGE: {r['POP_AGE']:,.0f}<br>"
                    f"NET_RATE: {r['NET_RATE']:.2f}/1k (rank {int(r['rank_net_rate'])})<br>"
                    f"NET_COUNT: {r['NET_COUNT']:,.0f} (rank {int(r['rank_net_count'])})<br>"
                    f"IN: {r['IN_COUNT']:,.0f} ({r['IN_RATE']:.2f}/1k)<br>"
                    f"OUT: {r['OUT_COUNT']:,.0f} ({r['OUT_RATE']:.2f}/1k)<br>"
                    f"Small-pop: {flag_str}"
                )

            trace_list.append((ag, is_small))
            fig.add_trace(go.Scatter(
                x=subset["POP_AGE"],
                y=subset["NET_RATE"],
                mode="markers+text",
                text=subset["abbr"],
                textposition="top center",
                textfont=dict(size=7, color="gray"),
                marker=dict(
                    size=size_scaled.loc[idx],
                    color=marker_color,
                    symbol=marker_symbol,
                    opacity=0.7,
                    line=dict(width=1, color=edge_color),
                ),
                hovertext=hover_texts,
                hoverinfo="text",
                visible=(i == 0),
                name=label,
                showlegend=True,
            ))

    # Dropdown: one button per age group, shows both regular + small traces
    buttons = []
    for i, ag in enumerate(AGE_GROUPS):
        vis = [False] * len(trace_list)
        vis[i * n_traces_per_ag] = True      # regular
        vis[i * n_traces_per_ag + 1] = True  # small-pop
        denom_flag = ag in DENOM_EFFECT_AGS
        denom_note = " ⚠ denominator-effect signal" if denom_flag else ""
        buttons.append(dict(
            label=AG_LABELS[ag],
            method="update",
            args=[{"visible": vis},
                  {"title": (f"Size Diagnostic: POP_AGE vs NET_RATE — "
                             f"Age {AG_LABELS[ag]} (2024)<br>"
                             f"<sup>Bubble size ∝ |NET_COUNT|. "
                             f"◆ red = small-pop (bottom quintile).{denom_note}</sup>")}],
        ))

    fig.update_layout(
        title=("Size Diagnostic: POP_AGE vs NET_RATE — Age 18–24 (2024)<br>"
               "<sup>Bubble size ∝ |NET_COUNT|. ◆ red = small-pop (bottom quintile). "
               "⚠ denominator-effect signal</sup>"),
        xaxis_title="Age-Group Population (POP_AGE)",
        yaxis_title="Net Migration Rate per 1,000 (NET_RATE)",
        height=650, width=950,
        xaxis=dict(type="log", title="Age-Group Population (POP_AGE, log scale)"),
        legend=dict(orientation="h", yanchor="bottom", y=1.01,
                    xanchor="center", x=0.5),
        updatemenus=[dict(
            type="dropdown", direction="down",
            x=0.01, y=0.99,
            buttons=buttons, showactive=True,
        )],
        annotations=[dict(
            text=FOOTER_NOTE,
            xref="paper", yref="paper", x=0.5, y=-0.08, showarrow=False,
            font=dict(size=9, color="gray"), align="center",
        )],
    )

    fig.add_hline(y=0, line_dash="dash", line_color="black", opacity=0.4)

    save_html(fig, "proto7_size_diagnostic_compare.html")


# ── Main ──────────────────────────────────────────────────────────

def main():
    os.makedirs(OUTDIR, exist_ok=True)

    df, diag = load_data()
    print(f"Loaded: {len(df)} states (wide), {len(diag)} rows (long diagnostic)")

    proto5b_state_profiles(df, diag)
    proto7_size_diagnostic(df, diag)

    print(f"\n{'='*60}")
    print(f"  Size-diagnostic prototypes generated in {OUTDIR}/")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
