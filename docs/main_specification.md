# Main Specification

## Research Scope

- **Geography**: 50 U.S. states only (DC, PR, and non-state geographies excluded)
- **Time**: 2024 cross-section only
- **Design**: State-level cross-sectional analysis of statistical association (not causal inference)
- **Explanatory variables**: Fixed set of 22 IVs (see `docs/research-brief.md` §7)

---

## Main Dependent Variable

**Interstate net migration rate per 1,000 age-group population (NET_RATE)**

Formula: `NET_RATE = 1000 × (IN_COUNT − OUT_COUNT) / POP_AGE`

Estimated separately for five age groups:

| Age Group | DV Column |
|-----------|-----------|
| 18–24 | NET_RATE_18_24 |
| 25–34 | NET_RATE_25_34 |
| 35–54 | NET_RATE_35_54 |
| 55–64 | NET_RATE_55_64 |
| 65+ | NET_RATE_65_PLUS |

Supplemental DVs (IN_RATE, OUT_RATE, NET_COUNT, IN_COUNT, OUT_COUNT) are available for diagnostic and contextual use but are not the main analysis target.

---

## Canonical Model Set (A6 Selected Models)

Source of truth: `outputs/tables/a6_selected_models.csv`

| Age Group | IVs | Adj R² | Selection Reason |
|-----------|-----|--------|------------------|
| 18–24 | COMMUTE_MED + MED_HOMEVAL | 0.171 | Highest adj_R2 with VIF<10 |
| 25–34 | NRI_RISK_INDEX + TRANSIT_SHARE | -0.012 | Highest adj_R2 with VIF<10 |
| 35–54 | REAL_PCPI + PERMITS | -0.004 | Highest adj_R2 with VIF<10 |
| 55–64 | NRI_RISK_INDEX + ELEC_PRICE_TOT | 0.013 | Highest adj_R2 with VIF<10 |
| 65+ | UNINSURED + RPP | 0.038 | Highest adj_R2 with VIF<10 |

The current selected specification uses 2-IV models for all five age groups.

---

## Denominator-Sensitivity Assessment

Size diagnostics (`scripts/size_diagnostics.py`) tested whether small-population states are over-represented in extreme NET_RATE rankings due to denominator effects.

| Age Group | Spearman rho (POP_AGE vs |NET_RATE|) | p-value | Signal |
|-----------|--------------------------------------|---------|--------|
| 18–24 | -0.418 | 0.0025 | Significant |
| 25–34 | -0.435 | 0.0016 | Significant |
| 35–54 | -0.208 | 0.1478 | Not significant |
| 55–64 | -0.089 | 0.5393 | Not significant |
| 65+ | -0.079 | 0.5833 | Not significant |

---

## Robustness Checks

Three specifications per age group (`scripts/robustness_denominator_checks.py`):

1. **Baseline OLS** — the A6 selected model (unweighted, n = 50)
2. **Population-weighted WLS** — WLS with POP_AGE as weights (n = 50)
3. **Exclusion OLS** — drop bottom-quintile POP_AGE states (n ≈ 40)

| Age Group | Baseline Adj R² | Weighted Adj R² | Exclude-smallest Adj R² | Sign flips vs baseline |
|-----------|-----------------|-----------------|--------------------------|------------------------|
| 18–24 | 0.171 | 0.169 | 0.180 | 2 |
| 25–34 | -0.012 | 0.095 | 0.065 | 1 |
| 35–54 | -0.004 | 0.245 | 0.115 | 2 |
| 55–64 | 0.013 | 0.231 | 0.084 | 2 |
| 65+ | 0.038 | 0.286 | 0.187 | 0 |

Current robustness checks show 7 coefficient sign flips versus baseline across weighted and exclusion specifications. The largest exclusion-based Adj R² decline appears in 18–24 (0.171 → 0.180).

---

## Provisional Data Sources

Two IVs use provisional/fallback data sources:

| IV | Issue | Fallback |
|----|-------|----------|
| CRIME_VIOLENT_RATE | FBI CDE API unreliable; SAPI endpoint deprecated | Manual CSV from CDE portal (`data_raw/fbi_crime_state_2024.csv`) |
| NRI_RISK_INDEX | FEMA NRI county-level data, Dec 2025 vintage | Population-weighted county→state aggregation (`data_raw/nri_counties_raw.csv`) |

NRI_RISK_INDEX uses Dec 2025-vintage data, which is a methodological exception to the 2024-only design scope. This is documented in `docs/deferred-iv-validation-memo.md`.

---

## File References

| Artifact | Path |
|----------|------|
| A6 selected models | `outputs/tables/a6_selected_models.csv` |
| A6 coefficients | `outputs/tables/a6_selected_coefficients.csv` |
| Size diagnostics (long) | `outputs/tables/size_diag_state_age_long.csv` |
| Size diagnostics (summary) | `outputs/tables/size_diag_summary_by_age.csv` |
| Robustness model comparison | `outputs/tables/robustness_model_compare.csv` |
| Robustness coefficient comparison | `outputs/tables/robustness_coeff_compare.csv` |
| Robustness notes | `outputs/tables/robustness_notes.md` |
| Size diagnostic notes | `outputs/tables/size_diag_notes.md` |
