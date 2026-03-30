#!/usr/bin/env python3
"""
A8 Reactive Visualization Dashboard — Research Polish (A8-3)
=============================================================
Consolidates A7 prototypes into a coordinated Dash application with
research-interpretability enhancements.

Run:
    pip install -r requirements.txt
    python scripts/a8_dashboard.py

Then open http://127.0.0.1:8050 in a browser.

Panels (A8-3):
  Row 1: Choropleth map  |  IV vs NET_RATE scatter
  Row 2: Residual map     |  State profile
  Row 3: Ranking table (with denominator context)
  Footer: Methodology notes
"""

from pathlib import Path

import numpy as np
import pandas as pd

try:
    import dash
    from dash import dcc, html, dash_table, Input, Output, State, ctx
    import plotly.graph_objects as go

    DASH_AVAILABLE = True
except ImportError:
    DASH_AVAILABLE = False

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = PROJECT_ROOT / "data_processed" / "analysis_ready.csv"
MODELS_PATH = PROJECT_ROOT / "outputs" / "tables" / "a6_selected_models.csv"
COEFFICIENTS_PATH = (
    PROJECT_ROOT / "outputs" / "tables" / "a6_selected_coefficients.csv"
)

AGE_GROUPS = ["18_24", "25_34", "35_54", "55_64", "65_PLUS"]
AGE_LABELS = {
    "18_24": "18\u201324",
    "25_34": "25\u201334",
    "35_54": "35\u201354",
    "55_64": "55\u201364",
    "65_PLUS": "65+",
}

# FIPS code -> two-letter abbreviation (50 states only)
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

# Diverging color scale centered at 0 (red = negative, blue = positive)
DIVERGING_SCALE = [
    [0.0, "#b2182b"], [0.25, "#ef8a62"], [0.5, "#f7f7f7"],
    [0.75, "#67a9cf"], [1.0, "#2166ac"],
]

# Bottom-N states by POP_AGE are flagged as small-denominator
SMALL_POP_N = 5

# Adj R-squared threshold below which a warning is shown
WEAK_FIT_THRESHOLD = 0.05

# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------


def load_data() -> pd.DataFrame:
    """Load the 50-state analysis-ready dataset and add abbreviations."""
    df = pd.read_csv(DATA_PATH, dtype={"state": str})
    df["state"] = df["state"].str.zfill(2)
    df["abbrev"] = df["state"].map(FIPS_TO_ABBREV)
    return df


def load_models() -> pd.DataFrame:
    """Load A6 selected models (one row per age group)."""
    return pd.read_csv(MODELS_PATH)


def load_coefficients() -> pd.DataFrame:
    """Load A6 coefficient estimates."""
    return pd.read_csv(COEFFICIENTS_PATH)


def get_ivs_for_age(models_df: pd.DataFrame, age_group: str) -> list[str]:
    """Return the list of IVs for a given age group from A6 selected models."""
    row = models_df.loc[models_df["age_group"] == age_group]
    if row.empty:
        return []
    iv_str = row.iloc[0]["selected_ivs"]
    return [iv.strip() for iv in iv_str.split(",")]


def get_adj_r2_for_age(models_df: pd.DataFrame, age_group: str) -> float:
    """Return adjusted R-squared for the selected model of an age group."""
    row = models_df.loc[models_df["age_group"] == age_group]
    if row.empty:
        return float("nan")
    return float(row.iloc[0]["adjusted_r2"])


def get_formula_for_age(models_df: pd.DataFrame, age_group: str) -> str:
    """Return the model formula string for an age group."""
    row = models_df.loc[models_df["age_group"] == age_group]
    if row.empty:
        return ""
    return str(row.iloc[0]["formula"])


def compute_predicted_and_residuals(
    df: pd.DataFrame, coef_df: pd.DataFrame, age_group: str
) -> tuple[pd.Series, pd.Series]:
    """Compute predicted NET_RATE and residuals from A6 coefficients."""
    dv_col = f"NET_RATE_{age_group}"
    age_coefs = coef_df[coef_df["age_group"] == age_group]
    if age_coefs.empty:
        nans = pd.Series(np.nan, index=df.index)
        return nans, nans
    const_val = float(
        age_coefs.loc[age_coefs["term"] == "const", "coef"].iloc[0]
    )
    predicted = pd.Series(const_val, index=df.index)
    iv_rows = age_coefs[age_coefs["term"] != "const"]
    for _, row in iv_rows.iterrows():
        term = row["term"]
        if term in df.columns:
            predicted = predicted + float(row["coef"]) * df[term]
    residual = df[dv_col] - predicted
    return predicted, residual


