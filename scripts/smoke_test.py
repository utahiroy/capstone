#!/usr/bin/env python3
"""Smoke test: fetch migration DVs and a small IV subset for 3 states.

Usage:
    python -m scripts.smoke_test

Outputs are saved to smoke_test_outputs/.
"""

import sys
import os
from pathlib import Path

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
from src.config_loader import load_api_keys
from src.fetch_census import fetch_all_migration_data, fetch_acs_variables
from src.fetch_bea import fetch_gdp
from src.build_variables import build_migration_dvs, build_cost_burden
from src.constants import (
    STATE_FIPS, AGE_GROUPS,
    COST_BURDEN_RENTER_TOTAL, COST_BURDEN_RENTER_BURDENED,
    COST_BURDEN_OWNER_TOTAL, COST_BURDEN_OWNER_BURDENED,
)

# ── Configuration ────────────────────────────────────────────────────────────
# Smoke test uses 3 states: California, Texas, New York
SMOKE_STATES = ["06", "48", "36"]
SMOKE_STATE_NAMES = {f: STATE_FIPS[f] for f in SMOKE_STATES}
OUTPUT_DIR = PROJECT_ROOT / "smoke_test_outputs"

# ── Helpers ──────────────────────────────────────────────────────────────────

def section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def validate_no_nulls(df, label):
    nulls = df.isnull().sum()
    bad = nulls[nulls > 0]
    if len(bad) > 0:
        print(f"  WARNING: {label} has nulls:\n{bad}")
        return False
    print(f"  OK: {label} — no nulls ({len(df)} rows)")
    return True


def validate_positive(df, cols, label):
    for col in cols:
        if (df[col] <= 0).any():
            print(f"  WARNING: {label}.{col} has non-positive values")
            return False
    print(f"  OK: {label} — all values positive for {len(cols)} columns")
    return True


