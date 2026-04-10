#!/usr/bin/env python3
"""
Focused Deep Dive Visualizations
=================================
Presentation-ready figures for REL_IN_25_34 and REL_IN_18_24.

Usage:
    python -m scripts.viz_focused_deep_dive
"""

from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats
import statsmodels.api as sm
import plotly.graph_objects as go
from plotly.subplots import make_subplots

PROJECT = Path(__file__).resolve().parent.parent
DATA_PATH = PROJECT / "data_processed" / "analysis_ready_specialization.csv"
SCREEN_PATH = PROJECT / "outputs" / "tables" / "focused_deep_dive" / "screening_summary.csv"
RESID_PATH = PROJECT / "outputs" / "tables" / "focused_deep_dive" / "selected_residuals.csv"
MODELS_PATH = PROJECT / "outputs" / "tables" / "focused_deep_dive" / "selected_models.csv"
FIG_DIR = PROJECT / "outputs" / "figures" / "focused_deep_dive"
FIG_DIR.mkdir(parents=True, exist_ok=True)

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

AGE_LABELS = {"25_34": "25\u201334", "18_24": "18\u201324"}

DIV_ONE = [
    [0.0, "#d95f02"], [0.25, "#fdb863"], [0.5, "#f7f7f7"],
    [0.75, "#80cdc1"], [1.0, "#1b7837"],
]
DIV_ZERO = [
    [0.0, "#b2182b"], [0.25, "#ef8a62"], [0.5, "#f7f7f7"],
    [0.75, "#67a9cf"], [1.0, "#2166ac"],
]

FONT = "system-ui, -apple-system, sans-serif"


def load_data():
    df = pd.read_csv(DATA_PATH, dtype={"state": str})
    df["state"] = df["state"].str.zfill(2)
    if "abbrev" not in df.columns:
        df["abbrev"] = df["state"].map(FIPS_TO_ABBREV)
    return df


def save(fig, name):
    fig.write_html(str(FIG_DIR / name), include_plotlyjs="cdn")


# =========================================================================
# Choropleth maps
# =========================================================================
def make_choropleth(df, col, title, subtitle, outname):
    vals = df[col]
    zmid = 1.0
    absdev = max(abs(vals.min() - zmid), abs(vals.max() - zmid)) or 0.1
    hover = [f"<b>{r['state_name']}</b><br>{col} = {r[col]:.3f}" for _, r in df.iterrows()]
    fig = go.Figure(go.Choropleth(
        locations=df["abbrev"], z=vals, locationmode="USA-states",
        colorscale=DIV_ONE, zmin=zmid - absdev, zmax=zmid + absdev,
        colorbar=dict(title="Ratio", thickness=12, len=0.6),
        text=hover, hovertemplate="%{text}<extra></extra>",
    ))
    fig.update_layout(
        title=dict(text=f"{title}<br><span style='font-size:12px;color:#666'>{subtitle}</span>", x=0.5, font=dict(size=16)),
        geo=dict(scope="usa", bgcolor="rgba(0,0,0,0)"),
        margin=dict(l=0, r=0, t=65, b=10), paper_bgcolor="white", font=dict(family=FONT),
    )
    save(fig, outname)


