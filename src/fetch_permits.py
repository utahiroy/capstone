"""Fetch Census Building Permits Survey (BPS) state annual data."""

import io
import requests
import pandas as pd

from src.constants import STATE_FIPS

# Census BPS state annual data — multiple URL patterns by year
BPS_URL_PATTERNS = [
    "https://www2.census.gov/econ/bps/State/st{yy}a.txt",
    "https://www2.census.gov/econ/bps/State/st{yyyy}a.txt",
    "https://www2.census.gov/econ/bps/State/st_annual_{yyyy}.csv",
]

# Census Building Permits API (JSON) — more reliable than text downloads
BPS_API_URL = "https://api.census.gov/data/timeseries/bps/houseunits"


def _try_download_bps(year):
    """Try to download the BPS text/CSV file from Census.

    Returns (response, url) or (None, None) if all patterns fail.
    """
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
    """Parse BPS text/CSV download into a DataFrame with state+PERMITS columns.

    The BPS state annual file is typically comma-separated with columns like:
    state, total, 1-unit, 2-unit, 3-4 unit, 5+ units, ...
    Some years use different header names or have extra header/footer rows.
    """
    # Try CSV parse, skipping bad lines
    try:
        df = pd.read_csv(
            io.StringIO(text),
            dtype=str,              # read all as string to avoid FIPS int conversion
            on_bad_lines="skip",
        )
    except Exception:
        try:
            df = pd.read_fwf(io.StringIO(text), dtype=str)
        except Exception as e:
            raise ValueError(f"Cannot parse BPS file from {url}: {e}")

    # Normalize column names
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]

    print(f"  PERMITS: columns = {list(df.columns)}")
    print(f"  PERMITS: first 3 rows:\n{df.head(3).to_string(index=False)}")

    # Find state FIPS column — prioritize explicitly numeric FIPS columns
    # over "state" which may contain state names
    fips_col = None
    for candidate in ["fips", "state_fips", "statefips", "stfips", "fipstate",
                       "code", "csa"]:
        if candidate in df.columns:
            fips_col = candidate
            break
    # Only use "state" column as FIPS if it contains numeric values
    if fips_col is None and "state" in df.columns:
        test_vals = pd.to_numeric(
            df["state"].astype(str).str.strip().str.replace(r"\.0$", "", regex=True),
            errors="coerce",
        )
        if test_vals.notna().sum() > 30:
            fips_col = "state"
        else:
            print(f"  PERMITS: 'state' column contains non-numeric values, skipping as FIPS")
    # Partial match fallback
    if fips_col is None:
        for c in df.columns:
            if "fips" in c:
                fips_col = c
                break

    # Find total units column — BPS state annual files typically have:
    #   fips, state, total, 1-unit bldgs, 1-unit units, 2-unit bldgs, ...
    # "total" = total units across all building types
    units_col = None
    for candidate in ["total", "units", "total_units", "1-unit_units",
                       "all_units", "tot", "bldgs", "1-unit"]:
        if candidate in df.columns:
            # Verify it looks numeric
            test_vals = pd.to_numeric(
                df[candidate].astype(str).str.replace(",", "").str.strip(),
                errors="coerce",
            )
            if test_vals.notna().sum() > 20:
                units_col = candidate
                break
    # Fallback: search for column containing "unit" or "total"
    if units_col is None:
        for c in df.columns:
            cl = c.lower()
            if "total" in cl or "unit" in cl:
                test_vals = pd.to_numeric(
                    df[c].astype(str).str.replace(",", "").str.strip(),
                    errors="coerce",
                )
                if test_vals.notna().sum() > 20:
                    units_col = c
                    break

    if fips_col is None or units_col is None:
        raise ValueError(
            f"Cannot identify BPS columns. "
            f"fips_col={fips_col}, units_col={units_col}. "
            f"Available: {list(df.columns)}"
        )

    print(f"  PERMITS: using fips_col={fips_col}, units_col={units_col}")

    # Normalize state FIPS to 2-digit zero-padded string
    df["state"] = (
        df[fips_col]
        .astype(str)
        .str.strip()
        .str.replace(r"\.0$", "", regex=True)   # handle "1.0" from float conversion
        .str.zfill(2)
    )

    # Parse units — remove commas, convert to numeric
    df["PERMITS"] = pd.to_numeric(
        df[units_col].astype(str).str.replace(",", "", regex=False).str.strip(),
        errors="coerce",
    )

    # Filter to 50 states only
    df = df[df["state"].isin(STATE_FIPS.keys())].copy()

    # If multiple rows per state (sub-categories), take the max (state total row)
    if df["state"].duplicated().any():
        df = df.groupby("state", as_index=False)["PERMITS"].max()

    return df[["state", "PERMITS"]].sort_values("state").reset_index(drop=True)


def _fetch_bps_api(year):
    """Fallback: use Census BPS JSON API for state-level total permits.

    This endpoint does not require an API key for basic queries.
    """
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

    Strategy:
    1. Try downloading the BPS state annual text/CSV file.
    2. If download fails or returns <50 states, try Census BPS API.

    Returns DataFrame with columns: state, PERMITS.
    """
    # Strategy 1: download text/CSV
    resp, url = _try_download_bps(year)
    if resp is not None:
        print(f"  PERMITS: downloaded from {url}")
        try:
            df = _parse_bps_text(resp.text, url)
            if len(df) == 50:
                return df
            print(f"  PERMITS: text parse returned {len(df)} states, trying API fallback")
        except Exception as e:
            print(f"  PERMITS: text parse failed ({e}), trying API fallback")

    # Strategy 2: Census BPS API
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