def validate_rate_range(df, cols, label, lo=-200, hi=200):
    for col in cols:
        mn, mx = df[col].min(), df[col].max()
        if mn < lo or mx > hi:
            print(f"  WARNING: {label}.{col} range [{mn:.1f}, {mx:.1f}] outside [{lo}, {hi}]")
            return False
    print(f"  OK: {label} — rates in plausible range")
    return True


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    all_ok = True

    # Load keys
    section("Loading API keys")
    keys = load_api_keys()
    census_key = keys["CENSUS_API_KEY"]
    bea_key = keys["BEA_API_KEY"]

    if not census_key:
        print("ERROR: CENSUS_API_KEY is empty. Set it in config/api_keys.py")
        sys.exit(1)

    print(f"  Census key: {'*' * 8}...{census_key[-4:]}")
    print(f"  BEA key:    {'*' * 8}...{bea_key[-4:]}" if bea_key else "  BEA key:    (empty — GDP fetch will be skipped)")
    print(f"  Smoke states: {SMOKE_STATE_NAMES}")

    # ── 1. Migration DVs ─────────────────────────────────────────────────
    section("Fetching ACS migration data (B07001 + B07401 + B01001)")
    df_in, df_out, df_pop = fetch_all_migration_data(census_key, SMOKE_STATES)
    print(f"  B07001 (in):  {df_in.shape}")
    print(f"  B07401 (out): {df_out.shape}")
    print(f"  B01001 (pop): {df_pop.shape}")

    section("Building migration DVs")
    dvs = build_migration_dvs(df_in, df_out, df_pop)
    dvs.insert(1, "state_name", dvs["state"].map(STATE_FIPS))
    print(dvs.to_string(index=False))

    # Validate
    section("Validating migration DVs")
    all_ok &= validate_no_nulls(dvs, "migration DVs")
    pop_cols = [f"POP_AGE_{ag}" for ag in AGE_GROUPS]
    in_cols = [f"IN_COUNT_{ag}" for ag in AGE_GROUPS]
    all_ok &= validate_positive(dvs, pop_cols, "POP_AGE")
    all_ok &= validate_positive(dvs, in_cols, "IN_COUNT")
    rate_cols = [f"NET_RATE_{ag}" for ag in AGE_GROUPS]
    all_ok &= validate_rate_range(dvs, rate_cols, "NET_RATE")

    # Sanity: NET_COUNT = IN - OUT
    for ag in AGE_GROUPS:
        expected = dvs[f"IN_COUNT_{ag}"] - dvs[f"OUT_COUNT_{ag}"]
        if not (dvs[f"NET_COUNT_{ag}"] == expected).all():
            print(f"  FAIL: NET_COUNT_{ag} != IN - OUT")
            all_ok = False
    if all_ok:
        print("  OK: NET_COUNT = IN_COUNT - OUT_COUNT for all age groups")

    # Sanity: NET_RATE = 1000 * NET_COUNT / POP_AGE
    for ag in AGE_GROUPS:
        expected = 1000 * dvs[f"NET_COUNT_{ag}"] / dvs[f"POP_AGE_{ag}"]
        diff = (dvs[f"NET_RATE_{ag}"] - expected).abs().max()
        if diff > 1e-10:
            print(f"  FAIL: NET_RATE_{ag} formula mismatch (max diff={diff})")
            all_ok = False
    if all_ok:
        print("  OK: NET_RATE = 1000 * NET_COUNT / POP_AGE for all age groups")

    dvs.to_csv(OUTPUT_DIR / "smoke_migration_dvs.csv", index=False)
    print(f"\n  Saved: smoke_migration_dvs.csv")

    # ── 2. IV: MED_RENT ──────────────────────────────────────────────────
    section("Fetching MED_RENT (B25064_001E)")
    df_rent = fetch_acs_variables(["B25064_001E"], census_key, SMOKE_STATES)
    df_rent = df_rent.rename(columns={"B25064_001E": "MED_RENT"})
    print(df_rent[["state", "MED_RENT"]].to_string(index=False))
    all_ok &= validate_no_nulls(df_rent[["MED_RENT"]], "MED_RENT")

    # ── 3. IV: COST_BURDEN_ALL ───────────────────────────────────────────
    section("Fetching COST_BURDEN_ALL (B25070 + B25091)")
    burden_vars = (
        [COST_BURDEN_RENTER_TOTAL] + COST_BURDEN_RENTER_BURDENED +
        [COST_BURDEN_OWNER_TOTAL] + COST_BURDEN_OWNER_BURDENED
    )
    df_burden = fetch_acs_variables(burden_vars, census_key, SMOKE_STATES)
    df_burden["COST_BURDEN_ALL"] = build_cost_burden(df_burden)
    print(df_burden[["state", "COST_BURDEN_ALL"]].to_string(index=False))
    all_ok &= validate_no_nulls(df_burden[["COST_BURDEN_ALL"]], "COST_BURDEN_ALL")

    # ── 4. IV: POP (Census API — use B01001_001E as proxy) ───────────────
    section("Fetching POP (B01001_001E total population)")
    df_pop_total = fetch_acs_variables(["B01001_001E"], census_key, SMOKE_STATES)
    df_pop_total = df_pop_total.rename(columns={"B01001_001E": "POP"})
    print(df_pop_total[["state", "POP"]].to_string(index=False))
    all_ok &= validate_positive(df_pop_total, ["POP"], "POP")

    # ── 5. IV: GDP (BEA) ────────────────────────────────────────────────
    if bea_key:
        section("Fetching GDP (BEA SAGDP2N)")
        try:
            df_gdp = fetch_gdp(bea_key)
            df_gdp = df_gdp[df_gdp["state"].isin(SMOKE_STATES)].copy()
            print(df_gdp[["state", "GeoName", "GDP"]].to_string(index=False))
            all_ok &= validate_no_nulls(df_gdp[["GDP"]], "GDP")
        except Exception as e:
            print(f"  ERROR fetching GDP: {e}")
            df_gdp = pd.DataFrame(columns=["state", "GeoName", "GDP"])
            all_ok = False
    else:
        section("Skipping GDP (no BEA_API_KEY)")
        df_gdp = pd.DataFrame(columns=["state", "GeoName", "GDP"])

    # ── 6. Join smoke IVs ────────────────────────────────────────────────
    section("Joining smoke-test IVs")
    ivs = df_pop_total[["state", "POP"]].copy()
    ivs = ivs.merge(df_rent[["state", "MED_RENT"]], on="state", how="left")
    ivs = ivs.merge(
        df_burden[["state", "COST_BURDEN_ALL"]], on="state", how="left"
    )
    if not df_gdp.empty:
        ivs = ivs.merge(df_gdp[["state", "GDP"]], on="state", how="left")
    else:
        ivs["GDP"] = None

    ivs.insert(1, "state_name", ivs["state"].map(STATE_FIPS))
    print(ivs.to_string(index=False))
    ivs.to_csv(OUTPUT_DIR / "smoke_ivs.csv", index=False)
    print(f"\n  Saved: smoke_ivs.csv")

    # ── 7. Combined output ───────────────────────────────────────────────
    section("Creating combined smoke-test table")
    combined = dvs.merge(ivs.drop(columns=["state_name"]), on="state", how="left")
    combined.to_csv(OUTPUT_DIR / "smoke_combined.csv", index=False)
    print(f"  Saved: smoke_combined.csv ({combined.shape[0]} rows, {combined.shape[1]} cols)")

    # ── Summary ──────────────────────────────────────────────────────────
    section("SMOKE TEST SUMMARY")
    if all_ok:
        print("  ALL CHECKS PASSED")
    else:
        print("  SOME CHECKS FAILED — review warnings above")
    print(f"\n  Output files in: {OUTPUT_DIR}/")
    for f in sorted(OUTPUT_DIR.glob("smoke_*.csv")):
        print(f"    {f.name}")

    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
