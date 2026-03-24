#!/usr/bin/env python3
"""
A8 Reactive Visualization Dashboard — Scaffold
================================================
Consolidates A7 prototypes into a coordinated Dash application.

Run:
    python scripts/a8_dashboard.py

Requires: dash>=2.14  (add to requirements.txt before first run)

Phase A8-1: scaffold only — callbacks contain placeholder logic.
Phase A8-2: full implementation of panels and cross-panel coordination.
"""

from pathlib import Path

import pandas as pd

# ---------------------------------------------------------------------------
# Dash will be imported at runtime; guard so the scaffold is parseable
# even before the dependency is installed.
# ---------------------------------------------------------------------------
try:
    import dash
    from dash import dcc, html, dash_table, Input, Output, State, callback
    import plotly.express as px
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
COEFFICIENTS_PATH = PROJECT_ROOT / "outputs" / "tables" / "a6_selected_coefficients.csv"

AGE_GROUPS = ["18_24", "25_34", "35_54", "55_64", "65_PLUS"]
AGE_LABELS = {
    "18_24": "18–24",
    "25_34": "25–34",
    "35_54": "35–54",
    "55_64": "55–64",
    "65_PLUS": "65+",
}

# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------


def load_data() -> pd.DataFrame:
    """Load the 50-state analysis-ready dataset."""
    df = pd.read_csv(DATA_PATH)
    return df


def load_models() -> pd.DataFrame:
    """Load A6 selected models (one row per age group)."""
    return pd.read_csv(MODELS_PATH)


def get_ivs_for_age(models_df: pd.DataFrame, age_group: str) -> list[str]:
    """Return the list of IVs for a given age group from A6 selected models."""
    row = models_df.loc[models_df["age_group"] == age_group]
    if row.empty:
        return []
    iv_str = row.iloc[0]["selected_ivs"]
    return [iv.strip() for iv in iv_str.split(",")]


# ---------------------------------------------------------------------------
# Layout builders  (Phase A8-2: flesh out each panel)
# ---------------------------------------------------------------------------


def build_control_bar() -> html.Div:
    """Top control bar with age-group and IV dropdowns."""
    return html.Div(
        id="control-bar",
        children=[
            html.Label("Age group:"),
            dcc.Dropdown(
                id="age-group-dropdown",
                options=[
                    {"label": AGE_LABELS[ag], "value": ag} for ag in AGE_GROUPS
                ],
                value=AGE_GROUPS[0],
                clearable=False,
                style={"width": "160px", "display": "inline-block"},
            ),
            html.Label("Explanatory variable:", style={"marginLeft": "24px"}),
            dcc.Dropdown(
                id="iv-dropdown",
                options=[],  # populated by callback
                value=None,
                clearable=False,
                style={"width": "220px", "display": "inline-block"},
            ),
            html.H3(
                "A8 Migration Dashboard (MVP)",
                style={"display": "inline-block", "float": "right", "margin": "0"},
            ),
        ],
        style={
            "display": "flex",
            "alignItems": "center",
            "gap": "8px",
            "padding": "12px",
            "borderBottom": "1px solid #ccc",
        },
    )


def build_map_panel() -> html.Div:
    """Choropleth map panel — NET_RATE by age group."""
    return html.Div(
        id="map-panel",
        children=[
            dcc.Graph(id="choropleth-map", style={"height": "100%"}),
        ],
        style={"height": "400px"},
    )


def build_scatter_panel() -> html.Div:
    """IV vs NET_RATE scatter panel."""
    return html.Div(
        id="scatter-panel",
        children=[
            dcc.Graph(id="scatter-plot", style={"height": "100%"}),
        ],
        style={"height": "400px"},
    )


def build_profile_panel() -> html.Div:
    """State profile panel — bar chart across age groups for selected state."""
    return html.Div(
        id="profile-panel",
        children=[
            html.H4(id="profile-title", children="Select a state"),
            dcc.Graph(id="profile-bars", style={"height": "90%"}),
        ],
        style={"height": "350px"},
    )


def build_ranking_panel() -> html.Div:
    """Top/bottom ranking table."""
    return html.Div(
        id="ranking-panel",
        children=[
            html.H4("Top / Bottom States"),
            dash_table.DataTable(
                id="ranking-table",
                columns=[
                    {"name": "Rank", "id": "rank"},
                    {"name": "State", "id": "state_name"},
                    {"name": "NET_RATE", "id": "net_rate", "type": "numeric",
                     "format": dash_table.FormatTemplate.fixed(2)},
                ],
                data=[],  # populated by callback
                row_selectable="single",
                style_table={"overflowY": "auto", "maxHeight": "300px"},
                style_cell={"textAlign": "left", "padding": "4px"},
            ),
        ],
        style={"height": "350px"},
    )


def build_layout() -> html.Div:
    """Assemble the full 2x2 dashboard layout."""
    return html.Div(
        [
            # Hidden store for selected state (shared state)
            dcc.Store(id="selected-state", data=None),
            # Control bar
            build_control_bar(),
            # Row 1: map + scatter
            html.Div(
                [build_map_panel(), build_scatter_panel()],
                style={
                    "display": "grid",
                    "gridTemplateColumns": "1fr 1fr",
                    "gap": "8px",
                    "padding": "8px",
                },
            ),
            # Row 2: profile + ranking
            html.Div(
                [build_profile_panel(), build_ranking_panel()],
                style={
                    "display": "grid",
                    "gridTemplateColumns": "1fr 1fr",
                    "gap": "8px",
                    "padding": "8px",
                },
            ),
            # Footer
            html.Div(
                "Data: synthetic placeholder (re-run pipeline with API access). "
                "Models: A6 canonical set (a6_selected_models.csv).",
                style={"padding": "8px", "fontSize": "11px", "color": "#888"},
            ),
        ]
    )