# =========================================================================
# Scatter plots
# =========================================================================
def make_scatter(df, dv, iv, title, subtitle, outname, highlight_states=None):
    x, y = df[iv], df[dv]
    mask = x.notna() & y.notna()
    coefs = np.polyfit(x[mask], y[mask], 1)
    x_line = np.linspace(x[mask].min(), x[mask].max(), 50)
    y_line = np.polyval(coefs, x_line)
    sp_rho, sp_p = stats.spearmanr(x[mask], y[mask])
    X = sm.add_constant(x[mask])
    m = sm.OLS(y[mask], X).fit()

    colors = []
    sizes = []
    hl = set(highlight_states or [])
    for a in df["abbrev"]:
        if a in hl:
            colors.append("#e31a1c")
            sizes.append(11)
        else:
            colors.append("#4292c6")
            sizes.append(7)

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=x_line, y=y_line, mode="lines",
                             line=dict(color="#bbb", dash="dash", width=1.5),
                             showlegend=False, hoverinfo="skip"))
    fig.add_trace(go.Scatter(
        x=x, y=y, mode="markers+text", text=df["abbrev"],
        textposition="top center", textfont=dict(size=7, color="#555"),
        marker=dict(color=colors, size=sizes, line=dict(width=0.5, color="white")),
        hovertemplate=f"<b>%{{text}}</b><br>{iv}: %{{x:.2f}}<br>{dv}: %{{y:.3f}}<extra></extra>",
        showlegend=False,
    ))
    fig.add_hline(y=1.0, line_dash="dot", line_color="#999", line_width=1,
                  annotation_text="1.0 = proportional", annotation_position="bottom right",
                  annotation_font_size=9, annotation_font_color="#999")
    fig.update_layout(
        title=dict(text=f"{title}<br><span style='font-size:11px;color:#666'>"
                        f"rho = {sp_rho:+.3f} (p = {sp_p:.4f})  |  adj R\u00b2 = {m.rsquared_adj:.3f}</span>",
                   x=0.5, font=dict(size=14)),
        xaxis_title=iv, yaxis_title=dv,
        margin=dict(l=50, r=20, t=65, b=45),
        paper_bgcolor="white", plot_bgcolor="#fafafa", font=dict(family=FONT),
    )
    save(fig, outname)


# =========================================================================
# Fitted vs actual
# =========================================================================
def make_fitted_actual(df, resid_df, model_id, dv, title, outname):
    rd = resid_df[resid_df["model_id"] == model_id].copy()
    fig = go.Figure()
    # 45-degree line
    mn = min(rd["actual"].min(), rd["predicted"].min()) - 0.05
    mx = max(rd["actual"].max(), rd["predicted"].max()) + 0.05
    fig.add_trace(go.Scatter(x=[mn, mx], y=[mn, mx], mode="lines",
                             line=dict(color="#ccc", dash="dash"), showlegend=False, hoverinfo="skip"))
    fig.add_trace(go.Scatter(
        x=rd["actual"], y=rd["predicted"], mode="markers+text",
        text=rd["abbrev"], textposition="top center", textfont=dict(size=7, color="#555"),
        marker=dict(size=7, color="#4292c6", line=dict(width=0.5, color="white")),
        hovertemplate="<b>%{text}</b><br>Actual: %{x:.3f}<br>Predicted: %{y:.3f}<extra></extra>",
        showlegend=False,
    ))
    fig.update_layout(
        title=dict(text=f"{title}<br><span style='font-size:11px;color:#666'>Dashed = perfect prediction</span>",
                   x=0.5, font=dict(size=14)),
        xaxis_title=f"Actual {dv}", yaxis_title=f"Predicted {dv}",
        margin=dict(l=50, r=20, t=65, b=45),
        paper_bgcolor="white", plot_bgcolor="#fafafa", font=dict(family=FONT),
    )
    save(fig, outname)


# =========================================================================
# Residual map
# =========================================================================
def make_residual_map(df, resid_df, model_id, title, subtitle, outname):
    rd = resid_df[resid_df["model_id"] == model_id].copy()
    merged = df[["abbrev", "state_name"]].merge(rd[["abbrev", "residual"]], on="abbrev")
    vals = merged["residual"]
    absmax = max(abs(vals.min()), abs(vals.max())) or 0.1
    hover = [f"<b>{r['state_name']}</b><br>Residual: {r['residual']:+.3f}" for _, r in merged.iterrows()]
    fig = go.Figure(go.Choropleth(
        locations=merged["abbrev"], z=vals, locationmode="USA-states",
        colorscale=DIV_ZERO, zmin=-absmax, zmax=absmax,
        colorbar=dict(title="Residual", thickness=12, len=0.6),
        text=hover, hovertemplate="%{text}<extra></extra>",
    ))
    fig.update_layout(
        title=dict(text=f"{title}<br><span style='font-size:11px;color:#666'>{subtitle}</span>",
                   x=0.5, font=dict(size=15)),
        geo=dict(scope="usa", bgcolor="rgba(0,0,0,0)"),
        margin=dict(l=0, r=0, t=65, b=10), paper_bgcolor="white", font=dict(family=FONT),
    )
    save(fig, outname)


