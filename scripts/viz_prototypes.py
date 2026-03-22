"""Phase A7: Visualization prototypes — exploratory sandbox.

Generates 6 interactive HTML prototypes from A2–A6 outputs.
Each prototype is a standalone HTML file viewable in any browser.

Run:  python -m scripts.viz_prototypes

Prototypes:
  1. Age-group NET_RATE choropleth explorer
  2. Key IV map explorer
  3. Linked scatterplot explorer (IV vs NET_RATE by age group)
  4. Residual map explorer (A6 selected models)
  5. State profile comparison dashboard
  6. Model summary explorer (coefficients / fit / signs)
"""

import os
import sys

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
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

IV_COLS = [
    "POP", "LAND_AREA", "POP_DENS", "GDP", "RPP", "REAL_PCPI",
    "UNEMP", "PRIV_EMP", "PRIV_ESTAB", "PRIV_AVG_PAY",
    "PERMITS", "MED_RENT", "MED_HOMEVAL", "COST_BURDEN_ALL", "VACANCY_RATE",
    "COMMUTE_MED", "TRANSIT_SHARE", "BA_PLUS", "UNINSURED", "ELEC_PRICE_TOT",
    "CRIME_VIOLENT_RATE", "NRI_RISK_INDEX",
]

# A6 selected models (hardcoded from a6_selected_models.csv)
SELECTED_MODELS = {
    "18_24": ["COMMUTE_MED", "MED_HOMEVAL", "UNINSURED"],
    "25_34": ["NRI_RISK_INDEX", "PRIV_ESTAB", "PRIV_AVG_PAY"],
    "35_54": ["REAL_PCPI", "PERMITS"],
    "55_64": ["NRI_RISK_INDEX", "PERMITS", "POP_DENS"],
    "65_PLUS": ["UNINSURED", "MED_HOMEVAL"],
}

PROVISIONAL_IVS = {"CRIME_VIOLENT_RATE", "NRI_RISK_INDEX"}


def load_data():
    path = "data_processed/analysis_ready.csv"
    df = pd.read_csv(path, dtype={"state": str})
    df["state"] = df["state"].str.zfill(2)
    df["abbr"] = df["state"].map(FIPS_TO_ABBR)
    return df


def save_html(fig, filename, title=None):
    path = os.path.join(OUTDIR, filename)
    fig.write_html(path, include_plotlyjs="cdn")
    print(f"  Saved: {path}")
    return path


# ── Prototype 1: Age-group NET_RATE choropleth explorer ───────────

def proto1_choropleth(df):
    """Choropleth maps of NET_RATE for each age group, with dropdown selector."""
    print("\n[1] Age-group NET_RATE choropleth explorer")

    fig = go.Figure()

    for i, ag in enumerate(AGE_GROUPS):
        col = f"NET_RATE_{ag}"
        vmax = max(abs(df[col].min()), abs(df[col].max()))

        fig.add_trace(go.Choropleth(
            locations=df["abbr"],
            z=df[col],
            locationmode="USA-states",
            colorscale="RdBu",
            zmid=0,
            zmin=-vmax,
            zmax=vmax,
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
            label=AG_LABELS[ag],
            method="update",
            args=[{"visible": vis},
                  {"title": f"Interstate Net Migration Rate per 1,000 — Age {AG_LABELS[ag]} (2024)"}],
        ))

    fig.update_layout(
        title="Interstate Net Migration Rate per 1,000 — Age 18–24 (2024)",
        geo=dict(scope="usa", projection_type="albers usa", showlakes=False),
        updatemenus=[dict(
            type="dropdown", direction="down", x=0.01, y=0.99,
            buttons=buttons, showactive=True,
        )],
        height=600, width=900,
        annotations=[dict(
            text="Source: ACS 2024 1-year (B07001, B07401, B01001). 50 states only.",
            xref="paper", yref="paper", x=0.5, y=-0.05, showarrow=False,
            font=dict(size=10, color="gray"),
        )],
    )

    save_html(fig, "proto1_net_rate_choropleth.html")


# ── Prototype 2: Key IV map explorer ──────────────────────────────

