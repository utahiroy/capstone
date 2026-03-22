"""Phase A7: Visualization prototypes — exploratory sandbox.

Generates 6+ interactive HTML prototypes from A2–A6 outputs.
Each prototype is a standalone HTML file viewable in any browser.

A6 selected models are loaded dynamically from outputs/tables/a6_selected_models.csv
so that A7 stays synchronized with A6 outputs automatically.

Run:  python -m scripts.viz_prototypes

Prototypes:
  1a. Age-group NET_RATE choropleth (per-age autoscaling)
  1b. Age-group NET_RATE choropleth (common scale for cross-age comparison)
  2.  Key IV map explorer
  3.  Bivariate scatterplot selector (IV vs NET_RATE by age group)
  4.  Residual map explorer (A6 selected models)
  5.  State profile comparison dashboard (with sort toggle and rate toggle)
  6.  Model summary explorer (coefficients / fit / signs)
"""

import os
import sys

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import statsmodels.api as sm

from src.constants import AGE_GROUPS, STATE_FIPS
from src.fetch_crime import STATE_ABBR_TO_FIPS

# ── Setup ─────────────────────────────────────────────────────────

OUTDIR = "outputs/viz"
FIPS_TO_ABBR = {v: k for k, v in STATE_ABBR_TO_FIPS.items()}

AG_LABELS = {
    "18_24": "18–24", "25_34": "25–34", "35_54": "35–54",
    "55_64": "55–64", "65_PLUS": "65+",
}

PROVISIONAL_IVS = {"CRIME_VIOLENT_RATE", "NRI_RISK_INDEX"}

CAVEAT_NOTE = (
    "50 U.S. states only (DC excluded). 2024 cross-section. "
    "Associations, not causal estimates. "
    "CRIME_VIOLENT_RATE and NRI_RISK_INDEX use provisional/fallback data sources "
    "(see docs/deferred-iv-validation-memo.md). "
    "NRI_RISK_INDEX uses Dec 2025-vintage data (methodological exception to 2024-only design)."
)

CAVEAT_SHORT = (
    "50 states, 2024 cross-section, non-causal. "
    "* = provisional data source."
)


def load_data():
    path = "data_processed/analysis_ready.csv"
    if not os.path.exists(path):
        print(f"ERROR: {path} not found. Run `python -m scripts.build_dataset` first.")
        sys.exit(1)
    df = pd.read_csv(path, dtype={"state": str})
    df["state"] = df["state"].str.zfill(2)
    df["abbr"] = df["state"].map(FIPS_TO_ABBR)
    return df


def load_selected_models():
    """Load A6 selected models dynamically from CSV output."""
    path = "outputs/tables/a6_selected_models.csv"
    if not os.path.exists(path):
        print(f"ERROR: {path} not found. Run `python -m scripts.multiple_ols_a6` first.")
        sys.exit(1)
    sel_df = pd.read_csv(path)
    models = {}
    for _, row in sel_df.iterrows():
        ag = row["age_group"]
        ivs = [iv.strip() for iv in row["selected_ivs"].split(",")]
        models[ag] = ivs
    print(f"  Loaded A6 selected models from {path}:")
    for ag, ivs in models.items():
        print(f"    {ag}: {', '.join(ivs)}")
    return models, sel_df


def save_html(fig, filename):
    path = os.path.join(OUTDIR, filename)
    fig.write_html(path, include_plotlyjs="cdn")
    print(f"  Saved: {path}")
    return path


# ── Prototype 1a: NET_RATE choropleth (per-age autoscaling) ───────

