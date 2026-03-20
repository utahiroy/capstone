"""Fetch BLS data: LAUS unemployment and QCEW employment/establishments/pay."""

import io
import requests
import pandas as pd

from src.constants import STATE_FIPS

# ── LAUS: Annual average unemployment rate ────────────────────────────

LAUS_API = "https://api.bls.gov/publicAPI/v2/timeseries/data/"


def _extract_laus_rate(series_data, year):
    """Extract annual unemployment rate from a single LAUS series response.

    Strategy: use M13 (annual average) if present; otherwise compute
    the simple average of M01-M12 monthly values.

    Returns (rate, method) or (None, None).
    """
    year_str = str(year)
    m13_val = None
    monthly_vals = []

    for obs in series_data:
        # BLS observations have "year" and "period" keys
        obs_year = obs.get("year", "")
        if obs_year != year_str:
            continue
        period = obs.get("period", "")
        value = obs.get("value", "")
        try:
            fval = float(value)
        except (ValueError, TypeError):
            continue

        if period == "M13":
            m13_val = fval
        elif period.startswith("M") and len(period) == 3 and period[1:].isdigit():
            month_num = int(period[1:])
            if 1 <= month_num <= 12:
                monthly_vals.append(fval)

    if m13_val is not None:
        return m13_val, "M13"
    if len(monthly_vals) >= 12:
        avg = round(sum(monthly_vals) / len(monthly_vals), 1)
        return avg, "M01-M12_avg"
    if len(monthly_vals) > 0:
        avg = round(sum(monthly_vals) / len(monthly_vals), 1)
        return avg, f"M_avg({len(monthly_vals)}mo)"
    return None, None


def fetch_unemployment(year=2024):
    """Fetch annual average unemployment rate for all 50 states.

    Uses BLS public API v2. Tries M13 (annual average) first; if
    unavailable, computes from monthly M01-M12 values.

    Returns DataFrame with columns: state, UNEMP.
    """
    fips_list = sorted(STATE_FIPS.keys())
    all_rows = []
    methods_used = set()

    batch_size = 25
    for i in range(0, len(fips_list), batch_size):
        batch_fips = fips_list[i : i + batch_size]

        # Try unadjusted first (may have M13), then seasonally adjusted
        for sa_code in ["U", "S"]:
            series_ids = [
                f"LA{sa_code}ST{fips}0000000000003" for fips in batch_fips
            ]
            payload = {
                "seriesid": series_ids,
                "startyear": str(year),
                "endyear": str(year),
            }
            resp = requests.post(LAUS_API, json=payload, timeout=60)
            resp.raise_for_status()
            result = resp.json()

            if result.get("status") != "REQUEST_SUCCEEDED":
                print(f"  LAUS: API status={result.get('status')}, "
                      f"message={result.get('message', '')}")
                continue

            batch_rows = []
            for series in result.get("Results", {}).get("series", []):
                sid = series["seriesID"]
                state_fips = sid[5:7]
                obs_list = series.get("data", [])

                # Debug: log first series in first batch
                if i == 0 and len(batch_rows) == 0:
                    periods = [o.get("period") for o in obs_list]
                    print(f"  LAUS debug: series={sid}, sa={sa_code}, "
                          f"n_obs={len(obs_list)}, periods={periods}")

                rate, method = _extract_laus_rate(obs_list, year)
                if rate is not None:
                    batch_rows.append({"state": state_fips, "UNEMP": rate})
                    methods_used.add(method)

            if batch_rows:
                print(f"  LAUS: batch {i//batch_size + 1}: {len(batch_rows)} states "
                      f"from sa_code={sa_code}")
                all_rows.extend(batch_rows)
                break  # this sa_code worked, skip the other
            else:
                print(f"  LAUS: sa_code={sa_code} yielded 0 rows for batch "
                      f"starting at FIPS {batch_fips[0]}")

    df = pd.DataFrame(all_rows)
    if df.empty:
        raise ValueError(f"No LAUS data returned for {year}.")

    print(f"  LAUS: {len(df)} states, methods={methods_used}")
    if len(df) != 50:
        print(f"  WARNING: LAUS returned {len(df)} states, expected 50")
    return df.sort_values("state").reset_index(drop=True)


# ── QCEW: Private employment, establishments, average pay ────────────

QCEW_CSV_URL = "https://data.bls.gov/cew/data/api/{year}/a/industry/10.csv"


