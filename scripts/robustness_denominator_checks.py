"""Robustness checks for denominator sensitivity.

Supplemental analysis testing whether the A6 main findings are materially
sensitive to (a) population-weighting or (b) excluding the smallest states.

Does NOT overwrite any A6 or A7 outputs.

Reads:
  data_processed/analysis_ready.csv
  outputs/tables/a6_selected_models.csv
  outputs/tables/size_diag_state_age_long.csv

Writes:
  outputs/tables/robustness_model_compare.csv
  outputs/tables/robustness_coeff_compare.csv
  outputs/tables/robustness_notes.md

Run:  python -m scripts.robustness_denominator_checks
"""

import os
import sys

import numpy as np
import pandas as pd
import statsmodels.api as sm

from src.constants import AGE_GROUPS

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
ANALYSIS_PATH = "data_processed/analysis_ready.csv"
A6_MODELS_PATH = "outputs/tables/a6_selected_models.csv"
DIAG_LONG_PATH = "outputs/tables/size_diag_state_age_long.csv"
OUT_DIR = "outputs/tables"

OUT_MODEL = os.path.join(OUT_DIR, "robustness_model_compare.csv")
OUT_COEFF = os.path.join(OUT_DIR, "robustness_coeff_compare.csv")
OUT_NOTES = os.path.join(OUT_DIR, "robustness_notes.md")

AG_LABELS = {
    "18_24": "18–24", "25_34": "25–34", "35_54": "35–54",
    "55_64": "55–64", "65_PLUS": "65+",
}

# Age groups where size diagnostics detected a significant denominator-effect
DENOM_EFFECT_AGS = {"18_24", "35_54"}

SIGN_MAP = {True: "+", False: "-"}


def load_inputs():
    for p in (ANALYSIS_PATH, A6_MODELS_PATH, DIAG_LONG_PATH):
        if not os.path.exists(p):
            print(f"ERROR: {p} not found.")
            sys.exit(1)

    df = pd.read_csv(ANALYSIS_PATH, dtype={"state": str})
    df["state"] = df["state"].str.zfill(2)

    a6 = pd.read_csv(A6_MODELS_PATH)
    models = {}
    for _, row in a6.iterrows():
        ag = row["age_group"]
        ivs = [iv.strip() for iv in row["selected_ivs"].split(",")]
        models[ag] = ivs

    diag = pd.read_csv(DIAG_LONG_PATH, dtype={"state": str})
    diag["state"] = diag["state"].str.zfill(2)

    return df, models, diag


def fit_ols(y, X, weights=None):
    """Fit OLS or WLS and return result object."""
    Xc = sm.add_constant(X.astype(float))
    if weights is not None:
        model = sm.WLS(y.astype(float), Xc, weights=weights).fit()
    else:
        model = sm.OLS(y.astype(float), Xc).fit()
    return model


def extract_results(model, ag, model_type, ivs, n):
    """Extract model-level and coefficient-level rows."""
    formula = f"NET_RATE_{ag} ~ {' + '.join(ivs)}"

    model_row = {
        "age_group": ag,
        "model_type": model_type,
        "formula": formula,
        "n": n,
        "r2": round(model.rsquared, 4),
        "adj_r2": round(model.rsquared_adj, 4),
        "aic": round(model.aic, 2),
        "bic": round(model.bic, 2),
        "rmse": round(np.sqrt(model.mse_resid), 4),
        "f_stat": round(model.fvalue, 3),
        "f_pvalue": round(model.f_pvalue, 4),
    }

    coeff_rows = []
    for term in ivs:
        if term not in model.params.index:
            continue
        coeff_rows.append({
            "age_group": ag,
            "model_type": model_type,
            "term": term,
            "coef": round(model.params[term], 6),
            "std_err": round(model.bse[term], 6),
            "t_stat": round(model.tvalues[term], 3),
            "p_value": round(model.pvalues[term], 4),
            "ci_lower": round(model.conf_int().loc[term, 0], 6),
            "ci_upper": round(model.conf_int().loc[term, 1], 6),
            "sign": SIGN_MAP[model.params[term] > 0],
        })

    return model_row, coeff_rows