def proto1a_choropleth(df):
    """Choropleth maps of NET_RATE with per-age-group autoscaling (exploratory)."""
    print("\n[1a] NET_RATE choropleth — per-age autoscaling")

    fig = go.Figure()

    for i, ag in enumerate(AGE_GROUPS):
        col = f"NET_RATE_{ag}"
        vmax = max(abs(df[col].min()), abs(df[col].max()))

        fig.add_trace(go.Choropleth(
            locations=df["abbr"],
            z=df[col],
            locationmode="USA-states",
            colorscale="RdBu",
            zmid=0, zmin=-vmax, zmax=vmax,
            colorbar_title="Net Rate<br>per 1,000",
            text=df["state_name"] + "<br>" + col + ": " + df[col].round(2).astype(str),
            hoverinfo="text",
            visible=(i == 0),
            name=AG_LABELS[ag],
        ))

    buttons = []
    for i, ag in enumerate(AGE_GROUPS):
        vis = [False] * len(AGE_GROUPS)
        vis[i] = True
        buttons.append(dict(
            label=AG_LABELS[ag], method="update",
            args=[{"visible": vis},
                  {"title": f"Net Migration Rate per 1,000 — Age {AG_LABELS[ag]} (2024)<br>"
                            "<sup>Per-age color scale (exploratory)</sup>"}],
        ))

    fig.update_layout(
        title=("Net Migration Rate per 1,000 — Age 18–24 (2024)<br>"
               "<sup>Per-age color scale (exploratory)</sup>"),
        geo=dict(scope="usa", projection_type="albers usa", showlakes=False),
        updatemenus=[dict(type="dropdown", direction="down", x=0.01, y=0.99,
                          buttons=buttons, showactive=True)],
        height=600, width=900,
        annotations=[dict(
            text=f"Source: ACS 2024 1-year. {CAVEAT_SHORT}",
            xref="paper", yref="paper", x=0.5, y=-0.05, showarrow=False,
            font=dict(size=10, color="gray"),
        )],
    )

    save_html(fig, "proto1a_choropleth_autoscale.html")


# ── Prototype 1b: NET_RATE choropleth (common scale) ─────────────

def proto1b_choropleth_common(df):
    """Choropleth maps of NET_RATE with common color scale across age groups."""
    print("\n[1b] NET_RATE choropleth — common scale")

    # Compute global max across all age groups
    rate_cols = [f"NET_RATE_{ag}" for ag in AGE_GROUPS]
    global_max = max(abs(df[rate_cols].min().min()), abs(df[rate_cols].max().max()))

    fig = go.Figure()

    for i, ag in enumerate(AGE_GROUPS):
        col = f"NET_RATE_{ag}"
        fig.add_trace(go.Choropleth(
            locations=df["abbr"],
            z=df[col],
            locationmode="USA-states",
            colorscale="RdBu",
            zmid=0, zmin=-global_max, zmax=global_max,
            colorbar_title="Net Rate<br>per 1,000",
            text=df["state_name"] + "<br>" + col + ": " + df[col].round(2).astype(str),
            hoverinfo="text",
            visible=(i == 0),
            name=AG_LABELS[ag],
        ))

    buttons = []
    for i, ag in enumerate(AGE_GROUPS):
        vis = [False] * len(AGE_GROUPS)
        vis[i] = True
        buttons.append(dict(
            label=AG_LABELS[ag], method="update",
            args=[{"visible": vis},
                  {"title": f"Net Migration Rate per 1,000 — Age {AG_LABELS[ag]} (2024)<br>"
                            f"<sup>Common scale ±{global_max:.1f} (cross-age comparison)</sup>"}],
        ))

    fig.update_layout(
        title=(f"Net Migration Rate per 1,000 — Age 18–24 (2024)<br>"
               f"<sup>Common scale ±{global_max:.1f} (cross-age comparison)</sup>"),
        geo=dict(scope="usa", projection_type="albers usa", showlakes=False),
        updatemenus=[dict(type="dropdown", direction="down", x=0.01, y=0.99,
                          buttons=buttons, showactive=True)],
        height=600, width=900,
        annotations=[dict(
            text=f"Source: ACS 2024 1-year. {CAVEAT_SHORT}",
            xref="paper", yref="paper", x=0.5, y=-0.05, showarrow=False,
            font=dict(size=10, color="gray"),
        )],
    )

    save_html(fig, "proto1b_choropleth_common_scale.html")


# ── Prototype 2: Key IV map explorer ──────────────────────────────

