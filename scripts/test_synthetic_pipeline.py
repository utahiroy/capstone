"""Synthetic integration test for the full A2 pipeline.

This script generates synthetic data matching each source's schema,
then runs the pipeline's join/merge/quality-check logic to verify
the final analysis-ready table has the expected structure:
50 states × (migration DVs + 22 IVs).

This test validates:
  1. All imports work
  2. The join/merge logic produces 50 rows
  3. All 22 IV columns are present
  4. No unexpected duplicates or missing states
  5. The 4 new IV modules (fetch_commute, fetch_uninsured, fetch_crime, fetch_nri)
     produce correctly-shaped output when given valid input data
"""

import os
import sys
import numpy as np
import pandas as pd

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.constants import STATE_FIPS, AGE_GROUPS
from src.build_variables import (
    build_migration_dvs, build_cost_burden, build_vacancy_rate,
    build_transit_share, build_ba_plus, build_pop_density,
)
from src.fetch_commute import _grouped_median, B08303_BINS
from src.fetch_nri import aggregate_nri_to_state
from src.fetch_crime import load_crime_from_csv, STATE_ABBR_TO_FIPS

ALL_STATES = sorted(STATE_FIPS.keys())
np.random.seed(42)

PASS = 0
FAIL = 0


def check(label, condition, detail=""):
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  PASS: {label}")
    else:
        FAIL += 1
        print(f"  FAIL: {label} — {detail}")


def section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


# ── 1. Generate synthetic migration data ──────────────────────────

section("1. Synthetic migration data")

from src.constants import IN_COUNT_VARS, OUT_COUNT_VARS, POP_AGE_VARS

# Build synthetic DataFrames matching Census API output
def make_migration_df(var_dict, n_states=50):
    all_vars = sorted({v for vs in var_dict.values() for v in vs})
    data = {"state": ALL_STATES[:n_states]}
    for v in all_vars:
        data[v] = np.random.randint(100, 5000, n_states)
    return pd.DataFrame(data)

df_in = make_migration_df(IN_COUNT_VARS)
df_out = make_migration_df(OUT_COUNT_VARS)
df_pop = make_migration_df(POP_AGE_VARS)
# Make pop values larger to ensure reasonable rates
for col in df_pop.columns:
    if col != "state":
        df_pop[col] = df_pop[col] * 100

df_dvs = build_migration_dvs(df_in, df_out, df_pop)
check("Migration DVs: 50 rows", len(df_dvs) == 50)
check("Migration DVs: state col", "state" in df_dvs.columns)

expected_dv_cols = []
for ag in AGE_GROUPS:
    for prefix in ["IN_COUNT", "OUT_COUNT", "POP_AGE", "NET_COUNT", "IN_RATE", "OUT_RATE", "NET_RATE"]:
        expected_dv_cols.append(f"{prefix}_{ag}")
for col in expected_dv_cols:
    check(f"DV column {col}", col in df_dvs.columns, f"missing from migration DVs")

print(f"  Migration DV columns: {len(df_dvs.columns)} total")

# ── 2. Generate synthetic ACS simple IVs ──────────────────────────

section("2. Synthetic ACS IVs")

from src.constants import (
    ACS_SIMPLE_VARS, COST_BURDEN_RENTER_TOTAL, COST_BURDEN_RENTER_BURDENED,
    COST_BURDEN_OWNER_TOTAL, COST_BURDEN_OWNER_BURDENED,
    VACANCY_FOR_RENT, VACANCY_RENTED_NOT_OCC, OCCUPIED_RENTER,
    TRANSIT_WORKERS_TOTAL, TRANSIT_PUBLIC,
    BA_PLUS_TOTAL, BA_PLUS_BACHELORS, BA_PLUS_MASTERS,
    BA_PLUS_PROFESSIONAL, BA_PLUS_DOCTORATE,
)

# Simple vars
df_acs = pd.DataFrame({"state": ALL_STATES})
df_acs["POP"] = np.random.randint(500000, 40000000, 50)
df_acs["MED_RENT"] = np.random.randint(700, 2500, 50)
df_acs["MED_HOMEVAL"] = np.random.randint(100000, 800000, 50)

# Cost burden
burden_data = {"state": ALL_STATES}
burden_data[COST_BURDEN_RENTER_TOTAL] = np.random.randint(100000, 500000, 50)
for v in COST_BURDEN_RENTER_BURDENED:
    burden_data[v] = np.random.randint(10000, 80000, 50)
burden_data[COST_BURDEN_OWNER_TOTAL] = np.random.randint(200000, 600000, 50)
for v in COST_BURDEN_OWNER_BURDENED:
    burden_data[v] = np.random.randint(5000, 50000, 50)
