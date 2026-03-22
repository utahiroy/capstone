# Size-Suppression Diagnostic Notes

**Small-population threshold**: bottom 20th percentile of POP_AGE within each age group (= 10 states per group).

---

## Age group: 18–24

**POP_AGE vs NET_RATE**: Spearman rho = 0.289 (p = 0.0418, significant)
  → larger states tend to have higher net rates

**POP_AGE vs |NET_RATE|**: Spearman rho = -0.432 (p = 0.0017, significant)
  → Small states show systematically more extreme rates (denominator effect detected).

**Top-10 overlap (rate vs count)**: 10/10 gaining, 6/10 losing
  → Moderate-to-high overlap in gainers.

**Small-state presence in rate extremes** (10 small states, expected ~2/10):
  - In top-10 NET_RATE: 1
  - In bottom-10 NET_RATE: 7
  - In top-10 |NET_RATE|: 7
  → Small states are **over-represented** in extreme rate rankings (expected ~2, got 7).

**Top 10 by NET_RATE**: Louisiana, Colorado, Vermont, Illinois, New Mexico, Kentucky, Kansas, Ohio, Virginia, Alabama
**Top 10 by NET_COUNT**: Louisiana, Colorado, New Mexico, Vermont, Illinois, Ohio, Kentucky, Virginia, Kansas, Alabama

---

## Age group: 25–34

**POP_AGE vs NET_RATE**: Spearman rho = -0.084 (p = 0.5642, not significant)
  → weak or negligible association

**POP_AGE vs |NET_RATE|**: Spearman rho = -0.205 (p = 0.1537, not significant)
  → Tendency for small states to have more extreme rates, but not statistically significant.

**Top-10 overlap (rate vs count)**: 9/10 gaining, 9/10 losing
  → Moderate-to-high overlap in gainers.

**Small-state presence in rate extremes** (10 small states, expected ~2/10):
  - In top-10 NET_RATE: 2
  - In bottom-10 NET_RATE: 3
  - In top-10 |NET_RATE|: 4
  → Small states are **moderately over-represented** in extreme rate rankings.

**Top 10 by NET_RATE**: Arkansas, Kansas, Wisconsin, New Jersey, Montana, Georgia, New Hampshire, Delaware, Washington, Alaska
**Top 10 by NET_COUNT**: New Hampshire, New Jersey, Montana, Arkansas, Georgia, Delaware, Washington, Wisconsin, Alaska, Wyoming

---

## Age group: 35–54

**POP_AGE vs NET_RATE**: Spearman rho = 0.191 (p = 0.1838, not significant)
  → weak or negligible association

**POP_AGE vs |NET_RATE|**: Spearman rho = -0.344 (p = 0.0144, significant)
  → Small states show systematically more extreme rates (denominator effect detected).

**Top-10 overlap (rate vs count)**: 9/10 gaining, 10/10 losing
  → Moderate-to-high overlap in gainers.

**Small-state presence in rate extremes** (10 small states, expected ~2/10):
  - In top-10 NET_RATE: 2
  - In bottom-10 NET_RATE: 4
  - In top-10 |NET_RATE|: 4
  → Small states are **moderately over-represented** in extreme rate rankings.

**Top 10 by NET_RATE**: California, Arizona, Florida, Montana, Louisiana, Utah, Mississippi, Wyoming, Kentucky, Kansas
**Top 10 by NET_COUNT**: California, Montana, Arizona, Utah, Louisiana, Florida, Mississippi, Kansas, Rhode Island, Wyoming

---

## Age group: 55–64

**POP_AGE vs NET_RATE**: Spearman rho = -0.022 (p = 0.8803, not significant)
  → weak or negligible association

**POP_AGE vs |NET_RATE|**: Spearman rho = -0.255 (p = 0.0743, not significant)
  → Tendency for small states to have more extreme rates, but not statistically significant.

**Top-10 overlap (rate vs count)**: 8/10 gaining, 9/10 losing
  → Moderate-to-high overlap in gainers.

**Small-state presence in rate extremes** (10 small states, expected ~2/10):
  - In top-10 NET_RATE: 4
  - In bottom-10 NET_RATE: 3
  - In top-10 |NET_RATE|: 4
  → Small states are **moderately over-represented** in extreme rate rankings.

**Top 10 by NET_RATE**: Idaho, Louisiana, South Carolina, Kentucky, California, New Jersey, Kansas, Oregon, Montana, Indiana
**Top 10 by NET_COUNT**: Idaho, Kentucky, Kansas, New Jersey, South Carolina, California, Montana, Louisiana, Michigan, Alabama

---

## Age group: 65+

**POP_AGE vs NET_RATE**: Spearman rho = 0.042 (p = 0.7715, not significant)
  → weak or negligible association

**POP_AGE vs |NET_RATE|**: Spearman rho = -0.061 (p = 0.6728, not significant)
  → No strong evidence that small states have systematically more extreme rates.

**Top-10 overlap (rate vs count)**: 9/10 gaining, 8/10 losing
  → Moderate-to-high overlap in gainers.

**Small-state presence in rate extremes** (10 small states, expected ~2/10):
  - In top-10 NET_RATE: 0
  - In bottom-10 NET_RATE: 2
  - In top-10 |NET_RATE|: 1
  → Small-state representation in extremes is roughly proportional.

**Top 10 by NET_RATE**: West Virginia, Pennsylvania, Illinois, Michigan, Oklahoma, North Dakota, Alaska, Ohio, New York, Delaware
**Top 10 by NET_COUNT**: West Virginia, Illinois, Pennsylvania, Michigan, Oklahoma, Alaska, Arkansas, North Dakota, Ohio, New York

---

## Overall Assessment

Denominator-effect signal detected in: 18–24, 35–54.
In these age groups, small-population states tend to appear at the extremes of NET_RATE rankings, which may inflate their apparent importance in OLS models that weight all states equally.

**Implication**: Consider reporting both rate and count rankings side by side. For robustness, a sensitivity check using population-weighted regression or excluding the smallest states could be informative, but is not required to change the main specification.
