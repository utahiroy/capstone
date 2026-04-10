#!/usr/bin/env python3
"""
Specialization / Deviation Analysis Pipeline
=============================================
Builds on the distribution-share dataset to create:
  - REL_IN / REL_OUT  (specialization ratios vs all-ages baseline)
  - DIFF_IN / DIFF_OUT (difference from all-ages baseline)
  - SHARE_GAP          (inflow share minus outflow share)
  - Rank shifts        (age-specific rank vs all-ages rank)

Then runs validation, descriptive analysis, and statistical screening
(Spearman, Kendall, single-variable OLS) against the fixed 22-IV framework.

Usage:
    python -m scripts.specialization_analysis

Note: "all ages" = sum of 5 defined age groups (18-24 through 65+).
      Under-18 movers are excluded.
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
DATA_IN = PROJECT / "data_processed" / "analysis_ready_distribution_shares.csv"
DATA_OUT = PROJECT / "data_processed" / "analysis_ready_specialization.csv"
TABLE_DIR = PROJECT / "outputs" / "tables" / "specialization"
TABLE_DIR.mkdir(parents=True, exist_ok=True)

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


# =========================================================================
# Phase 1: Engineer specialization metrics
# =========================================================================
def engineer_specialization(df: pd.DataFrame) -> pd.DataFrame:
    """Create REL, DIFF, SHARE_GAP metrics for each age group."""
    for ag in AGE_GROUPS:
        # 1A: Specialization ratios
        df[f"REL_IN_{ag}"] = df[f"IN_SHARE_{ag}"] / df["IN_SHARE_ALL_AGES"]
        df[f"REL_OUT_{ag}"] = df[f"OUT_SHARE_{ag}"] / df["OUT_SHARE_ALL_AGES"]
        # 1B: Differences from total
        df[f"DIFF_IN_{ag}"] = df[f"IN_SHARE_{ag}"] - df["IN_SHARE_ALL_AGES"]
        df[f"DIFF_OUT_{ag}"] = df[f"OUT_SHARE_{ag}"] - df["OUT_SHARE_ALL_AGES"]
        # 1C: Inflow-outflow share gap
        df[f"SHARE_GAP_{ag}"] = df[f"IN_SHARE_{ag}"] - df[f"OUT_SHARE_{ag}"]
    return df


def compute_rank_shifts(df: pd.DataFrame) -> pd.DataFrame:
    """Compute rank shifts: age-specific rank minus all-ages rank."""
    rows = []
    for direction in ["IN", "OUT"]:
        all_col = f"{direction}_SHARE_ALL_AGES"
        df[f"_rank_all_{direction}"] = df[all_col].rank(ascending=False, method="min").astype(int)
        for ag in AGE_GROUPS:
            age_col = f"{direction}_SHARE_{ag}"
            df[f"_rank_{ag}_{direction}"] = df[age_col].rank(ascending=False, method="min").astype(int)
            for _, r in df.iterrows():
                rank_age = int(r[f"_rank_{ag}_{direction}"])
                rank_all = int(r[f"_rank_all_{direction}"])
                shift = rank_all - rank_age  # positive = moved up for this age group
                rows.append({
                    "direction": direction,
                    "age_group": ag,
                    "state": r["state"],
                    "state_name": r["state_name"],
                    "abbrev": r["abbrev"],
                    "rank_age_specific": rank_age,
                    "rank_all_ages": rank_all,
                    "rank_shift": shift,
                    "share_age": round(r[age_col], 6),
                    "share_all": round(r[all_col], 6),
                    "rel_ratio": round(r[f"REL_{direction}_{ag}"], 4),
                })
    # Clean up temp columns
    for col in list(df.columns):
        if col.startswith("_rank_"):
            df.drop(columns=[col], inplace=True)
    return pd.DataFrame(rows)


# =========================================================================
# Phase 2: Validation
# =========================================================================
def validate_specialization(df: pd.DataFrame) -> pd.DataFrame:
    """Validate all new metric families."""
    results = []
    for ag in AGE_GROUPS:
        for prefix, expected_sum, metric_type in [
            (f"REL_IN_{ag}", None, "ratio"),
            (f"REL_OUT_{ag}", None, "ratio"),
            (f"DIFF_IN_{ag}", 0.0, "difference"),
            (f"DIFF_OUT_{ag}", 0.0, "difference"),
            (f"SHARE_GAP_{ag}", None, "gap"),
        ]:
            s = df[prefix]
            actual_sum = s.sum()
            results.append({
                "variable": prefix,
                "type": metric_type,
                "n": int(s.notna().sum()),
                "n_missing": int(s.isna().sum()),
                "n_inf": int(np.isinf(s).sum()),
                "min": round(s.min(), 6),
                "max": round(s.max(), 6),
                "mean": round(s.mean(), 6),
                "std": round(s.std(), 6),
                "sum": round(actual_sum, 6),
                "expected_sum": expected_sum,
                "sum_check": (
                    "OK" if expected_sum is None
                    else ("OK" if abs(actual_sum - expected_sum) < 1e-6 else "CHECK")
                ),
                "passes": "OK" if (s.notna().sum() == 50 and np.isinf(s).sum() == 0) else "CHECK",
            })
    return pd.DataFrame(results)


# =========================================================================
# Phase 4: Descriptive analysis
# =========================================================================
def summary_stats(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    records = []
    for col in cols:
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
            "cv": s.std() / abs(s.mean()) if s.mean() != 0 else np.nan,
        })
    return pd.DataFrame(records).round(6)


def build_rankings(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    rows = []
    for col in cols:
        sorted_df = df.sort_values(col, ascending=False).reset_index(drop=True)
        for i in range(5):
            r = sorted_df.iloc[i]
            rows.append({
                "variable": col, "rank_type": "top", "rank": i + 1,
                "state_name": r["state_name"], "abbrev": r["abbrev"],
                "value": round(r[col], 6),
            })
        for i in range(5):
            r = sorted_df.iloc[-(i + 1)]
            rows.append({
                "variable": col, "rank_type": "bottom", "rank": 50 - i,
                "state_name": r["state_name"], "abbrev": r["abbrev"],
                "value": round(r[col], 6),
            })
    return pd.DataFrame(rows)


# =========================================================================
# Phase 5: Statistical screening
# =========================================================================
def spearman_kendall_screen(df, dvs, ivs):
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
                "dv": dv, "iv": iv, "n": int(mask.sum()),
                "spearman_rho": round(sp_rho, 4), "spearman_p": round(sp_p, 6),
                "kendall_tau": round(kt_tau, 4), "kendall_p": round(kt_p, 6),
                "abs_spearman_rho": round(abs(sp_rho), 4),
            })
    result = pd.DataFrame(records)
    return result.sort_values(["dv", "abs_spearman_rho"], ascending=[True, False])


def single_ols_screen(df, dvs, ivs):
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
                "dv": dv, "iv": iv, "n": n,
                "coef": round(model.params.iloc[1], 10),
                "std_err": round(model.bse.iloc[1], 10),
                "t_value": round(model.tvalues.iloc[1], 4),
                "p_value": round(model.pvalues.iloc[1], 6),
                "r_squared": round(model.rsquared, 4),
                "adj_r_squared": round(model.rsquared_adj, 4),
                "sign": "+" if model.params.iloc[1] > 0 else "-",
            })
    result = pd.DataFrame(records)
    return result.sort_values(["dv", "adj_r_squared"], ascending=[True, False])


# =========================================================================
# Main
# =========================================================================
def main():
    print("=" * 70)
    print("Specialization / Deviation Analysis Pipeline")
    print("=" * 70)

    df = pd.read_csv(DATA_IN, dtype={"state": str})
    df["state"] = df["state"].str.zfill(2)
    print(f"\nLoaded {len(df)} states")

    # --- Phase 1 ---
    print("\n--- Phase 1: Engineering specialization metrics ---")
    df = engineer_specialization(df)

    # Metric column lists
    rel_cols = [f"REL_IN_{ag}" for ag in AGE_GROUPS] + [f"REL_OUT_{ag}" for ag in AGE_GROUPS]
    diff_cols = [f"DIFF_IN_{ag}" for ag in AGE_GROUPS] + [f"DIFF_OUT_{ag}" for ag in AGE_GROUPS]
    gap_cols = [f"SHARE_GAP_{ag}" for ag in AGE_GROUPS]
    all_new_dvs = rel_cols + diff_cols + gap_cols

    print(f"  REL ratios: {len(rel_cols)}")
    print(f"  DIFF metrics: {len(diff_cols)}")
    print(f"  SHARE_GAP: {len(gap_cols)}")
    print(f"  Total new DVs: {len(all_new_dvs)}")

    # Rank shifts
    rank_df = compute_rank_shifts(df)
    rank_df.to_csv(TABLE_DIR / "rank_shifts.csv", index=False)
    print(f"  Rank shifts: {len(rank_df)} rows")

    # Save
    df.to_csv(DATA_OUT, index=False)
    print(f"  Saved: {DATA_OUT.relative_to(PROJECT)}")

    # --- Phase 2 ---
    print("\n--- Phase 2: Validation ---")
    vdf = validate_specialization(df)
    vdf.to_csv(TABLE_DIR / "validation.csv", index=False)
    n_pass = (vdf["passes"] == "OK").sum()
    n_sum_ok = vdf[vdf["expected_sum"].notna()]["sum_check"].eq("OK").sum()
    n_sum_total = vdf["expected_sum"].notna().sum()
    print(f"  {n_pass}/{len(vdf)} variables pass (n=50, no inf/nan)")
    print(f"  {n_sum_ok}/{n_sum_total} difference sums ≈ 0")
    print(vdf[["variable", "type", "n", "min", "max", "sum", "sum_check", "passes"]].to_string(index=False))

    # --- Phase 4: Descriptive ---
    print("\n--- Phase 4: Descriptive statistics ---")
    stats_df = summary_stats(df, all_new_dvs)
    stats_df.to_csv(TABLE_DIR / "summary_stats.csv", index=False)
    print(stats_df[["variable", "mean", "std", "min", "median", "max"]].to_string(index=False))

    # Rankings
    rank_top = build_rankings(df, all_new_dvs)
    rank_top.to_csv(TABLE_DIR / "rankings.csv", index=False)

    # Print top-3 for REL_IN (most interesting)
    print("\n  === Top 3 by REL_IN (inflow specialization) ===")
    for ag in AGE_GROUPS:
        col = f"REL_IN_{ag}"
        top = rank_top[(rank_top["variable"] == col) & (rank_top["rank_type"] == "top")].head(3)
        states = ", ".join(f"{r['abbrev']}({r['value']:.2f})" for _, r in top.iterrows())
        print(f"    {col}: {states}")

    print("\n  === Top 3 by REL_OUT (outflow specialization) ===")
    for ag in AGE_GROUPS:
        col = f"REL_OUT_{ag}"
        top = rank_top[(rank_top["variable"] == col) & (rank_top["rank_type"] == "top")].head(3)
        states = ", ".join(f"{r['abbrev']}({r['value']:.2f})" for _, r in top.iterrows())
        print(f"    {col}: {states}")

    # Top rank shifts
    print("\n  === Largest positive rank shifts (age-specific rank higher than all-ages) ===")
    for direction in ["IN", "OUT"]:
        for ag in AGE_GROUPS:
            sub = rank_df[(rank_df["direction"] == direction) & (rank_df["age_group"] == ag)]
            top3 = sub.nlargest(3, "rank_shift")
            states = ", ".join(
                f"{r['abbrev']}(+{r['rank_shift']})" for _, r in top3.iterrows()
            )
            print(f"    {direction}_{ag}: {states}")

    # --- Phase 5: Statistical screening ---
    print("\n--- Phase 5: Spearman & Kendall screening ---")
    # Screen only the specialization/deviation DVs (not raw shares)
    screen_dvs = rel_cols + diff_cols + gap_cols
    available_ivs = [iv for iv in IVS if iv in df.columns]

    corr_df = spearman_kendall_screen(df, screen_dvs, available_ivs)
    corr_df.to_csv(TABLE_DIR / "a4_spearman_kendall.csv", index=False)
    print(f"  Correlation pairs: {len(corr_df)}")

    # Top-3 correlates for REL_IN (most interesting family)
    print("\n  === Top 3 Spearman correlates for REL_IN ===")
    for ag in AGE_GROUPS:
        dv = f"REL_IN_{ag}"
        top = corr_df[corr_df["dv"] == dv].head(3)
        if top.empty:
            continue
        s = ", ".join(
            f"{r['iv']}(rho={r['spearman_rho']:+.3f}, p={r['spearman_p']:.4f})"
            for _, r in top.iterrows()
        )
        print(f"    {dv}: {s}")

    print("\n  === Top 3 Spearman correlates for SHARE_GAP ===")
    for ag in AGE_GROUPS:
        dv = f"SHARE_GAP_{ag}"
        top = corr_df[corr_df["dv"] == dv].head(3)
        if top.empty:
            continue
        s = ", ".join(
            f"{r['iv']}(rho={r['spearman_rho']:+.3f}, p={r['spearman_p']:.4f})"
            for _, r in top.iterrows()
        )
        print(f"    {dv}: {s}")

    print("\n--- Phase 5: Single-variable OLS screening ---")
    ols_df = single_ols_screen(df, screen_dvs, available_ivs)
    ols_df.to_csv(TABLE_DIR / "a5_single_ols.csv", index=False)
    print(f"  OLS regressions: {len(ols_df)}")

    print("\n  === Top 3 by adj R-squared for REL_IN ===")
    for ag in AGE_GROUPS:
        dv = f"REL_IN_{ag}"
        top = ols_df[ols_df["dv"] == dv].head(3)
        if top.empty:
            continue
        s = ", ".join(
            f"{r['iv']}(adjR2={r['adj_r_squared']:.4f}, {r['sign']}, p={r['p_value']:.4f})"
            for _, r in top.iterrows()
        )
        print(f"    {dv}: {s}")

    print("\n  === Top 3 by adj R-squared for SHARE_GAP ===")
    for ag in AGE_GROUPS:
        dv = f"SHARE_GAP_{ag}"
        top = ols_df[ols_df["dv"] == dv].head(3)
        if top.empty:
            continue
        s = ", ".join(
            f"{r['iv']}(adjR2={r['adj_r_squared']:.4f}, {r['sign']}, p={r['p_value']:.4f})"
            for _, r in top.iterrows()
        )
        print(f"    {dv}: {s}")

    # Summary: is POP still dominating?
    print("\n  === Size-dominance check ===")
    size_ivs = {"POP", "GDP", "PRIV_EMP", "PRIV_ESTAB", "LAND_AREA"}
    for family_name, family_dvs in [("REL_IN", [f"REL_IN_{ag}" for ag in AGE_GROUPS]),
                                      ("REL_OUT", [f"REL_OUT_{ag}" for ag in AGE_GROUPS]),
                                      ("DIFF_IN", [f"DIFF_IN_{ag}" for ag in AGE_GROUPS]),
                                      ("DIFF_OUT", [f"DIFF_OUT_{ag}" for ag in AGE_GROUPS]),
                                      ("SHARE_GAP", gap_cols)]:
        top1_records = []
        for dv in family_dvs:
            top1 = ols_df[ols_df["dv"] == dv].head(1)
            if not top1.empty:
                top1_records.append(top1.iloc[0]["iv"])
        n_size = sum(1 for iv in top1_records if iv in size_ivs)
        print(f"    {family_name}: top-1 IV is size-related in {n_size}/{len(family_dvs)} age groups")

    print("\n" + "=" * 70)
    print("Pipeline complete.")
    for f in sorted(TABLE_DIR.glob("*.csv")):
        print(f"  {f.relative_to(PROJECT)}")
    print("=" * 70)


if __name__ == "__main__":
    main()