def proto2_iv_maps(df, selected_models):
    """Choropleth maps for key IVs used in A6 selected models."""
    print("\n[2] Key IV map explorer")

    key_ivs = sorted(set(iv for ivs in selected_models.values() for iv in ivs))

    fig = go.Figure()

    for i, iv in enumerate(key_ivs):
        prov_note = " [PROVISIONAL]" if iv in PROVISIONAL_IVS else ""
        fig.add_trace(go.Choropleth(
            locations=df["abbr"],
            z=df[iv],
            locationmode="USA-states",
            colorscale="Viridis",
            colorbar_title=iv,
            text=(df["state_name"] + "<br>" + iv + prov_note + ": "
                  + df[iv].round(2).astype(str)),
            hoverinfo="text",
            visible=(i == 0),
            name=iv,
        ))

    buttons = []
    for i, iv in enumerate(key_ivs):
        vis = [False] * len(key_ivs)
        vis[i] = True
        prov = " *" if iv in PROVISIONAL_IVS else ""
        buttons.append(dict(
            label=iv + prov, method="update",
            args=[{"visible": vis}, {"title": f"{iv}{prov} — State Distribution (2024)"}],
        ))

    fig.update_layout(
        title=f"{key_ivs[0]} — State Distribution (2024)",
        geo=dict(scope="usa", projection_type="albers usa", showlakes=False),
        updatemenus=[dict(type="dropdown", direction="down", x=0.01, y=0.99,
                          buttons=buttons, showactive=True)],
        height=600, width=900,
        annotations=[dict(
            text=f"IVs from A6 selected models. {CAVEAT_SHORT}",
            xref="paper", yref="paper", x=0.5, y=-0.05, showarrow=False,
            font=dict(size=10, color="gray"),
        )],
    )

    save_html(fig, "proto2_iv_maps.html")


# ── Prototype 3: Bivariate scatterplot selector ──────────────────

def proto3_scatterplots(df, selected_models):
    """Scatterplot: IV (x) vs NET_RATE (y), selectable by age group × IV."""
    print("\n[3] Bivariate scatterplot selector")

    key_ivs = sorted(set(iv for ivs in selected_models.values() for iv in ivs))

    fig = go.Figure()
    traces = []

    for ag in AGE_GROUPS:
        dv = f"NET_RATE_{ag}"
        for iv in key_ivs:
            traces.append((ag, iv))
            fig.add_trace(go.Scatter(
                x=df[iv], y=df[dv],
                mode="markers+text",
                text=df["abbr"],
                textposition="top center",
                textfont=dict(size=7),
                marker=dict(size=8, color="steelblue", opacity=0.7),
                hovertext=(df["state_name"] + "<br>" + iv + ": " + df[iv].round(2).astype(str)
                           + "<br>" + dv + ": " + df[dv].round(2).astype(str)),
                hoverinfo="text",
                visible=False,
                name=f"{AG_LABELS[ag]} vs {iv}",
            ))

    fig.data[0].visible = True

    combo_buttons = []
    for ai, ag in enumerate(AGE_GROUPS):
        for ii, iv in enumerate(key_ivs):
            idx = ai * len(key_ivs) + ii
            vis = [False] * len(traces)
            vis[idx] = True
            prov = " *" if iv in PROVISIONAL_IVS else ""
            combo_buttons.append(dict(
                label=f"{AG_LABELS[ag]} × {iv}",
                method="update",
                args=[{"visible": vis},
                      {"title": f"NET_RATE_{ag} vs {iv}{prov}",
                       "xaxis.title": iv + prov,
                       "yaxis.title": f"NET_RATE_{ag} (per 1,000)"}],
            ))

    fig.update_layout(
        title=f"NET_RATE_{AGE_GROUPS[0]} vs {key_ivs[0]}",
        xaxis_title=key_ivs[0],
        yaxis_title=f"NET_RATE_{AGE_GROUPS[0]} (per 1,000)",
        updatemenus=[dict(type="dropdown", direction="down", x=0.01, y=0.99,
                          buttons=combo_buttons, showactive=True)],
        height=600, width=800,
        annotations=[dict(
            text=f"Each dot = 1 state (n=50). No transforms. {CAVEAT_SHORT}",
            xref="paper", yref="paper", x=0.5, y=-0.08, showarrow=False,
            font=dict(size=10, color="gray"),
        )],
    )

    save_html(fig, "proto3_scatterplot_selector.html")


