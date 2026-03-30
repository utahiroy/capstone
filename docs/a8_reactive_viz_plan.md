# A8 Reactive Visualization — Design Memo

**Phase**: A8-3 (research polish)
**Status**: Working — real-data refresh integrated
**Date**: 2026-03-30

---

## 1. Objective

Consolidate the seven standalone A7 Plotly prototypes into a single coordinated
Dash application where selecting a state or age group in one panel updates all
other panels in real time.

### MVP scope (A8-1 / A8-2)

| Included | Excluded (deferred) |
|----------|---------------------|
| Coordinated U.S. choropleth map (NET_RATE by age group) | Robustness selector (WLS / exclusion toggle) |
| State profile panel (bar chart, all age groups for one state) | Residual map panel |
| IV vs NET_RATE scatter panel | Method / data-provenance drawer |
| Top/bottom ranking panel (sortable table) | Advanced styling / branding |

---

## 2. Technology choice

**Dash + Plotly** (pure Python, no JS build step).

Rationale:
- All A7 prototypes already use Plotly figures.
- Dash is the first-party reactive wrapper for Plotly.
- No additional front-end toolchain needed.
- Keeps the repo Python-only, consistent with the pipeline.

New dependency: `dash>=2.14` (add to `requirements.txt`).

---

## 3. Data inputs

All data is loaded once at app startup (50 rows — no database needed).

| Source file | Content | Used by |
|-------------|---------|---------|
| `data_processed/analysis_ready.csv` | 50 states × DVs + IVs | map, scatter, profile, ranking |
| `outputs/tables/a6_selected_models.csv` | canonical model set (5 age groups) | scatter IV selector, profile annotations |
| `outputs/tables/a6_selected_coefficients.csv` | coefficient estimates | scatter regression overlay (optional) |

---

## 4. Shared state (Dash callbacks)

Three pieces of shared state drive coordination:

| State variable | Type | Default | Set by |
|----------------|------|---------|--------|
| `selected_age_group` | dropdown | `"18_24"` | age-group dropdown |
| `selected_state` | string (FIPS or abbrev) | `None` (no selection) | map click, ranking row click |
| `selected_iv` | string | first IV for current age group | IV dropdown (auto-populated from A6 models) |

### Callback graph (simplified)

```
age_group ──┬──▶ map (recolor choropleth)
            ├──▶ scatter (update IV dropdown options, replot)
            ├──▶ ranking (re-sort by NET_RATE for age group)
            └──▶ profile (highlight age-group bar)

state ──────┬──▶ map (highlight border)
            ├──▶ scatter (highlight point)
            ├──▶ ranking (highlight row)
            └──▶ profile (show selected state's bars)

iv ─────────┬──▶ scatter (change x-axis variable)
            └──▶ map (no change)
```

---

## 5. Layout

```
┌──────────────────────────────────────────────────────┐
│  [Age Group ▼]   [IV ▼]              A8 Dashboard    │  <- control bar
├────────────────────────┬─────────────────────────────┤
│                        │                             │
│   U.S. Choropleth      │   IV vs NET_RATE Scatter    │
│   (NET_RATE by age)    │   (regression line overlay) │
│                        │                             │
│   click → set state    │   click → set state         │
│                        │                             │
├────────────────────────┼─────────────────────────────┤
│                        │                             │
│   State Profile        │   Top / Bottom Ranking      │
│   (5 age-group bars)   │   (sortable table, 10+10)   │
│                        │                             │
│   updates on state     │   click → set state         │
│   selection             │                             │
└────────────────────────┴─────────────────────────────┘
```

- 2 × 2 grid, equal columns.
- Control bar spans full width.
- Responsive via Dash Bootstrap Components (optional, can start with default CSS).

---

## 6. Panel responsibilities

### 6a. Choropleth map
- Reuses Proto 1a/1b logic.
- Fills states by `NET_RATE_{age}`.
- Diverging color scale (red-white-blue), centered at 0.
- On click: sets `selected_state`.
- On age-group change: recolors.

### 6b. IV vs NET_RATE scatter
- Reuses Proto 3 logic.
- X = selected IV, Y = `NET_RATE_{age}`.
- Points labeled by state abbreviation.
- OLS trend line overlaid (from A6 coefficients or computed live).
- On click: sets `selected_state`.
- IV dropdown options filtered to IVs in the A6 model for the current age group.

### 6c. State profile
- Reuses Proto 5 logic (simplified).
- Horizontal bar chart: one bar per age group showing `NET_RATE`.
- Title updates to selected state name.
- When no state selected: shows national median or placeholder.

### 6d. Top/bottom ranking
- Table showing top 10 and bottom 10 states by `NET_RATE_{age}`.
- Columns: rank, state, NET_RATE, (optionally IN_RATE, OUT_RATE).
- Highlighted row for selected state.
- Click row → sets `selected_state`.

---

## 7. File placement

```
scripts/
  a8_dashboard.py          # Dash app entry point (scaffold now, implement A8-2)
```

No new `src/` modules needed for the scaffold. Reusable helpers can be
extracted during A8-2 if warranted.

---

## 8. A8-2 implementation plan

| Step | Task | Depends on |
|------|------|------------|
| 1 | Add `dash>=2.14` to `requirements.txt`, verify install | — |
| 2 | Load data at startup, build long-form DataFrames | — |
| 3 | Implement choropleth panel + age-group callback | step 2 |
| 4 | Implement scatter panel + IV dropdown callback | step 2 |
| 5 | Implement state profile panel + state-selection callback | step 2 |
| 6 | Implement ranking panel + click-to-select callback | step 2 |
| 7 | Wire cross-panel coordination (map click ↔ scatter ↔ ranking → profile) | steps 3–6 |
| 8 | Add state-abbreviation labels, tooltips, color consistency | step 7 |
| 9 | Smoke test: run app, verify all callbacks with 2–3 states | step 7 |
| 10 | Document run instructions in this file or README | step 9 |

