# Specialization / Deviation Analysis Update

**Date**: 2026-04-10
**Branch**: `claude/setup-research-project-W4Fjs`
**Scope**: 50 U.S. states, 2024 cross-section, 5 age groups

---

## 1. Purpose

Raw distribution shares (IN_SHARE, OUT_SHARE) are dominated by state size:
large states capture large shares mechanically. This update creates
**specialization and deviation metrics** that remove the size baseline and
reveal which states are over- or under-represented for specific age groups
relative to their total migration footprint.

---

## 2. Metrics created

### 2A. Specialization ratios (REL_IN, REL_OUT)

```
REL_IN_{age}  = IN_SHARE_{age}  / IN_SHARE_ALL_AGES
REL_OUT_{age} = OUT_SHARE_{age} / OUT_SHARE_ALL_AGES
```

- `> 1` = state is over-represented for that age group vs its total
- `< 1` = under-represented
- `= 1` = proportional to overall migration footprint

### 2B. Difference from total (DIFF_IN, DIFF_OUT)

```
DIFF_IN_{age}  = IN_SHARE_{age}  - IN_SHARE_ALL_AGES
DIFF_OUT_{age} = OUT_SHARE_{age} - OUT_SHARE_ALL_AGES
```

- Positive = age-specific share above baseline
- Negative = below baseline
- Sums to 0 across 50 states (verified)

### 2C. Inflow-outflow share gap (SHARE_GAP)

```
SHARE_GAP_{age} = IN_SHARE_{age} - OUT_SHARE_{age}
```

- Positive = captures more inflow than outflow for that age group
- Negative = loses more than it gains

### 2D. Rank shifts

- Rank states by age-specific share and by all-ages share
- Shift = all-ages rank minus age-specific rank
- Positive shift = state ranks higher for this age group than overall

### Variables created: 25 metric columns + 500-row rank-shift table

| Family | Count | Variables |
|--------|-------|-----------|
| REL_IN | 5 | REL_IN_18_24 through REL_IN_65_PLUS |
| REL_OUT | 5 | REL_OUT_18_24 through REL_OUT_65_PLUS |
| DIFF_IN | 5 | DIFF_IN_18_24 through DIFF_IN_65_PLUS |
| DIFF_OUT | 5 | DIFF_OUT_18_24 through DIFF_OUT_65_PLUS |
| SHARE_GAP | 5 | SHARE_GAP_18_24 through SHARE_GAP_65_PLUS |

### "All ages" definition

Sum of 5 defined age groups (18-24 through 65+). Excludes under-18 movers.

---

## 3. Validation

- 25/25 variables pass (n=50, no missing, no infinities)
- 10/10 DIFF families sum to 0 across 50 states
- REL ratios range from ~0.37 to ~1.83 (plausible, no extreme outliers)
- No DC, PR, or non-state rows

---

## 4. Key substantive findings

### Size-dominance check

**Critical result**: After baseline adjustment, state-size IVs (POP, GDP,
PRIV_EMP) no longer dominate the top correlates.

| Metric family | Top-1 IV is size-related |
|---------------|--------------------------|
| REL_IN | 0 of 5 age groups |
| REL_OUT | 0 of 5 age groups |
| DIFF_IN | 0 of 5 age groups |
| DIFF_OUT | 1 of 5 age groups |
| SHARE_GAP | 3 of 5 age groups |

The specialization ratios (REL) and differences (DIFF) successfully remove
the mechanical size effect. SHARE_GAP retains some size sensitivity because
it compares raw shares across directions.

### Inflow specialization patterns (REL_IN)

| Age group | Top 3 over-represented states | Top Spearman correlate |
|-----------|-------------------------------|----------------------|
| 18-24 | ND (1.60), IA (1.51), VT (1.49) | COMMUTE_MED (rho = -0.48) |
| 25-34 | NY (1.27), AK (1.27), MD (1.20) | PRIV_AVG_PAY (rho = +0.63) |
| 35-54 | NV (1.39), GA (1.30), LA (1.25) | UNINSURED (rho = +0.48) |
| 55-64 | FL (1.70), DE (1.44), AZ (1.39) | REAL_PCPI (rho = -0.48) |
| 65+ | FL (1.83), AZ (1.62), ME (1.48) | REAL_PCPI (rho = -0.31) |

### Interpretation

**18-24 inflow specialization**: States like ND, IA, VT attract a
disproportionate share of young movers. Negatively correlated with commute
time and natural hazard risk. Likely reflects college-town and rural
university effects — **NOT** purely job-market driven.