def fetch_qcew(year=2024):
    """Fetch QCEW annual averages for private sector, all industries, state level.

    The QCEW CSV API returns one CSV for a given year + industry code.
    Industry code 10 = all industries (NAICS "10" = Total, all industries).

    Filter logic:
    - own_code=5 (private sector)
    - State-level rows: identified by agglvl_code and area_fips pattern
    - size_code=0 (all establishment sizes)

    Returns DataFrame with columns: state, PRIV_EMP, PRIV_ESTAB, PRIV_AVG_PAY.
    """
    url = QCEW_CSV_URL.format(year=year)
    resp = requests.get(url, timeout=120)
    resp.raise_for_status()

    df = pd.read_csv(io.StringIO(resp.text), dtype={"area_fips": str})

    print(f"  QCEW: raw CSV rows={len(df)}, columns={list(df.columns)}")

    # Coerce filter columns to numeric
    for col in ["own_code", "agglvl_code", "size_code"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
            uniq = sorted(df[col].dropna().unique())
            print(f"  QCEW: {col} unique={uniq[:15]}")

    # Diagnostic: print cross-tabulation of own_code x agglvl_code
    if "own_code" in df.columns and "agglvl_code" in df.columns:
        ct = df.groupby(["own_code", "agglvl_code"]).size().reset_index(name="n")
        print(f"  QCEW: own_code x agglvl_code combinations (top 20):")
        for _, row in ct.head(20).iterrows():
            print(f"    own={int(row['own_code'])}, agg={int(row['agglvl_code'])}, n={row['n']}")

    # Primary filter: own_code=5 (private), size_code=0 (all sizes)
    # For agglvl_code, try the standard state-level codes in order
    # 50 = state, all industries, all ownerships
    # 51 = state by supersector
    # 52 = state by sector (NAICS)
    # 53 = state by subsector
    # For industry_code=10 (total), agglvl_code=50 should give 1 row per state per ownership.
    # But the CSV for industry=10 may use a different agglvl_code.

    # Strategy: filter own_code=5, size_code=0, then identify state-level rows
    # by area_fips pattern (XX000 where XX is a 2-digit state code)
    own5 = df[(df["own_code"] == 5) & (df["size_code"] == 0)].copy()
    print(f"  QCEW: own_code=5 & size_code=0: {len(own5)} rows")

    if len(own5) == 0:
        # Try without size_code filter
        own5 = df[df["own_code"] == 5].copy()
        print(f"  QCEW: own_code=5 (no size filter): {len(own5)} rows")

    if len(own5) == 0:
        raise ValueError(
            f"QCEW: no rows with own_code=5 for year={year}. "
            f"Available own_codes: {sorted(df['own_code'].dropna().unique())}"
        )

    # Identify state-level rows by area_fips pattern: "XX000"
    own5["_fips_clean"] = own5["area_fips"].str.strip().str.zfill(5)
    state_mask = own5["_fips_clean"].str.match(r"^\d{2}000$")
    state_rows = own5[state_mask].copy()
    print(f"  QCEW: state-level rows (area_fips=XX000): {len(state_rows)}")

    if len(state_rows) == 0:
        # Show sample area_fips values for diagnosis
        print(f"  QCEW: sample area_fips values: {own5['area_fips'].head(10).tolist()}")
        raise ValueError(f"QCEW: no state-level rows found for own_code=5")

    # If multiple rows per state (different agglvl_code), keep the one with
    # the lowest agglvl_code (most aggregated)
    state_rows["state"] = state_rows["_fips_clean"].str[:2]
    state_rows = state_rows[state_rows["state"].isin(STATE_FIPS.keys())].copy()

    if state_rows["state"].duplicated().any():
        print(f"  QCEW: deduplicating by state (keeping lowest agglvl_code)")
        state_rows = state_rows.sort_values("agglvl_code")
        state_rows = state_rows.drop_duplicates(subset=["state"], keep="first")

    result = pd.DataFrame({
        "state": state_rows["state"].values,
        "PRIV_EMP": pd.to_numeric(state_rows["annual_avg_emplvl"], errors="coerce").values,
        "PRIV_ESTAB": pd.to_numeric(state_rows["annual_avg_estabs"], errors="coerce").values,
    })

    total_wages = pd.to_numeric(state_rows["total_annual_wages"], errors="coerce").values
    result["PRIV_AVG_PAY"] = total_wages / result["PRIV_EMP"]

    print(f"  QCEW: final output {len(result)} states")
    if len(result) != 50:
        print(f"  WARNING: QCEW returned {len(result)} states, expected 50")

    return result.sort_values("state").reset_index(drop=True)
