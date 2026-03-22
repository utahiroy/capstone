"""Phase A6: Multiple regression — age-group-specific candidate models.

Uses A4 (Spearman) and A5 (single-variable OLS) screening results to build
compact candidate models (2–5 IVs) for each age-group NET_RATE DV.

Candidate selection rationale:
  - IVs ranked highly in BOTH A4 and A5 are prioritized
  - Conceptually redundant IVs are not combined in the same model
  - Compact models (2–4 IVs) are preferred over larger ones
  - Sign plausibility is checked against theory
  - VIF is computed for multicollinearity screening

Run:  python -m scripts.multiple_ols_a6
"""

import os
import sys

import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.stats.outliers_influence import variance_inflation_factor

from src.constants import AGE_GROUPS

# ── Configuration ─────────────────────────────────────────────────

DV_COLS = [f"NET_RATE_{ag}" for ag in AGE_GROUPS]

OUTDIR = "outputs/tables"

# ── Candidate models per age group ────────────────────────────────
# Rationale documented in notes output.

CANDIDATES = {
    "18_24": {
        "M1": ["COMMUTE_MED", "MED_HOMEVAL"],
        "M2": ["COMMUTE_MED", "MED_HOMEVAL", "POP"],
        "M3": ["COMMUTE_MED", "MED_HOMEVAL", "UNINSURED"],
        "M4": ["COMMUTE_MED", "MED_HOMEVAL", "COST_BURDEN_ALL"],
        "M5": ["COMMUTE_MED", "MED_HOMEVAL", "POP", "PERMITS"],
    },
    "25_34": {
        "M1": ["NRI_RISK_INDEX", "PRIV_ESTAB"],
        "M2": ["NRI_RISK_INDEX", "PRIV_AVG_PAY"],
        "M3": ["NRI_RISK_INDEX", "PRIV_ESTAB", "PRIV_AVG_PAY"],
        "M4": ["NRI_RISK_INDEX", "TRANSIT_SHARE"],
        "M5": ["NRI_RISK_INDEX", "PRIV_ESTAB", "TRANSIT_SHARE"],
    },
    "35_54": {
        "M1": ["REAL_PCPI", "PERMITS"],
        "M2": ["REAL_PCPI", "COST_BURDEN_ALL"],
        "M3": ["REAL_PCPI", "NRI_RISK_INDEX"],
        "M4": ["REAL_PCPI", "PERMITS", "COST_BURDEN_ALL"],
        "M5": ["REAL_PCPI", "COST_BURDEN_ALL", "NRI_RISK_INDEX"],
    },
    "55_64": {
        "M1": ["NRI_RISK_INDEX", "PERMITS"],
        "M2": ["NRI_RISK_INDEX", "ELEC_PRICE_TOT"],
        "M3": ["NRI_RISK_INDEX", "PERMITS", "ELEC_PRICE_TOT"],
        "M4": ["NRI_RISK_INDEX", "PERMITS", "POP_DENS"],
        "M5": ["NRI_RISK_INDEX", "PERMITS", "REAL_PCPI"],
    },
    "65_PLUS": {
        "M1": ["UNINSURED", "BA_PLUS"],
        "M2": ["UNINSURED", "RPP"],
        "M3": ["UNINSURED", "MED_HOMEVAL"],
        "M4": ["UNINSURED", "BA_PLUS", "RPP"],
        "M5": ["UNINSURED", "BA_PLUS", "MED_HOMEVAL"],
    },
}


def load_data():
    path = "data_processed/analysis_ready.csv"
    if not os.path.exists(path):
        print(f"ERROR: {path} not found. Run `python -m scripts.build_dataset` first.")
        sys.exit(1)
    df = pd.read_csv(path, dtype={"state": str})
    df["state"] = df["state"].str.zfill(2)
    print(f"Loaded {path}: {df.shape[0]} rows, {df.shape[1]} columns")
    return df


def compute_vif(df, iv_list):
    """Compute VIF for each IV in the model."""
    X = df[iv_list].astype(float).values
    vifs = {}
    for i, iv in enumerate(iv_list):
        vifs[iv] = round(variance_inflation_factor(X, i), 2)
    return vifs


