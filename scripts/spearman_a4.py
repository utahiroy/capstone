"""Phase A4: Spearman rank correlation screening.

For each of the 5 main DVs (NET_RATE by age group), computes Spearman rho
against all 18 core IVs, ranks by |rho|, and saves outputs.

Run:  python -m scripts.spearman_a4
"""

import os
import sys

import pandas as pd
from scipy import stats

from src.constants import AGE_GROUPS

# ── Column definitions ───────────────────────────────────────────────

DV_COLS = [f"NET_RATE_{ag}" for ag in AGE_GROUPS]

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


def spearman_screen(df, dv_col, iv_cols):
    """Compute Spearman rho + p-value for dv_col vs each IV.

    Returns DataFrame with columns: iv, rho, abs_rho, p_value, rank.
    """
    rows = []
    for iv in iv_cols:
        x = df[iv].dropna()
        y = df.loc[x.index, dv_col].dropna()
        common = x.index.intersection(y.index)
        if len(common) < 10:
            continue
        rho, pval = stats.spearmanr(df.loc[common, iv], df.loc[common, dv_col])
        rows.append({
            "iv": iv,
            "rho": round(rho, 4),
            "abs_rho": round(abs(rho), 4),
            "p_value": round(pval, 6),
            "n": len(common),
        })
    result = pd.DataFrame(rows).sort_values("abs_rho", ascending=False).reset_index(drop=True)
    result["rank"] = range(1, len(result) + 1)
    return result


def top_associations_note(screen_df, dv_label, n=3):
    """Generate a brief factual note on the strongest associations."""
    lines = [f"  {dv_label}:"]
    top = screen_df.head(n)
    for _, row in top.iterrows():
        sign = "+" if row["rho"] > 0 else "-"
        sig = "***" if row["p_value"] < 0.001 else ("**" if row["p_value"] < 0.01 else ("*" if row["p_value"] < 0.05 else ""))
        lines.append(
            f"    {row['rank']:2d}. {row['iv']:18s}  rho={row['rho']:+.3f}{sig}  "
            f"|rho|={row['abs_rho']:.3f}"
        )
    # Strongest positive and negative
    pos = screen_df[screen_df["rho"] > 0]
    neg = screen_df[screen_df["rho"] < 0]
    if not pos.empty:
        best_pos = pos.iloc[0]
        lines.append(f"    Strongest positive: {best_pos['iv']} (rho={best_pos['rho']:+.3f})")
    if not neg.empty:
        best_neg = neg.iloc[0]
        lines.append(f"    Strongest negative: {best_neg['iv']} (rho={best_neg['rho']:+.3f})")
    return "\n".join(lines)


def main():
    os.makedirs(OUTDIR, exist_ok=True)
    df = load_data()

    # Verify columns exist
    iv_present = [c for c in IV_COLS if c in df.columns]
    missing_iv = set(IV_COLS) - set(iv_present)
    if missing_iv:
        print(f"  WARNING: missing IVs (excluded from screening): {missing_iv}")
    print(f"  DVs: {len(DV_COLS)}, IVs: {len(iv_present)}")

    # ── Age-group-specific tables ────────────────────────────────────
    all_screens = []
    notes = []

    print("\n" + "=" * 60)
    print("  Phase A4: Spearman Rank Correlation Screening")
    print("=" * 60)

    for dv in DV_COLS:
        ag = dv.replace("NET_RATE_", "")
        print(f"\n--- {dv} ---")

        screen = spearman_screen(df, dv, iv_present)
        screen.insert(0, "dv", dv)
        screen.insert(1, "age_group", ag)

        # Save age-group table
        path = f"{OUTDIR}/a4_spearman_{ag}.csv"
        screen.to_csv(path, index=False)
        print(f"  Saved: {path}")

        # Print top 5
        for _, row in screen.head(5).iterrows():
            sig = "***" if row["p_value"] < 0.001 else ("**" if row["p_value"] < 0.01 else ("*" if row["p_value"] < 0.05 else ""))
            print(f"    {row['rank']:2d}. {row['iv']:18s}  rho={row['rho']:+.4f}{sig:4s}  "
                  f"p={row['p_value']:.4f}")

        note = top_associations_note(screen, dv)
        notes.append(note)
        all_screens.append(screen)

    # ── Combined table ───────────────────────────────────────────────
    combined = pd.concat(all_screens, ignore_index=True)
    path = f"{OUTDIR}/a4_spearman_combined.csv"
    combined.to_csv(path, index=False)
    print(f"\n  Saved combined: {path}")

    # ── Pivot: rho matrix (IVs × age groups) ────────────────────────
    pivot = combined.pivot_table(
        index="iv", columns="age_group", values="rho", aggfunc="first"
    )
    # Reorder columns by age group order
    ag_order = [dv.replace("NET_RATE_", "") for dv in DV_COLS]
    pivot = pivot[[ag for ag in ag_order if ag in pivot.columns]]
    # Add mean |rho| across age groups
    pivot["mean_abs_rho"] = pivot.abs().mean(axis=1).round(4)
    pivot = pivot.sort_values("mean_abs_rho", ascending=False)
    path = f"{OUTDIR}/a4_spearman_matrix.csv"
    pivot.to_csv(path)
    print(f"  Saved matrix: {path}")

    # Print the matrix
    print("\n  Spearman rho matrix (IVs × age groups), sorted by mean |rho|:")
    print(pivot.to_string(float_format=lambda x: f"{x:+.3f}" if abs(x) < 10 else f"{x:.3f}"))

    # ── Notes ────────────────────────────────────────────────────────
    print("\n--- Strongest Associations (factual summary) ---")
    for note in notes:
        print(note)

    # Save notes
    path = f"{OUTDIR}/a4_spearman_notes.txt"
    with open(path, "w") as f:
        f.write("Phase A4: Spearman Screening — Strongest Associations\n")
        f.write("=" * 55 + "\n\n")
        f.write("Significance: *** p<0.001, ** p<0.01, * p<0.05\n")
        f.write("All correlations are Spearman rank (nonparametric).\n")
        f.write("Correlation does not imply causation.\n\n")
        for note in notes:
            f.write(note + "\n\n")
    print(f"\n  Saved: {path}")

    # ── Output inventory ─────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("  Phase A4 Spearman screening complete.")
    print("=" * 60)
    print(f"\nOutput files:")
    for fname in sorted(os.listdir(OUTDIR)):
        if fname.startswith("a4_"):
            print(f"  {os.path.join(OUTDIR, fname)}")


if __name__ == "__main__":
    main()
