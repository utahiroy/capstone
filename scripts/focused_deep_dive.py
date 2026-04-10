#!/usr/bin/env python3
"""
Focused Deep Dive: REL_IN_25_34 and REL_IN_18_24
=================================================
Targeted multivariable modeling, diagnostics, and robustness checks
for the two strongest specialization DVs.

Usage:
    python -m scripts.focused_deep_dive
"""

from pathlib import Path
from itertools import combinations

import numpy as np
import pandas as pd
from scipy import stats
import statsmodels.api as sm
from statsmodels.stats.outliers_influence import variance_inflation_factor, OLSInfluence

PROJECT = Path(__file__).resolve().parent.parent
DATA_PATH = PROJECT / "data_processed" / "analysis_ready_specialization.csv"
TABLE_DIR = PROJECT / "outputs" / "tables" / "focused_deep_dive"
TABLE_DIR.mkdir(parents=True, exist_ok=True)

AGE_LABELS = {"25_34": "25\u201334", "18_24": "18\u201324"}

IVS = [
    "POP", "LAND_AREA", "POP_DENS", "GDP", "RPP", "REAL_PCPI",
    "UNEMP", "PRIV_EMP", "PRIV_ESTAB", "PRIV_AVG_PAY", "PERMITS",
    "MED_RENT", "MED_HOMEVAL", "COST_BURDEN_ALL", "VACANCY_RATE",
    "COMMUTE_MED", "TRANSIT_SHARE", "BA_PLUS", "UNINSURED",
    "ELEC_PRICE_TOT", "CRIME_VIOLENT_RATE", "NRI_RISK_INDEX",
]

# Candidate IV pools (from task specification)
CANDIDATES_25_34 = [
    "PRIV_AVG_PAY", "RPP", "MED_RENT", "COMMUTE_MED", "TRANSIT_SHARE",
    "COST_BURDEN_ALL", "BA_PLUS", "POP_DENS",
]
CANDIDATES_18_24 = [
    "COMMUTE_MED", "NRI_RISK_INDEX", "MED_RENT", "PERMITS", "VACANCY_RATE",
    "BA_PLUS", "TRANSIT_SHARE", "POP_DENS",
]

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


def load_data():
    df = pd.read_csv(DATA_PATH, dtype={"state": str})
    df["state"] = df["state"].str.zfill(2)
    if "abbrev" not in df.columns:
        df["abbrev"] = df["state"].map(FIPS_TO_ABBREV)
    return df


# =========================================================================
# Phase 1A: Consolidated screening summary
# =========================================================================
def build_screening_summary(df, dvs):
    """Side-by-side screening table for two DVs across all 22 IVs."""
    rows = []
    for iv in IVS:
        row = {"iv": iv}
        for dv in dvs:
            y, x = df[dv], df[iv]
            mask = x.notna() & y.notna()
            sp_rho, sp_p = stats.spearmanr(x[mask], y[mask])
            kt_tau, kt_p = stats.kendalltau(x[mask], y[mask])
            X = sm.add_constant(x[mask])
            m = sm.OLS(y[mask], X).fit()
            tag = dv.replace("REL_IN_", "")
            row[f"sp_rho_{tag}"] = round(sp_rho, 4)
            row[f"sp_p_{tag}"] = round(sp_p, 6)
            row[f"kt_tau_{tag}"] = round(kt_tau, 4)
            row[f"kt_p_{tag}"] = round(kt_p, 6)
            row[f"coef_{tag}"] = round(m.params.iloc[1], 8)
            row[f"ols_p_{tag}"] = round(m.pvalues.iloc[1], 6)
            row[f"adj_r2_{tag}"] = round(m.rsquared_adj, 4)
            row[f"sign_{tag}"] = "+" if m.params.iloc[1] > 0 else "-"
        rows.append(row)
    result = pd.DataFrame(rows)
    # Add ranks
    for dv in dvs:
        tag = dv.replace("REL_IN_", "")
        result[f"rank_sp_{tag}"] = result[f"sp_rho_{tag}"].abs().rank(ascending=False, method="min").astype(int)
        result[f"rank_r2_{tag}"] = result[f"adj_r2_{tag}"].rank(ascending=False, method="min").astype(int)
    return result


# =========================================================================
# Phase 1B: Candidate multivariable models
# =========================================================================
def compute_vif(X_with_const):
    """VIF for each variable (excluding constant)."""
    vifs = {}
    for i in range(1, X_with_const.shape[1]):
        vifs[X_with_const.columns[i]] = round(
            variance_inflation_factor(X_with_const.values, i), 2
        )
    return vifs


