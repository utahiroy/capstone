"""Fetch BLS data: LAUS unemployment and QCEW employment/establishments/pay."""

import io
import requests
import pandas as pd

from src.constants import STATE_FIPS

# ── LAUS: Annual average unemployment rate ────────────────────────────

# BLS LAUS series ID format:
#   LA  = Local Area survey
#   U/S = seasonal adjustment (U = unadjusted, S = seasonally adjusted)
#   ST  = statewide area type
#   {FIPS} = 2-digit state FIPS
#   0000000000003 = measure code 03 = unemployment rate
#
# M13 = annual average period. Only published in unadjusted (U) series.
# If M13 is unavailable, we compute from monthly M01-M12.

LAUS_API = "https://api.bls.gov/publicAPI/v2/timeseries/data/"


def _extract_laus_rate(series_data, year):
    """Extract annual unemployment rate from a single LAUS series response.

    Returns (rate, method) where method is "M13" or "M01-M12_avg" or None.
    """
    year_str = str(year)
    m13_val = None
    monthly_vals = []

    for obs in series_data:
        if obs.get("year") != year_str:
            continue
        period = obs.get("period", "")
        value = obs.get("value", "")
        try:
            fval = float(value)
        except (ValueError, TypeError):
            continue

        if period == "M13":
            m13_val = fval
        elif period.startswith("M") and period[1:].isdigit():
            month_num = int(period[1:])
            if 1 <= month_num <= 12:
                monthly_vals.append(fval)

    if m13_val is not None:
        return m13_val, "M13"
    elif len(monthly_vals) >= 12:
        return sum(monthly_vals) / len(monthly_vals), "M01-M12_avg"
    elif len(monthly_vals) > 0:
        return sum(monthly_vals) / len(monthly_vals), f"M_avg({len(monthly_vals)}mo)"
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
    first_batch_logged = False

    # BLS public API allows 25 series per request (no key) or 50 (with key)
    batch_size = 25
    for i in range(0, len(fips_list), batch_size):
        batch_fips = fips_list[i : i + batch_size]

        # Try not-seasonally-adjusted first (has M13), then seasonally adjusted
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
            data = resp.json()

            if data.get("status") != "REQUEST_SUCCEEDED":
                print(f"  LAUS: API status={data.get('status')}, "
                      f"message={data.get('message', '')}")
                continue

            batch_rows = []
            for series in data.get("Results", {}).get("series", []):
                sid = series["seriesID"]
                # Extract FIPS: position 5:7 for both LAUST and LASST
                state_fips = sid[5:7]

                # Log first series data for debugging
                if not first_batch_logged:
                    periods = [obs.get("period") for obs in series.get("data", [])]
                    print(f"  LAUS debug: series={sid}, sa_code={sa_code}, "
                          f"periods={periods}")
                    first_batch_logged = True

                rate, method = _extract_laus_rate(series.get("data", []), year)
                if rate is not None:
                    batch_rows.append({
                        "state": state_fips,
                        "UNEMP": rate,
                    })
                    methods_used.add(method)

            if batch_rows:
                all_rows.extend(batch_rows)
                break  # got data from this sa_code, skip the other
            else:
                print(f"  LAUS: no data from sa_code={sa_code} for batch "
                      f"starting at FIPS {batch_fips[0]}")

    df = pd.DataFrame(all_rows)
    if df.empty:
        raise ValueError(
            f"No LAUS data returned for {year}. "
            f"Both LAUST (unadjusted) and LASST (adjusted) returned no data."
        )

    print(f"  LAUS: {len(df)} states, methods used: {methods_used}")
    if len(df) != 50:
        print(f"  WARNING: LAUS returned {len(df)} states, expected 50")
    return df.sort_values("state").reset_index(drop=True)


# ── QCEW: Private employment, establishments, average pay ────────────

QCEW_CSV_URL = "https://data.bls.gov/cew/data/api/{year}/a/industry/10.csv"


def fetch_qcew(year=2024):
    """Fetch QCEW annual averages for private sector, all industries, state level.

    Returns DataFrame with columns: state, PRIV_EMP, PRIV_ESTAB, PRIV_AVG_PAY.
    """
    url = QCEW_CSV_URL.format(year=year)
    resp = requests.get(url, timeout=120)
    resp.raise_for_status()

    # Force area_fips to string so leading zeros are preserved (e.g. "01000")
    df = pd.read_csv(io.StringIO(resp.text), dtype={"area_fips": str})

    print(f"  QCEW: raw CSV rows={len(df)}, columns={list(df.columns)}")

    # Diagnostic: print dtypes and unique values for filter columns
    for col in ["own_code", "agglvl_code", "size_code"]:
        if col in df.columns:
            print(f"  QCEW: {col} dtype={df[col].dtype}, "
                  f"unique={sorted(df[col].dropna().unique())[:10]}")
        else:
            print(f"  QCEW: column '{col}' NOT FOUND")

    # Ensure filter columns are numeric (some QCEW CSVs encode as strings)
    for col in ["own_code", "agglvl_code", "size_code"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Filter: private ownership (own_code=5), state level (agglvl_code=50),
    # all sizes (size_code=0)
    mask = (
        (df["own_code"] == 5)
        & (df["agglvl_code"] == 50)
        & (df["size_code"] == 0)
    )
    print(f"  QCEW: after filter own=5 & agg=50 & size=0: {mask.sum()} rows")

    # If no rows with agglvl_code=50, try alternative state-level codes
    if mask.sum() == 0:
        print(f"  QCEW: trying alternative agglvl_code values for state level...")
        # agglvl_code: 50=state total (all industries), 51-58=industry detail
        # Some QCEW vintages use different codes
        for alt_agg in [50, 51, 40, 52]:
            alt_mask = (
                (df["own_code"] == 5)
                & (df["agglvl_code"] == alt_agg)
                & (df["size_code"] == 0)
            )
            if alt_mask.sum() > 0:
                print(f"  QCEW: found {alt_mask.sum()} rows with agglvl_code={alt_agg}")
                mask = alt_mask
                break

    df = df[mask].copy()

    if df.empty:
        # Print sample of what IS in the data for diagnosis
        sample = df.head(0)  # empty
        # Look at what agglvl_code values exist for own_code=5
        own5 = df[df["own_code"] == 5] if "own_code" in df.columns else pd.DataFrame()
        raise ValueError(
            f"QCEW filter returned 0 rows for year={year}. "
            f"Total rows in CSV: {len(pd.read_csv(io.StringIO(resp.text), nrows=5))} (sample). "
            f"This may indicate 2024 annual data is not yet published."
        )

    # Extract 2-digit state FIPS from area_fips (format: "XX000")
    df["state"] = df["area_fips"].str.strip().str.zfill(5).str[:2]

    # Keep only 50 states
    df = df[df["state"].isin(STATE_FIPS.keys())].copy()

    # Build output
    result = pd.DataFrame({
        "state": df["state"].values,
        "PRIV_EMP": pd.to_numeric(df["annual_avg_emplvl"], errors="coerce").values,
        "PRIV_ESTAB": pd.to_numeric(df["annual_avg_estabs"], errors="coerce").values,
    })

    total_wages = pd.to_numeric(df["total_annual_wages"], errors="coerce").values
    result["PRIV_AVG_PAY"] = total_wages / result["PRIV_EMP"]

    print(f"  QCEW: final output {len(result)} states")
    if len(result) != 50:
        print(f"  WARNING: QCEW returned {len(result)} states, expected 50")

    return result.sort_values("state").reset_index(drop=True)
