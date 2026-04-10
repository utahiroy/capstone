# Focused Deep Dive: REL_IN_25_34 and REL_IN_18_24

**Date**: 2026-04-10
**Branch**: `claude/setup-research-project-W4Fjs`
**Scope**: Multivariable modeling, diagnostics, and presentation-ready figures

---

## 1. Storyline Memo (One-Page Summary)

### What we set out to show

After removing state-size confounding with specialization ratios, two age
groups emerged with the strongest and most interpretable inflow signals:

- **25–34** (early-career movers): Which state characteristics pull
  disproportionate young professional migration?
- **18–24** (college-age movers): What drives over-representation of the
  youngest adult migrants?

### What we found

**25–34 inflow specialization is driven by wages and accessibility.**
States with higher private-sector average pay and longer median commute times
attract disproportionately more 25–34 inflow. The best 2-IV model
(PRIV_AVG_PAY + COMMUTE_MED) explains 42% of cross-state variation
(adj R² = 0.42). Adding regional price parity (RPP) as a third IV offers
only marginal improvement (adj R² = 0.43) with increased collinearity.

The wage effect is intuitive: early-career workers move toward higher-paying
labor markets. The commute effect likely proxies for metro density and
job-center agglomeration — states with longer commutes tend to have large,
job-rich metro areas that attract young professionals.

Key states: NY and MD are prototypical high-pay, high-commute attractors.
AK is a high-pay outlier with short commutes (resource-economy effect).
WV shows the lowest 25–34 specialization, consistent with low wages and
limited metro job centers.

**18–24 inflow specialization is driven by accessibility and housing slack.**
States with shorter commute times and higher vacancy rates attract
disproportionately more 18–24 inflow. The best 2-IV model
(COMMUTE_MED + VACANCY_RATE) explains 38% of variation (adj R² = 0.38).
Adding transit share as a third IV improves fit to 42% (adj R² = 0.42)
with acceptable collinearity.

This pattern is the **opposite** of 25–34: young adults move toward
low-commute, high-vacancy states — consistent with college-town and
small-city migration rather than metro job-market migration. The transit
share effect in the 3-IV model suggests that states with more public transit
options (often college towns with bus systems) also attract this group.

Key states: ND (1.60×), IA (1.51×), VT (1.49×) are the most over-represented
for 18–24 inflow — all have prominent university systems relative to state
size. FL and TX are under-represented despite large absolute flows, because
their all-ages share is even larger.

### The punchline

**25–34 and 18–24 migration respond to opposite state characteristics.**
Early-career workers chase wages and dense metro labor markets. College-age
movers go where housing is available and commutes are short — hallmarks of
college towns and smaller cities. This divergence is the central finding.

### Robustness

All four selected models (2 DVs × 2 model sizes) show:
- Zero sign flips in leave-one-out analysis (every state removed, signs hold)
- Stable signs when excluding the 5 smallest states
- VIF < 3 for all terms (no multicollinearity concern)
- Cook's distance flags 3–5 influential observations per model, but none
  destabilizes the results

---

## 2. Selected Models Summary

### REL_IN_25_34 (25–34 Inflow Specialization)

| Model | IVs | Adj R² | AIC | BIC | Max VIF |
|-------|-----|--------|-----|-----|---------|
| **M25_2IV** (preferred) | PRIV_AVG_PAY + COMMUTE_MED | 0.4213 | -66.94 | -61.20 | 1.54 |
| M25_3IV | PRIV_AVG_PAY + RPP + COMMUTE_MED | 0.4328 | -67.02 | -59.37 | 2.86 |

**Preferred model**: M25_2IV — simpler, nearly identical fit, lower VIF.

Coefficients (M25_2IV):
| Term | Coef | Std Err | t | p | VIF |
|------|------|---------|---|---|-----|
| const | 0.217 | 0.123 | 1.76 | 0.086 | — |
| PRIV_AVG_PAY | 7.0e-06 | 2.0e-06 | 3.61 | 0.001 | 1.54 |
| COMMUTE_MED | 0.0114 | 0.0061 | 1.86 | 0.070 | 1.54 |

