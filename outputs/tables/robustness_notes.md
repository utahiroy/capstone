# Denominator-Sensitivity Robustness Notes

**Purpose**: Test whether A6 main findings change materially under (a) population-weighted WLS or (b) exclusion of bottom-quintile POP_AGE states.

**Main DV**: NET_RATE by age group (unchanged).

**Design**: 50 U.S. states, 2024 cross-section. Three specifications per age group:
  1. **baseline_ols** — unweighted OLS (the A6 selected model)
  2. **weighted_wls** — WLS with POP_AGE as weights
  3. **exclude_smallest_ols** — OLS dropping bottom-quintile POP_AGE states (n ≈ 40)

---

## 18–24 ⚠ denominator-effect signal

### Model-level fit

| Specification | n | Adj R² | AIC | RMSE | F-stat (p) |
|---|---|---|---|---|---|
| baseline_ols | 50 | 0.3121 | 162.5 | 1.1826 | 8.41 (0.0001) |
| weighted_wls | 50 | 0.2869 | 157.0 | 1550.9543 | 7.57 (0.0003) |
| exclude_smallest_ols | 40 | 0.2549 | 109.1 | 0.9025 | 5.45 (0.0034) |

### Coefficient comparison

| Term | Spec | Coef | Sign | Sign match | Rank | p-value |
|---|---|---|---|---|---|---|
| COMMUTE_MED | baseline_ols | -0.127223 | - | ✓ | 1 | 0.0007 |
| COMMUTE_MED | weighted_wls | -0.111168 | - | ✓ | 1 | 0.0014 |
| COMMUTE_MED | exclude_smallest_ols | -0.083791 | - | ✓ | 1 | 0.0090 |
| MED_HOMEVAL | baseline_ols | -0.000002 | - | ✓ | 3 | 0.0053 |
| MED_HOMEVAL | weighted_wls | -0.000002 | - | ✓ | 3 | 0.0044 |
| MED_HOMEVAL | exclude_smallest_ols | -0.000002 | - | ✓ | 3 | 0.0087 |
| UNINSURED | baseline_ols | -0.088754 | - | ✓ | 2 | 0.0304 |
| UNINSURED | weighted_wls | -0.069935 | - | ✓ | 2 | 0.0606 |
| UNINSURED | exclude_smallest_ols | -0.053215 | - | ✓ | 2 | 0.1065 |

### Interpretation

**Assessment**: **Stable**. Signs, rank ordering, and fit are broadly consistent across specifications.

---

## 35–54 ⚠ denominator-effect signal

### Model-level fit

| Specification | n | Adj R² | AIC | RMSE | F-stat (p) |
|---|---|---|---|---|---|
| baseline_ols | 50 | 0.0804 | 220.2 | 2.1261 | 3.14 (0.0524) |
| weighted_wls | 50 | 0.0742 | 214.0 | 2800.8705 | 2.96 (0.0613) |
| exclude_smallest_ols | 40 | 0.1015 | 160.2 | 1.7294 | 3.20 (0.0521) |

### Coefficient comparison

| Term | Spec | Coef | Sign | Sign match | Rank | p-value |
|---|---|---|---|---|---|---|
| REAL_PCPI | baseline_ols | 0.000053 | + | ✓ | 1 | 0.0428 |
| REAL_PCPI | weighted_wls | 0.000047 | + | ✓ | 1 | 0.0513 |
| REAL_PCPI | exclude_smallest_ols | 0.000047 | + | ✓ | 1 | 0.0491 |
| PERMITS | baseline_ols | -0.000007 | - | ✓ | 2 | 0.2431 |
| PERMITS | weighted_wls | -0.000006 | - | ✓ | 2 | 0.2463 |
| PERMITS | exclude_smallest_ols | -0.000006 | - | ✓ | 2 | 0.2796 |

### Interpretation

**Assessment**: **Stable**. Signs, rank ordering, and fit are broadly consistent across specifications.

---

## 25–34

### Model-level fit

| Specification | n | Adj R² | AIC | RMSE | F-stat (p) |
|---|---|---|---|---|---|
| baseline_ols | 50 | 0.1958 | 258.4 | 3.0844 | 4.98 (0.0045) |
| weighted_wls | 50 | 0.1844 | 253.7 | 2815.4622 | 4.69 (0.0061) |
| exclude_smallest_ols | 40 | 0.2012 | 197.8 | 2.7368 | 4.27 (0.0111) |

### Coefficient comparison

