#!/usr/bin/env python3
"""
Distribution-Share Analysis Pipeline
=====================================
Engineers IN_SHARE / OUT_SHARE DVs for 5 age groups + all-ages,
then runs validation, descriptive statistics, ranking, Spearman/Kendall
correlation screening, and single-variable OLS against the 22-IV framework.

Usage:
    python -m scripts.distribution_shares

Outputs:
    data_processed/analysis_ready_distribution_shares.csv
    outputs/tables/distribution_shares/share_validation.csv
    outputs/tables/distribution_shares/share_summary_stats.csv
    outputs/tables/distribution_shares/share_rankings_in.csv
    outputs/tables/distribution_shares/share_rankings_out.csv
    outputs/tables/distribution_shares/a4_spearman_kendall_shares.csv
    outputs/tables/distribution_shares/a5_single_ols_shares.csv
"""

from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats
import statsmodels.api as sm

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
PROJECT = Path(__file__).resolve().parent.parent
DATA_IN = PROJECT / "data_processed" / "analysis_ready.csv"
DATA_OUT = PROJECT / "data_processed" / "analysis_ready_distribution_shares.csv"
TABLE_DIR = PROJECT / "outputs" / "tables" / "distribution_shares"

AGE_GROUPS = ["18_24", "25_34", "35_54", "55_64", "65_PLUS"]
AGE_LABELS = {
    "18_24": "18-24", "25_34": "25-34", "35_54": "35-54",
    "55_64": "55-64", "65_PLUS": "65+",
}

IVS = [
    "POP", "LAND_AREA", "POP_DENS", "GDP", "RPP", "REAL_PCPI",
    "UNEMP", "PRIV_EMP", "PRIV_ESTAB", "PRIV_AVG_PAY", "PERMITS",
    "MED_RENT", "MED_HOMEVAL", "COST_BURDEN_ALL", "VACANCY_RATE",
    "COMMUTE_MED", "TRANSIT_SHARE", "BA_PLUS", "UNINSURED",
    "ELEC_PRICE_TOT", "CRIME_VIOLENT_RATE", "NRI_RISK_INDEX",
]


def load_data() -> pd.DataFrame:
    df = pd.read_csv(DATA_IN, dtype={"state": str})
    df["state"] = df["state"].str.zfill(2)
    return df


# =========================================================================
# Phase 1: Engineer share DVs
# =========================================================================
def engineer_shares(df: pd.DataFrame) -> pd.DataFrame:
    """Create 12 share variables: IN_SHARE and OUT_SHARE for 5 age groups + all-ages."""

    # Age-group shares
    for ag in AGE_GROUPS:
        in_col = f"IN_COUNT_{ag}"
        out_col = f"OUT_COUNT_{ag}"
        in_total = df[in_col].sum()
        out_total = df[out_col].sum()
        df[f"IN_SHARE_{ag}"] = df[in_col] / in_total
        df[f"OUT_SHARE_{ag}"] = df[out_col] / out_total

    # All-ages: derived by summing the 5 fixed age groups
    in_cols = [f"IN_COUNT_{ag}" for ag in AGE_GROUPS]
    out_cols = [f"OUT_COUNT_{ag}" for ag in AGE_GROUPS]
    df["IN_COUNT_ALL_AGES"] = df[in_cols].sum(axis=1)
    df["OUT_COUNT_ALL_AGES"] = df[out_cols].sum(axis=1)
    in_total_all = df["IN_COUNT_ALL_AGES"].sum()
    out_total_all = df["OUT_COUNT_ALL_AGES"].sum()
    df["IN_SHARE_ALL_AGES"] = df["IN_COUNT_ALL_AGES"] / in_total_all
    df["OUT_SHARE_ALL_AGES"] = df["OUT_COUNT_ALL_AGES"] / out_total_all

    # Percentage versions (for maps / readability)
    share_cols = (
        [f"IN_SHARE_{ag}" for ag in AGE_GROUPS]
        + [f"OUT_SHARE_{ag}" for ag in AGE_GROUPS]
        + ["IN_SHARE_ALL_AGES", "OUT_SHARE_ALL_AGES"]
    )
    for c in share_cols:
        df[c.replace("SHARE", "SHARE_PCT")] = df[c] * 100

    return df