Interpretation: Each $1,000 increase in private-sector average pay is
associated with a 0.007 increase in the 25–34 specialization ratio. Each
additional minute of median commute time is associated with a 0.011 increase.

### REL_IN_18_24 (18–24 Inflow Specialization)

| Model | IVs | Adj R² | AIC | BIC | Max VIF |
|-------|-----|--------|-----|-----|---------|
| M18_2IV | COMMUTE_MED + VACANCY_RATE | 0.3769 | -24.95 | -19.22 | 1.00 |
| **M18_3IV** (preferred) | COMMUTE_MED + VACANCY_RATE + TRANSIT_SHARE | 0.4154 | -27.22 | -19.57 | 1.90 |

**Preferred model**: M18_3IV — meaningful fit improvement (+0.04 adj R²),
VIF still well below 3.

Coefficients (M18_3IV):
| Term | Coef | Std Err | t | p | VIF |
|------|------|---------|---|---|-----|
| const | 2.225 | 0.194 | 11.49 | <0.001 | — |
| COMMUTE_MED | -0.0428 | 0.0096 | -4.48 | <0.001 | 1.73 |
| VACANCY_RATE | -0.0458 | 0.0181 | -2.52 | 0.015 | 1.24 |
| TRANSIT_SHARE | 0.0188 | 0.0093 | 2.03 | 0.049 | 1.90 |

Interpretation: Each additional minute of median commute is associated with
a 0.043 decrease in 18–24 specialization. Each percentage-point increase in
vacancy rate is associated with a 0.046 decrease. Each percentage-point
increase in transit share is associated with a 0.019 increase.

---

## 3. Speaker Notes by Figure Type

### Choropleth Maps (Figures 01, 09)

**What it shows**: Geographic distribution of the specialization ratio across
50 states. Orange = under-represented (ratio < 1), white = proportional,
teal/green = over-represented (ratio > 1).

**25–34 map** (Fig 01): The Northeast corridor (NY, NJ, MD, MA) and Alaska
stand out as over-represented. The Mountain West and Deep South are
under-represented. This is a wage-geography story.

**18–24 map** (Fig 09): The Upper Midwest (ND, IA, SD) and New England
(VT, ME) are over-represented. Sun Belt states (FL, TX, AZ) are
under-represented despite large absolute flows. This is a college-town story.

**Key talking point**: Compare the two maps side-by-side — the geographic
patterns are strikingly different, reinforcing that different age groups
respond to different state characteristics.

### Scatter Plots (Figures 02–04, 10–12)

**What they show**: Each dot is a state. X-axis is the IV, Y-axis is the
specialization ratio. OLS trend line with 95% CI band. Key states labeled.

**For 25–34**: The PRIV_AVG_PAY scatter (Fig 02) is the strongest single
relationship in the project (adj R² = 0.39). Point out NY, MA, and MD in
the upper-right quadrant (high pay, high specialization). WV sits in the
lower-left. The RPP scatter (Fig 03) shows a similar but weaker pattern
(price levels track wages). The COMMUTE_MED scatter (Fig 04) shows the
metro-density proxy effect.

**For 18–24**: The COMMUTE_MED scatter (Fig 10) shows an **inverse**
relationship — opposite direction from 25–34. ND and IA have short commutes
and high 18–24 specialization. The NRI_RISK_INDEX scatter (Fig 11) shows
that low-hazard states attract more young adults. The MED_RENT scatter
(Fig 12) is negatively associated — cheaper states attract 18–24 movers.

**Key talking point**: Highlight the sign reversal on COMMUTE_MED between
age groups. This single variable captures the fundamental divergence.

### Fitted vs. Actual (Figures 05, 13)

**What they show**: Model predicted values (x-axis) vs. observed values
(y-axis). Points on the 45° line indicate perfect prediction. States far
from the line are poorly predicted by the model.