Estimated touch points: 1 new file (`a8_dashboard.py`), 1 edit (`requirements.txt`).

---

## 9. Risks and mitigations

| Risk | Mitigation |
|------|------------|
| Dash adds a server dependency (vs static HTML) | App is local-only; document `python scripts/a8_dashboard.py` |
| Real data may show weak/null model fits | Display adj R² + fit-quality label; show residuals honestly |
| Most age groups have adj R² near zero | Display warning on scatter and residual panels; document in footnotes |
| Callback complexity grows with panels | Keep callback graph flat (no chained callbacks in MVP) |

---

## 10. Run instructions

```bash
# Install dependencies (one-time)
pip install -r requirements.txt

# Launch the dashboard
python scripts/a8_dashboard.py

# Open in browser
# http://127.0.0.1:8050
```

---

## 11. A8-2 implementation notes

**Completed** (2026-03-24):

All four MVP panels are fully implemented with cross-panel coordination:

| Panel | Implementation | Interactions |
|-------|---------------|--------------|
| Choropleth map | Diverging red-white-blue scale, auto-scaled per age group; star marker on selected state | Click → sets selected_state |
| IV vs NET_RATE scatter | Points labeled by abbreviation; OLS trendline; adj R² in title | Click → sets selected_state; IV dropdown filters to A6 model IVs |
| State profile | Horizontal bars for all 5 age groups; active age group highlighted in dark; placeholder when no state selected | Reacts to selected_state and age_group |
| Top/bottom ranking | Top 10 + bottom 10 table; color-coded positive/negative; selected state row highlighted yellow | Click → sets selected_state |

**Shared state wiring**: single `dcc.Store("selected-state")` updated by map click, scatter click, or ranking row click via `dash.ctx.triggered_id`. All four panels consume it.

**Files modified**:
- `scripts/a8_dashboard.py` — full MVP (~420 lines)
- `requirements.txt` — added `dash>=2.14`

**Deferred to future phases**:
- Robustness selector (WLS / smallest-state exclusion toggle)
- Method / data-provenance drawer
- Advanced styling and responsive layout polish

---

## 12. A8-3 research polish notes

**Completed** (2026-03-30):

Synced working branch with manually refreshed real-data outputs from `main`.
All canonical models now reflect the refreshed A6 results (weaker fits).

### New features

| Feature | Details |
|---------|---------|
| **Metric toggle** | RadioItems: NET_RATE (per 1k) / NET_COUNT; affects choropleth and described in tooltips |
| **Denominator context** | POP_AGE shown in map hover, profile hover, and ranking table column |
| **Small-pop flag** | Bottom 5 states by POP_AGE marked with ⚠ triangle on map, scatter, and ranking table |
| **Residual map panel** | New choropleth showing actual − predicted from A6 coefficients; diverging scale; selected-state highlighting; model formula + adj R² in subtitle |
| **Fit-quality warnings** | Scatter title and ranking subtitle display adj R² with human-readable label (no explanatory power / very weak / weak / modest) |
| **Profile with counts** | Hover on profile bars shows NET_COUNT and POP_AGE alongside NET_RATE |
| **Methodology footnotes** | Color legend, rate definition, small-pop explanation, 18–24 college caveat, model description |

### Canonical models (refreshed real data)

| Age group | IVs | Adj R² | Quality |
|-----------|-----|--------|---------|
| 18–24 | COMMUTE_MED + MED_HOMEVAL | 0.1713 | modest fit |
| 25–34 | NRI_RISK_INDEX + TRANSIT_SHARE | −0.0116 | no explanatory power |
| 35–54 | REAL_PCPI + PERMITS | −0.0036 | no explanatory power |
| 55–64 | NRI_RISK_INDEX + ELEC_PRICE_TOT | 0.0127 | very weak fit |
| 65+ | UNINSURED + RPP | 0.0382 | very weak fit |

### Layout (A8-3)

```
┌─────────────────────────────────────────────────────────────┐
│  [Age ▼] (NET_RATE / NET_COUNT) [IV ▼]    A8 Dashboard     │
├──────────────────────────┬──────────────────────────────────┤
│  Choropleth Map          │  IV vs NET_RATE Scatter          │
│  (metric toggle, ⚠ flag) │  (OLS line, adj R² warning)     │
├──────────────────────────┼──────────────────────────────────┤
│  Residual Map            │  State Profile                   │
│  (actual − predicted)    │  (5 age groups, POP context)     │
├──────────────────────────┴──────────────────────────────────┤
│  Top 10 / Bottom 10 Ranking                                │
│  (NET_RATE, NET_COUNT, POP_AGE, ⚠ flag, adj R² label)      │
├─────────────────────────────────────────────────────────────┤
│  Methodology footnotes                                      │
└─────────────────────────────────────────────────────────────┘
```

### Key interpretation note

> The 22 state-level IVs do **not** strongly explain age-specific interstate
> net migration in 2024. Only 18–24 shows modest explanatory power, and that
> group likely captures substantial college-related migration. The dashboard
> presents these weak results honestly with fit-quality labels and residual
> visualization.

### Remaining deferred items
- Full robustness selector (WLS / exclusion toggle)
- Method/data-provenance drawer with collapsible sections
- Advanced responsive styling
- IN_RATE / OUT_RATE decomposition view (considered but deferred to avoid clutter)
