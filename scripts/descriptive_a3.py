"""Phase A3: Descriptive analysis of the analysis-ready dataset.

Produces:
  - Summary statistics table (all DVs and IVs)
  - Distribution diagnostics (skewness, kurtosis)
  - Outlier report (IQR method)
  - Saved to outputs/tables/

Run:  python -m scripts.descriptive_a3
"""

import os
import sys

import numpy as np
import pandas as pd

from src.constants import AGE_GROUPS

# ── Column groups ────────────────────────────────────────────────────

DV_RATE_COLS = [f"NET_RATE_{ag}" for ag in AGE_GROUPS]
DV_SUPP_PREFIXES = ["IN_COUNT", "OUT_COUNT", "NET_COUNT", "IN_RATE", "OUT_RATE"]

IV_COLS = [
    "POP", "LAND_AREA", "POP_DENS",
    "GDP", "RPP", "REAL_PCPI",
    "UNEMP", "PRIV_EMP", "PRIV_ESTAB", "PRIV_AVG_PAY",
    "PERMITS", "MED_RENT", "MED_HOMEVAL",
    "COST_BURDEN_ALL", "VACANCY_RATE",
    "TRANSIT_SHARE", "BA_PLUS", "ELEC_PRICE_TOT",
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


def get_numeric_cols(df, col_list):
    """Return subset of col_list that exists in df and is numeric."""
    present = [c for c in col_list if c in df.columns]
    return present


def summary_statistics(df, cols, label):
    """Compute summary stats: n, mean, std, min, p25, median, p75, max."""
    stats = df[cols].describe(percentiles=[0.25, 0.5, 0.75]).T
    stats = stats[["count", "mean", "std", "min", "25%", "50%", "75%", "max"]]
    stats.columns = ["N", "Mean", "SD", "Min", "P25", "Median", "P75", "Max"]
    stats["N"] = stats["N"].astype(int)
    # Round numeric columns
    for c in ["Mean", "SD", "Min", "P25", "Median", "P75", "Max"]:
        stats[c] = stats[c].apply(lambda x: f"{x:.4g}")
    return stats


def distribution_diagnostics(df, cols):
    """Compute skewness, kurtosis, and flag strongly non-normal variables."""
    rows = []
    for c in cols:
        s = df[c].dropna()
        if len(s) < 5:
            continue
        skew = s.skew()
        kurt = s.kurtosis()  # excess kurtosis (0 = normal)
        cv = s.std() / s.mean() if s.mean() != 0 else np.nan
        flag = ""
        if abs(skew) > 2:
            flag += "HIGH_SKEW "
        elif abs(skew) > 1:
            flag += "MOD_SKEW "
        if abs(kurt) > 7:
            flag += "HIGH_KURT "
        rows.append({
            "variable": c,
            "skewness": round(skew, 3),
            "kurtosis": round(kurt, 3),
            "cv": round(cv, 3) if not np.isnan(cv) else np.nan,
            "flag": flag.strip(),
        })
    return pd.DataFrame(rows)


def outlier_report(df, cols):
    """Identify outliers via 1.5×IQR rule. Report state + value for each."""
    records = []
    for c in cols:
        s = df[c].dropna()
        q1, q3 = s.quantile(0.25), s.quantile(0.75)
        iqr = q3 - q1
        if iqr == 0:
            continue
        lo, hi = q1 - 1.5 * iqr, q3 + 1.5 * iqr
        mask = (df[c] < lo) | (df[c] > hi)
        outliers = df.loc[mask & df[c].notna(), ["state", "state_name", c]]
        for _, row in outliers.iterrows():
            records.append({
                "variable": c,
                "state": row["state"],
                "state_name": row["state_name"],
                "value": row[c],
                "lower_fence": round(lo, 2),
                "upper_fence": round(hi, 2),
                "direction": "low" if row[c] < lo else "high",
            })
    return pd.DataFrame(records)


def caution_notes(diag_df, outlier_df, iv_cols_present):
    """Generate brief notes on variables needing caution in later analysis."""
    notes = []

    # Highly skewed IVs
    skewed = diag_df[
        (diag_df["variable"].isin(iv_cols_present)) &
        (diag_df["flag"].str.contains("SKEW", na=False))
    ]
    if len(skewed) > 0:
        names = skewed["variable"].tolist()
        notes.append(
            f"Skewed IVs ({len(names)}): {', '.join(names)}. "
            "Consider log-transform or rank-based methods for correlation screening."
        )

    # IVs with many outliers (>3 states)
    if len(outlier_df) > 0:
        iv_outliers = outlier_df[outlier_df["variable"].isin(iv_cols_present)]
        oc = iv_outliers.groupby("variable").size()
        many = oc[oc > 3]
        if len(many) > 0:
            for var, cnt in many.items():
                notes.append(
                    f"{var}: {cnt} outlier states (IQR method). "
                    "May be influential in OLS — check leverage later."
                )

    # DVs: check if any age group has near-zero variance
    dv_diag = diag_df[diag_df["variable"].isin(DV_RATE_COLS)]
    low_var = dv_diag[dv_diag["cv"].abs() > 3]
    if len(low_var) > 0:
        for _, row in low_var.iterrows():
            notes.append(
                f"{row['variable']}: CV={row['cv']:.2f} — high relative dispersion."
            )

    return notes


def main():
    os.makedirs(OUTDIR, exist_ok=True)
    df = load_data()

    # Identify available columns
    dv_rate = get_numeric_cols(df, DV_RATE_COLS)
    dv_supp = []
    for prefix in DV_SUPP_PREFIXES:
        dv_supp.extend(get_numeric_cols(df, [f"{prefix}_{ag}" for ag in AGE_GROUPS]))
    all_dv = dv_rate + dv_supp
    iv_present = get_numeric_cols(df, IV_COLS)
    all_vars = all_dv + iv_present

    print(f"\nMain DVs:          {len(dv_rate)}")
    print(f"Supplemental DVs:  {len(dv_supp)}")
    print(f"IVs:               {len(iv_present)}")
    print(f"Total numeric:     {len(all_vars)}")

    # ── 1. Summary statistics ────────────────────────────────────────
    print("\n--- Summary Statistics ---")

    # Main DVs
    stats_dv = summary_statistics(df, dv_rate, "Main DVs")
    path = f"{OUTDIR}/a3_summary_dv_net_rate.csv"
    stats_dv.to_csv(path)
    print(f"  Saved: {path}")
    print(stats_dv.to_string())

    # Supplemental DVs
    if dv_supp:
        stats_dv_supp = summary_statistics(df, dv_supp, "Supplemental DVs")
        path = f"{OUTDIR}/a3_summary_dv_supplemental.csv"
        stats_dv_supp.to_csv(path)
        print(f"  Saved: {path}")

    # IVs
    stats_iv = summary_statistics(df, iv_present, "IVs")
    path = f"{OUTDIR}/a3_summary_ivs.csv"
    stats_iv.to_csv(path)
    print(f"\n  Saved: {path}")
    print(stats_iv.to_string())

    # ── 2. Distribution diagnostics ──────────────────────────────────
    print("\n--- Distribution Diagnostics ---")
    diag = distribution_diagnostics(df, all_vars)
    path = f"{OUTDIR}/a3_distribution_diagnostics.csv"
    diag.to_csv(path, index=False)
    print(f"  Saved: {path}")

    flagged = diag[diag["flag"] != ""]
    if len(flagged) > 0:
        print(f"\n  Flagged variables ({len(flagged)}):")
        for _, row in flagged.iterrows():
            print(f"    {row['variable']:25s}  skew={row['skewness']:+.3f}  "
                  f"kurt={row['kurtosis']:+.3f}  [{row['flag']}]")
    else:
        print("  No variables flagged for extreme skewness or kurtosis.")

    # ── 3. Outlier report ────────────────────────────────────────────
    print("\n--- Outlier Report (1.5×IQR) ---")
    outliers = outlier_report(df, all_vars)
    path = f"{OUTDIR}/a3_outlier_report.csv"
    outliers.to_csv(path, index=False)
    print(f"  Saved: {path}")

    if len(outliers) > 0:
        # Summarize by variable
        oc = outliers.groupby("variable").size().sort_values(ascending=False)
        print(f"\n  Outlier counts by variable (top 15):")
        for var, cnt in oc.head(15).items():
            states = outliers.loc[outliers["variable"] == var, "state_name"].tolist()
            print(f"    {var:25s}: {cnt} states  ({', '.join(states[:5])}{'...' if cnt > 5 else ''})")
    else:
        print("  No outliers detected.")

    # ── 4. Caution notes ─────────────────────────────────────────────
    print("\n--- Caution Notes for Later Analysis ---")
    notes = caution_notes(diag, outliers, iv_present)
    if notes:
        for i, note in enumerate(notes, 1):
            print(f"  {i}. {note}")
    else:
        print("  No special cautions identified.")

    # Save caution notes
    path = f"{OUTDIR}/a3_caution_notes.txt"
    with open(path, "w") as f:
        f.write("Phase A3: Caution Notes for Later Analysis\n")
        f.write("=" * 50 + "\n\n")
        if notes:
            for i, note in enumerate(notes, 1):
                f.write(f"{i}. {note}\n\n")
        else:
            f.write("No special cautions identified.\n")
    print(f"\n  Saved: {path}")

    # ── 5. State rankings for NET_RATE by age group ────────────────
    print("\n--- State Rankings: NET_RATE (top/bottom 10) ---")
    ranking_rows = []
    for col in dv_rate:
        ranked = (
            df[["state", "state_name", col]]
            .sort_values(col, ascending=False)
            .reset_index(drop=True)
        )
        ag_label = col.replace("NET_RATE_", "")
        for rank_pos, (_, row) in enumerate(ranked.iterrows(), 1):
            ranking_rows.append({
                "age_group": ag_label,
                "rank": rank_pos,
                "state": row["state"],
                "state_name": row["state_name"],
                "NET_RATE": round(row[col], 2),
            })
    ranking_df = pd.DataFrame(ranking_rows)
    path = f"{OUTDIR}/a3_state_rankings_net_rate.csv"
    ranking_df.to_csv(path, index=False)
    print(f"  Saved: {path}")

    # Print compact top/bottom 10 for each age group
    for col in dv_rate:
        ag_label = col.replace("NET_RATE_", "")
        ranked = df[["state_name", col]].sort_values(col, ascending=False)
        top5 = ranked.head(10)
        bot5 = ranked.tail(10).iloc[::-1]
        print(f"\n  {col}:")
        print(f"    Top 10 (highest net in-migration rate):")
        for _, r in top5.iterrows():
            print(f"      {r['state_name']:20s} {r[col]:+8.2f}")
        print(f"    Bottom 10 (highest net out-migration rate):")
        for _, r in bot5.iterrows():
            print(f"      {r['state_name']:20s} {r[col]:+8.2f}")

    # ── 6. Compact combined summary ──────────────────────────────────
    # One-stop table: all variables with stats + diagnostics
    stats_all = summary_statistics(df, all_vars, "All")
    stats_all.index.name = "variable"
    diag_indexed = diag.set_index("variable")
    combined = stats_all.join(diag_indexed[["skewness", "kurtosis", "flag"]], how="left")
    path = f"{OUTDIR}/a3_combined_summary.csv"
    combined.to_csv(path)
    print(f"  Saved: {path}")

    print("\n" + "=" * 60)
    print("  Phase A3 descriptive analysis complete.")
    print("=" * 60)

    # Print output file inventory
    print(f"\nOutput files:")
    for fname in sorted(os.listdir(OUTDIR)):
        if fname.startswith("a3_"):
            fpath = os.path.join(OUTDIR, fname)
            print(f"  {fpath}")


if __name__ == "__main__":
    main()
