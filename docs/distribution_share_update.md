# Distribution-Share DV Update

**Date**: 2026-04-10
**Branch**: `claude/setup-research-project-W4Fjs`
**Scope**: 50 U.S. states, 2024 cross-section, 5 age groups + all-ages

---

## 1. What changed

Previous main DV was `NET_RATE = 1000 * (IN - OUT) / POP`, a population-normalized
net migration rate. This update introduces **distribution-share** DVs based on
gross inflows and outflows.

### Formulas

For each age group *a* and state *s*:

```
IN_SHARE_{a,s}  = IN_COUNT_{a,s}  / SUM_over_50_states(IN_COUNT_{a})
OUT_SHARE_{a,s} = OUT_COUNT_{a,s} / SUM_over_50_states(OUT_COUNT_{a})
```

### Variables created (12 total)

| Variable | Description |
|----------|-------------|
| `IN_SHARE_18_24` | State share of national 18-24 interstate inflow |
| `IN_SHARE_25_34` | State share of national 25-34 interstate inflow |
| `IN_SHARE_35_54` | State share of national 35-54 interstate inflow |
| `IN_SHARE_55_64` | State share of national 55-64 interstate inflow |
| `IN_SHARE_65_PLUS` | State share of national 65+ interstate inflow |
| `IN_SHARE_ALL_AGES` | State share of national all-ages interstate inflow |
| `OUT_SHARE_18_24` | State share of national 18-24 interstate outflow |
| `OUT_SHARE_25_34` | State share of national 25-34 interstate outflow |
| `OUT_SHARE_35_54` | State share of national 35-54 interstate outflow |
| `OUT_SHARE_55_64` | State share of national 55-64 interstate outflow |
| `OUT_SHARE_65_PLUS` | State share of national 65+ interstate outflow |
| `OUT_SHARE_ALL_AGES` | State share of national all-ages interstate outflow |

Percentage versions (`*_SHARE_PCT_*`) are also included for readability.

### All-ages derivation

No all-ages gross-flow columns existed in the source data. `IN_COUNT_ALL_AGES`
and `OUT_COUNT_ALL_AGES` were derived by summing the 5 fixed age-group counts:

```
IN_COUNT_ALL_AGES  = IN_COUNT_18_24 + IN_COUNT_25_34 + IN_COUNT_35_54 + IN_COUNT_55_64 + IN_COUNT_65_PLUS
OUT_COUNT_ALL_AGES = OUT_COUNT_18_24 + OUT_COUNT_25_34 + OUT_COUNT_35_54 + OUT_COUNT_55_64 + OUT_COUNT_65_PLUS
```

This covers all five defined age groups but excludes under-18 movers.

---

## 2. Validation results

All 12 share families pass:
- n = 50 (no missing values)
- Sum = 1.000000 for each family
- No DC, PR, or non-state rows

---

## 3. Interpretation cautions

**These shares are NOT population-normalized rates.** They reflect:
- Each state's share of the national total gross flow for an age group
- State size and total migration volume are dominant drivers
- Large states (CA, TX, FL, NY) will naturally rank high on both IN and OUT shares

**What they measure:**
- "Of all 18-24 year olds who moved interstate in 2024, what fraction moved TO (or FROM) this state?"

**What they do NOT measure:**
- Whether migration is proportionate to state population
- Net migration balance
- Migration intensity relative to state size

**18-24 caveat:** This age group likely captures substantial college-related
migration and should not be interpreted as purely job-driven.

---

## 4. Key descriptive findings

### Top states by inflow share

| Age group | #1 | #2 | #3 |
|-----------|-----|-----|-----|
| 18-24 | TX (6.6%) | CA (5.9%) | NY (5.3%) |
| 25-34 | TX (8.4%) | CA (7.0%) | FL (6.2%) |
| 35-54 | TX (8.8%) | FL (8.3%) | CA (5.5%) |
| 55-64 | FL (13.6%) | TX (6.7%) | NC (4.9%) |
| 65+ | FL (14.7%) | TX (5.6%) | AZ (5.4%) |
| All ages | FL (8.0%) | TX (7.6%) | CA (5.9%) |

### Top states by outflow share

