# A8 Reactive Visualization — Design Memo

**Phase**: A8-1 (scaffold + design)
**Status**: Draft
**Date**: 2026-03-24

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
| Synthetic data may look odd in coordinated view | Note in UI footer; same caveat as A7 |
| 35–54 model is weak (adj R² = 0.08) | Display R² on scatter; do not hide weak fits |
| Callback complexity grows with panels | Keep callback graph flat (no chained callbacks in MVP) |