# =========================================================================
# Ranking bar chart
# =========================================================================
def make_ranking_chart(df, dv, title, outname, n=10):
    sorted_df = df.sort_values(dv, ascending=False).reset_index(drop=True)
    top = sorted_df.head(n)
    bottom = sorted_df.tail(n).iloc[::-1]
    show = pd.concat([top, bottom])
    colors = ["#1b7837" if v > 1 else "#d95f02" for v in show[dv]]
    fig = go.Figure(go.Bar(
        y=show["abbrev"] + " " + show["state_name"],
        x=show[dv], orientation="h", marker_color=colors,
        text=[f"{v:.3f}" for v in show[dv]], textposition="outside",
        hovertemplate="<b>%{y}</b><br>" + dv + ": %{x:.3f}<extra></extra>",
    ))
    fig.add_vline(x=1.0, line_dash="dot", line_color="#999", line_width=1.5)
    fig.update_layout(
        title=dict(text=title, x=0.5, font=dict(size=14)),
        xaxis_title=dv,
        yaxis=dict(autorange="reversed"),
        margin=dict(l=130, r=60, t=50, b=40), height=max(500, len(show) * 24 + 100),
        paper_bgcolor="white", plot_bgcolor="#fafafa", font=dict(family=FONT),
    )
    save(fig, outname)


# =========================================================================
# Heatmap: Two-DV × 22-IV correlation
# =========================================================================
def make_correlation_heatmap(screen_df, outname):
    ivs = screen_df["iv"].tolist()
    rho_25 = screen_df["sp_rho_25_34"].values
    rho_18 = screen_df["sp_rho_18_24"].values
    # Sort by difference to highlight contrast
    order = np.argsort(rho_25 - rho_18)[::-1]
    ivs_sorted = [ivs[i] for i in order]
    rho_25_sorted = rho_25[order]
    rho_18_sorted = rho_18[order]

    fig = go.Figure()
    fig.add_trace(go.Heatmap(
        z=[rho_25_sorted, rho_18_sorted],
        x=ivs_sorted,
        y=["REL_IN 25\u201334", "REL_IN 18\u201324"],
        colorscale=DIV_ZERO, zmin=-0.7, zmax=0.7,
        text=[[f"{v:+.2f}" for v in rho_25_sorted],
              [f"{v:+.2f}" for v in rho_18_sorted]],
        texttemplate="%{text}", textfont=dict(size=10),
        colorbar=dict(title="Spearman rho", thickness=12),
    ))
    fig.update_layout(
        title=dict(text="Spearman Correlations: 25\u201334 vs 18\u201324 Inflow Specialization"
                        "<br><span style='font-size:11px;color:#666'>Sorted by contrast (25\u201334 minus 18\u201324). "
                        "Blue = positive, Red = negative.</span>",
                   x=0.5, font=dict(size=14)),
        xaxis=dict(tickangle=45, tickfont=dict(size=10)),
        margin=dict(l=100, r=20, t=70, b=100), height=280,
        paper_bgcolor="white", font=dict(family=FONT),
    )
    save(fig, outname)


# =========================================================================
# Heatmap: Model comparison
# =========================================================================
def make_model_comparison_heatmap(models_df, outname):
    labels = models_df["model_id"].tolist()
    short = [m.replace("M25_", "25-34: ").replace("M18_", "18-24: ").replace("_", " ").replace("+", " + ") for m in labels]
    metrics = ["adj_r2", "aic", "bic", "max_vif"]
    z = models_df[metrics].values.T.tolist()
    text = [[f"{v:.2f}" if abs(v) < 100 else f"{v:.1f}" for v in row] for row in z]
    fig = go.Figure(go.Heatmap(
        z=z, x=short, y=["Adj R\u00b2", "AIC", "BIC", "Max VIF"],
        text=text, texttemplate="%{text}", textfont=dict(size=11),
        colorscale="Viridis", showscale=False,
    ))
    fig.update_layout(
        title=dict(text="Model Comparison: Selected Candidates"
                        "<br><span style='font-size:11px;color:#666'>Higher adj R\u00b2 = better fit. "
                        "Lower AIC/BIC = better. VIF < 10 = acceptable.</span>",
                   x=0.5, font=dict(size=14)),
        xaxis=dict(tickangle=20, tickfont=dict(size=9)),
        margin=dict(l=80, r=20, t=70, b=110), height=300,
        paper_bgcolor="white", font=dict(family=FONT),
    )
    save(fig, outname)