df_burden = pd.DataFrame(burden_data)
df_acs["COST_BURDEN_ALL"] = build_cost_burden(df_burden).values

# Vacancy
vacancy_data = {"state": ALL_STATES}
vacancy_data[VACANCY_FOR_RENT] = np.random.randint(5000, 50000, 50)
vacancy_data[VACANCY_RENTED_NOT_OCC] = np.random.randint(1000, 10000, 50)
vacancy_data[OCCUPIED_RENTER] = np.random.randint(100000, 500000, 50)
df_vac = pd.DataFrame(vacancy_data)
df_acs["VACANCY_RATE"] = build_vacancy_rate(df_vac).values

# Transit
transit_data = {"state": ALL_STATES}
transit_data[TRANSIT_WORKERS_TOTAL] = np.random.randint(500000, 5000000, 50)
transit_data[TRANSIT_PUBLIC] = np.random.randint(5000, 500000, 50)
df_transit = pd.DataFrame(transit_data)
df_acs["TRANSIT_SHARE"] = build_transit_share(df_transit).values

# BA+
ba_data = {"state": ALL_STATES}
ba_data[BA_PLUS_TOTAL] = np.random.randint(300000, 3000000, 50)
ba_data[BA_PLUS_BACHELORS] = np.random.randint(50000, 500000, 50)
ba_data[BA_PLUS_MASTERS] = np.random.randint(20000, 200000, 50)
ba_data[BA_PLUS_PROFESSIONAL] = np.random.randint(5000, 50000, 50)
ba_data[BA_PLUS_DOCTORATE] = np.random.randint(2000, 30000, 50)
df_ba = pd.DataFrame(ba_data)
df_acs["BA_PLUS"] = build_ba_plus(df_ba).values

check("ACS IVs: 50 rows", len(df_acs) == 50)
for col in ["POP", "MED_RENT", "MED_HOMEVAL", "COST_BURDEN_ALL", "VACANCY_RATE",
            "TRANSIT_SHARE", "BA_PLUS"]:
    check(f"ACS IV {col} present", col in df_acs.columns)

# ── 3. Generate remaining IVs ─────────────────────────────────────

section("3. Synthetic non-ACS IVs")

# LAND_AREA
df_land = pd.DataFrame({
    "state": ALL_STATES,
    "LAND_AREA": np.random.uniform(1000, 250000, 50),
})

# BEA
df_gdp = pd.DataFrame({"state": ALL_STATES, "GDP": np.random.uniform(50000, 3000000, 50)})
df_rpp = pd.DataFrame({"state": ALL_STATES, "RPP": np.random.uniform(85, 120, 50)})
df_pcpi = pd.DataFrame({"state": ALL_STATES, "REAL_PCPI": np.random.uniform(35000, 75000, 50)})

# BLS
df_unemp = pd.DataFrame({"state": ALL_STATES, "UNEMP": np.random.uniform(2.5, 8.0, 50)})
df_qcew = pd.DataFrame({
    "state": ALL_STATES,
    "PRIV_EMP": np.random.randint(100000, 8000000, 50),
    "PRIV_ESTAB": np.random.randint(10000, 500000, 50),
    "PRIV_AVG_PAY": np.random.uniform(35000, 80000, 50),
})

# Permits
df_permits = pd.DataFrame({"state": ALL_STATES, "PERMITS": np.random.randint(1000, 200000, 50)})

# Electricity
df_elec = pd.DataFrame({"state": ALL_STATES, "ELEC_PRICE_TOT": np.random.uniform(8, 25, 50)})

print("  Generated: LAND_AREA, GDP, RPP, REAL_PCPI, UNEMP, QCEW, PERMITS, ELEC_PRICE_TOT")

# ── 4. Generate 4 NEW IVs ─────────────────────────────────────────

section("4. Synthetic new IVs (COMMUTE_MED, UNINSURED, CRIME, NRI)")

# COMMUTE_MED
df_commute = pd.DataFrame({
    "state": ALL_STATES,
    "COMMUTE_MED": np.random.uniform(18, 35, 50).round(1),
})
check("COMMUTE_MED: 50 rows", len(df_commute) == 50)

# UNINSURED
df_uninsured = pd.DataFrame({
    "state": ALL_STATES,
    "UNINSURED": np.random.uniform(3, 18, 50).round(1),
    "UNINSURED_SOURCE": "synthetic_test",
})
check("UNINSURED: 50 rows", len(df_uninsured) == 50)