# =========================================================================
# Phase 2: Validation
# =========================================================================
def validate_shares(df: pd.DataFrame) -> pd.DataFrame:
    """Validate the 12 share families and return a validation table."""
    results = []
    share_families = (
        [(f"IN_SHARE_{ag}", f"IN ({AGE_LABELS[ag]})") for ag in AGE_GROUPS]
        + [(f"OUT_SHARE_{ag}", f"OUT ({AGE_LABELS[ag]})") for ag in AGE_GROUPS]
        + [("IN_SHARE_ALL_AGES", "IN (All Ages)"),
           ("OUT_SHARE_ALL_AGES", "OUT (All Ages)")]
    )
    for col, label in share_families:
        s = df[col]
        results.append({
            "variable": col,
            "label": label,
            "n": int(s.notna().sum()),
            "n_missing": int(s.isna().sum()),
            "sum": round(s.sum(), 6),
            "sum_pct": round(s.sum() * 100, 4),
            "min": round(s.min(), 6),
            "max": round(s.max(), 6),
            "mean": round(s.mean(), 6),
            "std": round(s.std(), 6),
            "passes": "OK" if (s.notna().sum() == 50 and abs(s.sum() - 1.0) < 1e-6) else "CHECK",
        })
    vdf = pd.DataFrame(results)
    return vdf


# =========================================================================
# Phase 4: Descriptive statistics + rankings
# =========================================================================
def summary_stats(df: pd.DataFrame, share_cols: list[str]) -> pd.DataFrame:
    """Summary statistics for share variables."""
    records = []
    for col in share_cols:
        s = df[col]
        records.append({
            "variable": col,
            "mean": s.mean(),
            "std": s.std(),
            "min": s.min(),
            "p25": s.quantile(0.25),
            "median": s.median(),
            "p75": s.quantile(0.75),
            "max": s.max(),
            "cv": s.std() / s.mean() if s.mean() != 0 else np.nan,
        })
    return pd.DataFrame(records).round(6)


def build_rankings(df: pd.DataFrame, share_cols: list[str], direction: str) -> pd.DataFrame:
    """Build top-5 / bottom-5 ranking table for a set of share variables."""
    rows = []
    for col in share_cols:
        sorted_df = df.sort_values(col, ascending=False).reset_index(drop=True)
        for rank_pos in range(5):
            r = sorted_df.iloc[rank_pos]
            rows.append({
                "variable": col,
                "rank_type": "top",
                "rank": rank_pos + 1,
                "state_name": r["state_name"],
                "abbrev": r.get("abbrev", ""),
                "share": round(r[col], 6),
                "share_pct": round(r[col] * 100, 2),
            })
        for rank_pos in range(5):
            r = sorted_df.iloc[-(rank_pos + 1)]
            rows.append({
                "variable": col,
                "rank_type": "bottom",
                "rank": 50 - rank_pos,
                "state_name": r["state_name"],
                "abbrev": r.get("abbrev", ""),
                "share": round(r[col], 6),
                "share_pct": round(r[col] * 100, 2),
            })
    return pd.DataFrame(rows)


# =========================================================================
# Phase 5: Statistical screening
# =========================================================================
def spearman_kendall_screen(
    df: pd.DataFrame, dvs: list[str], ivs: list[str]
) -> pd.DataFrame:
    """Spearman and Kendall rank correlations for each DV × IV pair."""
    records = []
    for dv in dvs:
        y = df[dv]
        for iv in ivs:
            x = df[iv]
            mask = x.notna() & y.notna()
            if mask.sum() < 10:
                continue
            sp_rho, sp_p = stats.spearmanr(x[mask], y[mask])
            kt_tau, kt_p = stats.kendalltau(x[mask], y[mask])
            records.append({
                "dv": dv,
                "iv": iv,
                "n": int(mask.sum()),
                "spearman_rho": round(sp_rho, 4),
                "spearman_p": round(sp_p, 6),
                "kendall_tau": round(kt_tau, 4),
                "kendall_p": round(kt_p, 6),
                "abs_spearman_rho": round(abs(sp_rho), 4),
            })
    result = pd.DataFrame(records)
    result = result.sort_values(["dv", "abs_spearman_rho"], ascending=[True, False])
    return result