def get_small_pop_states(
    df: pd.DataFrame, age_group: str, n: int = SMALL_POP_N
) -> set[str]:
    """Return abbreviations of the N smallest-denominator states."""
    pop_col = f"POP_AGE_{age_group}"
    if pop_col not in df.columns:
        return set()
    bottom = df.nsmallest(n, pop_col)
    return set(bottom["abbrev"].tolist())


def fit_quality_note(adj_r2: float) -> str:
    """Return a brief interpretive label for model fit quality."""
    if adj_r2 < 0:
        return "no explanatory power"
    if adj_r2 < WEAK_FIT_THRESHOLD:
        return "very weak fit"
    if adj_r2 < 0.10:
        return "weak fit"
    if adj_r2 < 0.25:
        return "modest fit"
    return "moderate fit"


# ---------------------------------------------------------------------------
# Layout builders
# ---------------------------------------------------------------------------

FONT = "system-ui, -apple-system, sans-serif"
PANEL_STYLE = {
    "border": "1px solid #e0e0e0",
    "borderRadius": "4px",
    "backgroundColor": "white",
    "padding": "4px",
}


def build_control_bar() -> html.Div:
    """Top control bar with age-group dropdown, metric toggle, and IV dropdown."""
    return html.Div(
        id="control-bar",
        children=[
            html.Label("Age group:", style={"fontWeight": "bold"}),
            dcc.Dropdown(
                id="age-group-dropdown",
                options=[
                    {"label": AGE_LABELS[ag], "value": ag} for ag in AGE_GROUPS
                ],
                value=AGE_GROUPS[0],
                clearable=False,
                style={"width": "130px"},
            ),
            html.Label(
                "Map metric:",
                style={"marginLeft": "16px", "fontWeight": "bold"},
            ),
            dcc.RadioItems(
                id="metric-toggle",
                options=[
                    {"label": "NET_RATE (per 1k)", "value": "NET_RATE"},
                    {"label": "NET_COUNT", "value": "NET_COUNT"},
                ],
                value="NET_RATE",
                inline=True,
                style={"fontSize": "13px"},
                inputStyle={"marginRight": "4px"},
                labelStyle={"marginRight": "12px"},
            ),
            html.Label(
                "Explanatory variable:",
                style={"marginLeft": "16px", "fontWeight": "bold"},
            ),
            dcc.Dropdown(
                id="iv-dropdown",
                options=[],
                value=None,
                clearable=False,
                style={"width": "200px"},
            ),
            html.Div(style={"flex": "1"}),
            html.H3(
                "A8 Migration Dashboard",
                style={"margin": "0", "whiteSpace": "nowrap", "fontSize": "18px"},
            ),
        ],
        style={
            "display": "flex",
            "alignItems": "center",
            "gap": "8px",
            "padding": "8px 16px",
            "borderBottom": "2px solid #ddd",
            "fontFamily": FONT,
            "flexWrap": "wrap",
        },
    )


def build_map_panel() -> html.Div:
    return html.Div(
        children=[dcc.Graph(id="choropleth-map", style={"height": "100%"})],
        style={**PANEL_STYLE, "height": "400px"},
    )


def build_scatter_panel() -> html.Div:
    return html.Div(
        children=[dcc.Graph(id="scatter-plot", style={"height": "100%"})],
        style={**PANEL_STYLE, "height": "400px"},
    )


def build_residual_panel() -> html.Div:
    return html.Div(
        children=[dcc.Graph(id="residual-map", style={"height": "100%"})],
        style={**PANEL_STYLE, "height": "380px"},
    )


def build_profile_panel() -> html.Div:
    return html.Div(
        children=[
            html.H4(
                id="profile-title",
                children="Click a state to see its migration profile",
                style={"margin": "4px 8px", "fontFamily": FONT, "fontSize": "14px"},
            ),
            dcc.Graph(id="profile-bars", style={"height": "calc(100% - 32px)"}),
        ],
        style={**PANEL_STYLE, "height": "380px"},
    )


