#!/usr/bin/env python3
"""
A8 Reactive Visualization Dashboard — MVP
==========================================
Consolidates A7 prototypes into a coordinated Dash application.

Run:
    pip install dash>=2.14
    python scripts/a8_dashboard.py

Then open http://127.0.0.1:8050 in a browser.

Panels:
  - Choropleth map: NET_RATE by age group, click to select state
  - Scatter: IV vs NET_RATE with OLS trendline, click to select state
  - State profile: horizontal bars for all 5 age groups
  - Ranking: top-10 / bottom-10 table, click to select state
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

# FIPS code → two-letter abbreviation (50 states only)
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

# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------


def load_data() -> pd.DataFrame:
    """Load the 50-state analysis-ready dataset and add abbreviations."""
    df = pd.read_csv(DATA_PATH, dtype={"state": str})
    # Ensure FIPS is zero-padded
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
    """Return adjusted R² for the selected model of an age group."""
    row = models_df.loc[models_df["age_group"] == age_group]
    if row.empty:
        return float("nan")
    return float(row.iloc[0]["adjusted_r2"])


# ---------------------------------------------------------------------------
# Layout builders
# ---------------------------------------------------------------------------


def build_control_bar() -> html.Div:
    """Top control bar with age-group and IV dropdowns."""
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
                style={"width": "140px"},
            ),
            html.Label(
                "Explanatory variable:",
                style={"marginLeft": "20px", "fontWeight": "bold"},
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
                style={"margin": "0", "whiteSpace": "nowrap"},
            ),
        ],
        style={
            "display": "flex",
            "alignItems": "center",
            "gap": "8px",
            "padding": "10px 16px",
            "borderBottom": "2px solid #ddd",
            "fontFamily": "sans-serif",
        },
    )


def build_map_panel() -> html.Div:
    return html.Div(
        children=[dcc.Graph(id="choropleth-map", style={"height": "100%"})],
        style={"height": "420px"},
    )


def build_scatter_panel() -> html.Div:
    return html.Div(
        children=[dcc.Graph(id="scatter-plot", style={"height": "100%"})],
        style={"height": "420px"},
    )


def build_profile_panel() -> html.Div:
    return html.Div(
        children=[
            html.H4(
                id="profile-title",
                children="Click a state to see its profile",
                style={"margin": "4px 8px", "fontFamily": "sans-serif"},
            ),
            dcc.Graph(id="profile-bars", style={"height": "calc(100% - 36px)"}),
        ],
        style={"height": "360px"},
    )


def build_ranking_panel() -> html.Div:
    return html.Div(
        children=[
            html.H4(
                id="ranking-title",
                children="Top / Bottom States",
                style={"margin": "4px 8px", "fontFamily": "sans-serif"},
            ),
            dash_table.DataTable(
                id="ranking-table",
                columns=[
                    {"name": "#", "id": "rank"},
                    {"name": "State", "id": "state_name"},
                    {
                        "name": "NET_RATE",
                        "id": "net_rate",
                        "type": "numeric",
                        "format": {"specifier": ".2f"},
                    },
                ],
                data=[],
                row_selectable="single",
                selected_rows=[],
                style_table={"overflowY": "auto", "maxHeight": "310px"},
                style_cell={
                    "textAlign": "left",
                    "padding": "4px 8px",
                    "fontFamily": "sans-serif",
                    "fontSize": "13px",
                },
                style_header={"fontWeight": "bold"},
                style_data_conditional=[
                    {
                        "if": {"filter_query": "{net_rate} < 0"},
                        "color": "#b2182b",
                    },
                    {
                        "if": {"filter_query": "{net_rate} >= 0"},
                        "color": "#2166ac",
                    },
                ],
            ),
        ],
        style={"height": "360px"},
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
                    "gap": "4px",
                    "padding": "4px 8px",
                },
            ),
            # Row 2: profile + ranking
            html.Div(
                [build_profile_panel(), build_ranking_panel()],
                style={
                    "display": "grid",
                    "gridTemplateColumns": "1fr 1fr",
                    "gap": "4px",
                    "padding": "4px 8px",
                },
            ),
            # Footer
            html.Div(
                "Data: synthetic placeholder (re-run pipeline with API access). "
                "Models: A6 canonical set. "
                "Color: blue = net in-migration, red = net out-migration.",
                style={
                    "padding": "6px 16px",
                    "fontSize": "11px",
                    "color": "#888",
                    "fontFamily": "sans-serif",
                },
            ),
        ],
        style={"backgroundColor": "#fafafa"},
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

    # -- 1. Age group → IV dropdown options --------------------------------
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
                return loc  # abbreviation
        if triggered == "scatter-plot" and scatter_click:
            text = scatter_click["points"][0].get("text", "")
            if text:
                return text  # abbreviation stored in text
        if triggered == "ranking-table" and ranking_rows:
            idx = ranking_rows[0]
            if idx < len(ranking_data):
                return ranking_data[idx].get("abbrev")
        return dash.no_update

    # -- 3. Choropleth map -------------------------------------------------
    @app.callback(
        Output("choropleth-map", "figure"),
        Input("age-group-dropdown", "value"),
        Input("selected-state", "data"),
    )
    def render_map(age_group, selected_state):
        dv_col = f"NET_RATE_{age_group}"
        vals = df[dv_col]
        abs_max = max(abs(vals.min()), abs(vals.max())) or 1

        fig = go.Figure()

        # Choropleth layer
        fig.add_trace(
            go.Choropleth(
                locations=df["abbrev"],
                z=vals,
                locationmode="USA-states",
                colorscale=DIVERGING_SCALE,
                zmin=-abs_max,
                zmax=abs_max,
                colorbar=dict(
                    title="NET_RATE",
                    thickness=12,
                    len=0.6,
                ),
                text=df["state_name"],
                hovertemplate=(
                    "<b>%{text}</b><br>"
                    f"{dv_col}: " + "%{z:.2f}<extra></extra>"
                ),
            )
        )

        # Highlight selected state with a marker
        if selected_state and selected_state in df["abbrev"].values:
            row = df.loc[df["abbrev"] == selected_state].iloc[0]
            fig.add_trace(
                go.Scattergeo(
                    locations=[selected_state],
                    locationmode="USA-states",
                    mode="markers",
                    marker=dict(size=14, color="black", symbol="star",
                                line=dict(width=1, color="white")),
                    text=[row["state_name"]],
                    hovertemplate="<b>%{text}</b><extra>selected</extra>",
                    showlegend=False,
                )
            )

        fig.update_layout(
            title=dict(
                text=f"Net Migration Rate \u2014 {AGE_LABELS.get(age_group, age_group)}",
                x=0.5,
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

        if iv is None or iv not in df.columns:
            fig = go.Figure()
            fig.update_layout(title="Select an explanatory variable")
            return fig

        x = df[iv]
        y = df[dv_col]

        # Highlight colors
        colors = [
            "black" if abbr == selected_state else "#5a8dbc"
            for abbr in df["abbrev"]
        ]
        sizes = [
            12 if abbr == selected_state else 7
            for abbr in df["abbrev"]
        ]

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
                marker=dict(color=colors, size=sizes, line=dict(width=0.5, color="white")),
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

        # Annotation: adj R²
        adj_r2 = get_adj_r2_for_age(models_df, age_group)
        fig.update_layout(
            title=dict(
                text=(
                    f"{iv} vs NET_RATE \u2014 {AGE_LABELS.get(age_group, age_group)}"
                    f"  (model adj R\u00b2 = {adj_r2:.3f})"
                ),
                x=0.5,
                font=dict(size=13),
            ),
            xaxis_title=iv,
            yaxis_title=dv_col,
            margin=dict(l=50, r=20, t=50, b=40),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="#fafafa",
        )
        return fig

    # -- 5. State profile --------------------------------------------------
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
                        showarrow=False, font=dict(size=14, color="#999"),
                    )
                ],
                xaxis=dict(visible=False),
                yaxis=dict(visible=False),
                margin=dict(l=10, r=10, t=10, b=10),
                paper_bgcolor="rgba(0,0,0,0)",
            )
            return "Click a state to see its profile", fig

        row = df.loc[df["abbrev"] == selected_state].iloc[0]
        state_name = row["state_name"]
        rates = [row[f"NET_RATE_{ag}"] for ag in AGE_GROUPS]
        labels = [AGE_LABELS[ag] for ag in AGE_GROUPS]

        # Color bars: blue positive, red negative; highlight active age group
        bar_colors = []
        for i, ag in enumerate(AGE_GROUPS):
            if ag == age_group:
                bar_colors.append("#333333")  # active age group highlighted
            elif rates[i] >= 0:
                bar_colors.append("#67a9cf")
            else:
                bar_colors.append("#ef8a62")

        fig = go.Figure()
        fig.add_trace(
            go.Bar(
                y=labels,
                x=rates,
                orientation="h",
                marker_color=bar_colors,
                text=[f"{r:+.2f}" for r in rates],
                textposition="outside",
                hovertemplate="%{y}: %{x:.2f}<extra></extra>",
            )
        )
        fig.add_vline(x=0, line_color="#999", line_width=1)
        fig.update_layout(
            margin=dict(l=60, r=40, t=10, b=20),
            xaxis_title="NET_RATE (per 1,000)",
            yaxis=dict(autorange="reversed"),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="#fafafa",
        )
        return f"{state_name} ({selected_state})", fig

    # -- 6. Ranking table --------------------------------------------------
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
        sorted_df = df.sort_values(dv_col, ascending=False).reset_index(drop=True)

        top10 = sorted_df.head(10)
        bot10 = sorted_df.tail(10)
        display = pd.concat([top10, bot10], ignore_index=True)

        records = []
        selected_idx = []
        for i, (_, r) in enumerate(display.iterrows()):
            rank_label = i + 1 if i < 10 else f"{len(df) - (19 - i)}"
            records.append({
                "rank": rank_label,
                "state_name": r["state_name"],
                "net_rate": round(r[dv_col], 2),
                "abbrev": r["abbrev"],
            })
            if r["abbrev"] == selected_state:
                selected_idx.append(i)

        title = (
            f"Top / Bottom States \u2014 {AGE_LABELS.get(age_group, age_group)}"
        )

        # Conditional styling
        style_cond = [
            {"if": {"filter_query": "{net_rate} < 0"}, "color": "#b2182b"},
            {"if": {"filter_query": "{net_rate} >= 0"}, "color": "#2166ac"},
        ]
        # Highlight selected state row
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
            "  pip install 'dash>=2.14'\n"
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