**25-34 inflow specialization**: High-pay states (NY, MD, MA) attract
disproportionate 25-34 inflow. Strong positive correlation with PRIV_AVG_PAY
(rho = +0.63, adj R² = 0.39). Consistent with early-career job migration.

**35-54 inflow specialization**: NV, GA, LA over-represented. Correlated with
UNINSURED (+) and VACANCY_RATE (+). May reflect cost-of-living-driven
mid-career relocation to less-regulated states.

**55-64 / 65+ inflow specialization**: FL, AZ, ME dominate. Negatively
correlated with REAL_PCPI (income). Classic retirement/pre-retirement
migration pattern. FL captures 1.70x its all-ages inflow share for 55-64
and 1.83x for 65+.

### OLS explanatory power (adj R²)

| DV | Best single IV | Adj R² |
|----|----------------|--------|
| REL_IN_18_24 | NRI_RISK_INDEX | 0.235 |
| REL_IN_25_34 | PRIV_AVG_PAY | 0.392 |
| REL_IN_35_54 | UNINSURED | 0.262 |
| REL_IN_55_64 | VACANCY_RATE | 0.163 |
| REL_IN_65_PLUS | VACANCY_RATE | 0.066 |

25-34 shows the strongest single-variable explanatory power. 65+ is weakest
at the single-IV level.

---

## 5. Visualizations generated (44 files)

| Category | Count | Description |
|----------|-------|-------------|
| REL maps | 10 | Specialization ratio maps (diverging at 1.0) |
| DIFF maps | 10 | Difference-from-baseline maps (diverging at 0) |
| SHARE_GAP maps | 5 | Inflow-outflow gap maps (diverging at 0) |
| State profiles | 9 | Bar charts for FL, CA, TX, NY, AZ, NV, ND, ME, HI |
| Rank-shift dumbbells | 10 | Age-specific vs all-ages rank comparisons |

---

## 6. Files created

| File | Description |
|------|-------------|
| `data_processed/analysis_ready_specialization.csv` | 50 states with 25 new metric columns |
| `outputs/tables/specialization/validation.csv` | Validation results |
| `outputs/tables/specialization/summary_stats.csv` | Descriptive statistics |
| `outputs/tables/specialization/rankings.csv` | Top-5/bottom-5 for each metric |
| `outputs/tables/specialization/rank_shifts.csv` | 500-row rank-shift table |
| `outputs/tables/specialization/a4_spearman_kendall.csv` | Rank correlations vs 22 IVs |
| `outputs/tables/specialization/a5_single_ols.csv` | Single-variable OLS vs 22 IVs |
| `outputs/figures/specialization/map_*.html` | 25 choropleth maps |
| `outputs/figures/specialization/profile_*.html` | 9 state profile charts |
| `outputs/figures/specialization/rankshift_*.html` | 10 rank-shift dumbbell plots |
| `scripts/specialization_analysis.py` | Pipeline script |
| `scripts/viz_specialization.py` | Visualization script |
| `docs/specialization_update.md` | This document |

---

## 7. Multivariable modeling assessment

**Not pursued in this phase.** Rationale:

- REL_IN_25_34 shows strong single-IV signal (adj R² = 0.39 with PRIV_AVG_PAY),
  which may warrant 2-3 IV modeling in a subsequent phase
- REL_IN_18_24 and REL_IN_35_54 show moderate signal worth exploring
- REL_IN_55_64 and REL_IN_65_PLUS have weaker signals that may not support
  stable multi-IV models with n=50
- The SHARE_GAP family retains size contamination and is less suitable for
  explanatory modeling

**Recommendation**: Proceed to multivariable screening for REL_IN_25_34 and
possibly REL_IN_18_24 / REL_IN_35_54 in a dedicated subsequent phase.

---

## 8. Interpretation cautions

- **18-24 caveat**: This age group likely captures substantial college-related
  migration. ND, IA, VT specialization may reflect university locations, not
  job markets.
- **Specialization ≠ causation**: Correlations with PRIV_AVG_PAY, VACANCY_RATE
  etc. are associations, not causal claims.
- **Small n**: With n=50, all regressions are limited in degrees of freedom.
  Multi-IV models must be compact.
- **All-ages baseline excludes under-18**: This may slightly distort
  specialization ratios for states with large child populations.
- **SHARE_GAP still size-sensitive**: Unlike REL and DIFF, SHARE_GAP compares
  raw shares across directions and retains some state-size influence.