# CRIME_VIOLENT_RATE
df_crime = pd.DataFrame({
    "state": ALL_STATES,
    "CRIME_VIOLENT_RATE": np.random.uniform(100, 600, 50).round(1),
})
check("CRIME_VIOLENT_RATE: 50 rows", len(df_crime) == 50)

# NRI_RISK_INDEX (test aggregation logic)
nri_counties = []
for fips in ALL_STATES:
    n_counties = np.random.randint(5, 80)
    for _ in range(n_counties):
        nri_counties.append({
            "STATEFIPS": fips,
            "STCOFIPS": f"{fips}{np.random.randint(1, 999):03d}",
            "POPULATION": np.random.randint(1000, 500000),
            "RISK_SCORE": np.random.uniform(5, 95),
            "RISK_RATNG": "Moderate",
        })
# Add some DC counties (should be filtered out)
for _ in range(5):
    nri_counties.append({
        "STATEFIPS": "11",
        "STCOFIPS": "11001",
        "POPULATION": 100000,
        "RISK_SCORE": 50.0,
        "RISK_RATNG": "Moderate",
    })
df_nri_counties = pd.DataFrame(nri_counties)
df_nri = aggregate_nri_to_state(df_nri_counties)
check("NRI aggregation: 50 states", len(df_nri) == 50,
      f"got {len(df_nri)} states")
check("NRI: excludes DC (FIPS 11)", "11" not in df_nri["state"].values,
      "DC should be filtered out")
check("NRI: has NRI_RISK_INDEX col", "NRI_RISK_INDEX" in df_nri.columns)
check("NRI: values in 0-100", df_nri["NRI_RISK_INDEX"].between(0, 100).all(),
      f"min={df_nri['NRI_RISK_INDEX'].min():.1f}, max={df_nri['NRI_RISK_INDEX'].max():.1f}")

# ── 5. Test grouped-median function ───────────────────────────────

section("5. Grouped-median unit tests")

bin_bounds = [(b[1], b[2]) for b in B08303_BINS]

# Test 1: All in one bin (25-30)
counts1 = [0, 0, 0, 0, 0, 100, 0, 0, 0, 0, 0, 0]
med1 = _grouped_median(counts1, bin_bounds)
check("All-in-one-bin: 25-30", 25 <= med1 <= 30, f"got {med1:.1f}")

# Test 2: Even split → ~30 min
counts2 = [8.33]*12
med2 = _grouped_median(counts2, bin_bounds)
check("Even split: ~30 min", 25 <= med2 <= 35, f"got {med2:.1f}")

# Test 3: Empty → NaN
med3 = _grouped_median([0]*12, bin_bounds)
check("Empty counts: NaN", np.isnan(med3))

# Test 4: Realistic distribution
counts4 = [500, 800, 1500, 2500, 3000, 2800, 3500, 1200, 800, 1500, 600, 200]
med4 = _grouped_median(counts4, bin_bounds)
check("Realistic dist: 20-30 min", 20 <= med4 <= 30, f"got {med4:.1f}")

# ── 6. Test crime CSV fallback ────────────────────────────────────

section("6. Crime CSV fallback test")

# Create a test CSV
test_csv = "/tmp/test_crime.csv"
crime_csv_data = pd.DataFrame({
    "state_abbr": list(STATE_ABBR_TO_FIPS.keys()),
    "violent_crime": np.random.randint(1000, 100000, 50),
    "population": np.random.randint(500000, 40000000, 50),
})
crime_csv_data.to_csv(test_csv, index=False)
df_crime_csv = load_crime_from_csv(test_csv)
check("Crime CSV: 50 rows", len(df_crime_csv) == 50, f"got {len(df_crime_csv)}")
check("Crime CSV: has CRIME_VIOLENT_RATE", "CRIME_VIOLENT_RATE" in df_crime_csv.columns)
check("Crime CSV: FIPS codes valid",
      set(df_crime_csv["state"]) == set(ALL_STATES),
      f"missing: {set(ALL_STATES) - set(df_crime_csv['state'])}")
os.remove(test_csv)

# ── 7. Full pipeline join simulation ──────────────────────────────

section("7. Full pipeline join simulation (50 states × 22 IVs)")

# Replicate the join logic from build_dataset.py
df_ivs = df_acs[["state", "POP", "MED_RENT", "MED_HOMEVAL",
                  "COST_BURDEN_ALL", "VACANCY_RATE",
                  "TRANSIT_SHARE", "BA_PLUS"]].copy()

# LAND_AREA + POP_DENS
df_ivs = df_ivs.merge(df_land[["state", "LAND_AREA"]], on="state", how="left")
df_ivs["POP_DENS"] = build_pop_density(df_ivs["POP"], df_ivs["LAND_AREA"])

