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
| baseline_ols | 50 | 0.1713 | 437.8 | 18.7317 | 6.07 (0.0045) |
| weighted_wls | 50 | 0.1694 | 426.4 | 10359.5989 | 6.00 (0.0048) |
| exclude_smallest_ols | 40 | 0.1804 | 324.2 | 13.4310 | 5.29 (0.0095) |

### Coefficient comparison

| Term | Spec | Coef | Sign | Sign match | Rank | p-value |
|---|---|---|---|---|---|---|
| COMMUTE_MED | baseline_ols | -2.786161 | - | ✓ | 1 | 0.0015 |
| COMMUTE_MED | weighted_wls | -1.694896 | - | ✓ | 1 | 0.0189 |
| COMMUTE_MED | exclude_smallest_ols | -1.611794 | - | ✓ | 1 | 0.0562 |
| MED_HOMEVAL | baseline_ols | 0.000009 | + | ✓ | 2 | 0.6607 |
| MED_HOMEVAL | weighted_wls | -0.000016 | - | ✗ FLIP | 2 | 0.1915 |
| MED_HOMEVAL | exclude_smallest_ols | -0.000025 | - | ✗ FLIP | 2 | 0.1638 |

### Interpretation

- Sign flip(s): MED_HOMEVAL (weighted_wls), MED_HOMEVAL (exclude_smallest_ols)

**Assessment**: **Sensitive**. Coefficient sign(s) reverse under alternative specification(s). The main story for 18–24 should be interpreted with caution.

---

## 35–54 ⚠ denominator-effect signal

### Model-level fit

| Specification | n | Adj R² | AIC | RMSE | F-stat (p) |
|---|---|---|---|---|---|
| baseline_ols | 50 | -0.0036 | 323.9 | 5.9973 | 0.91 (0.4086) |
| weighted_wls | 50 | 0.2447 | 322.3 | 6032.4620 | 8.94 (0.0005) |
| exclude_smallest_ols | 40 | 0.1154 | 242.5 | 4.8353 | 3.54 (0.0390) |

### Coefficient comparison

| Term | Spec | Coef | Sign | Sign match | Rank | p-value |
|---|---|---|---|---|---|---|
| REAL_PCPI | baseline_ols | -0.000187 | - | ✓ | 1 | 0.2046 |
| REAL_PCPI | weighted_wls | -0.000589 | - | ✓ | 1 | 0.0001 |
| REAL_PCPI | exclude_smallest_ols | -0.000369 | - | ✓ | 1 | 0.0116 |
| PERMITS | baseline_ols | -0.000011 | - | ✓ | 2 | 0.6095 |
| PERMITS | weighted_wls | 0.000001 | + | ✗ FLIP | 2 | 0.9147 |
| PERMITS | exclude_smallest_ols | 0.000004 | + | ✗ FLIP | 2 | 0.8200 |

### Interpretation

- Sign flip(s): PERMITS (weighted_wls), PERMITS (exclude_smallest_ols)
- WLS adj R² shift: +0.2483
- Exclusion adj R² shift: +0.1190

**Assessment**: **Sensitive**. Coefficient sign(s) reverse under alternative specification(s). The main story for 35–54 should be interpreted with caution.

---

## 25–34

### Model-level fit

| Specification | n | Adj R² | AIC | RMSE | F-stat (p) |
|---|---|---|---|---|---|
| baseline_ols | 50 | -0.0116 | 367.5 | 9.2685 | 0.72 (0.4925) |
| weighted_wls | 50 | 0.0953 | 355.5 | 6107.1375 | 3.58 (0.0356) |
| exclude_smallest_ols | 40 | 0.0653 | 268.7 | 6.7132 | 2.36 (0.1083) |

### Coefficient comparison

| Term | Spec | Coef | Sign | Sign match | Rank | p-value |
|---|---|---|---|---|---|---|
| NRI_RISK_INDEX | baseline_ols | 0.072423 | + | ✓ | 2 | 0.5258 |
| NRI_RISK_INDEX | weighted_wls | -0.034626 | - | ✗ FLIP | 2 | 0.7110 |
| NRI_RISK_INDEX | exclude_smallest_ols | 0.165422 | + | ✓ | 2 | 0.1497 |
| TRANSIT_SHARE | baseline_ols | -0.447234 | - | ✓ | 1 | 0.2441 |
| TRANSIT_SHARE | weighted_wls | -0.406021 | - | ✓ | 1 | 0.0178 |
| TRANSIT_SHARE | exclude_smallest_ols | -0.572802 | - | ✓ | 1 | 0.0485 |

### Interpretation

- Sign flip(s): NRI_RISK_INDEX (weighted_wls)
- WLS adj R² shift: +0.1069