def single_ols_screen(
    df: pd.DataFrame, dvs: list[str], ivs: list[str]
) -> pd.DataFrame:
    """Single-variable OLS for each DV × IV pair."""
    records = []
    for dv in dvs:
        y = df[dv]
        for iv in ivs:
            x = df[iv]
            mask = x.notna() & y.notna()
            n = int(mask.sum())
            if n < 10:
                continue
            X = sm.add_constant(x[mask])
            try:
                model = sm.OLS(y[mask], X).fit()
            except Exception:
                continue
            records.append({
                "dv": dv,
                "iv": iv,
                "n": n,
                "coef": round(model.params.iloc[1], 8),
                "std_err": round(model.bse.iloc[1], 8),
                "t_value": round(model.tvalues.iloc[1], 4),
                "p_value": round(model.pvalues.iloc[1], 6),
                "r_squared": round(model.rsquared, 4),
                "adj_r_squared": round(model.rsquared_adj, 4),
                "f_stat": round(model.fvalue, 4),
                "f_p_value": round(model.f_pvalue, 6),
                "sign": "+" if model.params.iloc[1] > 0 else "-",
            })
    result = pd.DataFrame(records)
    result = result.sort_values(["dv", "adj_r_squared"], ascending=[True, False])
    return result


# =========================================================================
# Main
# =========================================================================
def main():
    print("=" * 70)
    print("Distribution-Share Analysis Pipeline")
    print("=" * 70)

    # Load
    df = load_data()
    print(f"\nLoaded {len(df)} states from {DATA_IN.name}")

    # Add abbreviations for rankings
    FIPS_TO_ABBREV = {
        "01": "AL", "02": "AK", "04": "AZ", "05": "AR", "06": "CA",
        "08": "CO", "09": "CT", "10": "DE", "12": "FL", "13": "GA",
        "15": "HI", "16": "ID", "17": "IL", "18": "IN", "19": "IA",
        "20": "KS", "21": "KY", "22": "LA", "23": "ME", "24": "MD",
        "25": "MA", "26": "MI", "27": "MN", "28": "MS", "29": "MO",
        "30": "MT", "31": "NE", "32": "NV", "33": "NH", "34": "NJ",
        "35": "NM", "36": "NY", "37": "NC", "38": "ND", "39": "OH",
        "40": "OK", "41": "OR", "42": "PA", "44": "RI", "45": "SC",
        "46": "SD", "47": "TN", "48": "TX", "49": "UT", "50": "VT",
        "51": "VA", "53": "WA", "54": "WV", "55": "WI", "56": "WY",
    }
    df["abbrev"] = df["state"].map(FIPS_TO_ABBREV)

    # --- Phase 1: Engineer shares ---
    print("\n--- Phase 1: Engineering share DVs ---")
    df = engineer_shares(df)
    share_cols = (
        [f"IN_SHARE_{ag}" for ag in AGE_GROUPS]
        + [f"OUT_SHARE_{ag}" for ag in AGE_GROUPS]
        + ["IN_SHARE_ALL_AGES", "OUT_SHARE_ALL_AGES"]
    )
    print(f"  Created {len(share_cols)} share variables + 12 percent versions")

    # Save processed file
    df.to_csv(DATA_OUT, index=False)
    print(f"  Saved: {DATA_OUT.relative_to(PROJECT)}")

    # --- Phase 2: Validation ---
    print("\n--- Phase 2: Validation ---")
    vdf = validate_shares(df)
    vdf.to_csv(TABLE_DIR / "share_validation.csv", index=False)
    print(vdf[["variable", "n", "sum", "min", "max", "passes"]].to_string(index=False))
    n_pass = (vdf["passes"] == "OK").sum()
    print(f"\n  {n_pass}/{len(vdf)} share families pass validation")

    # --- Phase 4: Descriptive stats ---
    print("\n--- Phase 4: Descriptive statistics ---")
    stats_df = summary_stats(df, share_cols)
    stats_df.to_csv(TABLE_DIR / "share_summary_stats.csv", index=False)
    print(stats_df.to_string(index=False))

    # Rankings
    print("\n--- Phase 4: Rankings ---")
    in_share_cols = [f"IN_SHARE_{ag}" for ag in AGE_GROUPS] + ["IN_SHARE_ALL_AGES"]
    out_share_cols = [f"OUT_SHARE_{ag}" for ag in AGE_GROUPS] + ["OUT_SHARE_ALL_AGES"]

    rank_in = build_rankings(df, in_share_cols, "in")
    rank_in.to_csv(TABLE_DIR / "share_rankings_in.csv", index=False)
    print(f"  In-share rankings: {len(rank_in)} rows")

    rank_out = build_rankings(df, out_share_cols, "out")
    rank_out.to_csv(TABLE_DIR / "share_rankings_out.csv", index=False)
    print(f"  Out-share rankings: {len(rank_out)} rows")

    # Print top-3 for each share family for quick inspection
    print("\n  === Top 3 by IN_SHARE (each age group) ===")
    for col in in_share_cols:
        top3 = rank_in[(rank_in["variable"] == col) & (rank_in["rank_type"] == "top")].head(3)
        states = ", ".join(f"{r['abbrev']}({r['share_pct']:.1f}%)" for _, r in top3.iterrows())
        print(f"    {col}: {states}")

    print("\n  === Top 3 by OUT_SHARE (each age group) ===")
    for col in out_share_cols:
        top3 = rank_out[(rank_out["variable"] == col) & (rank_out["rank_type"] == "top")].head(3)
        states = ", ".join(f"{r['abbrev']}({r['share_pct']:.1f}%)" for _, r in top3.iterrows())
        print(f"    {col}: {states}")

    # --- Phase 5: Statistical screening ---
    print("\n--- Phase 5: Spearman & Kendall screening ---")
    # Filter to IVs that actually exist in the data
    available_ivs = [iv for iv in IVS if iv in df.columns]
    print(f"  IVs available: {len(available_ivs)} of {len(IVS)}")

    corr_df = spearman_kendall_screen(df, share_cols, available_ivs)
    corr_df.to_csv(TABLE_DIR / "a4_spearman_kendall_shares.csv", index=False)
    print(f"  Correlation pairs: {len(corr_df)}")

    # Show top-3 correlates for each DV
    print("\n  === Top 3 Spearman correlates per DV ===")
    for dv in share_cols:
        dv_corr = corr_df[corr_df["dv"] == dv].head(3)
        if dv_corr.empty:
            continue
        top = ", ".join(
            f"{r['iv']}(rho={r['spearman_rho']:+.3f}, p={r['spearman_p']:.4f})"
            for _, r in dv_corr.iterrows()
        )
        print(f"    {dv}: {top}")

    print("\n--- Phase 5: Single-variable OLS screening ---")
    ols_df = single_ols_screen(df, share_cols, available_ivs)
    ols_df.to_csv(TABLE_DIR / "a5_single_ols_shares.csv", index=False)
    print(f"  OLS regressions: {len(ols_df)}")

    # Show top-3 by adj R² for each DV
    print("\n  === Top 3 by adj R-squared per DV ===")
    for dv in share_cols:
        dv_ols = ols_df[ols_df["dv"] == dv].head(3)
        if dv_ols.empty:
            continue
        top = ", ".join(
            f"{r['iv']}(adjR2={r['adj_r_squared']:.4f}, p={r['p_value']:.4f})"
            for _, r in dv_ols.iterrows()
        )
        print(f"    {dv}: {top}")

    print("\n" + "=" * 70)
    print("Pipeline complete. Output files:")
    print(f"  {DATA_OUT.relative_to(PROJECT)}")
    for f in sorted(TABLE_DIR.glob("*.csv")):
        print(f"  {f.relative_to(PROJECT)}")
    print("=" * 70)


if __name__ == "__main__":
    main()