# =========================================================================
# State spotlight
# =========================================================================
def make_state_spotlight(df, states, dv, title, outname):
    sub = df[df["abbrev"].isin(states)].sort_values(dv, ascending=False)
    fig = go.Figure(go.Bar(
        y=sub["abbrev"] + " " + sub["state_name"],
        x=sub[dv], orientation="h",
        marker_color=["#1b7837" if v > 1 else "#d95f02" for v in sub[dv]],
        text=[f"{v:.3f}" for v in sub[dv]], textposition="outside",
    ))
    fig.add_vline(x=1.0, line_dash="dot", line_color="#999")
    fig.update_layout(
        title=dict(text=title, x=0.5, font=dict(size=14)),
        xaxis_title=dv, yaxis=dict(autorange="reversed"),
        margin=dict(l=130, r=60, t=50, b=40), height=max(300, len(states) * 35 + 80),
        paper_bgcolor="white", plot_bgcolor="#fafafa", font=dict(family=FONT),
    )
    save(fig, outname)


# =========================================================================
# Main
# =========================================================================
def main():
    df = load_data()
    screen = pd.read_csv(SCREEN_PATH)
    resid = pd.read_csv(RESID_PATH)
    models = pd.read_csv(MODELS_PATH)
    count = 0

    # --- REL_IN_25_34 figures ---
    print("=== REL_IN_25_34 ===")

    make_choropleth(df, "REL_IN_25_34",
                    "Where Do 25\u201334 Year Olds Move? Inflow Specialization",
                    "> 1 = over-represented vs all-ages baseline. States attracting disproportionate young-adult inflow.",
                    "01_map_REL_IN_25_34.html"); count += 1; print(f"  [{count}] map")

    make_scatter(df, "REL_IN_25_34", "PRIV_AVG_PAY",
                 "High Wages Pull Young Adults",
                 "States with higher private-sector pay attract disproportionate 25\u201334 inflow",
                 "02_scatter_25_34_pay.html",
                 highlight_states=["NY", "MD", "NJ", "AK", "MA"]); count += 1; print(f"  [{count}] scatter pay")

    make_scatter(df, "REL_IN_25_34", "RPP",
                 "Cost of Living and Young-Adult Inflow",
                 "Higher regional price parity is associated with 25\u201334 over-representation",
                 "03_scatter_25_34_rpp.html",
                 highlight_states=["NY", "MD", "NJ", "CA", "HI"]); count += 1; print(f"  [{count}] scatter rpp")

    make_scatter(df, "REL_IN_25_34", "COMMUTE_MED",
                 "Urban Commute Patterns and Young-Adult Pull",
                 "Longer median commutes correlate with more 25\u201334 inflow specialization",
                 "04_scatter_25_34_commute.html",
                 highlight_states=["NY", "MD", "NJ"]); count += 1; print(f"  [{count}] scatter commute")

    make_fitted_actual(df, resid, "M25_2IV_PRIV_AVG_PAY+COMMUTE_MED", "REL_IN_25_34",
                       "Model Fit: 25\u201334 Inflow Specialization (2-IV)",
                       "05_fitted_actual_25_34.html"); count += 1; print(f"  [{count}] fitted-actual")

    make_residual_map(df, resid, "M25_2IV_PRIV_AVG_PAY+COMMUTE_MED",
                      "Model Residuals: 25\u201334 Inflow",
                      "Blue = model under-predicts (actual > expected). Red = over-predicts.",
                      "06_residual_map_25_34.html"); count += 1; print(f"  [{count}] residual map")

    make_ranking_chart(df, "REL_IN_25_34",
                       "Top and Bottom States: 25\u201334 Inflow Specialization",
                       "07_ranking_25_34.html"); count += 1; print(f"  [{count}] ranking")

    make_state_spotlight(df, ["NY", "AK", "MD", "NJ", "RI", "CO", "WA", "CA"],
                         "REL_IN_25_34",
                         "State Spotlight: 25\u201334 Inflow (Career-Stage Migration)",
                         "08_spotlight_25_34.html"); count += 1; print(f"  [{count}] spotlight")

    # --- REL_IN_18_24 figures ---
    print("\n=== REL_IN_18_24 ===")

    make_choropleth(df, "REL_IN_18_24",
                    "Where Do 18\u201324 Year Olds Move? Inflow Specialization",
                    "> 1 = over-represented vs all-ages baseline. Likely reflects college / student migration.",
                    "09_map_REL_IN_18_24.html"); count += 1; print(f"  [{count}] map")

    make_scatter(df, "REL_IN_18_24", "COMMUTE_MED",
                 "Short Commutes and Student Inflow",
                 "States with shorter commutes attract disproportionate 18\u201324 inflow (college towns)",
                 "10_scatter_18_24_commute.html",
                 highlight_states=["ND", "IA", "VT", "UT"]); count += 1; print(f"  [{count}] scatter commute")

    make_scatter(df, "REL_IN_18_24", "NRI_RISK_INDEX",
                 "Natural Hazard Risk and 18\u201324 Migration",
                 "Low-risk states attract more young movers relative to their total footprint",
                 "11_scatter_18_24_nri.html",
                 highlight_states=["ND", "IA", "VT", "UT"]); count += 1; print(f"  [{count}] scatter nri")

    make_scatter(df, "REL_IN_18_24", "MED_RENT",
                 "Rent Levels and 18\u201324 Inflow",
                 "Lower-rent states attract disproportionate 18\u201324 inflow",
                 "12_scatter_18_24_rent.html",
                 highlight_states=["ND", "IA", "VT", "UT"]); count += 1; print(f"  [{count}] scatter rent")

    make_fitted_actual(df, resid, "M18_3IV_COMMUTE_MED+VACANCY_RATE+TRANSIT_SHARE", "REL_IN_18_24",
                       "Model Fit: 18\u201324 Inflow Specialization (3-IV)",
                       "13_fitted_actual_18_24.html"); count += 1; print(f"  [{count}] fitted-actual")

    make_residual_map(df, resid, "M18_3IV_COMMUTE_MED+VACANCY_RATE+TRANSIT_SHARE",
                      "Model Residuals: 18\u201324 Inflow",
                      "Blue = model under-predicts (actual > expected). Red = over-predicts.",
                      "14_residual_map_18_24.html"); count += 1; print(f"  [{count}] residual map")

    make_ranking_chart(df, "REL_IN_18_24",
                       "Top and Bottom States: 18\u201324 Inflow Specialization",
                       "15_ranking_18_24.html"); count += 1; print(f"  [{count}] ranking")

    make_state_spotlight(df, ["ND", "IA", "VT", "UT", "RI", "MA", "WI", "NH"],
                         "REL_IN_18_24",
                         "State Spotlight: 18\u201324 Inflow (College / Student Migration)",
                         "16_spotlight_18_24.html"); count += 1; print(f"  [{count}] spotlight")

    # --- Cross-DV figures ---
    print("\n=== Cross-DV comparison ===")

    make_correlation_heatmap(screen, "17_heatmap_correlation.html")
    count += 1; print(f"  [{count}] correlation heatmap")

    make_model_comparison_heatmap(models, "18_heatmap_models.html")
    count += 1; print(f"  [{count}] model comparison heatmap")

    print(f"\nGenerated {count} figures in {FIG_DIR.relative_to(PROJECT)}")


if __name__ == "__main__":
    main()