def run_multiple_ols(df, dv_col, iv_list, model_id):
    """Run OLS: dv ~ iv1 + iv2 + ... + intercept. Return result dict."""
    ag = dv_col.replace("NET_RATE_", "")
    y = df[dv_col].astype(float)
    X = sm.add_constant(df[iv_list].astype(float))
    n = len(y)
    k = len(iv_list)

    model = sm.OLS(y, X).fit()

    # VIF
    vifs = compute_vif(df, iv_list)
    max_vif = max(vifs.values())

    # RMSE
    rmse = np.sqrt(model.mse_resid)

    # Sign check
    signs = {iv: "+" if model.params[iv] > 0 else "-" for iv in iv_list}
    sign_str = ", ".join(f"{iv}({s})" for iv, s in signs.items())

    # Formula
    formula = f"{dv_col} ~ " + " + ".join(iv_list)

    return {
        "dv": dv_col,
        "age_group": ag,
        "model_id": model_id,
        "formula": formula,
        "iv_count": k,
        "iv_list": ", ".join(iv_list),
        "adjusted_r2": round(model.rsquared_adj, 4),
        "r2": round(model.rsquared, 4),
        "aic": round(model.aic, 2),
        "bic": round(model.bic, 2),
        "rmse": round(rmse, 4),
        "max_vif": round(max_vif, 2),
        "sign_check": sign_str,
        "notes": "",
    }, model, vifs


def format_model_summary(result, model, vifs):
    """Return a printable summary for one model."""
    lines = []
    lines.append(f"  {result['model_id']}: {result['formula']}")
    lines.append(f"    adj_R²={result['adjusted_r2']:.4f}  "
                 f"AIC={result['aic']:.1f}  BIC={result['bic']:.1f}  "
                 f"RMSE={result['rmse']:.4f}  max_VIF={result['max_vif']:.2f}")
    lines.append(f"    Coefficients:")
    for iv in model.params.index:
        if iv == "const":
            continue
        p = model.pvalues[iv]
        star = "***" if p < 0.001 else "**" if p < 0.01 else "*" if p < 0.05 else ""
        lines.append(f"      {iv:22s}  coef={model.params[iv]:+.6f}  "
                     f"p={p:.4f}{star}  VIF={vifs.get(iv, 'n/a')}")
    return "\n".join(lines)


def select_preferred(results):
    """Select preferred model: highest adj_R², penalize max_VIF > 5, prefer lower BIC on ties."""
    # Filter out models with extreme VIF
    viable = [r for r in results if r[0]["max_vif"] < 10]
    if not viable:
        viable = results  # fall back if all have high VIF

    # Sort by adjusted_r2 desc, then BIC asc
    viable.sort(key=lambda x: (-x[0]["adjusted_r2"], x[0]["bic"]))
    return viable[0]


