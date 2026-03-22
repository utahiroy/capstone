"""Phase A5: Single-variable OLS for each DV × IV combination.

For each of the 5 age-group NET_RATE DVs, regress on each of the 22 IVs
individually (with intercept). No transforms, no variable selection by p-value.

Produces:
  - Per-age-group CSVs (5 files)
  - Combined long-format CSV
  - Ranking matrix CSV (adjusted R² by IV × age group)
  - Short notes file

Run:  python -m scripts.single_ols_a5
"""

import os
import sys

import numpy as np
import pandas as pd
import statsmodels.api as sm

from src.constants import AGE_GROUPS

# ── Configuration ─────────────────────────────────────────────────

DV_COLS = [f"NET_RATE_{ag}" for ag in AGE_GROUPS]

IV_COLS = [
    "POP", "LAND_AREA", "POP_DENS",
    "GDP", "RPP", "REAL_PCPI",
    "UNEMP", "PRIV_EMP", "PRIV_ESTAB", "PRIV_AVG_PAY",
    "PERMITS", "MED_RENT", "MED_HOMEVAL",
    "COST_BURDEN_ALL", "VACANCY_RATE",
    "COMMUTE_MED", "TRANSIT_SHARE", "BA_PLUS",
    "UNINSURED", "ELEC_PRICE_TOT",
    "CRIME_VIOLENT_RATE", "NRI_RISK_INDEX",
]

OUTDIR = "outputs/tables"


def load_data():
    path = "data_processed/analysis_ready.csv"
    if not os.path.exists(path):
        print(f"ERROR: {path} not found. Run `python -m scripts.build_dataset` first.")
        sys.exit(1)
    df = pd.read_csv(path, dtype={"state": str})
    df["state"] = df["state"].str.zfill(2)
    print(f"Loaded {path}: {df.shape[0]} rows, {df.shape[1]} columns")
    return df


def run_single_ols(df, dv_col, iv_col):
    """Run OLS: dv ~ iv + intercept. Return result dict."""
    y = df[dv_col].astype(float)
    x = sm.add_constant(df[iv_col].astype(float))
    n = len(y)

    model = sm.OLS(y, x).fit()

    return {
        "dv": dv_col,
        "age_group": dv_col.replace("NET_RATE_", ""),
        "iv": iv_col,
        "coef": round(model.params[iv_col], 6),
        "coef_sign": "+" if model.params[iv_col] > 0 else "-",
        "intercept": round(model.params["const"], 4),
        "r2": round(model.rsquared, 4),
        "adjusted_r2": round(model.rsquared_adj, 4),
        "aic": round(model.aic, 2),
        "bic": round(model.bic, 2),
        "p_value": round(model.pvalues[iv_col], 6),
        "n": n,
    }


def main():
    os.makedirs(OUTDIR, exist_ok=True)
    df = load_data()

    # Validate columns
    missing_dv = [c for c in DV_COLS if c not in df.columns]
    missing_iv = [c for c in IV_COLS if c not in df.columns]
    if missing_dv or missing_iv:
        print(f"ERROR: Missing DVs: {missing_dv}, Missing IVs: {missing_iv}")
        sys.exit(1)

    all_results = []
    failed = []

    for dv in DV_COLS:
        ag = dv.replace("NET_RATE_", "")
        ag_results = []
        print(f"\n{'='*60}")
        print(f"  {dv}  ({len(IV_COLS)} IVs)")
        print(f"{'='*60}")

        for iv in IV_COLS:
            try:
                result = run_single_ols(df, dv, iv)
                ag_results.append(result)
                all_results.append(result)
            except Exception as e:
                print(f"  FAILED: {dv} ~ {iv}: {e}")
                failed.append({"dv": dv, "iv": iv, "error": str(e)})

        # Sort by adjusted_r2 descending
        ag_df = pd.DataFrame(ag_results).sort_values("adjusted_r2", ascending=False)

        # Save per-age-group CSV
        path = f"{OUTDIR}/a5_single_ols_{ag}.csv"
        ag_df.to_csv(path, index=False)
        print(f"  Saved: {path}")

        # Print top 5
        print(f"\n  Top 5 IVs by adjusted R²:")
        for i, (_, row) in enumerate(ag_df.head(5).iterrows(), 1):
            print(f"    {i}. {row['iv']:22s}  adj_R²={row['adjusted_r2']:.4f}  "
                  f"coef={row['coef']:+.6f}  p={row['p_value']:.4f}")

    # ── Combined long-format CSV ──────────────────────────────────
    combined = pd.DataFrame(all_results)
    path = f"{OUTDIR}/a5_single_ols_combined.csv"
    combined.to_csv(path, index=False)
    print(f"\nSaved combined: {path}")

    # ── Ranking matrix: adjusted R² by IV × age group ─────────────
    pivot = combined.pivot(index="iv", columns="age_group", values="adjusted_r2")
    # Reorder columns to match age group order
    pivot = pivot[[ag.replace("NET_RATE_", "") for ag in DV_COLS if ag.replace("NET_RATE_", "") in pivot.columns]]
    # Add mean across age groups
    pivot["mean_adj_r2"] = pivot.mean(axis=1)
    pivot = pivot.sort_values("mean_adj_r2", ascending=False)
    path = f"{OUTDIR}/a5_ranking_matrix.csv"
    pivot.to_csv(path)
    print(f"Saved ranking matrix: {path}")

    # ── Notes ─────────────────────────────────────────────────────
    notes_lines = [
        "Phase A5: Single-Variable OLS Results",
        "=" * 50,
        "",
        f"Total models: {len(all_results)}",
        f"Failed models: {len(failed)}",
        f"DVs: {len(DV_COLS)} (NET_RATE by age group)",
        f"IVs: {len(IV_COLS)}",
        f"Sample: n={df.shape[0]} states",
        "",
        "Top IV by adjusted R² for each age group:",
    ]

    for dv in DV_COLS:
        ag = dv.replace("NET_RATE_", "")
        ag_rows = [r for r in all_results if r["dv"] == dv]
        if ag_rows:
            best = max(ag_rows, key=lambda r: r["adjusted_r2"])
            notes_lines.append(
                f"  {ag:10s}: {best['iv']:22s}  adj_R²={best['adjusted_r2']:.4f}  "
                f"coef_sign={best['coef_sign']}  p={best['p_value']:.4f}"
            )

    notes_lines.extend([
        "",
        "Notes:",
        "- All models: OLS with intercept, no transforms",
        "- Comparison metric: adjusted R² (primary), AIC/BIC (secondary)",
        "- Negative adjusted R² means IV explains less variance than a null model",
        "- These are bivariate associations, not causal estimates",
    ])

    if failed:
        notes_lines.extend(["", "Failed models:"])
        for f in failed:
            notes_lines.append(f"  {f['dv']} ~ {f['iv']}: {f['error']}")

    path = f"{OUTDIR}/a5_notes.txt"
    with open(path, "w") as fh:
        fh.write("\n".join(notes_lines) + "\n")
    print(f"Saved notes: {path}")

    # ── Summary ───────────────────────────────────────────────────
    print(f"\n{'='*60}")
    print(f"  Phase A5 complete: {len(all_results)} models, {len(failed)} failed")
    print(f"{'='*60}")

    print(f"\nOutput files:")
    for fname in sorted(os.listdir(OUTDIR)):
        if fname.startswith("a5_"):
            print(f"  {os.path.join(OUTDIR, fname)}")


if __name__ == "__main__":
    main()
