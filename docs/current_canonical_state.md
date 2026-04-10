# Current Canonical State of the Repository

**Updated**: 2026-04-10
**Branch**: `claude/setup-research-project-W4Fjs`

---

## Active analytical framework

The current active analysis uses **distribution-share specialization metrics**
as the main dependent variables, not net migration rates. A **focused deep
dive** on the two strongest DVs (REL_IN_25_34, REL_IN_18_24) has been
completed with multivariable models and presentation-ready figures.

### DVs in use

| Layer | DVs | Purpose | Status |
|-------|-----|---------|--------|
| Raw shares | IN_SHARE, OUT_SHARE (×5 ages + all-ages) | Descriptive baseline | Complete |
| Specialization ratios | REL_IN, REL_OUT (×5 ages) | Main explanatory targets | Complete |
| Deviations | DIFF_IN, DIFF_OUT (×5 ages) | Supplementary | Complete |
| Share gaps | SHARE_GAP (×5 ages) | Supplementary (retains size effect) | Complete |
| Rank shifts | Age-specific vs all-ages rank | Diagnostic | Complete |

### IVs

The fixed 22 state-level explanatory variables are unchanged.

### Key finding (specialization screening)

Specialization ratios (REL_IN, REL_OUT) successfully remove state-size
confounding. Substantive IVs now emerge:
- 25-34: PRIV_AVG_PAY (adj R² = 0.39) — early-career wage pull
- 18-24: NRI_RISK_INDEX / COMMUTE_MED — college-town/rural pull
- 35-54: UNINSURED / VACANCY_RATE — cost-of-living relocation
- 55-64 / 65+: VACANCY_RATE / REAL_PCPI — retirement migration

### Key finding (focused deep dive — multivariable models)

| DV | Preferred Model | IVs | Adj R² | Max VIF | LOO Sign Flips |
|----|-----------------|-----|--------|---------|----------------|
| REL_IN_25_34 | M25_2IV | PRIV_AVG_PAY + COMMUTE_MED | 0.4213 | 1.54 | 0 |
| REL_IN_18_24 | M18_3IV | COMMUTE_MED + VACANCY_RATE + TRANSIT_SHARE | 0.4154 | 1.90 | 0 |

**Central finding**: 25–34 and 18–24 migration respond to opposite state
characteristics. Early-career workers chase wages and dense metro labor
markets. College-age movers go where housing is available and commutes are
short — hallmarks of college towns and smaller cities.

---

## Canonical data files

| File | Status | Description |
|------|--------|-------------|
| `data_processed/analysis_ready.csv` | Canonical | Master 50-state dataset (IVs + migration flows) |
| `data_processed/analysis_ready_distribution_shares.csv` | Canonical | + raw share variables |
| `data_processed/analysis_ready_specialization.csv` | Canonical | + specialization/deviation metrics |

---

## Canonical output files

### Current (distribution-share / specialization phase)

| Directory | Contents |
|-----------|----------|
| `outputs/tables/distribution_shares/` | Raw share validation, stats, rankings, correlations, OLS |
| `outputs/tables/specialization/` | Specialization validation, stats, rankings, correlations, OLS, rank shifts |
| `outputs/figures/distribution_shares/` | 12 raw share choropleth maps |
| `outputs/figures/specialization/` | 25 maps + 9 profiles + 10 rank-shift dumbbells |

### Current (focused deep dive phase)

| Directory | Contents |
|-----------|----------|
| `outputs/tables/focused_deep_dive/` | 11 CSVs: screening summary, candidates, selected models/coefficients/residuals, LOO, robustness |
| `outputs/figures/focused_deep_dive/` | 18 presentation-ready HTML figures (maps, scatters, fitted-actual, residuals, rankings, spotlights, heatmaps) |

### Current documentation