**Talking point**: Most states cluster near the line, confirming reasonable
model fit. Call out any states that deviate substantially — these are where
unmeasured factors (unique labor markets, policy, geography) play a role.

### Residual Maps (Figures 06, 14)

**What they show**: Geographic distribution of model residuals. Blue = model
under-predicts (actual ratio higher than expected). Red = model over-predicts
(actual ratio lower than expected).

**Talking point**: Look for spatial clustering in residuals. If residuals
cluster regionally, there may be an unmeasured regional factor. Scattered
residuals suggest the model captures the main spatial pattern.

### Ranking Charts (Figures 07, 15)

**What they show**: All 50 states ranked by specialization ratio, displayed
as horizontal bars. Color intensity reflects the ratio value.

**25–34** (Fig 07): NY, AK, MD lead. WV, MS, WY trail.

**18–24** (Fig 15): ND, IA, VT lead. FL, TX, NV trail.

**Talking point**: The top-5 and bottom-5 lists for each age group have
almost no overlap, reinforcing the different-drivers narrative.

### State Spotlights (Figures 08, 16)

**What they show**: Multi-panel profiles of key states, showing their
position across multiple IVs and DVs simultaneously.

**Talking point**: Use these to tell the story of individual states.
For 25–34, NY is the archetype — high pay, high commute, high specialization.
For 18–24, ND is the archetype — short commute, high vacancy, high
specialization, prominent university system relative to population.

### Correlation Heatmap (Figure 17)

**What it shows**: Spearman rank correlations between both DVs and all 22
IVs, displayed as a color matrix. Blue = positive, red = negative.

**Talking point**: The heatmap makes the sign-reversal pattern immediately
visible. PRIV_AVG_PAY is strongly positive for 25–34 but near-zero for
18–24. COMMUTE_MED is positive for 25–34 but strongly negative for 18–24.
VACANCY_RATE is near-zero for 25–34 but strongly negative for 18–24.

### Model Comparison Heatmap (Figure 18)

**What it shows**: Summary comparison of all four selected models across key
diagnostics: adj R², AIC, BIC, max VIF, LOO stability, small-state
robustness.

**Talking point**: All models are well-behaved. Use this figure to justify
the preferred model choices (2IV for 25–34, 3IV for 18–24).

---

## 4. Presentation Shortlist (Best 6–10 Figures)

These are the **most important figures** for a slide presentation, ranked
by priority. A compelling 10-minute presentation can be built from just
these figures.

| Priority | File | Title | Why It Matters |
|----------|------|-------|----------------|
| 1 | `01_map_REL_IN_25_34.html` | 25–34 inflow specialization map | Opens the narrative — where do young professionals go? |
| 2 | `09_map_REL_IN_18_24.html` | 18–24 inflow specialization map | Side-by-side contrast with 25–34 is the core finding |
| 3 | `02_scatter_25_34_pay.html` | 25–34 vs. private-sector pay | Strongest single relationship in the project (R² = 0.39) |
| 4 | `10_scatter_18_24_commute.html` | 18–24 vs. commute time | Shows inverse relationship — opposite direction from 25–34 |
| 5 | `17_heatmap_correlation.html` | Cross-DV correlation heatmap | Makes sign-reversal pattern visually immediate |
| 6 | `05_fitted_actual_25_34.html` | 25–34 fitted vs. actual | Validates model fit — shows prediction quality |
| 7 | `13_fitted_actual_18_24.html` | 18–24 fitted vs. actual | Validates 18–24 model fit |
| 8 | `06_residual_map_25_34.html` | 25–34 residual map | Shows what the model misses geographically |
| 9 | `07_ranking_25_34.html` | 25–34 state rankings | Clean visual for top/bottom states |
| 10 | `18_heatmap_models.html` | Model comparison summary | Technical validation slide |

### Suggested slide sequence