def proto2_iv_maps(df):
    """Choropleth maps for key IVs used in A6 selected models."""
    print("\n[2] Key IV map explorer")

    # Collect unique IVs from selected models
    key_ivs = sorted(set(iv for ivs in SELECTED_MODELS.values() for iv in ivs))

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
            label=iv + prov,
            method="update",
            args=[{"visible": vis}, {"title": f"{iv}{prov} — State-Level Distribution (2024)"}],
        ))

    fig.update_layout(
        title=f"{key_ivs[0]} — State-Level Distribution (2024)",
        geo=dict(scope="usa", projection_type="albers usa", showlakes=False),
        updatemenus=[dict(
            type="dropdown", direction="down", x=0.01, y=0.99,
            buttons=buttons, showactive=True,
        )],
        height=600, width=900,
        annotations=[dict(
            text="* = provisional data source (see docs). IVs shown are those in A6 selected models.",
            xref="paper", yref="paper", x=0.5, y=-0.05, showarrow=False,
            font=dict(size=10, color="gray"),
        )],
    )

    save_html(fig, "proto2_iv_maps.html")


# ── Prototype 3: Linked scatterplot explorer ──────────────────────

def proto3_scatterplots(df):
    """Scatterplot: IV (x) vs NET_RATE (y), with dropdown for age group and IV."""
    print("\n[3] Linked scatterplot explorer")

    # Use IVs from A6 selected models
    key_ivs = sorted(set(iv for ivs in SELECTED_MODELS.values() for iv in ivs))

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

    # Make first trace visible
    fig.data[0].visible = True

    # Build nested dropdowns: age group buttons × IV buttons
    # Use two dropdown menus
    ag_buttons = []
    for ai, ag in enumerate(AGE_GROUPS):
        vis = [False] * len(traces)
        # Show first IV for this age group
        idx = ai * len(key_ivs)
        vis[idx] = True
        ag_buttons.append(dict(
            label=AG_LABELS[ag], method="update",
            args=[{"visible": vis},
                  {"title": f"NET_RATE_{ag} vs {key_ivs[0]}",
                   "xaxis.title": key_ivs[0],
                   "yaxis.title": f"NET_RATE_{ag}"}],
        ))

    iv_buttons = []
    for ii, iv in enumerate(key_ivs):
        vis = [False] * len(traces)
        # Show this IV for first age group
        idx = ii
        vis[idx] = True
        prov = " *" if iv in PROVISIONAL_IVS else ""
        iv_buttons.append(dict(
            label=iv + prov, method="update",
            args=[{"visible": vis},
                  {"title": f"NET_RATE_18_24 vs {iv}",
                   "xaxis.title": iv + prov,
                   "yaxis.title": "NET_RATE_18_24"}],
        ))

    # Simpler approach: one flat dropdown with ag×iv combos
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
        updatemenus=[dict(
            type="dropdown", direction="down", x=0.01, y=0.99,
            buttons=combo_buttons, showactive=True,
        )],
        height=600, width=800,
        annotations=[dict(
            text="* = provisional. Each dot = 1 state (n=50). No transforms applied.",
            xref="paper", yref="paper", x=0.5, y=-0.08, showarrow=False,
            font=dict(size=10, color="gray"),
        )],
    )

    save_html(fig, "proto3_scatterplots.html")


# ── Prototype 4: Residual map explorer ────────────────────────────