# ── Prototype 4: Residual map explorer ────────────────────────────

def proto4_residual_maps(df, selected_models):
    """Choropleth of OLS residuals from A6 selected models."""
    print("\n[4] Residual map explorer")

    fig = go.Figure()
    model_fits = {}

    for i, ag in enumerate(AGE_GROUPS):
        dv = f"NET_RATE_{ag}"
        ivs = selected_models[ag]
        y = df[dv].astype(float)
        X = sm.add_constant(df[ivs].astype(float))
        model = sm.OLS(y, X).fit()
        resid = model.resid
        model_fits[ag] = model

        vmax = max(abs(resid.min()), abs(resid.max()))

        prov_ivs = [iv for iv in ivs if iv in PROVISIONAL_IVS]
        prov_tag = " *" if prov_ivs else ""

        fig.add_trace(go.Choropleth(
            locations=df["abbr"],
            z=resid,
            locationmode="USA-states",
            colorscale="RdBu",
            zmid=0, zmin=-vmax, zmax=vmax,
            colorbar_title="Residual<br>(per 1,000)",
            text=(df["state_name"] + "<br>Residual: " + resid.round(3).astype(str)
                  + "<br>Actual: " + df[dv].round(2).astype(str)
                  + "<br>Predicted: " + model.fittedvalues.round(2).astype(str)),
            hoverinfo="text",
            visible=(i == 0),
            name=f"Resid {AG_LABELS[ag]}",
        ))

    buttons = []
    for i, ag in enumerate(AGE_GROUPS):
        vis = [False] * len(AGE_GROUPS)
        vis[i] = True
        ivs = selected_models[ag]
        formula = " + ".join(ivs)
        mdl = model_fits[ag]
        prov_ivs = [iv for iv in ivs if iv in PROVISIONAL_IVS]
        prov_tag = " (uses provisional IV)" if prov_ivs else ""
        buttons.append(dict(
            label=AG_LABELS[ag], method="update",
            args=[{"visible": vis},
                  {"title": (f"OLS Residuals — NET_RATE_{ag} ~ {formula}{prov_tag}<br>"
                             f"adj R² = {mdl.rsquared_adj:.3f}")}],
        ))

    mdl0 = model_fits[AGE_GROUPS[0]]
    ivs0 = selected_models[AGE_GROUPS[0]]

    fig.update_layout(
        title=(f"OLS Residuals — NET_RATE_{AGE_GROUPS[0]} ~ {' + '.join(ivs0)}<br>"
               f"adj R² = {mdl0.rsquared_adj:.3f}"),
        geo=dict(scope="usa", projection_type="albers usa", showlakes=False),
        updatemenus=[dict(type="dropdown", direction="down", x=0.01, y=0.99,
                          buttons=buttons, showactive=True)],
        height=600, width=900,
        annotations=[dict(
            text=(f"Red = underpredicted, Blue = overpredicted. {CAVEAT_SHORT}"),
            xref="paper", yref="paper", x=0.5, y=-0.05, showarrow=False,
            font=dict(size=10, color="gray"),
        )],
    )

    save_html(fig, "proto4_residual_maps.html")


# ── Prototype 5: State profile dashboard ─────────────────────────

