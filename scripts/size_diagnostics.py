"""Size-suppression diagnostics for age-group migration rates.

Diagnoses whether small-population states are over-represented in extreme
rate rankings due to denominator effects, without changing the main DV.

Reads:  data_processed/analysis_ready.csv
Writes: outputs/tables/size_diag_state_age_long.csv
        outputs/tables/size_diag_summary_by_age.csv
        outputs/tables/size_diag_notes.md

Run:  python -m scripts.size_diagnostics
"""

import os
import sys

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
AGE_GROUPS = ["18_24", "25_34", "35_54", "55_64", "65_PLUS"]
AGE_LABELS = {
    "18_24": "18–24", "25_34": "25–34", "35_54": "35–54",
    "55_64": "55–64", "65_PLUS": "65+",
}
SMALL_POP_QUANTILE = 0.20  # bottom quintile within each age group
TOP_N = 10  # for overlap analysis

INPUT = "data_processed/analysis_ready.csv"
OUT_DIR = "outputs/tables"
OUT_LONG = os.path.join(OUT_DIR, "size_diag_state_age_long.csv")
OUT_SUMMARY = os.path.join(OUT_DIR, "size_diag_summary_by_age.csv")
OUT_NOTES = os.path.join(OUT_DIR, "size_diag_notes.md")


def load_data():
    if not os.path.exists(INPUT):
        print(f"ERROR: {INPUT} not found.")
        sys.exit(1)
    df = pd.read_csv(INPUT)
    if len(df) != 50:
        print(f"WARNING: Expected 50 rows, got {len(df)}.")
    return df


def build_long(df):
    """Melt wide analysis_ready into state × age_group long format."""
    rows = []
    for ag in AGE_GROUPS:
        for _, r in df.iterrows():
            rows.append({
                "state": r["state"],
                "state_name": r["state_name"],
                "age_group": ag,
                "POP_AGE": r[f"POP_AGE_{ag}"],
                "IN_COUNT": r[f"IN_COUNT_{ag}"],
                "OUT_COUNT": r[f"OUT_COUNT_{ag}"],
                "NET_COUNT": r[f"NET_COUNT_{ag}"],
                "IN_RATE": r[f"IN_RATE_{ag}"],
                "OUT_RATE": r[f"OUT_RATE_{ag}"],
                "NET_RATE": r[f"NET_RATE_{ag}"],
            })
    long = pd.DataFrame(rows)
    long["state"] = long["state"].astype(str).str.zfill(2)

    # Rankings within each age group (1 = highest / most positive)
    for ag in AGE_GROUPS:
        mask = long["age_group"] == ag
        sub = long.loc[mask].copy()

        long.loc[mask, "rank_net_rate"] = sub["NET_RATE"].rank(ascending=False).astype(int)
        long.loc[mask, "rank_net_count"] = sub["NET_COUNT"].rank(ascending=False).astype(int)
        long.loc[mask, "rank_abs_net_rate"] = sub["NET_RATE"].abs().rank(ascending=False).astype(int)
        long.loc[mask, "rank_abs_net_count"] = sub["NET_COUNT"].abs().rank(ascending=False).astype(int)
        long.loc[mask, "pop_rank_within_age"] = sub["POP_AGE"].rank(ascending=False).astype(int)

        threshold = sub["POP_AGE"].quantile(SMALL_POP_QUANTILE)
        long.loc[mask, "small_pop_flag"] = (sub["POP_AGE"] <= threshold).astype(int)

    # Ensure int columns
    int_cols = ["rank_net_rate", "rank_net_count", "rank_abs_net_rate",
                "rank_abs_net_count", "pop_rank_within_age", "small_pop_flag"]
    for c in int_cols:
        long[c] = long[c].astype(int)

    return long