def proto4_residual_maps(df):
    """Choropleth of OLS residuals from A6 selected models."""
    print("\n[4] Residual map explorer")

    fig = go.Figure()
    resid_data = {}

    for i, ag in enumerate(AGE_GROUPS):
        dv = f"NET_RATE_{ag}"
        ivs = SELECTED_MODELS[ag]
        y = df[dv].astype(float)
        X = sm.add_constant(df[ivs].astype(float))
        model = sm.OLS(y, X).fit()
        resid = model.resid
        resid_data[ag] = resid

        vmax = max(abs(resid.min()), abs(resid.max()))

        prov_ivs = [iv for iv in ivs if iv in PROVISIONAL_IVS]
        prov_note = f" (uses {', '.join(prov_ivs)})" if prov_ivs else ""

        fig.add_trace(go.Choropleth(
            locations=df["abbr"],
            z=resid,
            locationmode="USA-states",
            colorscale="RdBu",
            zmid=0,
            zmin=-vmax,
            zmax=vmax,
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
        ivs = SELECTED_MODELS[ag]
        formula = " + ".join(ivs)
        adj_r2 = resid_data[ag]  # recompute for label
        y = df[f"NET_RATE_{ag}"].astype(float)
        X = sm.add_constant(df[ivs].astype(float))
        mdl = sm.OLS(y, X).fit()
        buttons.append(dict(
            label=AG_LABELS[ag],
            method="update",
            args=[{"visible": vis},
                  {"title": (f"OLS Residuals — NET_RATE_{ag} ~ {formula}<br>"
                             f"adj R² = {mdl.rsquared_adj:.3f}")}],
        ))

    ivs0 = SELECTED_MODELS[AGE_GROUPS[0]]
    y0 = df[f"NET_RATE_{AGE_GROUPS[0]}"].astype(float)
    X0 = sm.add_constant(df[ivs0].astype(float))
    mdl0 = sm.OLS(y0, X0).fit()

    fig.update_layout(
        title=(f"OLS Residuals — NET_RATE_{AGE_GROUPS[0]} ~ {' + '.join(ivs0)}<br>"
               f"adj R² = {mdl0.rsquared_adj:.3f}"),
        geo=dict(scope="usa", projection_type="albers usa", showlakes=False),
        updatemenus=[dict(
            type="dropdown", direction="down", x=0.01, y=0.99,
            buttons=buttons, showactive=True,
        )],
        height=600, width=900,
        annotations=[dict(
            text=("Red = model underpredicts (actual > predicted). "
                  "Blue = model overpredicts. Source: A6 selected models."),
            xref="paper", yref="paper", x=0.5, y=-0.05, showarrow=False,
            font=dict(size=10, color="gray"),
        )],
    )

    save_html(fig, "proto4_residual_maps.html")


# ── Prototype 5: State profile comparison dashboard ───────────────

def proto5_state_profiles(df):
    """Small-multiple bar chart: NET_RATE by age group for each state."""
    print("\n[5] State profile comparison dashboard")

    # Reshape to long format
    rate_cols = [f"NET_RATE_{ag}" for ag in AGE_GROUPS]
    df_long = df.melt(
        id_vars=["state", "abbr", "state_name"],
        value_vars=rate_cols,
        var_name="age_group_col",
        value_name="net_rate",
    )
    df_long["age_group"] = df_long["age_group_col"].str.replace("NET_RATE_", "")
    df_long["age_label"] = df_long["age_group"].map(AG_LABELS)

    # Sort states by overall average NET_RATE
    avg_rate = df[rate_cols].mean(axis=1)
    df["avg_net_rate"] = avg_rate
    state_order = df.sort_values("avg_net_rate", ascending=True)["state_name"].tolist()

    fig = px.bar(
        df_long,
        x="net_rate",
        y="state_name",
        color="age_label",
        orientation="h",
        barmode="group",
        category_orders={"state_name": state_order,
                         "age_label": [AG_LABELS[ag] for ag in AGE_GROUPS]},
        labels={"net_rate": "Net Migration Rate (per 1,000)",
                "state_name": "",
                "age_label": "Age Group"},
        title="State Profile: Net Migration Rate by Age Group (2024)",
        color_discrete_sequence=px.colors.qualitative.Set2,
    )

    fig.update_layout(
        height=1400,
        width=900,
        yaxis=dict(dtick=1),
        legend=dict(orientation="h", yanchor="bottom", y=1.01, xanchor="center", x=0.5),
        annotations=[dict(
            text="Source: ACS 2024 1-year. 50 states, DC excluded. Bars right of 0 = net in-migration.",
            xref="paper", yref="paper", x=0.5, y=-0.02, showarrow=False,
            font=dict(size=10, color="gray"),
        )],
    )

    fig.add_vline(x=0, line_dash="dash", line_color="black", opacity=0.5)

    save_html(fig, "proto5_state_profiles.html")


# ── Prototype 6: Model summary explorer ───────────────────────────

def proto6_model_summary(df):
    """Interactive table + coefficient dot plot for A6 selected models."""
    print("\n[6] Model summary explorer")

    # Load coefficient data
    coef_path = "outputs/tables/a6_selected_coefficients.csv"
    if not os.path.exists(coef_path):
        print(f"  WARNING: {coef_path} not found, skipping proto6")
        return

    coef_df = pd.read_csv(coef_path)
    # Exclude intercept for visualization
    coef_iv = coef_df[coef_df["term"] != "const"].copy()
    coef_iv["age_label"] = coef_iv["age_group"].map(AG_LABELS)
    coef_iv["sig"] = coef_iv["p_value"].apply(
        lambda p: "***" if p < 0.001 else "**" if p < 0.01 else "*" if p < 0.05 else "n.s.")
    coef_iv["provisional"] = coef_iv["term"].isin(PROVISIONAL_IVS)

    # Coefficient dot plot with CI
    fig = go.Figure()

    colors = px.colors.qualitative.Set2
    for i, ag in enumerate(AGE_GROUPS):
        sub = coef_iv[coef_iv["age_group"] == ag]
        for _, row in sub.iterrows():
            marker_symbol = "diamond" if row["provisional"] else "circle"
            fig.add_trace(go.Scatter(
                x=[row["coef"]],
                y=[f"{AG_LABELS[ag]}: {row['term']}"],
                error_x=dict(
                    type="data",
                    symmetric=False,
                    array=[row["ci_upper"] - row["coef"]],
                    arrayminus=[row["coef"] - row["ci_lower"]],
                ),
                mode="markers",
                marker=dict(size=10, color=colors[i % len(colors)],
                            symbol=marker_symbol),
                name=AG_LABELS[ag],
                showlegend=(sub.index.tolist().index(row.name) == 0),
                hovertext=(f"{row['term']} ({AG_LABELS[ag]})<br>"
                           f"coef={row['coef']:.6f}<br>"
                           f"p={row['p_value']:.4f} {row['sig']}<br>"
                           f"VIF={row['vif']:.1f}<br>"
                           f"{'PROVISIONAL' if row['provisional'] else ''}"),
                hoverinfo="text",
            ))

    fig.add_vline(x=0, line_dash="dash", line_color="gray", opacity=0.5)

    # Add model fit summary as annotation
    sel_path = "outputs/tables/a6_selected_models.csv"
    sel_df = pd.read_csv(sel_path)
    fit_text = "<br>".join(
        f"{AG_LABELS.get(r['age_group'], r['age_group'])}: "
        f"adj R²={r['adjusted_r2']:.3f}, max VIF={r['max_vif']:.1f}"
        for _, r in sel_df.iterrows()
    )

    fig.update_layout(
        title="A6 Selected Model Coefficients with 95% CI",
        xaxis_title="Coefficient (unstandardized)",
        yaxis_title="",
        height=500,
        width=900,
        yaxis=dict(autorange="reversed"),
        annotations=[dict(
            text=fit_text,
            xref="paper", yref="paper", x=0.98, y=0.02,
            showarrow=False, font=dict(size=9, family="monospace"),
            align="right", bgcolor="rgba(255,255,255,0.8)",
            bordercolor="gray", borderwidth=1,
        ), dict(
            text="Diamond markers = provisional data source. Bars = 95% CI.",
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

    proto1_choropleth(df)
    proto2_iv_maps(df)
    proto3_scatterplots(df)
    proto4_residual_maps(df)
    proto5_state_profiles(df)
    proto6_model_summary(df)

    print(f"\n{'='*60}")
    print(f"  All prototypes generated in {OUTDIR}/")
    print(f"{'='*60}")
    print(f"\nFiles:")
    for f in sorted(os.listdir(OUTDIR)):
        if f.endswith(".html") or f.endswith(".md"):
            print(f"  {os.path.join(OUTDIR, f)}")


if __name__ == "__main__":
    main()
