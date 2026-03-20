"""Fetch Census Building Permits Survey (BPS) state annual data."""

import io
import requests
import pandas as pd

from src.constants import STATE_FIPS

# Census BPS state annual data — multiple URL patterns by year
BPS_URL_PATTERNS = [
    "https://www2.census.gov/econ/bps/State/st{yyyy}a.txt",
    "https://www2.census.gov/econ/bps/State/st{yy}a.txt",
    "https://www2.census.gov/econ/bps/State/st_annual_{yyyy}.csv",
]

# Census Building Permits API (JSON) — fallback
BPS_API_URL = "https://api.census.gov/data/timeseries/bps/houseunits"

# Known BPS state annual file structure (2024 vintage):
#
#   The file has a 2-row header. The raw CSV columns are:
#     survey_date, fips, region, division, state_name,
#     1unit_bldgs, 1unit_units, 1unit_value,
#     2unit_bldgs, 2unit_units, 2unit_value,
#     34unit_bldgs, 34unit_units, 34unit_value,
#     5plus_bldgs, 5plus_units, 5plus_value,
#     [optional: _rep columns for each category]
#
#   Data rows look like: 202499,01,3,6,Alabama,17423,17423,...
#
#   PERMITS = 1unit_units + 2unit_units + 34unit_units + 5plus_units

# Canonical column names we assign after skipping the 2-row header.
# The exact number of columns varies (some years include _rep columns).
# We define the first 17 columns which are always present.
_BPS_CORE_COLS = [
    "survey", "fips", "region", "division", "state_name",
    "1unit_bldgs", "1unit_units", "1unit_value",
    "2unit_bldgs", "2unit_units", "2unit_value",
    "34unit_bldgs", "34unit_units", "34unit_value",
    "5plus_bldgs", "5plus_units", "5plus_value",
]

_UNIT_COLS = ["1unit_units", "2unit_units", "34unit_units", "5plus_units"]


def _try_download_bps(year):
    """Try to download the BPS text/CSV file from Census."""
    yy = str(year)[-2:]
    yyyy = str(year)
    for pattern in BPS_URL_PATTERNS:
        url = pattern.format(yy=yy, yyyy=yyyy)
        try:
            resp = requests.get(url, timeout=60)
            if resp.status_code == 200 and len(resp.text) > 200:
                return resp, url
        except requests.RequestException:
            continue
    return None, None


