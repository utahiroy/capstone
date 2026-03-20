"""Fetch BLS data: LAUS unemployment and QCEW employment/establishments/pay."""

import io
import requests
import pandas as pd

from src.constants import STATE_FIPS

# ── LAUS: Annual average unemployment rate ────────────────────────────

# BLS LAUS series ID pattern: LAUST{FIPS}0000000000003
#   - LA  = Local Area
#   - U   = not seasonally adjusted (S = seasonally adjusted)
#   - ST  = statewide
#   - {FIPS} = 2-digit state FIPS
#   - 0000000000003 = measure code 03 = unemployment rate
# Period M13 = annual average (only in not-seasonally-adjusted series).

LAUS_API = "https://api.bls.gov/publicAPI/v2/timeseries/data/"


def fetch_unemployment(year=2024):
    """Fetch annual average unemployment rate for all 50 states.

    Uses BLS public API v2 (no key required for <=25 series).
    Batches requests to stay within limits.

    Returns DataFrame with columns: state, UNEMP.
    """
    fips_list = sorted(STATE_FIPS.keys())
    all_rows = []

    # BLS public API allows 25 series per request (no key) or 50 (with key)
    batch_size = 25
    for i in range(0, len(fips_list), batch_size):
        batch_fips = fips_list[i : i + batch_size]
        # LAUST = not seasonally adjusted; M13 annual average only exists
        # in the unadjusted series (LASST is seasonally adjusted, no M13).
        series_ids = [f"LAUST{fips}0000000000003" for fips in batch_fips]

        payload = {
            "seriesid": series_ids,
            "startyear": str(year),
            "endyear": str(year),
        }
        resp = requests.post(LAUS_API, json=payload, timeout=60)
        resp.raise_for_status()
        data = resp.json()

        if data.get("status") != "REQUEST_SUCCEEDED":
            raise ValueError(f"BLS LAUS API error: {data.get('message', data)}")

        for series in data["Results"]["series"]:
            sid = series["seriesID"]
            # Extract FIPS from series ID: LAUST{2-digit FIPS}00...
            state_fips = sid[5:7]
            for obs in series["data"]:
                if obs["period"] == "M13":  # annual average
                    all_rows.append({
                        "state": state_fips,
                        "UNEMP": float(obs["value"]),
                    })

    df = pd.DataFrame(all_rows)
    if df.empty:
        raise ValueError(f"No LAUS annual average data returned for {year}")
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

    # Filter: private ownership (own_code=5), state level (agglvl_code=50),
    # all sizes (size_code=0)
    mask = (
        (df["own_code"] == 5)
        & (df["agglvl_code"] == 50)
        & (df["size_code"] == 0)
    )
    df = df[mask].copy()

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

    if len(result) != 50:
        print(f"  WARNING: QCEW returned {len(result)} states, expected 50")

    return result.sort_values("state").reset_index(drop=True)
