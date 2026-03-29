# Size-Suppression Diagnostic Notes

**Small-population threshold**: bottom 20th percentile of POP_AGE within each age group (= 10 states per group).

---

## Age group: 18–24

**POP_AGE vs NET_RATE**: Spearman rho = -0.308 (p = 0.0293, significant)
  → smaller states tend to have higher net rates

**POP_AGE vs |NET_RATE|**: Spearman rho = -0.418 (p = 0.0025, significant)
  → Small states show systematically more extreme rates (denominator effect detected).

**Top-10 overlap (rate vs count)**: 2/10 gaining, 7/10 losing
  → Low overlap in gainers: rate rankings emphasize different states than count rankings.

**Small-state presence in rate extremes** (10 small states, expected ~2/10):
  - In top-10 NET_RATE: 6
  - In bottom-10 NET_RATE: 2
  - In top-10 |NET_RATE|: 6
  → Small states are **over-represented** in extreme rate rankings (expected ~2, got 6).

**Top 10 by NET_RATE**: Vermont, Wyoming, North Dakota, Hawaii, Rhode Island, South Carolina, Montana, West Virginia, Arkansas, Kentucky
**Top 10 by NET_COUNT**: South Carolina, North Carolina, Tennessee, Missouri, Arizona, Virginia, Kentucky, Oklahoma, Utah, Alabama

---

## Age group: 25–34

**POP_AGE vs NET_RATE**: Spearman rho = 0.062 (p = 0.6674, not significant)
  → weak or negligible association

**POP_AGE vs |NET_RATE|**: Spearman rho = -0.435 (p = 0.0016, significant)
  → Small states show systematically more extreme rates (denominator effect detected).

**Top-10 overlap (rate vs count)**: 5/10 gaining, 5/10 losing
  → Moderate-to-high overlap in gainers.

**Small-state presence in rate extremes** (10 small states, expected ~2/10):
  - In top-10 NET_RATE: 4
  - In bottom-10 NET_RATE: 4
  - In top-10 |NET_RATE|: 5
  → Small states are **over-represented** in extreme rate rankings (expected ~2, got 5).

**Top 10 by NET_RATE**: Maine, Nevada, Rhode Island, Maryland, New Mexico, Tennessee, Washington, Wyoming, New Hampshire, South Carolina
**Top 10 by NET_COUNT**: Texas, Washington, Tennessee, Maryland, Arizona, Nevada, South Carolina, Ohio, Wisconsin, Missouri

---

## Age group: 35–54

**POP_AGE vs NET_RATE**: Spearman rho = -0.284 (p = 0.0455, significant)
  → smaller states tend to have higher net rates

**POP_AGE vs |NET_RATE|**: Spearman rho = -0.208 (p = 0.1478, not significant)
  → Tendency for small states to have more extreme rates, but not statistically significant.

**Top-10 overlap (rate vs count)**: 4/10 gaining, 8/10 losing
  → Low overlap in gainers: rate rankings emphasize different states than count rankings.

**Small-state presence in rate extremes** (10 small states, expected ~2/10):
  - In top-10 NET_RATE: 6
  - In bottom-10 NET_RATE: 2
  - In top-10 |NET_RATE|: 6
  → Small states are **over-represented** in extreme rate rankings (expected ~2, got 6).

**Top 10 by NET_RATE**: Nevada, Delaware, Vermont, North Dakota, New Hampshire, Maine, South Carolina, Oklahoma, Georgia, Wyoming
**Top 10 by NET_COUNT**: Texas, Georgia, Nevada, North Carolina, South Carolina, Ohio, Arizona, Oklahoma, Maryland, Alabama

---

## Age group: 55–64

**POP_AGE vs NET_RATE**: Spearman rho = -0.212 (p = 0.1396, not significant)
  → smaller states tend to have higher net rates

**POP_AGE vs |NET_RATE|**: Spearman rho = -0.089 (p = 0.5393, not significant)
  → No strong evidence that small states have systematically more extreme rates.

**Top-10 overlap (rate vs count)**: 6/10 gaining, 7/10 losing
  → Moderate-to-high overlap in gainers.

**Small-state presence in rate extremes** (10 small states, expected ~2/10):
  - In top-10 NET_RATE: 3
  - In bottom-10 NET_RATE: 2
  - In top-10 |NET_RATE|: 4
  → Small states are **moderately over-represented** in extreme rate rankings.

**Top 10 by NET_RATE**: Vermont, South Carolina, Nevada, Delaware, Florida, Arizona, Idaho, Oklahoma, Maine, North Carolina
**Top 10 by NET_COUNT**: Florida, North Carolina, South Carolina, Arizona, Tennessee, Nevada, Alabama, Oklahoma, Texas, Georgia

---

## Age group: 65+

**POP_AGE vs NET_RATE**: Spearman rho = -0.072 (p = 0.6175, not significant)
  → weak or negligible association

**POP_AGE vs |NET_RATE|**: Spearman rho = -0.079 (p = 0.5833, not significant)
  → No strong evidence that small states have systematically more extreme rates.

**Top-10 overlap (rate vs count)**: 7/10 gaining, 7/10 losing
  → Moderate-to-high overlap in gainers.

**Small-state presence in rate extremes** (10 small states, expected ~2/10):
  - In top-10 NET_RATE: 2
  - In bottom-10 NET_RATE: 3
  - In top-10 |NET_RATE|: 2
  → Small-state representation in extremes is roughly proportional.

**Top 10 by NET_RATE**: Idaho, Nevada, Arizona, South Carolina, Florida, Mississippi, Oklahoma, Delaware, New Hampshire, Virginia
**Top 10 by NET_COUNT**: Florida, Arizona, South Carolina, Texas, Virginia, North Carolina, Nevada, Idaho, Oklahoma, Ohio

---

## Overall Assessment

Denominator-effect signal detected in: 18–24, 25–34.
In these age groups, small-population states tend to appear at the extremes of NET_RATE rankings, which may inflate their apparent importance in OLS models that weight all states equally.

**Implication**: Consider reporting both rate and count rankings side by side. For robustness, a sensitivity check using population-weighted regression or excluding the smallest states could be informative, but is not required to change the main specification.