| Age group | #1 | #2 | #3 |
|-----------|-----|-----|-----|
| 18-24 | CA (8.4%) | TX (6.6%) | FL (5.2%) |
| 25-34 | CA (9.1%) | TX (6.8%) | NY (6.5%) |
| 35-54 | CA (10.1%) | FL (8.1%) | TX (7.2%) |
| 55-64 | CA (10.0%) | FL (7.6%) | NY (6.4%) |
| 65+ | FL (10.2%) | CA (9.4%) | NY (5.7%) |
| All ages | CA (9.3%) | FL (7.0%) | TX (6.6%) |

**Pattern**: CA, TX, and FL dominate both in- and out-shares across all age groups,
reflecting their large populations. FL's inflow share is disproportionately high for
55-64 and 65+ (retirement migration). CA's outflow share exceeds its inflow share
across all groups.

---

## 5. Statistical screening summary

### Spearman rank correlations

Distribution shares correlate very strongly (rho > 0.9) with state-size
indicators: POP, GDP, PRIV_EMP, PRIV_ESTAB. This is expected because shares
are not population-normalized.

Top correlates are nearly identical across all 12 DVs — all dominated by
state-size proxies.

### Single-variable OLS

Adj R² values are very high (0.47 to 0.94) but almost entirely driven by
state-size variables (POP, PRIV_EMP, GDP, PERMITS). This reflects the
mechanical relationship: bigger states have larger gross flows.

### Implication for multi-variable modeling

The extremely high correlation between share DVs and state-size IVs means:
- Multi-variable OLS would be heavily confounded by scale
- Any IV correlated with state population would appear "significant"
- Models would need to control for population first, or shares would need
  to be population-adjusted, to isolate non-mechanical relationships
- **Recommendation**: Before running A6-style multi-variable models on shares,
  consider whether the research question is better served by (a) examining
  residuals after controlling for POP, or (b) using per-capita share ratios

---

## 6. Files created

| File | Description |
|------|-------------|
| `data_processed/analysis_ready_distribution_shares.csv` | 50 states with 12 share + 12 pct columns |
| `outputs/tables/distribution_shares/share_validation.csv` | Validation: n, sum, min, max, pass/fail |
| `outputs/tables/distribution_shares/share_summary_stats.csv` | Mean, std, quartiles, CV for all 12 shares |
| `outputs/tables/distribution_shares/share_rankings_in.csv` | Top-5 / bottom-5 for each inflow share |
| `outputs/tables/distribution_shares/share_rankings_out.csv` | Top-5 / bottom-5 for each outflow share |
| `outputs/tables/distribution_shares/a4_spearman_kendall_shares.csv` | Spearman + Kendall for 12 DVs x 22 IVs |
| `outputs/tables/distribution_shares/a5_single_ols_shares.csv` | Single-variable OLS for 12 DVs x 22 IVs |
| `outputs/figures/distribution_shares/map_*.html` | 12 choropleth maps (6 IN + 6 OUT) |
| `scripts/distribution_shares.py` | Pipeline: engineering, validation, stats, screening |
| `scripts/viz_distribution_shares.py` | Map generation script |
| `docs/distribution_share_update.md` | This document |

---

## 7. Stale files

The following files reflect the prior NET_RATE DV and should NOT be used as
evidence for the distribution-share analysis:

- `outputs/tables/a6_selected_models.csv` — NET_RATE models
- `outputs/tables/a6_selected_coefficients.csv` — NET_RATE coefficients
- `outputs/tables/a6_candidates_*.csv` — NET_RATE candidates
- `outputs/tables/robustness_*.csv` — NET_RATE robustness checks
- `outputs/tables/size_diag_*.csv` — NET_RATE denominator diagnostics
- `docs/main_specification.md` — NET_RATE specification
- `docs/merge_ready_summary.md` — NET_RATE summary
- `scripts/a8_dashboard.py` — dashboard built for NET_RATE DVs
- `outputs/viz/proto*.html` — A7 prototypes for NET_RATE

These files are preserved for reference but are not canonical for the
distribution-share analysis.

---

## 8. Decisions needed

1. **Multi-variable modeling**: Should A6-style models be run on raw shares,
   or should shares be population-adjusted first? Raw shares will produce
   high R² but mostly reflect state size.
2. **Dashboard update**: Should the A8 dashboard be adapted for share DVs,
   or should it remain as a NET_RATE reference?
3. **Under-18 exclusion**: All-ages counts exclude under-18 movers. Is this
   acceptable, or should a separate total be sourced?