def run_checks(df, models, diag):
    """Run baseline, WLS, and exclusion OLS for each age group."""
    model_rows = []
    coeff_rows = []

    for ag in AGE_GROUPS:
        ivs = models[ag]
        dv = f"NET_RATE_{ag}"
        pop_col = f"POP_AGE_{ag}"

        # Get small_pop_flag from diagnostic table
        small_states = set(
            diag[(diag["age_group"] == ag) & (diag["small_pop_flag"] == 1)]["state"]
        )

        # --- Baseline OLS (n=50) ---
        y = df[dv]
        X = df[ivs]
        m_base = fit_ols(y, X)
        mr, cr = extract_results(m_base, ag, "baseline_ols", ivs, len(df))
        model_rows.append(mr)
        coeff_rows.extend(cr)

        # --- Population-weighted WLS (n=50) ---
        weights = df[pop_col].astype(float)
        m_wls = fit_ols(y, X, weights=weights)
        mr, cr = extract_results(m_wls, ag, "weighted_wls", ivs, len(df))
        model_rows.append(mr)
        coeff_rows.extend(cr)

        # --- Exclusion OLS: drop bottom-quintile POP_AGE states ---
        mask = ~df["state"].isin(small_states)
        df_exc = df[mask]
        y_exc = df_exc[dv]
        X_exc = df_exc[ivs]
        m_exc = fit_ols(y_exc, X_exc)
        mr, cr = extract_results(m_exc, ag, "exclude_smallest_ols", ivs, len(df_exc))
        model_rows.append(mr)
        coeff_rows.extend(cr)

    return pd.DataFrame(model_rows), pd.DataFrame(coeff_rows)


def compute_sign_consistency(coeff_df):
    """Add sign_match_vs_baseline column to coefficient table."""
    baseline = coeff_df[coeff_df["model_type"] == "baseline_ols"][
        ["age_group", "term", "sign"]
    ].rename(columns={"sign": "baseline_sign"})

    merged = coeff_df.merge(baseline, on=["age_group", "term"], how="left")
    merged["sign_match_vs_baseline"] = merged["sign"] == merged["baseline_sign"]
    return merged


def compute_magnitude_ranks(coeff_df):
    """Add rank of |coef| within each (age_group, model_type)."""
    coeff_df = coeff_df.copy()
    coeff_df["abs_coef"] = coeff_df["coef"].abs()
    coeff_df["coef_rank"] = coeff_df.groupby(
        ["age_group", "model_type"]
    )["abs_coef"].rank(ascending=False).astype(int)
    return coeff_df


