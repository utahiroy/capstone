"""Phase A2: Full 50-state dataset build.

Ingests all migration DVs and core IVs, joins into analysis-ready table.
Saves raw, interim, and processed outputs.

Run:  python -m scripts.build_dataset
"""

import os
import sys
import datetime
import traceback

import pandas as pd

# ── Imports ───────────────────────────────────────────────────────────

from src.config_loader import load_api_keys
from src.constants import STATE_FIPS, AGE_GROUPS, ACS_SIMPLE_VARS
from src.constants import (
    COST_BURDEN_RENTER_TOTAL, COST_BURDEN_RENTER_BURDENED,
    COST_BURDEN_OWNER_TOTAL, COST_BURDEN_OWNER_BURDENED,
    VACANCY_FOR_RENT, VACANCY_RENTED_NOT_OCC, OCCUPIED_RENTER,
    TRANSIT_WORKERS_TOTAL, TRANSIT_PUBLIC,
    BA_PLUS_TOTAL, BA_PLUS_BACHELORS, BA_PLUS_MASTERS,
    BA_PLUS_PROFESSIONAL, BA_PLUS_DOCTORATE,
)
from src.fetch_census import (
    fetch_acs_variables,
    fetch_all_migration_data,
)
from src.fetch_bea import fetch_gdp, fetch_rpp, fetch_real_pcpi
from src.fetch_bls import fetch_unemployment, fetch_qcew
from src.fetch_eia import fetch_electricity_price
from src.fetch_permits import fetch_permits
from src.fetch_land_area import fetch_land_area
from src.build_variables import (
    build_migration_dvs,
    build_cost_burden,
    build_vacancy_rate,
    build_transit_share,
    build_ba_plus,
    build_pop_density,
)


# ── Helpers ───────────────────────────────────────────────────────────

ALL_STATES = sorted(STATE_FIPS.keys())
TIMESTAMP = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")


def ensure_dirs():
    for d in [
        "data_raw", "data_interim", "data_processed",
        "outputs/tables", "outputs/figures", "outputs/logs",
    ]:
        os.makedirs(d, exist_ok=True)


def normalize_state_col(df):
    """Ensure 'state' column is 2-digit zero-padded string, no duplicates."""
    df["state"] = df["state"].astype(str).str.strip().str.replace(r"\.0$", "", regex=True).str.zfill(2)
    # Filter to 50 states only
    df = df[df["state"].isin(STATE_FIPS.keys())].copy()
    # Drop duplicate state rows (keep first)
    if df["state"].duplicated().any():
        print(f"  WARNING: dropping {df['state'].duplicated().sum()} duplicate state rows")
        df = df.drop_duplicates(subset=["state"], keep="first")
    return df


def assert_50_rows(df, label):
    """Fail fast if a DataFrame does not have exactly 50 state rows."""
    n = len(df)
    if n != 50:
        raise ValueError(
            f"ASSERTION FAILED: {label} has {n} rows, expected 50. "
            f"States present: {sorted(df['state'].unique())}"
        )


def safe_merge(left, right, label):
    """Left-merge on 'state' with row-count assertion."""
    n_before = len(left)
    result = left.merge(right, on="state", how="left")
    if len(result) != n_before:
        raise ValueError(
            f"MERGE EXPANSION: {label} merge changed row count "
            f"from {n_before} to {len(result)}. "
            f"Right-side likely has duplicate state keys."
        )
    return result


def section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def save_raw(df, name):
    path = f"data_raw/{name}.csv"
    df.to_csv(path, index=False)
    print(f"  Saved raw: {path} ({len(df)} rows, {len(df.columns)} cols)")


def save_interim(df, name):
    path = f"data_interim/{name}.csv"
    df.to_csv(path, index=False)
    print(f"  Saved interim: {path} ({len(df)} rows, {len(df.columns)} cols)")


def save_processed(df, name):
    path = f"data_processed/{name}.csv"
    df.to_csv(path, index=False)
    print(f"  Saved processed: {path} ({len(df)} rows, {len(df.columns)} cols)")


# ── Main pipeline ─────────────────────────────────────────────────────