def build_summary(long):
    """Per-age-group summary: correlations, top-10 overlap, small-state dominance."""
    records = []
    for ag in AGE_GROUPS:
        sub = long[long["age_group"] == ag].copy()

        # Spearman correlations
        rho_net, p_net = spearmanr(sub["POP_AGE"], sub["NET_RATE"])
        rho_abs, p_abs = spearmanr(sub["POP_AGE"], sub["NET_RATE"].abs())

        # Top 10 by NET_RATE vs NET_COUNT
        top_rate = set(sub.nlargest(TOP_N, "NET_RATE")["state"])
        top_count = set(sub.nlargest(TOP_N, "NET_COUNT")["state"])
        overlap_top = len(top_rate & top_count)

        # Bottom 10 (most negative)
        bot_rate = set(sub.nsmallest(TOP_N, "NET_RATE")["state"])
        bot_count = set(sub.nsmallest(TOP_N, "NET_COUNT")["state"])
        overlap_bot = len(bot_rate & bot_count)

        # Top 10 abs(NET_RATE) vs abs(NET_COUNT)
        sub_abs = sub.copy()
        sub_abs["_abs_rate"] = sub_abs["NET_RATE"].abs()
        sub_abs["_abs_count"] = sub_abs["NET_COUNT"].abs()
        top_abs_rate_set = set(sub_abs.nlargest(TOP_N, "_abs_rate")["state"])
        top_abs_count_set = set(sub_abs.nlargest(TOP_N, "_abs_count")["state"])
        overlap_abs = len(top_abs_rate_set & top_abs_count_set)

        # Small-state share in top/bottom 10 rate rankings
        small_mask = sub["small_pop_flag"] == 1
        n_small = small_mask.sum()
        small_in_top_rate = len(top_rate & set(sub[small_mask]["state"]))
        small_in_bot_rate = len(bot_rate & set(sub[small_mask]["state"]))
        small_in_top_abs_rate = len(top_abs_rate_set & set(sub[small_mask]["state"]))

        # Top 10 lists as strings (use state_name for readability)
        top_rate_list = ", ".join(sub.nlargest(TOP_N, "NET_RATE")["state_name"].tolist())
        top_count_list = ", ".join(sub.nlargest(TOP_N, "NET_COUNT")["state_name"].tolist())

        records.append({
            "age_group": ag,
            "spearman_rho_pop_vs_net_rate": round(rho_net, 3),
            "p_value_pop_vs_net_rate": round(p_net, 4),
            "spearman_rho_pop_vs_abs_net_rate": round(rho_abs, 3),
            "p_value_pop_vs_abs_net_rate": round(p_abs, 4),
            "top10_net_rate_states": top_rate_list,
            "top10_net_count_states": top_count_list,
            "overlap_top10_rate_vs_count": overlap_top,
            "overlap_bottom10_rate_vs_count": overlap_bot,
            "overlap_top10_abs_rate_vs_abs_count": overlap_abs,
            "n_small_pop_states": n_small,
            "small_in_top10_net_rate": small_in_top_rate,
            "small_in_bottom10_net_rate": small_in_bot_rate,
            "small_in_top10_abs_net_rate": small_in_top_abs_rate,
        })

    return pd.DataFrame(records)


