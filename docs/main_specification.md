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
| 18–24 | COMMUTE_MED + MED_HOMEVAL + UNINSURED | 0.312 | Simpler model (adj R² diff < 0.02) |
| 25–34 | NRI_RISK_INDEX + PRIV_ESTAB + PRIV_AVG_PAY | 0.196 | Highest adj R² with VIF < 10 |
| 35–54 | REAL_PCPI + PERMITS | 0.080 | Simpler model (adj R² diff < 0.02) |
| 55–64 | NRI_RISK_INDEX + PERMITS + POP_DENS | 0.235 | Highest adj R² with VIF < 10 |
| 65+ | UNINSURED + MED_HOMEVAL | 0.131 | Simpler model (adj R² diff < 0.02) |

This is a mixed 2–3 IV specification: three age groups use 3-IV models and two use 2-IV models.

### Why mixed 2–3 IV is preferred over uniform 2-IV

The A6 model selection procedure (documented in `scripts/multiple_ols_a6.py`) evaluates up to 5 candidate models per age group, selecting the preferred model based on:

1. **Adjusted R²** (primary fit metric)
2. **AIC / BIC** (parsimony-adjusted fit)
3. **VIF < 10** (multicollinearity constraint, per Marquardt 1970)
4. **Theoretical sign plausibility** (coefficient signs checked against priors)
5. **Simplicity preference** (if adj R² difference < 0.02, prefer the simpler model)

Under these rules:
- 18–24, 25–34, and 55–64 retain 3-IV models because the third IV contributes meaningfully to adj R² (difference ≥ 0.02 vs the 2-IV variant).
- 35–54 and 65+ use 2-IV models because the third candidate IV does not improve adj R² by the 0.02 threshold.

Forcing all models to uniform 2-IV would discard explanatory power in three age groups without a methodological justification. The mixed specification follows the selection rules stated in `docs/research-brief.md` §10 and `CLAUDE.md` without ad hoc overrides.

---

## Denominator-Sensitivity Assessment

Size diagnostics (`scripts/size_diagnostics.py`) tested whether small-population states are over-represented in extreme NET_RATE rankings due to denominator effects.

### Signal detected

| Age Group | Spearman rho (POP_AGE vs \|NET_RATE\|) | p-value | Signal |
|-----------|----------------------------------------|---------|--------|
| 18–24 | −0.432 | 0.002 | Significant |
| 35–54 | −0.344 | 0.014 | Significant |
| 25–34 | −0.205 | 0.154 | Not significant |
| 55–64 | −0.255 | 0.074 | Borderline |
| 65+ | −0.061 | 0.673 | Not significant |

18–24 and 35–54 show statistically significant denominator-effect signals: small states tend to have more extreme NET_RATE values.

### Robustness checks

Three specifications per age group (`scripts/robustness_denominator_checks.py`):

1. **Baseline OLS** — the A6 selected model (unweighted, n = 50)
2. **Population-weighted WLS** — WLS with POP_AGE as weights (n = 50)
3. **Exclusion OLS** — drop bottom-quintile POP_AGE states (n ≈ 40)

### Results

- **Zero coefficient sign flips** across all 5 age groups × 3 specifications.
- **Coefficient magnitude rank ordering** preserved everywhere.
- **18–24**: Stable. Adj R² drops modestly (0.312 → 0.255 under exclusion) but all signs, rankings, and significance patterns hold.
- **35–54**: Stable. Adj R² slightly improves under exclusion (0.080 → 0.102). Signs preserved.
- **55–64**: Moderately sensitive. Adj R² drops from 0.235 to 0.133 under exclusion (POP_DENS loses significance at p = 0.648). Signs preserved but precision weakens.
- **25–34, 65+**: Stable across all specifications.

### Conclusion

The main findings are directionally robust to both population-weighting and smallest-state exclusion. The denominator-effect signal in 18–24 and 35–54 does not materially alter the substantive interpretation. No change to the main specification is warranted.

The 55–64 model is directionally consistent but should be interpreted with the caveat that its fit is somewhat sensitive to sample composition, particularly the inclusion of the smallest states.

---

## Provisional Data Sources

Two IVs use provisional/fallback data sources:

| IV | Issue | Fallback |
|----|-------|----------|
| CRIME_VIOLENT_RATE | FBI CDE API unreliable; SAPI endpoint deprecated | Manual CSV from CDE portal (`data_raw/fbi_crime_state_2024.csv`) |
| NRI_RISK_INDEX | FEMA NRI county-level data, Dec 2025 vintage | Population-weighted county→state aggregation (`data_raw/nri_counties_raw.csv`) |

NRI_RISK_INDEX uses Dec 2025-vintage data, which is a methodological exception to the 2024-only design scope. This is documented in `docs/deferred-iv-validation-memo.md` and flagged in all visualization prototypes.

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
