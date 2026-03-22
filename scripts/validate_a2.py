"""Post-pipeline validation for Phase A2.

Run AFTER scripts/build_dataset.py to verify the outputs.
Reports: row count, state coverage, column completeness, nulls, duplicates.

Usage:  python -m scripts.validate_a2
"""

import sys
import pandas as pd
from src.constants import STATE_FIPS, AGE_GROUPS

ANALYSIS_PATH = "data_processed/analysis_ready.csv"

# Expected DV columns (8 per age group)
DV_PREFIXES = ["IN_COUNT_", "OUT_COUNT_", "POP_AGE_", "NET_COUNT_",
               "IN_RATE_", "OUT_RATE_", "NET_RATE_"]
EXPECTED_DV_COLS = ["state"] + [
    f"{prefix}{ag}" for ag in AGE_GROUPS for prefix in DV_PREFIXES
]

# Expected IV columns (22 total: 18 core + 4 newly added)
EXPECTED_IV_COLS = [
    "POP", "LAND_AREA", "POP_DENS", "GDP", "RPP", "REAL_PCPI",
    "UNEMP", "PRIV_EMP", "PRIV_ESTAB", "PRIV_AVG_PAY", "PERMITS",
    "MED_RENT", "MED_HOMEVAL", "COST_BURDEN_ALL", "VACANCY_RATE",
    "COMMUTE_MED", "TRANSIT_SHARE", "BA_PLUS",
    "UNINSURED", "ELEC_PRICE_TOT",
    "CRIME_VIOLENT_RATE", "NRI_RISK_INDEX",
]

EXCLUDED_FIPS = {"11", "72"}  # DC, PR
VALID_FIPS = set(STATE_FIPS.keys())


def section(title):
    print(f"\n{'─'*60}")
    print(f"  {title}")
    print(f"{'─'*60}")


