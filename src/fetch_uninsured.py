"""Fetch uninsured rate from ACS 2024 1-year subject table S2701.

Source: ACS 2024 1-year, subject table S2701 (Health Insurance Coverage Status).
Variable: UNINSURED — percent of civilian noninstitutionalized population without
          health insurance coverage.

Primary: S2701_C05_001E (percent uninsured, total population).
  - C05 = "Percent Uninsured" column
  - 001 = total population row
  - API endpoint: /data/2024/acs/acs1/subject

Fallback: Detail table B27010 (Types of Health Insurance Coverage by Age).
  - Uninsured count = B27010_017E + B27010_033E + B27010_050E + B27010_066E
  - Total = B27010_001E
  - UNINSURED = 100 * uninsured_count / total
  - These codes verified against Census Reporter ACS 2024 1-year metadata.
"""

import requests
import pandas as pd

ACS_SUBJECT_BASE = "https://api.census.gov/data/2024/acs/acs1/subject"
ACS_DETAIL_BASE = "https://api.census.gov/data/2024/acs/acs1"

# Primary: subject table
S2701_UNINSURED_PCT = "S2701_C05_001E"

# Cross-check variables
S2701_UNINSURED_COUNT = "S2701_C04_001E"
S2701_TOTAL_POP = "S2701_C01_001E"

# Fallback: detail table B27010
B27010_TOTAL = "B27010_001E"
B27010_UNINSURED = [
    "B27010_017E",  # Under 19, no health insurance
    "B27010_033E",  # 19 to 34, no health insurance
    "B27010_050E",  # 35 to 64, no health insurance
    "B27010_066E",  # 65+, no health insurance
]


def _fetch_subject_table(var_codes, api_key, state_fips_list):
    """Fetch variables from the ACS subject table endpoint."""
    var_str = ",".join(var_codes)
    params = {
        "get": var_str,
        "for": "state:*",
        "key": api_key,
    }
    resp = requests.get(ACS_SUBJECT_BASE, params=params, timeout=60)
    resp.raise_for_status()
    data = resp.json()
    df = pd.DataFrame(data[1:], columns=data[0])
    if state_fips_list is not None:
        df = df[df["state"].isin(state_fips_list)].copy()
    for col in var_codes:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    return df.reset_index(drop=True)


def fetch_uninsured(api_key, state_fips_list):
    """Fetch UNINSURED rate for each state.

    Tries subject table S2701 first; falls back to detail table B27010.

    Parameters
    ----------
    api_key : str
        Census API key.
    state_fips_list : list[str]
        List of 2-digit FIPS codes.

    Returns
    -------
    pd.DataFrame
        Columns: state, UNINSURED, UNINSURED_SOURCE
    """
    # --- Try S2701 subject table (primary) ---
    try:
        print("  Trying S2701 subject table...")
        vars_to_fetch = [S2701_UNINSURED_PCT, S2701_UNINSURED_COUNT, S2701_TOTAL_POP]
        df = _fetch_subject_table(vars_to_fetch, api_key, state_fips_list)

        if df[S2701_UNINSURED_PCT].notna().sum() >= 40:
            # Cross-check: recompute from count/total
            recomputed = 100 * df[S2701_UNINSURED_COUNT] / df[S2701_TOTAL_POP]
            diff = (df[S2701_UNINSURED_PCT] - recomputed).abs()
            max_diff = diff.max()
            print(f"  S2701 cross-check: max |direct% - recomputed%| = {max_diff:.3f}")

            if max_diff > 1.0:
                print(f"  WARNING: Cross-check difference > 1.0 pp for some states")

            result = pd.DataFrame({
                "state": df["state"],
                "UNINSURED": df[S2701_UNINSURED_PCT],
                "UNINSURED_SOURCE": "S2701_C05_001E",
            })
            print(f"  S2701 succeeded: {len(result)} states, "
                  f"median={result['UNINSURED'].median():.1f}%")
            return result

        print("  S2701 returned too many nulls, trying B27010 fallback...")

    except Exception as e:
        print(f"  S2701 failed ({e}), trying B27010 fallback...")

    # --- Fallback: B27010 detail table ---
    from src.fetch_census import fetch_acs_variables

    print("  Using B27010 fallback...")
    all_vars = [B27010_TOTAL] + B27010_UNINSURED
    df = fetch_acs_variables(all_vars, api_key, state_fips_list)

    uninsured_count = df[B27010_UNINSURED].sum(axis=1)
    total = df[B27010_TOTAL]

    result = pd.DataFrame({
        "state": df["state"],
        "UNINSURED": 100 * uninsured_count / total,
        "UNINSURED_SOURCE": "B27010_fallback",
    })

    # Sanity check
    med = result["UNINSURED"].median()
    if not (2 <= med <= 25):
        raise ValueError(
            f"UNINSURED sanity check failed: median = {med:.1f}% "
            f"(expected 2–25%). Check B27010 data."
        )

    print(f"  B27010 fallback succeeded: {len(result)} states, "
          f"median={med:.1f}%")
    return result