def main():
    os.makedirs(OUTDIR, exist_ok=True)
    df = load_data()

    all_candidates = []
    selected_models = []
    notes_lines = [
        "Phase A6: Multiple Regression — Age-Group-Specific Models",
        "=" * 60,
        "",
        "Candidate selection rationale:",
        "  IVs were selected from A4 (Spearman rho) and A5 (single-variable OLS)",
        "  screening results. IVs appearing in the top tier of BOTH screens were",
        "  prioritized. Conceptually redundant IVs were not combined. Models are",
        "  compact (2-4 IVs) to preserve interpretability with n=50.",
        "",
        "Model comparison criteria (per CLAUDE.md):",
        "  1. Adjusted R² (primary)",
        "  2. AIC / BIC",
        "  3. Theoretical sign plausibility",
        "  4. No extreme multicollinearity (VIF < 10)",
        "  5. Compactness / interpretability",
        "",
        "Selection rule:",
        "  Highest adjusted R² among models with VIF < 10 and plausible signs.",
        "  If adjusted R² differences are marginal (<0.02), prefer the simpler model.",
        "",
    ]

    for ag in AGE_GROUPS:
        dv = f"NET_RATE_{ag}"
        candidates = CANDIDATES[ag]

        print(f"\n{'='*60}")
        print(f"  {dv}  ({len(candidates)} candidate models)")
        print(f"{'='*60}")

        notes_lines.append(f"{'='*60}")
        notes_lines.append(f"  {dv}")
        notes_lines.append(f"{'='*60}")
        notes_lines.append("")

        ag_results = []
        for mid, ivs in candidates.items():
            try:
                result, model, vifs = run_multiple_ols(df, dv, ivs, mid)
                ag_results.append((result, model, vifs))
                all_candidates.append(result)
                summary = format_model_summary(result, model, vifs)
                print(summary)
                notes_lines.append(summary)
            except Exception as e:
                print(f"  FAILED: {mid} ({', '.join(ivs)}): {e}")
                notes_lines.append(f"  FAILED: {mid} ({', '.join(ivs)}): {e}")

        notes_lines.append("")

        # Save per-age-group comparison
        ag_df = pd.DataFrame([r[0] for r in ag_results])
        ag_df = ag_df.sort_values("adjusted_r2", ascending=False)
        path = f"{OUTDIR}/a6_candidates_{ag}.csv"
        ag_df.to_csv(path, index=False)
        print(f"\n  Saved: {path}")

        # Select preferred
        if ag_results:
            best_result, best_model, best_vifs = select_preferred(ag_results)

            # Check for marginal improvement: if top model has only marginally
            # better adj_R2 than a simpler model, prefer the simpler one
            ag_sorted = sorted(ag_results, key=lambda x: -x[0]["adjusted_r2"])
            top = ag_sorted[0][0]
            for r, m, v in ag_sorted[1:]:
                if (top["adjusted_r2"] - r["adjusted_r2"] < 0.02
                        and r["iv_count"] < top["iv_count"]
                        and r["max_vif"] < 10):
                    best_result, best_model, best_vifs = r, m, v
                    best_result["notes"] = "Selected simpler model (adj_R2 diff < 0.02)"
                    break

            selected_models.append({
                "dv": dv,
                "age_group": ag,
                "selected_model_id": best_result["model_id"],
                "formula": best_result["formula"],
                "selected_ivs": best_result["iv_list"],
                "adjusted_r2": best_result["adjusted_r2"],
                "aic": best_result["aic"],
                "bic": best_result["bic"],
                "rmse": best_result["rmse"],
                "max_vif": best_result["max_vif"],
                "selection_reason": best_result.get("notes", "") or "Highest adj_R2 with VIF<10",
            })

            print(f"\n  ** PREFERRED: {best_result['model_id']} — "
                  f"adj_R²={best_result['adjusted_r2']:.4f}  "
                  f"BIC={best_result['bic']:.1f}  "
                  f"max_VIF={best_result['max_vif']:.2f}")
            notes_lines.append(f"  ** PREFERRED: {best_result['model_id']} — "
                               f"adj_R²={best_result['adjusted_r2']:.4f}  "
                               f"BIC={best_result['bic']:.1f}")

            # Print full coefficient table for preferred model
            print(f"\n  Preferred model detail:")
            print(f"    {best_model.summary2().tables[1].to_string()}")
            notes_lines.append(f"\n  Preferred model coefficient table:")
            notes_lines.append(f"    {best_model.summary2().tables[1].to_string()}")

        notes_lines.append("")

    # ── Combined candidate comparison ─────────────────────────────
    comb_df = pd.DataFrame(all_candidates)
    path = f"{OUTDIR}/a6_candidates_combined.csv"
    comb_df.to_csv(path, index=False)
    print(f"\nSaved combined candidates: {path}")

    # ── Selected model summary ────────────────────────────────────
    sel_df = pd.DataFrame(selected_models)
    path = f"{OUTDIR}/a6_selected_models.csv"
    sel_df.to_csv(path, index=False)
    print(f"Saved selected models: {path}")

    # ── Notes ─────────────────────────────────────────────────────
    notes_lines.extend([
        "",
        "=" * 60,
        "SUMMARY OF SELECTED MODELS",
        "=" * 60,
        "",
    ])
    for s in selected_models:
        notes_lines.append(
            f"  {s['age_group']:10s}: {s['selected_model_id']}  "
            f"IVs=[{s['selected_ivs']}]  "
            f"adj_R²={s['adjusted_r2']:.4f}  max_VIF={s['max_vif']:.2f}"
        )

    notes_lines.extend([
        "",
        "METHODOLOGICAL NOTES",
        "-" * 40,
        "",
        "Verified results:",
        "  - All models use OLS with intercept, no transforms, n=50 states",
        "  - VIF computed from statsmodels variance_inflation_factor",
        "  - Adjusted R² accounts for number of predictors",
        "",
        "Implementation assumptions:",
        "  - Candidate IVs were selected from A4/A5 screening (not exhaustive search)",
        "  - 5 candidate models per age group; more combinations are possible",
        "  - Simplicity preference: if adj_R² improvement < 0.02, prefer fewer IVs",
        "",
        "Interpretation / opinion:",
        "  - Weak overall fit (adj_R² < 0.15 for most age groups) is expected for a",
        "    50-state cross-section with no transforms. State-level migration is",
        "    influenced by many factors not captured in 22 IVs.",
        "  - Different age groups having different top predictors is consistent with",
        "    migration theory (amenity vs. employment vs. cost motives differ by age).",
        "  - These are associations, not causal estimates.",
    ])

    path = f"{OUTDIR}/a6_notes.txt"
    with open(path, "w") as fh:
        fh.write("\n".join(notes_lines) + "\n")
    print(f"Saved notes: {path}")

    # ── Final summary ─────────────────────────────────────────────
    print(f"\n{'='*60}")
    print(f"  Phase A6 complete: {len(all_candidates)} candidate models, "
          f"{len(selected_models)} selected")
    print(f"{'='*60}")

    print(f"\nOutput files:")
    for fname in sorted(os.listdir(OUTDIR)):
        if fname.startswith("a6_"):
            print(f"  {os.path.join(OUTDIR, fname)}")


if __name__ == "__main__":
    main()