def build_ranking_panel() -> html.Div:
    return html.Div(
        children=[
            html.H4(
                id="ranking-title",
                children="Top / Bottom States",
                style={"margin": "4px 8px", "fontFamily": FONT, "fontSize": "14px"},
            ),
            dash_table.DataTable(
                id="ranking-table",
                columns=[
                    {"name": "#", "id": "rank"},
                    {"name": "State", "id": "state_name"},
                    {"name": "NET_RATE", "id": "net_rate", "type": "numeric",
                     "format": {"specifier": ".2f"}},
                    {"name": "NET_COUNT", "id": "net_count", "type": "numeric",
                     "format": {"specifier": ","}},
                    {"name": "POP_AGE", "id": "pop_age", "type": "numeric",
                     "format": {"specifier": ","}},
                    {"name": "Flag", "id": "flag"},
                ],
                data=[],
                row_selectable="single",
                selected_rows=[],
                style_table={"overflowY": "auto", "maxHeight": "280px"},
                style_cell={
                    "textAlign": "left",
                    "padding": "3px 6px",
                    "fontFamily": FONT,
                    "fontSize": "12px",
                },
                style_header={"fontWeight": "bold", "fontSize": "12px"},
            ),
        ],
        style={**PANEL_STYLE, "height": "340px"},
    )


def build_footnotes() -> html.Div:
    """Methodology footnotes at the bottom of the dashboard."""
    notes = [
        html.Strong("Color: "),
        html.Span(
            "blue", style={"color": "#2166ac", "fontWeight": "bold"}
        ),
        " = net in-migration, ",
        html.Span(
            "red", style={"color": "#b2182b", "fontWeight": "bold"}
        ),
        " = net out-migration. ",
        html.Br(),
        html.Strong("Rates "),
        "are per 1,000 age-group population (POP_AGE). ",
        "States with small POP_AGE denominators are flagged ",
        html.Span("\u26a0", style={"color": "#d4a017"}),
        " because their rates may be volatile. ",
        html.Br(),
        html.Strong("Models: "),
        "A6 canonical 2-IV OLS selected by adjusted R\u00b2 with VIF < 10. "
        "Most age groups show weak or negligible explanatory power "
        "with the current 22-IV framework. ",
        html.Br(),
        html.Strong("18\u201324 caveat: "),
        "this age group likely captures substantial college-related migration "
        "and should not be interpreted as purely job-driven. ",
        html.Br(),
        html.Strong("Residuals: "),
        "positive residual (blue) = model under-predicts actual in-migration; "
        "negative residual (red) = model under-predicts out-migration. ",
        html.Br(),
        html.Strong("Data: "),
        "2024 ACS 1-year state-level migration flows + BEA/BLS/Census/FEMA IVs. "
        "50 U.S. states only (DC and territories excluded).",
    ]
    return html.Div(
        notes,
        style={
            "padding": "8px 16px",
            "fontSize": "11px",
            "color": "#666",
            "fontFamily": FONT,
            "lineHeight": "1.6",
            "borderTop": "1px solid #ddd",
            "marginTop": "4px",
        },
    )


def build_layout() -> html.Div:
    return html.Div(
        [
            dcc.Store(id="selected-state", data=None),
            build_control_bar(),
            # Row 1: map + scatter
            html.Div(
                [build_map_panel(), build_scatter_panel()],
                style={
                    "display": "grid",
                    "gridTemplateColumns": "1fr 1fr",
                    "gap": "6px",
                    "padding": "6px 8px 2px",
                },
            ),
            # Row 2: residual + profile
            html.Div(
                [build_residual_panel(), build_profile_panel()],
                style={
                    "display": "grid",
                    "gridTemplateColumns": "1fr 1fr",
                    "gap": "6px",
                    "padding": "2px 8px",
                },
            ),
            # Row 3: ranking (full width)
            html.Div(
                [build_ranking_panel()],
                style={"padding": "2px 8px"},
            ),
            # Footnotes
            build_footnotes(),
        ],
        style={"backgroundColor": "#f5f5f5", "fontFamily": FONT},
    )


# ---------------------------------------------------------------------------
# Callbacks
# ---------------------------------------------------------------------------