| File | Contents |
|------|----------|
| `docs/distribution_share_update.md` | Raw share methodology and results |
| `docs/specialization_update.md` | Specialization methodology and results |
| `docs/focused_deep_dive_18_24_25_34.md` | Storyline memo, speaker notes, figure index, presentation shortlist |
| `docs/current_canonical_state.md` | This file |

---

## Legacy / non-canonical files

These files reflect earlier NET_RATE-based analysis or older synthetic data.
They are preserved for reference but are **not** the active analytical path.

| File | Status | Notes |
|------|--------|-------|
| `outputs/tables/a6_selected_models.csv` | Legacy | NET_RATE models (weak fits) |
| `outputs/tables/a6_selected_coefficients.csv` | Legacy | NET_RATE coefficients |
| `outputs/tables/a6_candidates_*.csv` | Legacy | NET_RATE candidate models |
| `outputs/tables/a6_notes.txt` | Legacy | NET_RATE model selection notes |
| `outputs/tables/robustness_*.csv` | Legacy | NET_RATE robustness checks |
| `outputs/tables/size_diag_*.csv` | Legacy | NET_RATE denominator diagnostics |
| `outputs/viz/proto*.html` | Legacy | A7 NET_RATE prototype visualizations |
| `scripts/a8_dashboard.py` | Legacy | Dash dashboard built for NET_RATE DVs |
| `docs/a8_reactive_viz_plan.md` | Legacy | Dashboard design (NET_RATE era) |
| `docs/main_specification.md` | Legacy | NET_RATE model specification |
| `docs/merge_ready_summary.md` | Legacy | NET_RATE completion summary |
| `docs/prototype_memo.md` | Legacy | A7 prototype ranking |
| `docs/deferred-iv-validation-memo.md` | Legacy | IV validation notes |

### Still-valid reference files

| File | Status | Notes |
|------|--------|-------|
| `docs/research-brief.md` | Reference | Original research specification (scope, IVs, age groups) |
| `docs/source-contract.md` | Reference | Variable source documentation |
| `docs/variable-dictionary.csv` | Reference | Column metadata |
| `docs/source-notes.md` | Reference | Data source notes |

---

## Scripts

| Script | Status | Purpose |
|--------|--------|---------|
| `scripts/distribution_shares.py` | Active | Raw share engineering + screening |
| `scripts/specialization_analysis.py` | Active | Specialization metrics + screening |
| `scripts/focused_deep_dive.py` | Active | Multivariable modeling + diagnostics for REL_IN_25_34, REL_IN_18_24 |
| `scripts/viz_distribution_shares.py` | Active | Raw share maps |
| `scripts/viz_specialization.py` | Active | Specialization maps + profiles |
| `scripts/viz_focused_deep_dive.py` | Active | 18 presentation-ready figures for deep dive |
| `scripts/build_dataset.py` | Reference | Data pipeline (source fetching) |
| `scripts/descriptive_a3.py` | Legacy | NET_RATE descriptive stats |
| `scripts/spearman_a4.py` | Legacy | NET_RATE Spearman screening |
| `scripts/single_ols_a5.py` | Legacy | NET_RATE single-variable OLS |
| `scripts/multiple_ols_a6.py` | Legacy | NET_RATE multi-variable OLS |
| `scripts/viz_prototypes.py` | Legacy | A7 NET_RATE prototype maps |
| `scripts/a8_dashboard.py` | Legacy | Dash dashboard (NET_RATE) |

---

## Recommended next steps

1. ~~**Multivariable modeling** on REL_IN_25_34 and REL_IN_18_24~~ — **DONE**
   (focused deep dive complete with 4 models, diagnostics, 18 figures)
2. **Presentation package** — storyline memo and figure shortlist created in
   `docs/focused_deep_dive_18_24_25_34.md`; slide deck assembly is the next step
3. **Optional: REL_IN_35_54 deep dive** — moderate signal (UNINSURED, adj R² = 0.26),
   could extend the analysis if time permits
4. **Optional: Updated dashboard** if interactive exploration is needed for the
   new DVs