def fit_model(df, dv, ivs):
    """Fit OLS and return comprehensive diagnostics."""
    y = df[dv]
    X = sm.add_constant(df[ivs])
    model = sm.OLS(y, X).fit()
    vifs = compute_vif(X)
    infl = OLSInfluence(model)
    cooks_d = infl.cooks_distance[0]

    # Residual details
    resid_df = pd.DataFrame({
        "state_name": df["state_name"].values,
        "abbrev": df["abbrev"].values,
        "actual": y.values,
        "predicted": model.fittedvalues.values,
        "residual": model.resid.values,
        "cooks_d": cooks_d,
    })

    return {
        "model": model,
        "ivs": list(ivs),
        "n_ivs": len(ivs),
        "adj_r2": round(model.rsquared_adj, 4),
        "r2": round(model.rsquared, 4),
        "aic": round(model.aic, 2),
        "bic": round(model.bic, 2),
        "f_stat": round(model.fvalue, 4),
        "f_p": round(model.f_pvalue, 6),
        "max_vif": max(vifs.values()) if vifs else 0,
        "vifs": vifs,
        "max_cooks_d": round(max(cooks_d), 4),
        "n_influential": int((cooks_d > 4 / len(df)).sum()),
        "resid_df": resid_df,
        "coef_table": model.summary2().tables[1],
    }


def run_candidate_models(df, dv, candidate_ivs, label):
    """Run all 2-IV and 3-IV combinations from the candidate pool."""
    results = []
    # 2-IV models
    for combo in combinations(candidate_ivs, 2):
        r = fit_model(df, dv, list(combo))
        r["model_id"] = f"{label}_2IV_{'+'.join(combo)}"
        r["dv"] = dv
        results.append(r)
    # 3-IV models
    for combo in combinations(candidate_ivs, 3):
        r = fit_model(df, dv, list(combo))
        r["model_id"] = f"{label}_3IV_{'+'.join(combo)}"
        r["dv"] = dv
        results.append(r)
    return results


def make_candidate_table(results):
    """Create a compact comparison table."""
    rows = []
    for r in results:
        rows.append({
            "model_id": r["model_id"],
            "dv": r["dv"],
            "ivs": " + ".join(r["ivs"]),
            "n_ivs": r["n_ivs"],
            "adj_r2": r["adj_r2"],
            "aic": r["aic"],
            "bic": r["bic"],
            "max_vif": r["max_vif"],
            "f_stat": r["f_stat"],
            "f_p": r["f_p"],
            "max_cooks_d": r["max_cooks_d"],
            "n_influential": r["n_influential"],
        })
    return pd.DataFrame(rows).sort_values("adj_r2", ascending=False)


def make_coef_table(result):
    """Extract coefficient details from a fitted model."""
    m = result["model"]
    rows = []
    for term in m.params.index:
        rows.append({
            "model_id": result["model_id"],
            "term": term,
            "coef": round(m.params[term], 6),
            "std_err": round(m.bse[term], 6),
            "t": round(m.tvalues[term], 4),
            "p": round(m.pvalues[term], 6),
            "ci_lower": round(m.conf_int().loc[term, 0], 6),
            "ci_upper": round(m.conf_int().loc[term, 1], 6),
            "vif": result["vifs"].get(term, ""),
        })
    return pd.DataFrame(rows)


# =========================================================================
# Phase 1D: Robustness checks
# =========================================================================
def leave_one_out_check(df, dv, ivs, model_id):
    """Leave-one-out: refit dropping each state, track coefficient stability."""
    full = fit_model(df, dv, ivs)
    full_coefs = {term: full["model"].params[term] for term in ivs}
    rows = []
    for idx in df.index:
        sub = df.drop(idx)
        y = sub[dv]
        X = sm.add_constant(sub[ivs])
        m = sm.OLS(y, X).fit()
        row = {
            "dropped_state": df.loc[idx, "abbrev"],
            "dropped_name": df.loc[idx, "state_name"],
            "adj_r2": round(m.rsquared_adj, 4),
        }
        for term in ivs:
            row[f"coef_{term}"] = round(m.params[term], 6)
            row[f"sign_{term}"] = "+" if m.params[term] > 0 else "-"
        rows.append(row)
    loo_df = pd.DataFrame(rows)

    # Summary: any sign flips?
    sign_flips = {}
    for term in ivs:
        full_sign = "+" if full_coefs[term] > 0 else "-"
        flips = (loo_df[f"sign_{term}"] != full_sign).sum()
        sign_flips[term] = flips

    return loo_df, sign_flips, full["adj_r2"]


