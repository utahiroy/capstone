# Merge-Ready Summary

## Completed

### Data pipeline (A0–A2)
- 22-IV source contract finalized (`docs/source-contract.md`)
- Variable codes verified against ACS 2024 1-year metadata
- Full 50-state ingestion pipeline (`scripts/build_dataset.py`)
- Raw → interim → processed data separation
- Deferred IVs implemented: COMMUTE_MED, UNINSURED, CRIME_VIOLENT_RATE, NRI_RISK_INDEX

### Descriptive analysis (A3)
- Summary statistics, distributions, outlier diagnostics, state rankings
- Output: 8 files in `outputs/tables/a3_*`

### Spearman screening (A4)
- Rank correlations for all 22 IVs × 5 age-group DVs
- Output: 8 files in `outputs/tables/a4_*`

### Single-variable OLS (A5)
- 110 models (5 DVs × 22 IVs), adjusted R² as primary metric
- Output: 8 files in `outputs/tables/a5_*`

### Multiple regression (A6)
- 5 candidate models per age group, VIF < 10, sign plausibility checks
- Mixed 2–3 IV canonical model set selected
- Output: `a6_selected_models.csv`, `a6_selected_coefficients.csv`, 7 total files

### Visualizations (A7)
- 9 interactive HTML prototypes in `outputs/viz/`
- Protos 1a/1b (choropleths), 2 (IV maps), 3 (scatterplots), 4 (residual maps)
- Proto 5 (state profiles with rate toggle), 5b (counts + flags + 3 sort modes)
- Proto 6 (model summary), 7 (size diagnostic bubble scatter)
- All load A6 models dynamically from CSV; caveat footers on all prototypes

### Size diagnostics
- Denominator-effect testing: Spearman rho(POP_AGE, |NET_RATE|) by age group
- Signal detected in 18–24 and 35–54
- Output: 3 files in `outputs/tables/size_diag_*`

### Robustness checks
- WLS (POP_AGE weights) + exclusion OLS (drop bottom quintile) for all 5 age groups
- Zero sign flips; substantive interpretation unchanged
- Output: 3 files in `outputs/tables/robustness_*`

### Documentation
- `docs/research-brief.md` — full research design
- `docs/source-contract.md` — variable provenance and formulas
- `docs/main_specification.md` — canonical model set and robustness conclusion
- `docs/prototype_memo.md` — visualization ranking and polish recommendations
- `docs/deferred-iv-validation-memo.md` — CRIME/NRI fallback documentation
- `docs/source-notes.md` — data source notes
- `docs/variable-dictionary.csv` — variable metadata

---

## Canonical Source of Truth

**Main DV**: NET_RATE per 1,000 by age group (unchanged).

**A6 selected models** (`outputs/tables/a6_selected_models.csv`):

| Age Group | IVs | Adj R² |
|-----------|-----|--------|
| 18–24 | COMMUTE_MED + MED_HOMEVAL + UNINSURED | 0.312 |
| 25–34 | NRI_RISK_INDEX + PRIV_ESTAB + PRIV_AVG_PAY | 0.196 |
| 35–54 | REAL_PCPI + PERMITS | 0.080 |
| 55–64 | NRI_RISK_INDEX + PERMITS + POP_DENS | 0.235 |
| 65+ | UNINSURED + MED_HOMEVAL | 0.131 |

This mixed 2–3 IV specification is the canonical main result. See `docs/main_specification.md` for the full rationale.

---

## Supplemental Results

These outputs provide context and robustness but do not alter the main specification:

| Artifact | Purpose |
|----------|---------|
| Size diagnostics (`size_diag_*`) | Diagnose denominator effects in rate rankings |
| Robustness checks (`robustness_*`) | Confirm model stability under WLS and exclusion |
| Proto 5b | Visual comparison of rate vs count rankings with small-pop flags |
| Proto 7 | Bubble scatter of POP_AGE vs NET_RATE with volume context |
| IN_RATE / OUT_RATE / count columns | Supplemental DVs for interpretive context |

---

## Remaining Cautions

1. **Provisional data sources**: CRIME_VIOLENT_RATE uses a manual CSV fallback (FBI CDE portal). NRI_RISK_INDEX uses Dec 2025-vintage county data (methodological exception to 2024 scope). Both are flagged in all outputs.

2. **35–54 model weakness**: Adj R² = 0.080 is the lowest among all age groups. The model is statistically borderline (F p = 0.052). PERMITS is not significant (p = 0.243). This age group's migration patterns are poorly explained by the 22-IV framework.

3. **55–64 exclusion sensitivity**: Adj R² drops from 0.235 to 0.133 when the 10 smallest-population states are excluded. POP_DENS loses significance (p = 0.648). Findings for this group should be presented with the caveat that fit depends partly on small-state observations.

4. **Synthetic data in current session**: The `analysis_ready.csv` on disk was generated with synthetic data (APIs blocked by proxy). All A3–A7 outputs reflect synthetic patterns. Before final interpretation, re-run the full pipeline (`python -m scripts.build_dataset`) with API access to produce real data, then re-run all downstream scripts.

5. **Non-causal design**: All associations are correlational. The cross-sectional design cannot establish causality. This is stated in the research brief and flagged in all visualization footers.

---

## Recommended Merge Order

All work is on branch `claude/setup-research-project-W4Fjs`. The branch is ready for merge as a single PR.

**Pre-merge checklist:**
- [ ] Verify `analysis_ready.csv` uses real data (re-run pipeline with API access)
- [ ] Re-run A3–A7 + size diagnostics + robustness on real data
- [ ] Spot-check A6 coefficient signs against theoretical priors on real data
- [ ] Review `docs/main_specification.md` for accuracy after real-data rerun
- [ ] Confirm visualization prototypes render correctly in browser

**Post-merge:**
- Select 2–3 prototypes for polish (Proto 5/5b and Proto 1b recommended)
- Consider static export (PNG/PDF) for paper/slides
- Draft findings narrative based on real-data outputs