def main():
    ensure_dirs()
    log_lines = []
    failed_vars = []
    completed_vars = []

    def log(msg):
        print(msg)
        log_lines.append(msg)

    log(f"Phase A2 pipeline started at {TIMESTAMP}")
    log(f"Target: 50 states, 2024 cross-section")

    # ── 0. Load API keys ──────────────────────────────────────────────
    section("Loading API keys")
    keys = load_api_keys()
    census_key = keys["CENSUS_API_KEY"]
    bea_key = keys["BEA_API_KEY"]
    eia_key = keys.get("EIA_API_KEY", "")

    if not census_key:
        log("FATAL: CENSUS_API_KEY is empty. Cannot proceed.")
        sys.exit(1)

    log(f"  Census key: {'*' * 8}...{census_key[-4:]}")
    log(f"  BEA key:    {'*' * 8}...{bea_key[-4:]}" if bea_key else "  BEA key: (empty)")
    log(f"  EIA key:    {'*' * 8}...{eia_key[-4:]}" if eia_key else "  EIA key: (empty)")

    # ── 1. Migration DVs (ACS) ────────────────────────────────────────
    section("1. Fetching migration data (ACS B07001, B07401, B01001)")
    df_in, df_out, df_pop = fetch_all_migration_data(census_key, ALL_STATES)
    save_raw(df_in, "acs_b07001_in_migration")
    save_raw(df_out, "acs_b07401_out_migration")
    save_raw(df_pop, "acs_b01001_population_by_age")

    log("  Building migration DVs...")
    df_dvs = build_migration_dvs(df_in, df_out, df_pop)
    df_dvs = normalize_state_col(df_dvs)
    save_interim(df_dvs, "migration_dvs")
    assert_50_rows(df_dvs, "migration_dvs")
    log(f"  Migration DVs: {len(df_dvs)} states, {len(df_dvs.columns)} columns")
    completed_vars.append("Migration DVs (all 5 age groups)")

    # ── 2. ACS simple IVs ─────────────────────────────────────────────
    section("2. Fetching ACS simple IVs (POP, MED_RENT, MED_HOMEVAL)")
    acs_simple_codes = list(ACS_SIMPLE_VARS.values())
    df_acs_simple = fetch_acs_variables(acs_simple_codes, census_key, ALL_STATES)
    save_raw(df_acs_simple, "acs_simple_ivs_raw")

    # Rename to friendly names
    rename_map = {v: k for k, v in ACS_SIMPLE_VARS.items()}
    df_acs_simple = df_acs_simple.rename(columns=rename_map)
    df_acs_simple = normalize_state_col(df_acs_simple)
    assert_50_rows(df_acs_simple, "acs_simple_ivs")
    log(f"  ACS simple IVs: {list(ACS_SIMPLE_VARS.keys())}")
    completed_vars.extend(["POP", "MED_RENT", "MED_HOMEVAL"])

    # ── 3. COST_BURDEN_ALL (ACS B25070 + B25091) ─────────────────────
    section("3. Fetching cost burden components (ACS B25070 + B25091)")
    burden_vars = (
        [COST_BURDEN_RENTER_TOTAL] + COST_BURDEN_RENTER_BURDENED
        + [COST_BURDEN_OWNER_TOTAL] + COST_BURDEN_OWNER_BURDENED
    )
    df_burden = fetch_acs_variables(burden_vars, census_key, ALL_STATES)
    save_raw(df_burden, "acs_cost_burden_raw")
    cost_burden = build_cost_burden(df_burden)
    df_acs_simple["COST_BURDEN_ALL"] = cost_burden.values
    log(f"  COST_BURDEN_ALL computed")
    completed_vars.append("COST_BURDEN_ALL")

    # ── 4. VACANCY_RATE (ACS B25004 + B25003) ────────────────────────
    section("4. Fetching vacancy rate components (ACS B25004 + B25003)")
    vacancy_vars = [VACANCY_FOR_RENT, VACANCY_RENTED_NOT_OCC, OCCUPIED_RENTER]
    df_vacancy = fetch_acs_variables(vacancy_vars, census_key, ALL_STATES)
    save_raw(df_vacancy, "acs_vacancy_raw")
    vacancy_rate = build_vacancy_rate(df_vacancy)
    df_acs_simple["VACANCY_RATE"] = vacancy_rate.values
    log(f"  VACANCY_RATE computed")
    completed_vars.append("VACANCY_RATE")

    # ── 5. TRANSIT_SHARE (ACS B08301) ─────────────────────────────────
    section("5. Fetching transit share components (ACS B08301)")
    transit_vars = [TRANSIT_WORKERS_TOTAL, TRANSIT_PUBLIC]
    df_transit = fetch_acs_variables(transit_vars, census_key, ALL_STATES)
    save_raw(df_transit, "acs_transit_raw")
    transit_share = build_transit_share(df_transit)
    df_acs_simple["TRANSIT_SHARE"] = transit_share.values
    log(f"  TRANSIT_SHARE computed")
    completed_vars.append("TRANSIT_SHARE")

    # ── 6. BA_PLUS (ACS B15003) ───────────────────────────────────────
    section("6. Fetching education components (ACS B15003)")
    ba_vars = [BA_PLUS_TOTAL, BA_PLUS_BACHELORS, BA_PLUS_MASTERS,
               BA_PLUS_PROFESSIONAL, BA_PLUS_DOCTORATE]
    df_ba = fetch_acs_variables(ba_vars, census_key, ALL_STATES)
    save_raw(df_ba, "acs_education_raw")
    ba_plus = build_ba_plus(df_ba)
    df_acs_simple["BA_PLUS"] = ba_plus.values
    log(f"  BA_PLUS computed")
    completed_vars.append("BA_PLUS")

    save_interim(df_acs_simple, "acs_ivs_all")

    # ── 7. LAND_AREA ─────────────────────────────────────────────────
    section("7. Fetching land area (Census reference)")
    try:
        df_land = fetch_land_area()
        save_raw(df_land, "land_area")
        completed_vars.append("LAND_AREA")
        log(f"  LAND_AREA: {len(df_land)} states")
    except Exception as e:
        log(f"  ERROR: LAND_AREA failed: {e}")
        traceback.print_exc()
        df_land = None
        failed_vars.append("LAND_AREA")

    # ── 8. GDP (BEA) ─────────────────────────────────────────────────
    section("8. Fetching GDP (BEA)")
    df_gdp = None
    if bea_key:
        try:
            df_gdp = fetch_gdp(bea_key)
            save_raw(df_gdp, "bea_gdp")
            completed_vars.append("GDP")
            log(f"  GDP: {len(df_gdp)} states")
        except Exception as e:
            log(f"  ERROR: GDP failed: {e}")
            traceback.print_exc()
            failed_vars.append("GDP")
    else:
        log("  SKIPPED: No BEA_API_KEY")
        failed_vars.append("GDP (no key)")

    # ── 9. RPP (BEA) ─────────────────────────────────────────────────
    section("9. Fetching RPP (BEA)")
    df_rpp = None
    if bea_key:
        try:
            df_rpp = fetch_rpp(bea_key)
            save_raw(df_rpp, "bea_rpp")
            completed_vars.append("RPP")
            log(f"  RPP: {len(df_rpp)} states")
        except Exception as e:
            log(f"  ERROR: RPP failed: {e}")
            traceback.print_exc()
            failed_vars.append("RPP")
    else:
        log("  SKIPPED: No BEA_API_KEY")
        failed_vars.append("RPP (no key)")

    # ── 10. REAL_PCPI (BEA) ──────────────────────────────────────────
    section("10. Fetching REAL_PCPI (BEA)")
    df_pcpi = None
    if bea_key:
        try:
            df_pcpi = fetch_real_pcpi(bea_key)
            save_raw(df_pcpi, "bea_real_pcpi")
            completed_vars.append("REAL_PCPI")
            log(f"  REAL_PCPI: {len(df_pcpi)} states")
        except Exception as e:
            log(f"  ERROR: REAL_PCPI failed: {e}")
            traceback.print_exc()
            failed_vars.append("REAL_PCPI")
    else:
        log("  SKIPPED: No BEA_API_KEY")
        failed_vars.append("REAL_PCPI (no key)")

    # ── 11. UNEMP (BLS LAUS) ─────────────────────────────────────────
    section("11. Fetching unemployment (BLS LAUS)")
    df_unemp = None
    try:
        df_unemp = fetch_unemployment()
        save_raw(df_unemp, "bls_laus_unemployment")
        completed_vars.append("UNEMP")
        log(f"  UNEMP: {len(df_unemp)} states")
    except Exception as e:
        log(f"  ERROR: UNEMP failed: {e}")
        traceback.print_exc()
        failed_vars.append("UNEMP")

    # ── 12. QCEW (BLS) ───────────────────────────────────────────────
    section("12. Fetching QCEW (BLS)")
    df_qcew = None
    try:
        df_qcew = fetch_qcew()
        save_raw(df_qcew, "bls_qcew")
        completed_vars.extend(["PRIV_EMP", "PRIV_ESTAB", "PRIV_AVG_PAY"])
        log(f"  QCEW: {len(df_qcew)} states, cols: {list(df_qcew.columns)}")
    except Exception as e:
        log(f"  ERROR: QCEW failed: {e}")
        traceback.print_exc()
        failed_vars.extend(["PRIV_EMP", "PRIV_ESTAB", "PRIV_AVG_PAY"])

    # ── 13. PERMITS (Census BPS) ──────────────────────────────────────
    section("13. Fetching building permits (Census BPS)")
    df_permits = None
    try:
        df_permits = fetch_permits()
        save_raw(df_permits, "census_bps_permits")
        completed_vars.append("PERMITS")
        log(f"  PERMITS: {len(df_permits)} states")
    except Exception as e:
        log(f"  ERROR: PERMITS failed: {e}")
        traceback.print_exc()
        failed_vars.append("PERMITS")

    # ── 14. ELEC_PRICE_TOT (EIA) ─────────────────────────────────────
    section("14. Fetching electricity price (EIA)")
    df_elec = None
    if eia_key:
        try:
            df_elec = fetch_electricity_price(eia_key)
            save_raw(df_elec, "eia_electricity_price")
            completed_vars.append("ELEC_PRICE_TOT")
            log(f"  ELEC_PRICE_TOT: {len(df_elec)} states")
        except Exception as e:
            log(f"  ERROR: ELEC_PRICE_TOT failed: {e}")
            traceback.print_exc()
            failed_vars.append("ELEC_PRICE_TOT")
    else:
        log("  SKIPPED: No EIA_API_KEY")
        failed_vars.append("ELEC_PRICE_TOT (no key)")

    # ── 15. Join all IVs ──────────────────────────────────────────────
    section("15. Joining all IVs into master table")

    # Start with ACS IVs (POP, MED_RENT, MED_HOMEVAL, COST_BURDEN_ALL,
    # VACANCY_RATE, TRANSIT_SHARE, BA_PLUS)
    df_ivs = df_acs_simple[["state", "POP", "MED_RENT", "MED_HOMEVAL",
                             "COST_BURDEN_ALL", "VACANCY_RATE",
                             "TRANSIT_SHARE", "BA_PLUS"]].copy()

    # Add LAND_AREA and POP_DENS
    if df_land is not None:
        df_land = normalize_state_col(df_land)
        df_ivs = safe_merge(df_ivs, df_land[["state", "LAND_AREA"]], "LAND_AREA")
        df_ivs["POP_DENS"] = build_pop_density(df_ivs["POP"], df_ivs["LAND_AREA"])
        log("  Joined: LAND_AREA, POP_DENS")
    else:
        log("  SKIPPED join: LAND_AREA (failed)")

    # Add BEA variables
    for label, df_bea, col in [
        ("GDP", df_gdp, "GDP"),
        ("RPP", df_rpp, "RPP"),
        ("REAL_PCPI", df_pcpi, "REAL_PCPI"),
    ]:
        if df_bea is not None:
            df_bea = normalize_state_col(df_bea)
            merge_cols = ["state", col]
            if "GDP_YEAR_NOTE" in df_bea.columns:
                merge_cols.append("GDP_YEAR_NOTE")
            df_ivs = safe_merge(df_ivs, df_bea[merge_cols], label)
            log(f"  Joined: {label}")
        else:
            log(f"  SKIPPED join: {label}")

    # Add BLS variables
    if df_unemp is not None:
        df_unemp = normalize_state_col(df_unemp)
        df_ivs = safe_merge(df_ivs, df_unemp[["state", "UNEMP"]], "UNEMP")
        log("  Joined: UNEMP")

    if df_qcew is not None:
        df_qcew = normalize_state_col(df_qcew)
        df_ivs = safe_merge(
            df_ivs,
            df_qcew[["state", "PRIV_EMP", "PRIV_ESTAB", "PRIV_AVG_PAY"]],
            "QCEW",
        )
        log("  Joined: PRIV_EMP, PRIV_ESTAB, PRIV_AVG_PAY")

    # Add PERMITS
    if df_permits is not None:
        df_permits = normalize_state_col(df_permits)
        df_ivs = safe_merge(df_ivs, df_permits[["state", "PERMITS"]], "PERMITS")
        log("  Joined: PERMITS")

    # Add electricity
    if df_elec is not None:
        df_elec = normalize_state_col(df_elec)
        df_ivs = safe_merge(df_ivs, df_elec[["state", "ELEC_PRICE_TOT"]], "ELEC_PRICE_TOT")
        log("  Joined: ELEC_PRICE_TOT")

    # Add state name
    df_ivs.insert(1, "state_name", df_ivs["state"].map(STATE_FIPS))

    save_interim(df_ivs, "ivs_all")
    log(f"  IVs master: {len(df_ivs)} states, {len(df_ivs.columns)} columns")

    # ── 16. Build final analysis-ready table ──────────────────────────
    section("16. Building analysis-ready table (DVs + IVs)")

    df_final = df_dvs.merge(df_ivs, on="state", how="inner")
    assert_50_rows(df_final, "analysis_ready")
    save_processed(df_final, "analysis_ready")
    log(f"  Final table: {len(df_final)} states, {len(df_final.columns)} columns")

    # ── 17. Quality checks ────────────────────────────────────────────
    section("17. Quality checks")

    # Check state count
    if len(df_final) != 50:
        log(f"  WARNING: {len(df_final)} states in final table (expected 50)")

    # Check for null columns
    null_report = df_final.isnull().sum()
    cols_with_nulls = null_report[null_report > 0]
    if len(cols_with_nulls) > 0:
        log("  Columns with missing values:")
        for col, count in cols_with_nulls.items():
            log(f"    {col}: {count} missing ({count}/{len(df_final)})")
    else:
        log("  No missing values in any column")

    # List all columns
    log(f"\n  All columns ({len(df_final.columns)}):")
    for i, col in enumerate(df_final.columns):
        log(f"    {i+1:3d}. {col}")

    # ── 18. Summary ───────────────────────────────────────────────────
    section("18. A2 Pipeline Summary")

    # Cross-check: any "completed" variable that is 100% null in the final
    # table should be reclassified as effectively failed.
    iv_cols_expected = [
        "POP", "MED_RENT", "MED_HOMEVAL", "COST_BURDEN_ALL", "VACANCY_RATE",
        "TRANSIT_SHARE", "BA_PLUS", "LAND_AREA", "POP_DENS",
        "GDP", "RPP", "REAL_PCPI", "UNEMP",
        "PRIV_EMP", "PRIV_ESTAB", "PRIV_AVG_PAY",
        "PERMITS", "ELEC_PRICE_TOT",
    ]
    all_null_vars = []
    for col in iv_cols_expected:
        if col in df_final.columns and df_final[col].isna().all():
            all_null_vars.append(col)

    if all_null_vars:
        log(f"\n  WARNING: These columns are present but 100% null (data not actually loaded):")
        for v in all_null_vars:
            log(f"    ! {v}")
        # Move from completed to failed
        for v in all_null_vars:
            if v in completed_vars:
                completed_vars.remove(v)
                failed_vars.append(f"{v} (100% null)")

    log(f"\n  Completed variables ({len(completed_vars)}):")
    for v in completed_vars:
        log(f"    + {v}")

    if failed_vars:
        log(f"\n  Failed/skipped variables ({len(failed_vars)}):")
        for v in failed_vars:
            log(f"    - {v}")
    else:
        log("\n  No failed variables!")

    log(f"\n  Output files:")
    log(f"    data_raw/          — raw API downloads")
    log(f"    data_interim/      — cleaned intermediate tables")
    log(f"    data_processed/    — analysis-ready joined table")

    # ── Save log ──────────────────────────────────────────────────────
    log_path = f"outputs/logs/build_dataset_{TIMESTAMP}.log"
    with open(log_path, "w") as f:
        f.write("\n".join(log_lines))
    print(f"\n  Log saved: {log_path}")

    return len(failed_vars) == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
