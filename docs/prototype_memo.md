# Visualization Prototype Comparison Memo

## Overview

Seven interactive HTML prototypes were generated from the A2–A6 pipeline outputs.
All use Plotly with CDN-linked JavaScript (no local dependencies to serve).
Each file is self-contained and viewable in any modern browser.

Selected models are loaded dynamically from `outputs/tables/a6_selected_models.csv`
(produced by A6). No model specifications are hardcoded in the visualization script.

All prototypes include a caveat footer noting that CRIME_VIOLENT_RATE and
NRI_RISK_INDEX use provisional data sources.

---

## Prototype Descriptions

### Proto 1a: Age-Group NET_RATE Choropleth (per-age autoscaling)
**File**: `proto1a_choropleth_autoscale.html`

Maps the primary DV (net migration rate per 1,000) across 50 states, with a
dropdown to switch between the five age groups. Diverging RdBu color scale
centered at zero, with color range fitted to each age group's data range.
Hover shows state name and exact value.

### Proto 1b: Age-Group NET_RATE Choropleth (common scale)
**File**: `proto1b_choropleth_common_scale.html`

Same as 1a but uses a single fixed color range across all age groups, making
cross-age-group magnitude comparisons valid. Useful for seeing that 65+ moves
are much larger than 35–54 moves, for example.

### Proto 2: Key IV Map Explorer
**File**: `proto2_iv_maps.html`

Maps the IVs used in A6 selected models. Dropdown selector. Provisional
variables marked with asterisk. Viridis color scale. IV list is read
dynamically from A6 output.

### Proto 3: Bivariate Scatterplot Selector
**File**: `proto3_scatterplot_selector.html`

Scatterplots of NET_RATE (y) vs each key IV (x), with dropdown for all
age-group × IV combinations. State abbreviation labels on each point.
Useful for spotting leverage points and nonlinear patterns.

### Proto 4: Residual Map Explorer
**File**: `proto4_residual_maps.html`

Maps OLS residuals from the A6 selected models. Dropdown switches age groups.
Red = model underpredicts (actual net rate > predicted). Blue = overpredicts.
Title shows the model formula and adjusted R². Hover shows actual, predicted,
and residual values.

### Proto 5: State Profile Comparison Dashboard
**File**: `proto5_state_profiles.html`

Horizontal grouped bar chart: all 50 states on the y-axis, 5 age-group bars
per state. Includes dropdown toggles for:
- **Rate type**: NET_RATE, IN_RATE, or OUT_RATE
- **Sort order**: average net rate or alphabetical

Instantly reveals which states are consistently gaining or losing across all
age groups vs. which have age-specific patterns.

### Proto 6: Model Summary Explorer
**File**: `proto6_model_summary.html`

Coefficient dot plot with 95% CIs for all A6 selected model terms.
Diamond markers indicate provisional data sources. Annotation box shows
model-level fit metrics (adj R², max VIF). Zero reference line.

---

## Ranking

| Rank | Prototype | Interpretability | Research Alignment | Comparison Value | Professor-Facing | Portfolio/Demo |
|------|-----------|-----------------|-------------------|-----------------|-----------------|----------------|
| 1 | **Proto 5**: State Profiles | High | High | **Best** — shows all age groups × all states at once | Excellent — narrative entry point | High |
| 2 | **Proto 1b**: Common-Scale Choropleth | High | High | **Best** for cross-age comparison | Excellent — immediately recognizable | **Best** for portfolio |
| 3 | **Proto 1a**: Autoscale Choropleth | High | High | Good — maximizes within-age contrast | Excellent | High |
| 4 | **Proto 4**: Residual Maps | Medium | **Best** — directly tied to model diagnostics | Good | Good — shows where the model fails | High |
| 5 | **Proto 6**: Model Summary | Medium | High — shows coefficients and fit | Medium | Good — compact summary | Medium |
| 6 | **Proto 3**: Scatterplots | Medium | Medium | Medium — one pair at a time | Medium | Medium |
| 7 | **Proto 2**: IV Maps | Medium | Low — descriptive only | Low — no DV link | Low — context only | Low |

### Rationale

**Proto 5 (State Profiles)** ranks highest overall because it is the only
prototype that shows all 5 age groups and all 50 states simultaneously. A
reviewer can immediately see, for example, that Florida gains 65+ migrants
but loses 18–24, or that Texas gains across multiple age groups. The rate
type and sort toggles make it versatile for different questions.

**Proto 1b (Common-Scale Choropleth)** is the most portfolio-ready and enables
valid cross-age-group magnitude comparisons. Proto 1a complements it by
maximizing within-age-group contrast.

**Proto 4 (Residual Maps)** is the most methodologically aligned because it
directly surfaces where the A6 models succeed and fail geographically.
Residual clustering could reveal omitted spatial factors.

**Proto 6 (Model Summary)** is compact and useful for a methods appendix or
slide deck, but it requires some statistical literacy to interpret.

**Proto 3 (Scatterplots)** is useful for diagnostics (spotting outliers,
nonlinearity) but is less effective for communication because each dropdown
selection shows only one pair.

**Proto 2 (IV Maps)** provides geographic context for the IVs but does not
connect them to the DVs, making it the weakest standalone prototype.

---

## Recommended Polish Plan

### Priority 1: Polish Proto 5 (State Profiles)
- Add a highlight/filter mode to select specific states for comparison
- Add a compact ranking table below the chart

### Priority 2: Polish Proto 1b (Common-Scale Choropleth)
- Add a faceted "small multiples" version showing all 5 age groups at once
- Add state labels for top-5 and bottom-5 states in each view
- Add a static (PNG/PDF) export option for the paper/slides

### Optional: Combine Proto 1 + Proto 4
- Side-by-side: actual NET_RATE map (left) and residual map (right)
- Immediately shows what the model explains vs. what remains unexplained

---

## Caveats

- **Data note**: CRIME_VIOLENT_RATE and NRI_RISK_INDEX use provisional data
  sources (CSV fallback for CRIME, Dec 2025 vintage for NRI). These are
  marked in the prototype interfaces where they appear, and a caveat footer
  is included on every prototype.
- **Synthetic data**: If the current `analysis_ready.csv` contains synthetic
  data (from a session without API access), all map values reflect synthetic
  patterns, not real geographic distributions. Re-run the full pipeline on
  real data before using these for interpretation.
- **Proto 3 file size**: The scatterplot prototype is the largest because it
  embeds all age-group × IV combinations as separate traces. This could be
  optimized by generating separate files per age group.