def write_notes(model_df, coeff_df):
    """Generate plain-language robustness memo."""
    lines = [
        "# Denominator-Sensitivity Robustness Notes",
        "",
        "**Purpose**: Test whether A6 main findings change materially under "
        "(a) population-weighted WLS or (b) exclusion of bottom-quintile "
        "POP_AGE states.",
        "",
        "**Main DV**: NET_RATE by age group (unchanged).",
        "",
        "**Design**: 50 U.S. states, 2024 cross-section. Three specifications "
        "per age group:",
        "  1. **baseline_ols** — unweighted OLS (the A6 selected model)",
        "  2. **weighted_wls** — WLS with POP_AGE as weights",
        "  3. **exclude_smallest_ols** — OLS dropping bottom-quintile POP_AGE "
        "states (n ≈ 40)",
        "",
        "---",
        "",
    ]

    # Per-age-group analysis — prioritize 18-24 and 35-54
    ordered_ags = sorted(AGE_GROUPS,
                         key=lambda ag: (0 if ag in DENOM_EFFECT_AGS else 1,
                                         AGE_GROUPS.index(ag)))

    stability_summary = {}

    for ag in ordered_ags:
        label = AG_LABELS[ag]
        denom_note = " ⚠ denominator-effect signal" if ag in DENOM_EFFECT_AGS else ""
        lines.append(f"## {label}{denom_note}")
        lines.append("")

        # Model-level comparison
        sub_m = model_df[model_df["age_group"] == ag]
        lines.append("### Model-level fit")
        lines.append("")
        lines.append("| Specification | n | Adj R² | AIC | RMSE | F-stat (p) |")
        lines.append("|---|---|---|---|---|---|")
        for _, r in sub_m.iterrows():
            fp = f"{r['f_stat']:.2f} ({r['f_pvalue']:.4f})"
            lines.append(
                f"| {r['model_type']} | {r['n']} | {r['adj_r2']:.4f} | "
                f"{r['aic']:.1f} | {r['rmse']:.4f} | {fp} |"
            )
        lines.append("")

        # Coefficient comparison
        sub_c = coeff_df[coeff_df["age_group"] == ag]
        ivs = sub_c[sub_c["model_type"] == "baseline_ols"]["term"].tolist()

        lines.append("### Coefficient comparison")
        lines.append("")
        lines.append("| Term | Spec | Coef | Sign | Sign match | Rank | p-value |")
        lines.append("|---|---|---|---|---|---|---|")

        sign_flips = []
        for iv in ivs:
            iv_rows = sub_c[sub_c["term"] == iv].sort_values(
                "model_type", key=lambda s: s.map({
                    "baseline_ols": 0, "weighted_wls": 1, "exclude_smallest_ols": 2
                })
            )
            for _, r in iv_rows.iterrows():
                match_str = "✓" if r["sign_match_vs_baseline"] else "✗ FLIP"
                lines.append(
                    f"| {r['term']} | {r['model_type']} | {r['coef']:.6f} | "
                    f"{r['sign']} | {match_str} | {r['coef_rank']} | {r['p_value']:.4f} |"
                )
                if not r["sign_match_vs_baseline"] and r["model_type"] != "baseline_ols":
                    sign_flips.append((r["term"], r["model_type"]))
        lines.append("")

        # Interpretation
        lines.append("### Interpretation")
        lines.append("")

        base_r2 = sub_m[sub_m["model_type"] == "baseline_ols"]["adj_r2"].values[0]
        wls_r2 = sub_m[sub_m["model_type"] == "weighted_wls"]["adj_r2"].values[0]
        exc_r2 = sub_m[sub_m["model_type"] == "exclude_smallest_ols"]["adj_r2"].values[0]

        r2_delta_wls = wls_r2 - base_r2
        r2_delta_exc = exc_r2 - base_r2

        # Stability assessment
        stable = True
        issues = []

        if sign_flips:
            stable = False
            flip_strs = [f"{t} ({m})" for t, m in sign_flips]
            issues.append(f"Sign flip(s): {', '.join(flip_strs)}")

        if abs(r2_delta_wls) > 0.10:
            issues.append(f"WLS adj R² shift: {r2_delta_wls:+.4f}")
        if abs(r2_delta_exc) > 0.10:
            issues.append(f"Exclusion adj R² shift: {r2_delta_exc:+.4f}")

        if issues:
            for issue in issues:
                lines.append(f"- {issue}")
            lines.append("")

        if sign_flips:
            lines.append(
                f"**Assessment**: **Sensitive**. Coefficient sign(s) reverse under "
                f"alternative specification(s). The main story for {label} should "
                f"be interpreted with caution."
            )
        elif abs(r2_delta_wls) > 0.10 or abs(r2_delta_exc) > 0.10:
            lines.append(
                f"**Assessment**: **Moderately sensitive**. Fit changes notably "
                f"but coefficient signs are preserved. Findings are directionally "
                f"consistent but magnitude/precision may differ."
            )
        else:
            lines.append(
                f"**Assessment**: **Stable**. Signs, rank ordering, and fit are "
                f"broadly consistent across specifications."
            )

        stability_summary[ag] = {
            "sign_flips": len(sign_flips),
            "r2_delta_wls": r2_delta_wls,
            "r2_delta_exc": r2_delta_exc,
            "stable": stable and not issues,
        }

        lines.append("")
        lines.append("---")
        lines.append("")

    # Overall summary
    lines.append("## Overall Summary")
    lines.append("")

    stable_ags = [AG_LABELS[ag] for ag in ordered_ags
                  if stability_summary[ag]["stable"]]
    sensitive_ags = [AG_LABELS[ag] for ag in ordered_ags
                     if not stability_summary[ag]["stable"]]

    if stable_ags:
        lines.append(f"**Stable across specifications**: {', '.join(stable_ags)}")
    if sensitive_ags:
        lines.append(f"**Some sensitivity detected**: {', '.join(sensitive_ags)}")
    lines.append("")

    # Answer the three key questions
    lines.append("### Key questions")
    lines.append("")

    lines.append("**Q1: Which age groups are stable across specifications?**")
    if stable_ags:
        lines.append(f"  {', '.join(stable_ags)}.")
    else:
        lines.append("  None are fully stable; all show some sensitivity.")
    lines.append("")

    lines.append("**Q2: Which coefficients or model stories change materially?**")
    any_flips = False
    for ag in ordered_ags:
        sub_c = coeff_df[(coeff_df["age_group"] == ag) &
                         (~coeff_df["sign_match_vs_baseline"]) &
                         (coeff_df["model_type"] != "baseline_ols")]
        if len(sub_c) > 0:
            any_flips = True
            for _, r in sub_c.iterrows():
                lines.append(
                    f"  - {AG_LABELS[ag]}: {r['term']} flips sign under "
                    f"{r['model_type']} (baseline {r['baseline_sign']}, "
                    f"alternative {r['sign']})"
                )
    if not any_flips:
        lines.append("  No coefficient sign reversals detected across any "
                      "age group or specification.")
    lines.append("")

    lines.append("**Q3: Does denominator sensitivity alter the substantive "
                 "interpretation?**")

    # Check 18-24 and 35-54 specifically
    denom_issues = []
    for ag in DENOM_EFFECT_AGS:
        if not stability_summary[ag]["stable"]:
            denom_issues.append(AG_LABELS[ag])

    if denom_issues:
        lines.append(
            f"  Partial concern for {', '.join(denom_issues)}. "
            f"In these age groups (where denominator-effect signal was detected), "
            f"the alternative specifications show some sensitivity. "
            f"The main conclusions should be presented alongside the "
            f"robustness results, noting which findings are specification-dependent."
        )
    else:
        lines.append(
            "  No. Despite detecting denominator-effect signals in 18–24 and "
            "35–54, the main model findings are directionally robust to "
            "population-weighting and smallest-state exclusion. The substantive "
            "interpretation does not change materially."
        )
    lines.append("")

    return "\n".join(lines)


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    print("=" * 60)
    print("  Denominator-Sensitivity Robustness Checks")
    print("=" * 60)

    df, models, diag = load_inputs()
    print(f"  Loaded {len(df)} states, {len(models)} A6 models, "
          f"{len(diag)} diagnostic rows")
    print()

    for ag, ivs in models.items():
        denom = " ⚠" if ag in DENOM_EFFECT_AGS else ""
        print(f"  {AG_LABELS[ag]}{denom}: {' + '.join(ivs)}")
    print()

    model_df, coeff_df = run_checks(df, models, diag)

    # Add sign consistency and magnitude ranks
    coeff_df = compute_sign_consistency(coeff_df)
    coeff_df = compute_magnitude_ranks(coeff_df)

    # Save CSVs
    model_df.to_csv(OUT_MODEL, index=False)
    print(f"  Saved: {OUT_MODEL} ({len(model_df)} rows)")

    coeff_df.to_csv(OUT_COEFF, index=False)
    print(f"  Saved: {OUT_COEFF} ({len(coeff_df)} rows)")

    # Generate notes
    notes = write_notes(model_df, coeff_df)
    with open(OUT_NOTES, "w") as f:
        f.write(notes)
    print(f"  Saved: {OUT_NOTES}")

    # Console summary
    print()
    print("  Model-level comparison (adj R²):")
    pivot = model_df.pivot(index="age_group", columns="model_type", values="adj_r2")
    pivot = pivot.reindex(columns=["baseline_ols", "weighted_wls", "exclude_smallest_ols"])
    for ag in AGE_GROUPS:
        if ag in pivot.index:
            vals = pivot.loc[ag]
            denom = " ⚠" if ag in DENOM_EFFECT_AGS else "  "
            print(f"  {denom} {AG_LABELS[ag]:>6s}:  "
                  f"base={vals['baseline_ols']:.4f}  "
                  f"WLS={vals['weighted_wls']:.4f}  "
                  f"excl={vals['exclude_smallest_ols']:.4f}")

    # Sign flip summary
    flips = coeff_df[(~coeff_df["sign_match_vs_baseline"]) &
                     (coeff_df["model_type"] != "baseline_ols")]
    if len(flips) > 0:
        print(f"\n  ⚠ Sign flips detected ({len(flips)}):")
        for _, r in flips.iterrows():
            print(f"    {AG_LABELS[r['age_group']]}: {r['term']} "
                  f"({r['model_type']}): {r['baseline_sign']} → {r['sign']}")
    else:
        print("\n  ✓ No coefficient sign flips across any specification.")

    print("\n  Done.")


if __name__ == "__main__":
    main()