1. **Motivation**: Why study age-specific migration? (no figure needed)
2. **Method overview**: Specialization ratios remove size confound (no figure)
3. **25–34 map** (Fig 01) — "Where do young professionals go?"
4. **25–34 scatter** (Fig 02) — "Wages explain 39% of variation"
5. **18–24 map** (Fig 09) — "College-age movers go somewhere completely different"
6. **18–24 scatter** (Fig 10) — "Short commutes, not high wages"
7. **Correlation heatmap** (Fig 17) — "The sign reversal across all 22 IVs"
8. **Fitted vs. actual** (Figs 05, 13) — "Both models fit well"
9. **Residual map** (Fig 06 or 14) — "What the model doesn't capture"
10. **Model comparison** (Fig 18) — "Robustness summary"
11. **Conclusions and limitations** (no figure needed)

---

## 5. Complete Figure Index

| # | Filename | DV | Type | IVs/Content |
|---|----------|-----|------|-------------|
| 01 | `01_map_REL_IN_25_34.html` | REL_IN_25_34 | Choropleth | Specialization ratio |
| 02 | `02_scatter_25_34_pay.html` | REL_IN_25_34 | Scatter | PRIV_AVG_PAY |
| 03 | `03_scatter_25_34_rpp.html` | REL_IN_25_34 | Scatter | RPP |
| 04 | `04_scatter_25_34_commute.html` | REL_IN_25_34 | Scatter | COMMUTE_MED |
| 05 | `05_fitted_actual_25_34.html` | REL_IN_25_34 | Fitted vs Actual | M25_2IV model |
| 06 | `06_residual_map_25_34.html` | REL_IN_25_34 | Residual map | M25_2IV residuals |
| 07 | `07_ranking_25_34.html` | REL_IN_25_34 | Ranking | All 50 states |
| 08 | `08_spotlight_25_34.html` | REL_IN_25_34 | State spotlight | Key states profile |
| 09 | `09_map_REL_IN_18_24.html` | REL_IN_18_24 | Choropleth | Specialization ratio |
| 10 | `10_scatter_18_24_commute.html` | REL_IN_18_24 | Scatter | COMMUTE_MED |
| 11 | `11_scatter_18_24_nri.html` | REL_IN_18_24 | Scatter | NRI_RISK_INDEX |
| 12 | `12_scatter_18_24_rent.html` | REL_IN_18_24 | Scatter | MED_RENT |
| 13 | `13_fitted_actual_18_24.html` | REL_IN_18_24 | Fitted vs Actual | M18_3IV model |
| 14 | `14_residual_map_18_24.html` | REL_IN_18_24 | Residual map | M18_3IV residuals |
| 15 | `15_ranking_18_24.html` | REL_IN_18_24 | Ranking | All 50 states |
| 16 | `16_spotlight_18_24.html` | REL_IN_18_24 | State spotlight | Key states profile |
| 17 | `17_heatmap_correlation.html` | Both | Heatmap | Spearman rho × 22 IVs |
| 18 | `18_heatmap_models.html` | Both | Heatmap | 4 models × diagnostics |

---

## 6. Interpretation Cautions

- **Correlation ≠ causation**: All associations are cross-sectional. Wages
  may attract 25–34 movers, or high-wage states may attract them for other
  unmeasured reasons (culture, amenities, networks).
- **College-migration caveat** (professor's note): The 18–24 pattern likely
  reflects college enrollment migration, not pure labor-market choice.
  ND, IA, VT specialization may be driven by university capacity relative
  to state population.
- **Small n**: With n = 50, 2–3 IV models are near the complexity limit.
  Do not over-interpret marginal significance.
- **COMMUTE_MED as proxy**: Commute time is not a direct causal driver of
  migration. It proxies for metro density, job-center agglomeration, and
  urbanization — the underlying constructs that plausibly drive location
  choice.
- **All-ages baseline excludes under-18**: Specialization ratios are
  computed against the sum of 5 adult age groups, not total population.