def _parse_bps_text(text, url):
    """Parse BPS state annual text file with known column structure.

    Skips the 2-row header, assigns canonical column names, and sums
    the 4 primary unit columns to compute total PERMITS.

    Returns DataFrame with columns: state, PERMITS.
    """
    lines = text.strip().split("\n")
    print(f"  PERMITS: total lines = {len(lines)}")
    for i, line in enumerate(lines[:5]):
        print(f"  PERMITS: raw line {i}: {line[:150]}")

    # Find where data rows start by looking for the first line that
    # begins with a 6-digit survey code (e.g. "202499")
    data_start = None
    for i, line in enumerate(lines):
        fields = line.split(",")
        if len(fields) >= 10:
            first_field = fields[0].strip().strip('"')
            if first_field.isdigit() and len(first_field) == 6:
                data_start = i
                break

    if data_start is None:
        raise ValueError(
            f"Cannot find data start in BPS file. "
            f"First 5 lines: {lines[:5]}"
        )

    print(f"  PERMITS: data starts at line {data_start}")

    # Read only the data rows (skip all header rows)
    data_text = "\n".join(lines[data_start:])
    df = pd.read_csv(io.StringIO(data_text), header=None, dtype=str,
                      on_bad_lines="skip")

    n_cols = len(df.columns)
    print(f"  PERMITS: {len(df)} data rows, {n_cols} columns")

    # Assign canonical column names for the first 17 columns
    n_core = min(n_cols, len(_BPS_CORE_COLS))
    col_names = list(_BPS_CORE_COLS[:n_core])
    # Name any extra columns generically
    for j in range(n_core, n_cols):
        col_names.append(f"extra_{j}")
    df.columns = col_names

    print(f"  PERMITS: assigned columns: {list(df.columns)}")
    print(f"  PERMITS: first 3 data rows:\n{df.head(3).to_string(index=False)}")

    # Verify alignment: fips should be 1-2 digit state codes,
    # state_name should be text
    sample_fips = df["fips"].head(5).tolist()
    sample_names = df["state_name"].head(5).tolist()
    print(f"  PERMITS: sample fips={sample_fips}, names={sample_names}")

    # Normalize state FIPS to 2-digit zero-padded string
    df["state"] = (
        df["fips"].astype(str).str.strip().str.strip('"')
        .str.replace(r"\.0$", "", regex=True)
        .str.zfill(2)
    )

    # Parse and sum the 4 primary unit columns
    for col in _UNIT_COLS:
        if col not in df.columns:
            raise ValueError(f"Expected column '{col}' not found. Have: {list(df.columns)}")
        df[col] = pd.to_numeric(
            df[col].astype(str).str.replace(",", "").str.strip().str.strip('"'),
            errors="coerce",
        )

    df["PERMITS"] = df[_UNIT_COLS].sum(axis=1)
    print(f"  PERMITS: summing {_UNIT_COLS}")

    # Filter to 50 states
    df = df[df["state"].isin(STATE_FIPS.keys())].copy()

    # Deduplicate (shouldn't happen with annual state-level data, but be safe)
    if df["state"].duplicated().any():
        df = df.groupby("state", as_index=False)["PERMITS"].sum()

    print(f"  PERMITS: {len(df)} states after filtering")
    return df[["state", "PERMITS"]].sort_values("state").reset_index(drop=True)


def _fetch_bps_api(year):
    """Fallback: use Census BPS JSON API for state-level total permits."""
    params = {
        "get": "units",
        "for": "state:*",
        "time": str(year),
        "category_code": "TOTAL",
    }
    resp = requests.get(BPS_API_URL, params=params, timeout=60)
    if resp.status_code != 200:
        raise ValueError(
            f"BPS API returned HTTP {resp.status_code}. "
            f"URL: {BPS_API_URL}, params: {params}"
        )
    data = resp.json()
    df = pd.DataFrame(data[1:], columns=data[0])
    df["state"] = df["state"].astype(str).str.zfill(2)
    df["PERMITS"] = pd.to_numeric(df["units"], errors="coerce")
    df = df[df["state"].isin(STATE_FIPS.keys())].copy()
    return df[["state", "PERMITS"]].sort_values("state").reset_index(drop=True)


def fetch_permits(year=2024):
    """Fetch total housing units authorized by building permits, state-level.

    PERMITS = 1-unit + 2-units + 3-4 units + 5+ units (housing units authorized).

    Strategy:
    1. Download BPS state annual text file, skip 2-row header, sum unit columns.
    2. If text parse fails or returns <48 states, try Census BPS API.

    Returns DataFrame with columns: state, PERMITS.
    """
    resp, url = _try_download_bps(year)
    if resp is not None:
        print(f"  PERMITS: downloaded from {url}")
        try:
            df = _parse_bps_text(resp.text, url)
            if len(df) >= 48:
                if len(df) != 50:
                    print(f"  WARNING: BPS text returned {len(df)} states")
                return df
            print(f"  PERMITS: text parse returned {len(df)} states, trying API")
        except Exception as e:
            print(f"  PERMITS: text parse failed ({e}), trying API")

    print("  PERMITS: trying Census BPS API")
    try:
        df = _fetch_bps_api(year)
        print(f"  PERMITS: API returned {len(df)} states")
        if len(df) != 50:
            print(f"  WARNING: BPS returned {len(df)} states, expected 50")
        return df
    except Exception as e:
        print(f"  PERMITS: API also failed: {e}")

    raise ValueError(
        f"Could not fetch building permits for {year}. "
        f"Both text download and API fallback failed."
    )