def main():
    all_ok = True

    # ── 1. File exists ────────────────────────────────────────────
    section("1. Check output file exists")
    try:
        df = pd.read_csv(ANALYSIS_PATH)
        print(f"  OK: {ANALYSIS_PATH} loaded")
    except FileNotFoundError:
        print(f"  FAIL: {ANALYSIS_PATH} not found. Run build_dataset first.")
        sys.exit(1)

    # ── 2. Row count ──────────────────────────────────────────────
    section("2. Row count")
    n_rows = len(df)
    print(f"  Rows: {n_rows}")
    if n_rows == 50:
        print("  OK: exactly 50 rows")
    else:
        print(f"  FAIL: expected 50, got {n_rows}")
        all_ok = False

    # ── 3. State FIPS validation ──────────────────────────────────
    section("3. State FIPS validation")
    states_in_data = set(df["state"].astype(str).str.zfill(2))

    # Check for excluded geographies
    excluded_present = states_in_data & EXCLUDED_FIPS
    if excluded_present:
        print(f"  FAIL: DC/PR found in data: {excluded_present}")
        all_ok = False
    else:
        print("  OK: DC (11) and PR (72) absent")

    # Check coverage
    missing_states = VALID_FIPS - states_in_data
    extra_states = states_in_data - VALID_FIPS
    if missing_states:
        print(f"  FAIL: missing states: {sorted(missing_states)}")
        all_ok = False
    else:
        print("  OK: all 50 states present")
    if extra_states:
        print(f"  FAIL: unexpected FIPS codes: {sorted(extra_states)}")
        all_ok = False

    # ── 4. Duplicate rows ─────────────────────────────────────────
    section("4. Duplicate check")
    dup_count = df["state"].duplicated().sum()
    if dup_count > 0:
        print(f"  FAIL: {dup_count} duplicate state rows")
        dups = df[df["state"].duplicated(keep=False)]["state"].unique()
        print(f"  Duplicate FIPS: {sorted(dups)}")
        all_ok = False
    else:
        print("  OK: no duplicate state rows")

    # ── 5. Column presence ────────────────────────────────────────
    section("5. Column presence")
    actual_cols = set(df.columns)

    print(f"  Total columns: {len(df.columns)}")
    print(f"\n  Full column list:")
    for i, c in enumerate(df.columns):
        print(f"    {i+1:3d}. {c}")

    # Check DVs
    missing_dvs = [c for c in EXPECTED_DV_COLS if c not in actual_cols]
    if missing_dvs:
        print(f"\n  FAIL: missing DV columns ({len(missing_dvs)}):")
        for c in missing_dvs:
            print(f"    - {c}")
        all_ok = False
    else:
        print(f"\n  OK: all {len(EXPECTED_DV_COLS)} DV columns present")

    # Check IVs
    missing_ivs = [c for c in EXPECTED_IV_COLS if c not in actual_cols]
    present_ivs = [c for c in EXPECTED_IV_COLS if c in actual_cols]
    if missing_ivs:
        print(f"  WARNING: missing IV columns ({len(missing_ivs)}):")
        for c in missing_ivs:
            print(f"    - {c}")
        all_ok = False
    else:
        print(f"  OK: all {len(EXPECTED_IV_COLS)} core IV columns present")
    print(f"  Present IVs: {len(present_ivs)}/{len(EXPECTED_IV_COLS)}")

    # ── 6. Missing values ─────────────────────────────────────────
    section("6. Missing values by column")
    null_report = df.isnull().sum()
    any_missing = False
    for col in df.columns:
        n_null = null_report[col]
        if n_null > 0:
            print(f"  {col}: {n_null}/{n_rows} missing")
            any_missing = True
    if not any_missing:
        print("  OK: no missing values in any column")

    # ── 7. Basic sanity checks ────────────────────────────────────
    section("7. Basic sanity checks")

    # POP should be positive and > 500k for all states
    if "POP" in actual_cols:
        min_pop = df["POP"].min()
        max_pop = df["POP"].max()
        print(f"  POP range: {min_pop:,.0f} – {max_pop:,.0f}")
        if min_pop < 100000:
            print("  WARNING: unusually low POP value")

    # NET_RATE should be in plausible range (-100 to +100 per 1000)
    for ag in AGE_GROUPS:
        col = f"NET_RATE_{ag}"
        if col in actual_cols:
            vmin, vmax = df[col].min(), df[col].max()
            if vmin < -200 or vmax > 200:
                print(f"  WARNING: {col} range [{vmin:.1f}, {vmax:.1f}] seems extreme")

    # GDP should be positive
    if "GDP" in actual_cols:
        min_gdp = df["GDP"].min()
        print(f"  GDP min: {min_gdp:,.0f}")
        if min_gdp <= 0:
            print("  WARNING: non-positive GDP value")

    # COMMUTE_MED should be 5-60 minutes
    if "COMMUTE_MED" in actual_cols:
        vmin, vmax = df["COMMUTE_MED"].min(), df["COMMUTE_MED"].max()
        print(f"  COMMUTE_MED range: {vmin:.1f} – {vmax:.1f} min")
        if vmin < 5 or vmax > 60:
            print("  WARNING: COMMUTE_MED out of expected 5–60 min range")

    # UNINSURED should be 2-25%
    if "UNINSURED" in actual_cols:
        vmin, vmax = df["UNINSURED"].min(), df["UNINSURED"].max()
        print(f"  UNINSURED range: {vmin:.1f} – {vmax:.1f}%")
        if vmin < 1 or vmax > 30:
            print("  WARNING: UNINSURED out of expected 1–30% range")

    # CRIME_VIOLENT_RATE should be 50-800 per 100k
    if "CRIME_VIOLENT_RATE" in actual_cols:
        vmin, vmax = df["CRIME_VIOLENT_RATE"].min(), df["CRIME_VIOLENT_RATE"].max()
        print(f"  CRIME_VIOLENT_RATE range: {vmin:.1f} – {vmax:.1f} per 100k")
        if vmin < 30 or vmax > 1000:
            print("  WARNING: CRIME_VIOLENT_RATE out of expected 30–1000 range")

    # NRI_RISK_INDEX should be 0-100
    if "NRI_RISK_INDEX" in actual_cols:
        vmin, vmax = df["NRI_RISK_INDEX"].min(), df["NRI_RISK_INDEX"].max()
        print(f"  NRI_RISK_INDEX range: {vmin:.1f} – {vmax:.1f}")
        if vmin < 0 or vmax > 100:
            print("  WARNING: NRI_RISK_INDEX out of expected 0–100 range")

    # ── 8. List output files ──────────────────────────────────────
    section("8. Output files")
    import os
    for dirpath in ["data_raw", "data_interim", "data_processed", "outputs/logs"]:
        if os.path.exists(dirpath):
            files = sorted(os.listdir(dirpath))
            csv_files = [f for f in files if f.endswith((".csv", ".log"))]
            if csv_files:
                print(f"  {dirpath}/")
                for f in csv_files:
                    fpath = os.path.join(dirpath, f)
                    size = os.path.getsize(fpath)
                    print(f"    {f} ({size:,} bytes)")

    # ── Summary ───────────────────────────────────────────────────
    section("VALIDATION SUMMARY")
    if all_ok:
        print("  ALL CHECKS PASSED")
    else:
        print("  SOME CHECKS FAILED — review output above")

    return all_ok


if __name__ == "__main__":
    ok = main()
    sys.exit(0 if ok else 1)