# ---------------------------------------------------------------------------
# Callback stubs  (Phase A8-2: implement each)
# ---------------------------------------------------------------------------
# Each callback below is a stub that returns an empty/placeholder figure.
# The function signatures and Input/Output wiring define the coordination
# contract for A8-2 implementation.


def register_callbacks(app: dash.Dash, df: pd.DataFrame, models_df: pd.DataFrame):
    """Register all Dash callbacks on the app instance."""

    # --- 1. Age group change → update IV dropdown options ----------------
    @app.callback(
        Output("iv-dropdown", "options"),
        Output("iv-dropdown", "value"),
        Input("age-group-dropdown", "value"),
    )
    def update_iv_dropdown(age_group):
        """Populate IV dropdown from A6 model for the selected age group."""
        ivs = get_ivs_for_age(models_df, age_group)
        options = [{"label": iv, "value": iv} for iv in ivs]
        default = ivs[0] if ivs else None
        return options, default

    # --- 2. Map click → set selected state -------------------------------
    @app.callback(
        Output("selected-state", "data", allow_duplicate=True),
        Input("choropleth-map", "clickData"),
        prevent_initial_call=True,
    )
    def map_click_to_state(click_data):
        """Extract state from map click event."""
        # A8-2: parse click_data["points"][0]["location"] → state FIPS/abbrev
        if click_data is None:
            return dash.no_update
        return None  # placeholder

    # --- 3. Ranking row click → set selected state -----------------------
    @app.callback(
        Output("selected-state", "data", allow_duplicate=True),
        Input("ranking-table", "selected_rows"),
        State("ranking-table", "data"),
        prevent_initial_call=True,
    )
    def ranking_click_to_state(selected_rows, table_data):
        """Set selected state from ranking table row click."""
        # A8-2: look up state from table_data[selected_rows[0]]
        if not selected_rows:
            return dash.no_update
        return None  # placeholder

    # --- 4. Render choropleth map ----------------------------------------
    @app.callback(
        Output("choropleth-map", "figure"),
        Input("age-group-dropdown", "value"),
        Input("selected-state", "data"),
    )
    def render_map(age_group, selected_state):
        """Render the U.S. choropleth colored by NET_RATE for the age group."""
        # A8-2: build plotly choropleth, highlight selected_state border
        fig = go.Figure()
        fig.update_layout(
            title=f"NET_RATE — {AGE_LABELS.get(age_group, age_group)}",
            geo_scope="usa",
        )
        return fig

    # --- 5. Render scatter plot ------------------------------------------
    @app.callback(
        Output("scatter-plot", "figure"),
        Input("age-group-dropdown", "value"),
        Input("iv-dropdown", "value"),
        Input("selected-state", "data"),
    )
    def render_scatter(age_group, iv, selected_state):
        """Render IV vs NET_RATE scatter with OLS trend line."""
        # A8-2: build scatter, highlight selected_state, add trendline
        fig = go.Figure()
        fig.update_layout(
            title=f"{iv} vs NET_RATE — {AGE_LABELS.get(age_group, age_group)}",
            xaxis_title=iv or "",
            yaxis_title=f"NET_RATE_{age_group}",
        )
        return fig

    # --- 6. Render state profile -----------------------------------------
    @app.callback(
        Output("profile-title", "children"),
        Output("profile-bars", "figure"),
        Input("selected-state", "data"),
    )
    def render_profile(selected_state):
        """Render bar chart of NET_RATE across age groups for selected state."""
        # A8-2: filter df to selected_state, build horizontal bar chart
        title = selected_state if selected_state else "Select a state"
        fig = go.Figure()
        fig.update_layout(title="")
        return title, fig

    # --- 7. Render ranking table -----------------------------------------
    @app.callback(
        Output("ranking-table", "data"),
        Input("age-group-dropdown", "value"),
    )
    def render_ranking(age_group):
        """Build top-10 / bottom-10 ranking by NET_RATE for the age group."""
        # A8-2: sort df by NET_RATE_{age_group}, take head/tail 10
        return []  # placeholder


# ---------------------------------------------------------------------------
# App entry point
# ---------------------------------------------------------------------------


def main():
    if not DASH_AVAILABLE:
        print(
            "ERROR: dash is not installed.\n"
            "  pip install dash>=2.14\n"
            "Then re-run: python scripts/a8_dashboard.py"
        )
        return

    # Load data
    df = load_data()
    models_df = load_models()

    # Create Dash app
    app = dash.Dash(
        __name__,
        title="A8 Migration Dashboard",
        suppress_callback_exceptions=True,
    )
    app.layout = build_layout()

    # Register callbacks
    register_callbacks(app, df, models_df)

    # Run dev server
    print("Starting A8 dashboard at http://127.0.0.1:8050")
    app.run(debug=True, port=8050)


if __name__ == "__main__":
    main()