**Assessment**: **Sensitive**. Coefficient sign(s) reverse under alternative specification(s). The main story for 25–34 should be interpreted with caution.

---

## 55–64

### Model-level fit

| Specification | n | Adj R² | AIC | RMSE | F-stat (p) |
|---|---|---|---|---|---|
| baseline_ols | 50 | 0.0127 | 332.9 | 6.5634 | 1.31 (0.2783) |
| weighted_wls | 50 | 0.2305 | 335.9 | 4839.2824 | 8.34 (0.0008) |
| exclude_smallest_ols | 40 | 0.0840 | 249.6 | 5.2847 | 2.79 (0.0745) |

### Coefficient comparison

| Term | Spec | Coef | Sign | Sign match | Rank | p-value |
|---|---|---|---|---|---|---|
| NRI_RISK_INDEX | baseline_ols | -0.024877 | - | ✓ | 2 | 0.7552 |
| NRI_RISK_INDEX | weighted_wls | 0.054333 | + | ✗ FLIP | 2 | 0.5327 |
| NRI_RISK_INDEX | exclude_smallest_ols | 0.025443 | + | ✗ FLIP | 2 | 0.7894 |
| ELEC_PRICE_TOT | baseline_ols | -0.236015 | - | ✓ | 1 | 0.1726 |
| ELEC_PRICE_TOT | weighted_wls | -0.567112 | - | ✓ | 1 | 0.0004 |
| ELEC_PRICE_TOT | exclude_smallest_ols | -0.480373 | - | ✓ | 1 | 0.0336 |

### Interpretation

- Sign flip(s): NRI_RISK_INDEX (weighted_wls), NRI_RISK_INDEX (exclude_smallest_ols)
- WLS adj R² shift: +0.2178

**Assessment**: **Sensitive**. Coefficient sign(s) reverse under alternative specification(s). The main story for 55–64 should be interpreted with caution.

---

## 65+

### Model-level fit

| Specification | n | Adj R² | AIC | RMSE | F-stat (p) |
|---|---|---|---|---|---|
| baseline_ols | 50 | 0.0382 | 302.9 | 4.8579 | 1.97 (0.1503) |
| weighted_wls | 50 | 0.2865 | 292.8 | 3859.7404 | 10.84 (0.0001) |
| exclude_smallest_ols | 40 | 0.1872 | 223.7 | 3.8217 | 5.49 (0.0082) |

### Coefficient comparison

| Term | Spec | Coef | Sign | Sign match | Rank | p-value |
|---|---|---|---|---|---|---|
| UNINSURED | baseline_ols | 0.287449 | + | ✓ | 1 | 0.3133 |
| UNINSURED | weighted_wls | 0.514944 | + | ✓ | 1 | 0.0023 |
| UNINSURED | exclude_smallest_ols | 0.680447 | + | ✓ | 1 | 0.0092 |
| RPP | baseline_ols | -0.142742 | - | ✓ | 2 | 0.1944 |
| RPP | weighted_wls | -0.172482 | - | ✓ | 2 | 0.0254 |
| RPP | exclude_smallest_ols | -0.102846 | - | ✓ | 2 | 0.2816 |

### Interpretation

- WLS adj R² shift: +0.2483
- Exclusion adj R² shift: +0.1490

**Assessment**: **Moderately sensitive**. Fit changes notably but coefficient signs are preserved. Findings are directionally consistent but magnitude/precision may differ.

---

## Overall Summary

**Some sensitivity detected**: 18–24, 35–54, 25–34, 55–64, 65+

### Key questions

**Q1: Which age groups are stable across specifications?**
  None are fully stable; all show some sensitivity.

**Q2: Which coefficients or model stories change materially?**
  - 18–24: MED_HOMEVAL flips sign under weighted_wls (baseline +, alternative -)
  - 18–24: MED_HOMEVAL flips sign under exclude_smallest_ols (baseline +, alternative -)
  - 35–54: PERMITS flips sign under weighted_wls (baseline -, alternative +)
  - 35–54: PERMITS flips sign under exclude_smallest_ols (baseline -, alternative +)
  - 25–34: NRI_RISK_INDEX flips sign under weighted_wls (baseline +, alternative -)
  - 55–64: NRI_RISK_INDEX flips sign under weighted_wls (baseline -, alternative +)
  - 55–64: NRI_RISK_INDEX flips sign under exclude_smallest_ols (baseline -, alternative +)

**Q3: Does denominator sensitivity alter the substantive interpretation?**
  Partial concern for 18–24, 35–54. In these age groups (where denominator-effect signal was detected), the alternative specifications show some sensitivity. The main conclusions should be presented alongside the robustness results, noting which findings are specification-dependent.