def small_state_sensitivity(df, dv, ivs, n_exclude=5):
    """Refit excluding the N smallest states by POP."""
    full = fit_model(df, dv, ivs)
    smallest = df.nsmallest(n_exclude, "POP")
    sub = df.drop(smallest.index)
    reduced = fit_model(sub, dv, ivs)
    return {
        "full_adj_r2": full["adj_r2"],
        "reduced_adj_r2": reduced["adj_r2"],
        "dropped_states": list(smallest["abbrev"]),
        "full_signs": {iv: ("+" if full["model"].params[iv] > 0 else "-") for iv in ivs},
        "reduced_signs": {iv: ("+" if reduced["model"].params[iv] > 0 else "-") for iv in ivs},
    }


# =========================================================================
# Main
# =========================================================================
def main():
    print("=" * 70)
    print("Focused Deep Dive: REL_IN_25_34 and REL_IN_18_24")
    print("=" * 70)

    df = load_data()
    dvs = ["REL_IN_25_34", "REL_IN_18_24"]

    # --- 1A: Screening summary ---
    print("\n--- 1A: Consolidated screening summary ---")
    screen = build_screening_summary(df, dvs)
    screen.to_csv(TABLE_DIR / "screening_summary.csv", index=False)
    print(f"  Saved screening_summary.csv ({len(screen)} IVs)")

    # Print top 5 for each DV
    for dv in dvs:
        tag = dv.replace("REL_IN_", "")
        top5 = screen.nsmallest(5, f"rank_r2_{tag}")
        print(f"\n  Top 5 IVs for {dv} (by adj R²):")
        for _, r in top5.iterrows():
            print(f"    {r['iv']:20s} rho={r[f'sp_rho_{tag}']:+.3f}  adjR2={r[f'adj_r2_{tag}']:.4f}  {r[f'sign_{tag}']}")

    # --- 1B: Candidate models ---
    print("\n--- 1B: Candidate multivariable models ---")

    # Also add PRIV_AVG_PAY as falsification check for 18-24
    cands_18_24_plus = CANDIDATES_18_24 + ["PRIV_AVG_PAY"]

    results_25 = run_candidate_models(df, "REL_IN_25_34", CANDIDATES_25_34, "M25")
    results_18 = run_candidate_models(df, "REL_IN_18_24", cands_18_24_plus, "M18")

    cand_25 = make_candidate_table(results_25)
    cand_18 = make_candidate_table(results_18)
    cand_25.to_csv(TABLE_DIR / "candidates_25_34.csv", index=False)
    cand_18.to_csv(TABLE_DIR / "candidates_18_24.csv", index=False)
    print(f"  25-34: {len(cand_25)} candidates, best adj R² = {cand_25.iloc[0]['adj_r2']:.4f}")
    print(f"  18-24: {len(cand_18)} candidates, best adj R² = {cand_18.iloc[0]['adj_r2']:.4f}")

    # Select top models: best 2-IV and best 3-IV for each, with VIF < 10
    selected = {}
    for dv, cand, results, label in [
        ("REL_IN_25_34", cand_25, results_25, "25_34"),
        ("REL_IN_18_24", cand_18, results_18, "18_24"),
    ]:
        viable = cand[cand["max_vif"] < 10].copy()
        best_2 = viable[viable["n_ivs"] == 2].head(1)
        best_3 = viable[viable["n_ivs"] == 3].head(1)
        picks = pd.concat([best_2, best_3])
        selected[label] = []
        for _, p in picks.iterrows():
            mid = p["model_id"]
            match = [r for r in results if r["model_id"] == mid][0]
            selected[label].append(match)
        print(f"\n  Selected for {dv}:")
        for m in selected[label]:
            print(f"    {m['model_id']}: adjR2={m['adj_r2']}, VIF={m['max_vif']}, AIC={m['aic']}")

    # Save selected model details
    all_coefs = []
    all_resids = []
    for label in ["25_34", "18_24"]:
        for m in selected[label]:
            ct = make_coef_table(m)
            all_coefs.append(ct)
            rd = m["resid_df"].copy()
            rd["model_id"] = m["model_id"]
            all_resids.append(rd)

    coef_df = pd.concat(all_coefs, ignore_index=True)
    resid_df = pd.concat(all_resids, ignore_index=True)
    coef_df.to_csv(TABLE_DIR / "selected_coefficients.csv", index=False)
    resid_df.to_csv(TABLE_DIR / "selected_residuals.csv", index=False)

    # Selected models summary
    sel_rows = []
    for label in ["25_34", "18_24"]:
        for m in selected[label]:
            sel_rows.append({
                "dv": f"REL_IN_{label}",
                "model_id": m["model_id"],
                "ivs": " + ".join(m["ivs"]),
                "n_ivs": m["n_ivs"],
                "adj_r2": m["adj_r2"],
                "aic": m["aic"],
                "bic": m["bic"],
                "max_vif": m["max_vif"],
                "max_cooks_d": m["max_cooks_d"],
                "n_influential": m["n_influential"],
            })
    sel_df = pd.DataFrame(sel_rows)
    sel_df.to_csv(TABLE_DIR / "selected_models.csv", index=False)
    print("\n  Selected models:")
    print(sel_df.to_string(index=False))

    # --- 1C: "What changes when adding controls" ---
    print("\n--- 1C: Control-addition tables ---")
    for label in ["25_34", "18_24"]:
        dv = f"REL_IN_{label}"
        models = selected[label]
        if len(models) >= 2:
            m2, m3 = models[0], models[1]
            print(f"\n  {dv}: 2-IV → 3-IV comparison")
            print(f"    2-IV ({' + '.join(m2['ivs'])}): adjR2={m2['adj_r2']}")
            print(f"    3-IV ({' + '.join(m3['ivs'])}): adjR2={m3['adj_r2']}")
            # Show coefficient changes for shared IVs
            shared = set(m2["ivs"]) & set(m3["ivs"])
            for iv in shared:
                c2 = m2["model"].params[iv]
                c3 = m3["model"].params[iv]
                pct_change = ((c3 - c2) / abs(c2) * 100) if c2 != 0 else float("inf")
                print(f"    {iv}: {c2:+.6f} → {c3:+.6f} ({pct_change:+.1f}%)")

    # --- 1D: Robustness ---
    print("\n--- 1D: Robustness checks ---")
    rob_rows = []
    for label in ["25_34", "18_24"]:
        dv = f"REL_IN_{label}"
        for m in selected[label]:
            # Leave-one-out
            loo_df, sign_flips, full_r2 = leave_one_out_check(df, dv, m["ivs"], m["model_id"])
            loo_df.to_csv(TABLE_DIR / f"loo_{m['model_id']}.csv", index=False)

            # Small-state sensitivity
            ss = small_state_sensitivity(df, dv, m["ivs"])

            # Sign flips
            any_flip = any(v > 0 for v in sign_flips.values())
            flip_detail = "; ".join(f"{k}:{v}" for k, v in sign_flips.items() if v > 0)

            rob_rows.append({
                "model_id": m["model_id"],
                "dv": dv,
                "full_adj_r2": full_r2,
                "loo_adj_r2_min": round(loo_df["adj_r2"].min(), 4),
                "loo_adj_r2_max": round(loo_df["adj_r2"].max(), 4),
                "sign_flips": flip_detail if any_flip else "none",
                "small_state_adj_r2": ss["reduced_adj_r2"],
                "small_state_dropped": ", ".join(ss["dropped_states"]),
                "small_state_signs_stable": all(
                    ss["full_signs"][iv] == ss["reduced_signs"][iv] for iv in m["ivs"]
                ),
            })
            print(f"\n  {m['model_id']}:")
            print(f"    LOO adj R² range: [{loo_df['adj_r2'].min():.4f}, {loo_df['adj_r2'].max():.4f}]")
            print(f"    Sign flips: {flip_detail if any_flip else 'none'}")
            print(f"    Small-state (drop {ss['dropped_states']}): adj R² {ss['reduced_adj_r2']:.4f}, signs stable: {rob_rows[-1]['small_state_signs_stable']}")

    rob_df = pd.DataFrame(rob_rows)
    rob_df.to_csv(TABLE_DIR / "robustness_summary.csv", index=False)

    # --- Print top/bottom residual states ---
    print("\n--- Top residual states (selected models) ---")
    for label in ["25_34", "18_24"]:
        for m in selected[label]:
            rd = m["resid_df"].sort_values("residual", ascending=False)
            print(f"\n  {m['model_id']} — model under-predicts (positive residual):")
            for _, r in rd.head(3).iterrows():
                print(f"    {r['abbrev']:3s} actual={r['actual']:.4f} pred={r['predicted']:.4f} resid={r['residual']:+.4f}")
            print(f"  {m['model_id']} — model over-predicts (negative residual):")
            for _, r in rd.tail(3).iterrows():
                print(f"    {r['abbrev']:3s} actual={r['actual']:.4f} pred={r['predicted']:.4f} resid={r['residual']:+.4f}")

    print("\n" + "=" * 70)
    print("Statistical analysis complete.")
    for f in sorted(TABLE_DIR.glob("*.csv")):
        print(f"  {f.relative_to(PROJECT)}")
    print("=" * 70)

    # Return selected models for use by viz script
    return selected


if __name__ == "__main__":
    main()