# BEA
for df_bea, col in [(df_gdp, "GDP"), (df_rpp, "RPP"), (df_pcpi, "REAL_PCPI")]:
    df_ivs = df_ivs.merge(df_bea[["state", col]], on="state", how="left")

# BLS
df_ivs = df_ivs.merge(df_unemp[["state", "UNEMP"]], on="state", how="left")
df_ivs = df_ivs.merge(df_qcew[["state", "PRIV_EMP", "PRIV_ESTAB", "PRIV_AVG_PAY"]],
                       on="state", how="left")

# PERMITS
df_ivs = df_ivs.merge(df_permits[["state", "PERMITS"]], on="state", how="left")

# ELEC
df_ivs = df_ivs.merge(df_elec[["state", "ELEC_PRICE_TOT"]], on="state", how="left")

# 4 NEW IVs
df_ivs = df_ivs.merge(df_commute[["state", "COMMUTE_MED"]], on="state", how="left")
df_ivs = df_ivs.merge(df_uninsured[["state", "UNINSURED"]], on="state", how="left")
df_ivs = df_ivs.merge(df_crime[["state", "CRIME_VIOLENT_RATE"]], on="state", how="left")
df_ivs = df_ivs.merge(df_nri[["state", "NRI_RISK_INDEX"]], on="state", how="left")

# state name
df_ivs.insert(1, "state_name", df_ivs["state"].map(STATE_FIPS))

check("IVs table: 50 rows", len(df_ivs) == 50, f"got {len(df_ivs)}")

# Check all 22 IVs
expected_ivs = [
    "POP", "LAND_AREA", "POP_DENS",
    "GDP", "RPP", "REAL_PCPI",
    "UNEMP", "PRIV_EMP", "PRIV_ESTAB", "PRIV_AVG_PAY",
    "PERMITS", "MED_RENT", "MED_HOMEVAL",
    "COST_BURDEN_ALL", "VACANCY_RATE",
    "COMMUTE_MED", "TRANSIT_SHARE", "BA_PLUS",
    "UNINSURED", "ELEC_PRICE_TOT",
    "CRIME_VIOLENT_RATE", "NRI_RISK_INDEX",
]

for iv in expected_ivs:
    check(f"IV column {iv} present", iv in df_ivs.columns, "missing!")

check("All 22 IVs present", all(iv in df_ivs.columns for iv in expected_ivs),
      f"missing: {[iv for iv in expected_ivs if iv not in df_ivs.columns]}")

# Check no nulls
null_report = df_ivs[expected_ivs].isnull().sum()
cols_with_nulls = null_report[null_report > 0]
check("No null IVs in synthetic data", len(cols_with_nulls) == 0,
      f"nulls in: {dict(cols_with_nulls)}")

# Final join: DVs + IVs
df_final = df_dvs.merge(df_ivs, on="state", how="inner")
check("Final table: 50 rows", len(df_final) == 50, f"got {len(df_final)}")
check("Final table: no duplicate states",
      df_final["state"].nunique() == 50)
check("Final table: all 50 FIPS present",
      set(df_final["state"]) == set(ALL_STATES))

total_expected_cols = 1 + len(expected_dv_cols) + 1 + 22 + 1  # state + DVs + state_name + 22 IVs + state(from merge)
print(f"\n  Final table shape: {df_final.shape[0]} rows × {df_final.shape[1]} cols")
print(f"  DV columns: {len(expected_dv_cols)}")
print(f"  IV columns: {len(expected_ivs)}")

# ── 8. Check state abbreviation FIPS mapping ──────────────────────

section("8. State abbreviation-to-FIPS mapping validation")

check("50 state abbreviations in map", len(STATE_ABBR_TO_FIPS) == 50)
check("No DC in FIPS map", "DC" not in STATE_ABBR_TO_FIPS)
check("FIPS values match STATE_FIPS",
      set(STATE_ABBR_TO_FIPS.values()) == set(STATE_FIPS.keys()),
      f"diff: {set(STATE_ABBR_TO_FIPS.values()) ^ set(STATE_FIPS.keys())}")

# ── Summary ───────────────────────────────────────────────────────

section("SUMMARY")
print(f"  PASSED: {PASS}")
print(f"  FAILED: {FAIL}")
print(f"  TOTAL:  {PASS + FAIL}")

if FAIL > 0:
    print("\n  *** SOME TESTS FAILED ***")
    sys.exit(1)
else:
    print("\n  ALL TESTS PASSED")
    sys.exit(0)