def proto5_state_profiles(df):
    """State profiles with sort toggle and NET/IN/OUT rate toggle."""
    print("\n[5] State profile comparison dashboard")

    rate_types = {
        "NET_RATE": "Net Migration Rate",
        "IN_RATE": "In-Migration Rate",
        "OUT_RATE": "Out-Migration Rate",
    }

    sort_modes = {
        "avg_net": "Average NET_RATE",
        "alpha": "Alphabetical",
    }

    # Precompute sort orders
    net_cols = [f"NET_RATE_{ag}" for ag in AGE_GROUPS]
    avg_net = df[net_cols].mean(axis=1)
    order_by_avg = df.assign(avg=avg_net).sort_values("avg", ascending=True)["state_name"].tolist()
    order_alpha = sorted(df["state_name"].tolist(), reverse=True)

    fig = go.Figure()
    traces = []

    for rt_key, rt_label in rate_types.items():
        for sort_key, sort_label in sort_modes.items():
            rate_cols = [f"{rt_key}_{ag}" for ag in AGE_GROUPS]
            # Check columns exist
            missing = [c for c in rate_cols if c not in df.columns]
            if missing:
                continue

            state_order = order_by_avg if sort_key == "avg_net" else order_alpha

            df_long = df.melt(
                id_vars=["state", "abbr", "state_name"],
                value_vars=rate_cols,
                var_name="age_col",
                value_name="rate",
            )
            df_long["age_group"] = df_long["age_col"].str.replace(f"{rt_key}_", "")
            df_long["age_label"] = df_long["age_group"].map(AG_LABELS)

            colors = px.colors.qualitative.Set2
            for ai, ag in enumerate(AGE_GROUPS):
                sub = df_long[df_long["age_group"] == ag]
                # Reorder by state_order
                sub = sub.set_index("state_name").loc[
                    [s for s in state_order if s in sub["state_name"].values]
                ].reset_index()

                traces.append((rt_key, sort_key, ag))
                fig.add_trace(go.Bar(
                    x=sub["rate"],
                    y=sub["state_name"],
                    orientation="h",
                    name=AG_LABELS[ag],
                    marker_color=colors[ai % len(colors)],
                    visible=False,
                    hovertext=(sub["state_name"] + "<br>" + AG_LABELS[ag]
                               + ": " + sub["rate"].round(2).astype(str) + " per 1,000"),
                    hoverinfo="text",
                ))

    # Default: NET_RATE, avg_net sort — show all 5 age-group traces
    n_ags = len(AGE_GROUPS)
    for k in range(n_ags):
        fig.data[k].visible = True

    # Build dropdown buttons: rate_type × sort_mode
    combo_buttons = []
    trace_idx = 0
    for rt_key, rt_label in rate_types.items():
        for sort_key, sort_label in sort_modes.items():
            rate_cols = [f"{rt_key}_{ag}" for ag in AGE_GROUPS]
            if any(c not in df.columns for c in rate_cols):
                continue
            vis = [False] * len(traces)
            for k in range(n_ags):
                vis[trace_idx + k] = True
            combo_buttons.append(dict(
                label=f"{rt_label} / {sort_label}",
                method="update",
                args=[{"visible": vis},
                      {"title": f"State Profile: {rt_label} by Age Group (2024)<br>"
                                f"<sup>Sorted by {sort_label}</sup>"}],
            ))
            trace_idx += n_ags

    fig.update_layout(
        title="State Profile: Net Migration Rate by Age Group (2024)<br>"
              "<sup>Sorted by Average NET_RATE</sup>",
        barmode="group",
        height=1400, width=950,
        yaxis=dict(dtick=1, categoryorder="array", categoryarray=order_by_avg),
        xaxis_title="Rate per 1,000 population",
        legend=dict(orientation="h", yanchor="bottom", y=1.01, xanchor="center", x=0.5),
        updatemenus=[dict(type="dropdown", direction="down", x=0.01, y=0.99,
                          buttons=combo_buttons, showactive=True)],
        annotations=[dict(
            text=f"ACS 2024 1-year. {CAVEAT_SHORT}",
            xref="paper", yref="paper", x=0.5, y=-0.02, showarrow=False,
            font=dict(size=10, color="gray"),
        )],
    )

    fig.add_vline(x=0, line_dash="dash", line_color="black", opacity=0.5)

    save_html(fig, "proto5_state_profiles.html")


# ── Prototype 6: Model summary explorer ───────────────────────────