| Term | Spec | Coef | Sign | Sign match | Rank | p-value |
|---|---|---|---|---|---|---|
| NRI_RISK_INDEX | baseline_ols | -0.051406 | - | ✓ | 1 | 0.0346 |
| NRI_RISK_INDEX | weighted_wls | -0.051383 | - | ✓ | 1 | 0.0235 |
| NRI_RISK_INDEX | exclude_smallest_ols | -0.051465 | - | ✓ | 1 | 0.0318 |
| PRIV_ESTAB | baseline_ols | -0.000009 | - | ✓ | 3 | 0.0155 |
| PRIV_ESTAB | weighted_wls | -0.000008 | - | ✓ | 3 | 0.0154 |
| PRIV_ESTAB | exclude_smallest_ols | -0.000008 | - | ✓ | 3 | 0.0211 |
| PRIV_AVG_PAY | baseline_ols | 0.000059 | + | ✓ | 2 | 0.1049 |
| PRIV_AVG_PAY | weighted_wls | 0.000044 | + | ✓ | 2 | 0.1954 |
| PRIV_AVG_PAY | exclude_smallest_ols | 0.000031 | + | ✓ | 2 | 0.3828 |

### Interpretation

**Assessment**: **Stable**. Signs, rank ordering, and fit are broadly consistent across specifications.

---

## 55–64

### Model-level fit

| Specification | n | Adj R² | AIC | RMSE | F-stat (p) |
|---|---|---|---|---|---|
| baseline_ols | 50 | 0.2347 | 194.1 | 1.6226 | 6.01 (0.0015) |
| weighted_wls | 50 | 0.2113 | 192.2 | 1956.9782 | 5.38 (0.0029) |
| exclude_smallest_ols | 40 | 0.1333 | 152.9 | 1.5601 | 3.00 (0.0432) |

### Coefficient comparison

| Term | Spec | Coef | Sign | Sign match | Rank | p-value |
|---|---|---|---|---|---|---|
| NRI_RISK_INDEX | baseline_ols | 0.040779 | + | ✓ | 1 | 0.0018 |
| NRI_RISK_INDEX | weighted_wls | 0.036838 | + | ✓ | 1 | 0.0033 |
| NRI_RISK_INDEX | exclude_smallest_ols | 0.028626 | + | ✓ | 1 | 0.0375 |
| PERMITS | baseline_ols | -0.000009 | - | ✓ | 3 | 0.0590 |
| PERMITS | weighted_wls | -0.000009 | - | ✓ | 3 | 0.0455 |
| PERMITS | exclude_smallest_ols | -0.000009 | - | ✓ | 3 | 0.0643 |
| POP_DENS | baseline_ols | -0.000339 | - | ✓ | 2 | 0.0456 |
| POP_DENS | weighted_wls | -0.000318 | - | ✓ | 2 | 0.1210 |
| POP_DENS | exclude_smallest_ols | -0.000270 | - | ✓ | 2 | 0.6480 |

### Interpretation

- Exclusion adj R² shift: -0.1014

**Assessment**: **Moderately sensitive**. Fit changes notably but coefficient signs are preserved. Findings are directionally consistent but magnitude/precision may differ.

---

## 65+

### Model-level fit

| Specification | n | Adj R² | AIC | RMSE | F-stat (p) |
|---|---|---|---|---|---|
| baseline_ols | 50 | 0.1310 | 161.2 | 1.1778 | 4.69 (0.0139) |
| weighted_wls | 50 | 0.1544 | 159.5 | 2016.0596 | 5.47 (0.0073) |
| exclude_smallest_ols | 40 | 0.1766 | 131.8 | 1.2115 | 5.18 (0.0104) |

### Coefficient comparison

| Term | Spec | Coef | Sign | Sign match | Rank | p-value |
|---|---|---|---|---|---|---|
| UNINSURED | baseline_ols | -0.101385 | - | ✓ | 1 | 0.0114 |
| UNINSURED | weighted_wls | -0.108278 | - | ✓ | 1 | 0.0057 |
| UNINSURED | exclude_smallest_ols | -0.124577 | - | ✓ | 1 | 0.0073 |
| MED_HOMEVAL | baseline_ols | 0.000001 | + | ✓ | 2 | 0.1048 |
| MED_HOMEVAL | weighted_wls | 0.000001 | + | ✓ | 2 | 0.1200 |
| MED_HOMEVAL | exclude_smallest_ols | 0.000001 | + | ✓ | 2 | 0.1125 |

### Interpretation

**Assessment**: **Stable**. Signs, rank ordering, and fit are broadly consistent across specifications.

---

## Overall Summary

**Stable across specifications**: 18–24, 35–54, 25–34, 65+
**Some sensitivity detected**: 55–64

### Key questions

**Q1: Which age groups are stable across specifications?**
  18–24, 35–54, 25–34, 65+.

**Q2: Which coefficients or model stories change materially?**
  No coefficient sign reversals detected across any age group or specification.

**Q3: Does denominator sensitivity alter the substantive interpretation?**
  No. Despite detecting denominator-effect signals in 18–24 and 35–54, the main model findings are directionally robust to population-weighting and smallest-state exclusion. The substantive interpretation does not change materially.
