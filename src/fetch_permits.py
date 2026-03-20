"""Fetch Census Building Permits Survey (BPS) state annual data."""

import io
import requests
import pandas as pd

from src.constants import STATE_FIPS

# Census BPS state annual data — CSV download
# The URL pattern for annual state-level data:
BPS_URL = "https://www2.census.gov/econ/bps/State/st{year}a.txt"
# Alternative formats the Census may use
BPS_ALT_URLS = [
    "https://www2.census.gov/econ/bps/State/st{year}a.txt",
    "https://www2.census.gov/econ/bps/State/st_annual_{year}.csv",
]


def fetch_permits(year=2024):
    """Fetch total housing units authorized by building permits, state-level.

    Returns DataFrame with columns: state, PERMITS.
    """
    # Try each URL pattern
    resp = None
    for url_template in BPS_ALT_URLS:
        url = url_template.format(year=str(year)[-2:])
        try:
            resp = requests.get(url, timeout=60)
            if resp.status_code == 200:
                break
        except requests.RequestException:
            continue

    # Also try with full year
    if resp is None or resp.status_code != 200:
        for url_template in BPS_ALT_URLS:
            url = url_template.format(year=year)
            try:
                resp = requests.get(url, timeout=60)
                if resp.status_code == 200:
                    break
            except requests.RequestException:
                continue

    if resp is None or resp.status_code != 200:
        raise ValueError(
            f"Could not download BPS state annual data for {year}. "
            f"Tried multiple URL patterns. Census may use a different format."
        )

    # Parse the fixed-width or CSV file
    text = resp.text
    # Try CSV first
    try:
        df = pd.read_csv(io.StringIO(text))
    except Exception:
        # Try fixed-width
        df = pd.read_fwf(io.StringIO(text))

    # Normalize column names
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]

    # Look for state FIPS column and total units column
    # Common column names: "state_fips", "fips", "state", "statefips"
    fips_col = None
    for candidate in ["state_fips", "statefips", "fips", "state", "csa"]:
        if candidate in df.columns:
            fips_col = candidate
            break

    # Look for total units column
    units_col = None
    for candidate in ["total", "units", "total_units", "1-unit", "bldgs"]:
        if candidate in df.columns:
            units_col = candidate
            break

    if fips_col is None or units_col is None:
        raise ValueError(
            f"Cannot identify BPS columns. Available: {list(df.columns)}"
        )

    df["state"] = df[fips_col].astype(str).str.zfill(2)
    df["PERMITS"] = pd.to_numeric(df[units_col], errors="coerce")

    # Filter to 50 states
    df = df[df["state"].isin(STATE_FIPS.keys())].copy()

    if len(df) != 50:
        print(f"  WARNING: BPS returned {len(df)} states, expected 50")

    return df[["state", "PERMITS"]].sort_values("state").reset_index(drop=True)