def proto6_model_summary(sel_df):
    """Coefficient dot plot for A6 selected models."""
    print("\n[6] Model summary explorer")

    coef_path = "outputs/tables/a6_selected_coefficients.csv"
    if not os.path.exists(coef_path):
        print(f"  WARNING: {coef_path} not found, skipping proto6")
        return

    coef_df = pd.read_csv(coef_path)
    coef_iv = coef_df[coef_df["term"] != "const"].copy()
    coef_iv["age_label"] = coef_iv["age_group"].map(AG_LABELS)
    coef_iv["sig"] = coef_iv["p_value"].apply(
        lambda p: "***" if p < 0.001 else "**" if p < 0.01 else "*" if p < 0.05 else "n.s.")
    coef_iv["provisional"] = coef_iv["term"].isin(PROVISIONAL_IVS)

    fig = go.Figure()

    colors = px.colors.qualitative.Set2
    for i, ag in enumerate(AGE_GROUPS):
        sub = coef_iv[coef_iv["age_group"] == ag]
        first = True
        for _, row in sub.iterrows():
            marker_symbol = "diamond" if row["provisional"] else "circle"
            fig.add_trace(go.Scatter(
                x=[row["coef"]],
                y=[f"{AG_LABELS[ag]}: {row['term']}"],
                error_x=dict(
                    type="data", symmetric=False,
                    array=[row["ci_upper"] - row["coef"]],
                    arrayminus=[row["coef"] - row["ci_lower"]],
                ),
                mode="markers",
                marker=dict(size=10, color=colors[i % len(colors)],
                            symbol=marker_symbol),
                name=AG_LABELS[ag],
                showlegend=first,
                hovertext=(f"{row['term']} ({AG_LABELS[ag]})<br>"
                           f"coef={row['coef']:.6f}<br>"
                           f"p={row['p_value']:.4f} {row['sig']}<br>"
                           f"VIF={row['vif']:.1f}<br>"
                           f"{'PROVISIONAL SOURCE' if row['provisional'] else ''}"),
                hoverinfo="text",
            ))
            first = False

    fig.add_vline(x=0, line_dash="dash", line_color="gray", opacity=0.5)

    fit_text = "<br>".join(
        f"{AG_LABELS.get(r['age_group'], r['age_group'])}: "
        f"adj R²={r['adjusted_r2']:.3f}, max VIF={r['max_vif']:.1f}"
        for _, r in sel_df.iterrows()
    )

    fig.update_layout(
        title="A6 Selected Model Coefficients with 95% CI",
        xaxis_title="Coefficient (unstandardized)",
        yaxis_title="",
        height=500, width=900,
        yaxis=dict(autorange="reversed"),
        annotations=[dict(
            text=fit_text,
            xref="paper", yref="paper", x=0.98, y=0.02,
            showarrow=False, font=dict(size=9, family="monospace"),
            align="right", bgcolor="rgba(255,255,255,0.8)",
            bordercolor="gray", borderwidth=1,
        ), dict(
            text=f"Diamond = provisional source. Bars = 95% CI. {CAVEAT_SHORT}",
            xref="paper", yref="paper", x=0.5, y=-0.1, showarrow=False,
            font=dict(size=10, color="gray"),
        )],
    )

    save_html(fig, "proto6_model_summary.html")


# ── Main ──────────────────────────────────────────────────────────

def main():
    os.makedirs(OUTDIR, exist_ok=True)
    df = load_data()
    print(f"Loaded data: {df.shape[0]} states, {df.shape[1]} columns")

    selected_models, sel_df = load_selected_models()

    proto1a_choropleth(df)
    proto1b_choropleth_common(df)
    proto2_iv_maps(df, selected_models)
    proto3_scatterplots(df, selected_models)
    proto4_residual_maps(df, selected_models)
    proto5_state_profiles(df)
    proto6_model_summary(sel_df)

    print(f"\n{'='*60}")
    print(f"  All prototypes generated in {OUTDIR}/")
    print(f"{'='*60}")
    print(f"\nFiles:")
    for f in sorted(os.listdir(OUTDIR)):
        if f.endswith(".html"):
            print(f"  {os.path.join(OUTDIR, f)}")


if __name__ == "__main__":
    main()