def write_notes(long, summary):
    """Generate plain-language interpretation as Markdown."""
    lines = [
        "# Size-Suppression Diagnostic Notes",
        "",
        f"**Small-population threshold**: bottom {int(SMALL_POP_QUANTILE*100)}th "
        f"percentile of POP_AGE within each age group "
        f"(= {int(50 * SMALL_POP_QUANTILE)} states per group).",
        "",
        "---",
        "",
    ]

    for _, row in summary.iterrows():
        ag = row["age_group"]
        label = AGE_LABELS[ag]
        lines.append(f"## Age group: {label}")
        lines.append("")

        # Correlation interpretation
        rho = row["spearman_rho_pop_vs_net_rate"]
        p = row["p_value_pop_vs_net_rate"]
        rho_abs = row["spearman_rho_pop_vs_abs_net_rate"]
        p_abs = row["p_value_pop_vs_abs_net_rate"]

        sig = "significant" if p < 0.05 else "not significant"
        sig_abs = "significant" if p_abs < 0.05 else "not significant"

        lines.append(f"**POP_AGE vs NET_RATE**: Spearman rho = {rho:.3f} "
                      f"(p = {p:.4f}, {sig})")
        direction = "larger states tend to have higher net rates" if rho > 0 else \
                    "smaller states tend to have higher net rates"
        if abs(rho) < 0.2:
            direction = "weak or negligible association"
        lines.append(f"  → {direction}")
        lines.append("")

        lines.append(f"**POP_AGE vs |NET_RATE|**: Spearman rho = {rho_abs:.3f} "
                      f"(p = {p_abs:.4f}, {sig_abs})")
        if rho_abs < -0.2 and p_abs < 0.05:
            lines.append("  → Small states show systematically more extreme rates "
                          "(denominator effect detected).")
        elif rho_abs < -0.2:
            lines.append("  → Tendency for small states to have more extreme rates, "
                          "but not statistically significant.")
        else:
            lines.append("  → No strong evidence that small states have systematically "
                          "more extreme rates.")
        lines.append("")

        # Top-10 overlap
        overlap_top = row["overlap_top10_rate_vs_count"]
        overlap_bot = row["overlap_bottom10_rate_vs_count"]
        lines.append(f"**Top-10 overlap (rate vs count)**: "
                      f"{overlap_top}/10 gaining, {overlap_bot}/10 losing")
        if overlap_top <= 4:
            lines.append("  → Low overlap in gainers: rate rankings emphasize "
                          "different states than count rankings.")
        else:
            lines.append("  → Moderate-to-high overlap in gainers.")
        lines.append("")

        # Small-state presence
        n_small = row["n_small_pop_states"]
        s_top = row["small_in_top10_net_rate"]
        s_bot = row["small_in_bottom10_net_rate"]
        s_abs = row["small_in_top10_abs_net_rate"]
        expected = n_small / 50 * 10  # expected under uniform

        lines.append(f"**Small-state presence in rate extremes** "
                      f"({n_small} small states, expected ~{expected:.0f}/10):")
        lines.append(f"  - In top-10 NET_RATE: {s_top}")
        lines.append(f"  - In bottom-10 NET_RATE: {s_bot}")
        lines.append(f"  - In top-10 |NET_RATE|: {s_abs}")
        if s_abs > expected * 2:
            lines.append(f"  → Small states are **over-represented** in extreme "
                          f"rate rankings (expected ~{expected:.0f}, got {s_abs}).")
        elif s_abs > expected * 1.5:
            lines.append(f"  → Small states are **moderately over-represented** "
                          f"in extreme rate rankings.")
        else:
            lines.append(f"  → Small-state representation in extremes is roughly "
                          f"proportional.")
        lines.append("")

        # Top-10 rate list
        lines.append(f"**Top 10 by NET_RATE**: {row['top10_net_rate_states']}")
        lines.append(f"**Top 10 by NET_COUNT**: {row['top10_net_count_states']}")
        lines.append("")
        lines.append("---")
        lines.append("")

    # Overall summary
    lines.append("## Overall Assessment")
    lines.append("")

    # Count age groups with significant negative rho_abs
    denom_groups = []
    for _, row in summary.iterrows():
        if row["spearman_rho_pop_vs_abs_net_rate"] < -0.2 and \
           row["p_value_pop_vs_abs_net_rate"] < 0.05:
            denom_groups.append(AGE_LABELS[row["age_group"]])

    if denom_groups:
        lines.append(f"Denominator-effect signal detected in: "
                      f"{', '.join(denom_groups)}.")
        lines.append("In these age groups, small-population states tend to appear "
                      "at the extremes of NET_RATE rankings, which may inflate "
                      "their apparent importance in OLS models that weight all "
                      "states equally.")
        lines.append("")
        lines.append("**Implication**: Consider reporting both rate and count "
                      "rankings side by side. For robustness, a sensitivity check "
                      "using population-weighted regression or excluding the "
                      "smallest states could be informative, but is not required "
                      "to change the main specification.")
    else:
        lines.append("No strong denominator-effect signal detected across age groups.")
        lines.append("Small-population states do not systematically dominate "
                      "extreme rate rankings beyond what would be expected by chance.")
        lines.append("")
        lines.append("**Implication**: The unweighted OLS on NET_RATE is not "
                      "obviously distorted by small-state denominator effects. "
                      "No change to the main specification is warranted on this basis.")

    lines.append("")

    return "\n".join(lines)


def main():
    print("=" * 60)
    print("  Size-Suppression Diagnostics")
    print("=" * 60)

    df = load_data()
    print(f"  Loaded {len(df)} states from {INPUT}")

    long = build_long(df)
    long.to_csv(OUT_LONG, index=False)
    print(f"  Saved: {OUT_LONG} ({len(long)} rows)")

    summary = build_summary(long)
    summary.to_csv(OUT_SUMMARY, index=False)
    print(f"  Saved: {OUT_SUMMARY}")

    notes = write_notes(long, summary)
    with open(OUT_NOTES, "w") as f:
        f.write(notes)
    print(f"  Saved: {OUT_NOTES}")

    # Print a compact console summary
    print()
    for _, row in summary.iterrows():
        ag = AGE_LABELS[row["age_group"]]
        rho = row["spearman_rho_pop_vs_abs_net_rate"]
        p = row["p_value_pop_vs_abs_net_rate"]
        ovlp = row["overlap_top10_rate_vs_count"]
        s_abs = row["small_in_top10_abs_net_rate"]
        flag = " *" if (rho < -0.2 and p < 0.05) else ""
        print(f"  {ag:>6s}: rho(POP,|NET_RATE|)={rho:+.3f} (p={p:.3f}){flag}  "
              f"top10 overlap={ovlp}/10  small_in_extremes={s_abs}")

    print()
    print("  Done.")


if __name__ == "__main__":
    main()