def register_callbacks(
    app: dash.Dash,
    df: pd.DataFrame,
    models_df: pd.DataFrame,
    coef_df: pd.DataFrame,
):
    """Register all Dash callbacks."""

    # -- 1. Age group -> IV dropdown options --------------------------------
    @app.callback(
        Output("iv-dropdown", "options"),
        Output("iv-dropdown", "value"),
        Input("age-group-dropdown", "value"),
    )
    def update_iv_dropdown(age_group):
        ivs = get_ivs_for_age(models_df, age_group)
        options = [{"label": iv, "value": iv} for iv in ivs]
        return options, ivs[0] if ivs else None

    # -- 2. State selection from map, scatter, or ranking ------------------
    @app.callback(
        Output("selected-state", "data"),
        Input("choropleth-map", "clickData"),
        Input("scatter-plot", "clickData"),
        Input("ranking-table", "selected_rows"),
        State("ranking-table", "data"),
        State("selected-state", "data"),
        prevent_initial_call=True,
    )
    def update_selected_state(
        map_click, scatter_click, ranking_rows, ranking_data, current_state
    ):
        triggered = ctx.triggered_id
        if triggered == "choropleth-map" and map_click:
            loc = map_click["points"][0].get("location")
            if loc:
                return loc
        if triggered == "scatter-plot" and scatter_click:
            text = scatter_click["points"][0].get("text", "")
            if text:
                return text
        if triggered == "ranking-table" and ranking_rows:
            idx = ranking_rows[0]
            if idx < len(ranking_data):
                return ranking_data[idx].get("abbrev")
        return dash.no_update

    # -- 3. Choropleth map -------------------------------------------------
    @app.callback(
        Output("choropleth-map", "figure"),
        Input("age-group-dropdown", "value"),
        Input("metric-toggle", "value"),
        Input("selected-state", "data"),
    )
    def render_map(age_group, metric, selected_state):
        col = f"{metric}_{age_group}"
        pop_col = f"POP_AGE_{age_group}"
        vals = df[col]
        abs_max = max(abs(vals.min()), abs(vals.max())) or 1
        small_pop = get_small_pop_states(df, age_group)

        unit = "per 1,000" if metric == "NET_RATE" else "persons"
        label = f"Net Migration {'Rate' if metric == 'NET_RATE' else 'Count'}"

        # Build hover text with POP_AGE context
        hover_texts = []
        for _, r in df.iterrows():
            flag = " \u26a0 small POP" if r["abbrev"] in small_pop else ""
            hover_texts.append(
                f"<b>{r['state_name']}</b>{flag}<br>"
                f"{col}: {r[col]:,.2f}<br>"
                f"POP_AGE: {r[pop_col]:,.0f}"
            )

        fig = go.Figure()
        fig.add_trace(
            go.Choropleth(
                locations=df["abbrev"],
                z=vals,
                locationmode="USA-states",
                colorscale=DIVERGING_SCALE,
                zmin=-abs_max,
                zmax=abs_max,
                colorbar=dict(title=dict(text=metric), thickness=12, len=0.6),
                text=hover_texts,
                hovertemplate="%{text}<extra></extra>",
            )
        )

        # Mark small-pop states with triangles
        small_df = df[df["abbrev"].isin(small_pop)]
        if not small_df.empty:
            fig.add_trace(
                go.Scattergeo(
                    locations=small_df["abbrev"],
                    locationmode="USA-states",
                    mode="markers",
                    marker=dict(
                        size=8, color="#d4a017", symbol="triangle-up",
                        line=dict(width=0.5, color="white"),
                    ),
                    text=[f"{r['state_name']} (small POP_AGE)"
                          for _, r in small_df.iterrows()],
                    hovertemplate="%{text}<extra>\u26a0</extra>",
                    showlegend=False,
                    name="small POP_AGE",
                )
            )

        # Highlight selected state
        if selected_state and selected_state in df["abbrev"].values:
            row = df.loc[df["abbrev"] == selected_state].iloc[0]
            fig.add_trace(
                go.Scattergeo(
                    locations=[selected_state],
                    locationmode="USA-states",
                    mode="markers",
                    marker=dict(
                        size=14, color="black", symbol="star",
                        line=dict(width=1, color="white"),
                    ),
                    text=[row["state_name"]],
                    hovertemplate="<b>%{text}</b><extra>selected</extra>",
                    showlegend=False,
                )
            )

        fig.update_layout(
            title=dict(
                text=f"{label} \u2014 {AGE_LABELS.get(age_group, age_group)} ({unit})",
                x=0.5,
                font=dict(size=14),
            ),
            geo=dict(scope="usa", bgcolor="rgba(0,0,0,0)"),
            margin=dict(l=0, r=0, t=40, b=0),
            paper_bgcolor="rgba(0,0,0,0)",
            dragmode=False,
        )
        return fig

    # -- 4. Scatter plot ---------------------------------------------------
    @app.callback(
        Output("scatter-plot", "figure"),
        Input("age-group-dropdown", "value"),
        Input("iv-dropdown", "value"),
        Input("selected-state", "data"),
    )
    def render_scatter(age_group, iv, selected_state):
        dv_col = f"NET_RATE_{age_group}"
        adj_r2 = get_adj_r2_for_age(models_df, age_group)
        quality = fit_quality_note(adj_r2)

        if iv is None or iv not in df.columns:
            fig = go.Figure()
            fig.update_layout(title="Select an explanatory variable")
            return fig

        x = df[iv]
        y = df[dv_col]
        small_pop = get_small_pop_states(df, age_group)

        # Point styling
        colors = []
        sizes = []
        symbols = []
        for abbr in df["abbrev"]:
            is_sel = abbr == selected_state
            is_small = abbr in small_pop
            colors.append("black" if is_sel else ("#d4a017" if is_small else "#5a8dbc"))
            sizes.append(12 if is_sel else 7)
            symbols.append("star" if is_sel else ("triangle-up" if is_small else "circle"))

        fig = go.Figure()

        # OLS trendline
        mask = x.notna() & y.notna()
        if mask.sum() > 2:
            coefs = np.polyfit(x[mask], y[mask], 1)
            x_line = np.linspace(x[mask].min(), x[mask].max(), 50)
            y_line = np.polyval(coefs, x_line)
            fig.add_trace(
                go.Scatter(
                    x=x_line, y=y_line,
                    mode="lines",
                    line=dict(color="#aaa", dash="dash", width=1.5),
                    showlegend=False,
                    hoverinfo="skip",
                )
            )

        # Scatter points
        fig.add_trace(
            go.Scatter(
                x=x,
                y=y,
                mode="markers+text",
                marker=dict(
                    color=colors, size=sizes, symbol=symbols,
                    line=dict(width=0.5, color="white"),
                ),
                text=df["abbrev"],
                textposition="top center",
                textfont=dict(size=8, color="#555"),
                hovertemplate=(
                    "<b>%{text}</b><br>"
                    f"{iv}: " + "%{x:.2f}<br>"
                    f"{dv_col}: " + "%{y:.2f}<extra></extra>"
                ),
                showlegend=False,
            )
        )

        # Title with fit quality warning
        r2_text = f"adj R\u00b2 = {adj_r2:.4f}"
        if adj_r2 < WEAK_FIT_THRESHOLD:
            r2_text += f" \u26a0 {quality}"

        fig.update_layout(
            title=dict(
                text=(
                    f"{iv} vs NET_RATE \u2014 "
                    f"{AGE_LABELS.get(age_group, age_group)}"
                    f"<br><span style='font-size:11px;color:#888'>"
                    f"{r2_text}</span>"
                ),
                x=0.5,
                font=dict(size=13),
            ),
            xaxis_title=iv,
            yaxis_title=f"NET_RATE_{age_group} (per 1,000)",
            margin=dict(l=50, r=20, t=60, b=40),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="#fafafa",
        )
        return fig

    # -- 5. Residual map ---------------------------------------------------
    @app.callback(
        Output("residual-map", "figure"),
        Input("age-group-dropdown", "value"),
        Input("selected-state", "data"),
    )
    def render_residual_map(age_group, selected_state):
        adj_r2 = get_adj_r2_for_age(models_df, age_group)
        formula = get_formula_for_age(models_df, age_group)
        quality = fit_quality_note(adj_r2)
        predicted, residuals = compute_predicted_and_residuals(
            df, coef_df, age_group
        )

        abs_max = max(abs(residuals.min()), abs(residuals.max())) or 1

        hover_texts = []
        for i, (_, r) in enumerate(df.iterrows()):
            dv_col = f"NET_RATE_{age_group}"
            hover_texts.append(
                f"<b>{r['state_name']}</b><br>"
                f"Actual: {r[dv_col]:+.2f}<br>"
                f"Predicted: {predicted.iloc[i]:+.2f}<br>"
                f"Residual: {residuals.iloc[i]:+.2f}"
            )

        fig = go.Figure()
        fig.add_trace(
            go.Choropleth(
                locations=df["abbrev"],
                z=residuals,
                locationmode="USA-states",
                colorscale=DIVERGING_SCALE,
                zmin=-abs_max,
                zmax=abs_max,
                colorbar=dict(
                    title=dict(text="Residual"),
                    thickness=12,
                    len=0.6,
                ),
                text=hover_texts,
                hovertemplate="%{text}<extra></extra>",
            )
        )

        # Highlight selected state
        if selected_state and selected_state in df["abbrev"].values:
            row = df.loc[df["abbrev"] == selected_state].iloc[0]
            idx = df.index[df["abbrev"] == selected_state][0]
            fig.add_trace(
                go.Scattergeo(
                    locations=[selected_state],
                    locationmode="USA-states",
                    mode="markers",
                    marker=dict(
                        size=14, color="black", symbol="star",
                        line=dict(width=1, color="white"),
                    ),
                    text=[
                        f"{row['state_name']}: "
                        f"resid = {residuals.loc[idx]:+.2f}"
                    ],
                    hovertemplate="<b>%{text}</b><extra>selected</extra>",
                    showlegend=False,
                )
            )

        # Subtitle with model formula and fit warning
        subtitle = f"{formula}  |  adj R\u00b2 = {adj_r2:.4f} ({quality})"

        fig.update_layout(
            title=dict(
                text=(
                    f"Model Residuals \u2014 "
                    f"{AGE_LABELS.get(age_group, age_group)}"
                    f"<br><span style='font-size:10px;color:#888'>"
                    f"{subtitle}</span>"
                ),
                x=0.5,
                font=dict(size=14),
            ),
            geo=dict(scope="usa", bgcolor="rgba(0,0,0,0)"),
            margin=dict(l=0, r=0, t=55, b=0),
            paper_bgcolor="rgba(0,0,0,0)",
            dragmode=False,
        )
        return fig

    # -- 6. State profile --------------------------------------------------
    @app.callback(
        Output("profile-title", "children"),
        Output("profile-bars", "figure"),
        Input("selected-state", "data"),
        Input("age-group-dropdown", "value"),
    )
    def render_profile(selected_state, age_group):
        if not selected_state or selected_state not in df["abbrev"].values:
            fig = go.Figure()
            fig.update_layout(
                annotations=[
                    dict(
                        text="Click a state on the map, scatter, or ranking table",
                        xref="paper", yref="paper", x=0.5, y=0.5,
                        showarrow=False, font=dict(size=13, color="#999"),
                    )
                ],
                xaxis=dict(visible=False),
                yaxis=dict(visible=False),
                margin=dict(l=10, r=10, t=10, b=10),
                paper_bgcolor="rgba(0,0,0,0)",
            )
            return "Click a state to see its migration profile", fig

        row = df.loc[df["abbrev"] == selected_state].iloc[0]
        state_name = row["state_name"]
        rates = [row[f"NET_RATE_{ag}"] for ag in AGE_GROUPS]
        counts = [row[f"NET_COUNT_{ag}"] for ag in AGE_GROUPS]
        pops = [row[f"POP_AGE_{ag}"] for ag in AGE_GROUPS]
        labels = [AGE_LABELS[ag] for ag in AGE_GROUPS]

        # Color: highlight active age group; blue/red for sign
        bar_colors = []
        for i, ag in enumerate(AGE_GROUPS):
            if ag == age_group:
                bar_colors.append("#333333")
            elif rates[i] >= 0:
                bar_colors.append("#67a9cf")
            else:
                bar_colors.append("#ef8a62")

        # Custom hover with denominator context
        hover_texts = []
        for i, ag in enumerate(AGE_GROUPS):
            hover_texts.append(
                f"<b>{labels[i]}</b><br>"
                f"NET_RATE: {rates[i]:+.2f} per 1,000<br>"
                f"NET_COUNT: {counts[i]:+,.0f}<br>"
                f"POP_AGE: {pops[i]:,.0f}"
            )

        fig = go.Figure()
        fig.add_trace(
            go.Bar(
                y=labels,
                x=rates,
                orientation="h",
                marker_color=bar_colors,
                text=[f"{r:+.2f}" for r in rates],
                textposition="outside",
                hovertext=hover_texts,
                hovertemplate="%{hovertext}<extra></extra>",
            )
        )
        fig.add_vline(x=0, line_color="#999", line_width=1)
        fig.update_layout(
            margin=dict(l=60, r=60, t=10, b=30),
            xaxis_title="NET_RATE (per 1,000 age-group pop.)",
            yaxis=dict(autorange="reversed"),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="#fafafa",
        )
        return f"{state_name} ({selected_state}) \u2014 Migration Profile", fig

    # -- 7. Ranking table --------------------------------------------------
    @app.callback(
        Output("ranking-table", "data"),
        Output("ranking-title", "children"),
        Output("ranking-table", "selected_rows"),
        Output("ranking-table", "style_data_conditional"),
        Input("age-group-dropdown", "value"),
        Input("selected-state", "data"),
    )
    def render_ranking(age_group, selected_state):
        dv_col = f"NET_RATE_{age_group}"
        count_col = f"NET_COUNT_{age_group}"
        pop_col = f"POP_AGE_{age_group}"
        small_pop = get_small_pop_states(df, age_group)

        sorted_df = df.sort_values(dv_col, ascending=False).reset_index(drop=True)
        top10 = sorted_df.head(10)
        bot10 = sorted_df.tail(10)
        display = pd.concat([top10, bot10], ignore_index=True)

        records = []
        selected_idx = []
        for i, (_, r) in enumerate(display.iterrows()):
            rank_label = i + 1 if i < 10 else len(df) - (19 - i)
            flag = "\u26a0" if r["abbrev"] in small_pop else ""
            records.append({
                "rank": rank_label,
                "state_name": r["state_name"],
                "net_rate": round(r[dv_col], 2),
                "net_count": int(r[count_col]),
                "pop_age": int(r[pop_col]),
                "flag": flag,
                "abbrev": r["abbrev"],
            })
            if r["abbrev"] == selected_state:
                selected_idx.append(i)

        adj_r2 = get_adj_r2_for_age(models_df, age_group)
        quality = fit_quality_note(adj_r2)
        title = (
            f"Top 10 / Bottom 10 \u2014 "
            f"{AGE_LABELS.get(age_group, age_group)}"
            f"    |  Model: adj R\u00b2 = {adj_r2:.4f} ({quality})"
        )

        # Conditional styling
        style_cond = [
            {"if": {"filter_query": "{net_rate} < 0"}, "color": "#b2182b"},
            {"if": {"filter_query": "{net_rate} >= 0"}, "color": "#2166ac"},
            # Yellow flag for small-pop states
            {"if": {"filter_query": '{flag} = "\u26a0"'},
             "backgroundColor": "#fff8e1"},
        ]
        if selected_state:
            style_cond.append({
                "if": {"filter_query": f"{{abbrev}} = {selected_state}"},
                "backgroundColor": "#ffffcc",
                "fontWeight": "bold",
            })

        return records, title, selected_idx, style_cond


# ---------------------------------------------------------------------------
# App entry point
# ---------------------------------------------------------------------------


def main():
    if not DASH_AVAILABLE:
        print(
            "ERROR: dash is not installed.\n"
            "  pip install -r requirements.txt\n"
            "Then re-run: python scripts/a8_dashboard.py"
        )
        return

    df = load_data()
    models_df = load_models()
    coef_df = load_coefficients()

    app = dash.Dash(
        __name__,
        title="A8 Migration Dashboard",
        suppress_callback_exceptions=True,
    )
    app.layout = build_layout()
    register_callbacks(app, df, models_df, coef_df)

    print("Starting A8 dashboard at http://127.0.0.1:8050")
    app.run(debug=True, port=8050)


if __name__ == "__main__":
    main()
