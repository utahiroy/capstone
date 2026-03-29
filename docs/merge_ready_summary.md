# Merge-Ready Summary

## Completed in this refresh

- Re-ran **A6** (`python -m scripts.multiple_ols_a6`) against the current `data_processed/analysis_ready.csv`
- Re-ran **size diagnostics** (`python -m scripts.size_diagnostics`) against the same dataset
- Re-ran **robustness checks** (`python -m scripts.robustness_denominator_checks`) against the same dataset
- Rebuilt `docs/main_specification.md` and this summary from the refreshed outputs

---

## Canonical Source of Truth

**Main DV**: NET_RATE per 1,000 by age group (unchanged).

**A6 selected models** (`outputs/tables/a6_selected_models.csv`):

| Age Group | IVs | Adj R² |
|-----------|-----|--------|
| 18–24 | COMMUTE_MED + MED_HOMEVAL | 0.171 |
| 25–34 | NRI_RISK_INDEX + TRANSIT_SHARE | -0.012 |
| 35–54 | REAL_PCPI + PERMITS | -0.004 |
| 55–64 | NRI_RISK_INDEX + ELEC_PRICE_TOT | 0.013 |
| 65+ | UNINSURED + RPP | 0.038 |

Highest current fit: **18–24** (0.171).  
Lowest current fit: **25–34** (-0.012).

---

## Supplemental Results

- `outputs/tables/size_diag_*` — denominator-effect diagnostics
- `outputs/tables/robustness_*` — weighted and exclusion checks
- `outputs/viz/` — visual artifacts that should now be interpreted against the refreshed A6 outputs

---

## Remaining Cautions

1. **Provisional data sources** remain for `CRIME_VIOLENT_RATE` and `NRI_RISK_INDEX`.
2. **Robustness sensitivity**: Current robustness checks show 7 coefficient sign flips versus baseline across weighted and exclusion specifications. The largest exclusion-based Adj R² decline appears in 18–24 (0.171 → 0.180).
3. **Non-causal design**: all results remain correlational.

---

## Refresh Metadata

- Input dataset: `data_processed/analysis_ready.csv`
- Refreshed artifacts: A6, size diagnostics, robustness, `docs/main_specification.md`, `docs/merge_ready_summary.md`
