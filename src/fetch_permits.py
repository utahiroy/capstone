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
    """Parse BPS state annual text file.

    The 2024 file has a 2-row header structure and columns:
        FIPS, State, 1-unit (Bldgs, Units, Value),
        2-units (Bldgs, Units, Value), 3-4 units (...), 5+ units (...)
    There is no single "total" column, so we sum the unit columns:
        PERMITS = 1-unit_units + 2-units_units + 3-4_units_units + 5+_units_units

    Returns DataFrame with columns: state, PERMITS.
    """
    # Read lines to inspect header structure
    lines = text.strip().split("\n")
    print(f"  PERMITS: total lines = {len(lines)}")
    for i, line in enumerate(lines[:5]):
        print(f"  PERMITS: line {i}: {line[:120]}")

    # Try parsing with header=0 first (single-row header)
    df = pd.read_csv(io.StringIO(text), dtype=str, on_bad_lines="skip")
    orig_columns = list(df.columns)
    # Normalize column names: lowercase, strip, replace spaces with _
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
    norm_columns = list(df.columns)
    print(f"  PERMITS: parsed columns = {norm_columns}")

    # If the first data row looks like a sub-header (contains non-numeric
    # values in what should be numeric columns), skip it
    if len(df) > 1:
        first_row = df.iloc[0]
        numeric_cols = [c for c in df.columns if c not in ("fips", "state")]
        if numeric_cols:
            test = pd.to_numeric(
                first_row[numeric_cols[0:1]].astype(str).str.replace(",", ""),
                errors="coerce",
            )
            if test.isna().all():
                print(f"  PERMITS: first data row looks like sub-header, skipping")
                # Re-read with header=[0,1] to merge the two header rows
                try:
                    df2 = pd.read_csv(
                        io.StringIO(text), header=[0, 1], dtype=str,
                        on_bad_lines="skip",
                    )
                    # Flatten multi-level column names
                    df2.columns = [
                        "_".join(str(c).strip() for c in col).strip("_")
                        for col in df2.columns
                    ]
                    df2.columns = [
                        c.strip().lower().replace(" ", "_")
                        for c in df2.columns
                    ]
                    df = df2
                    norm_columns = list(df.columns)
                    print(f"  PERMITS: re-parsed with 2-row header: {norm_columns}")
                except Exception as e:
                    print(f"  PERMITS: 2-row header parse failed ({e}), "
                          f"falling back to skip row 0")
                    df = df.iloc[1:].reset_index(drop=True)

    print(f"  PERMITS: final columns = {list(df.columns)}")
    print(f"  PERMITS: {len(df)} data rows")
    if len(df) > 0:
        print(f"  PERMITS: first 3 rows:\n{df.head(3).to_string(index=False)}")

    # Find FIPS column — must contain numeric state FIPS codes
    fips_col = None
    for candidate in df.columns:
        cl = candidate.lower()
        if "fips" in cl:
            fips_col = candidate
            break
    # If no "fips" column, check if "state" has numeric values
    if fips_col is None:
        for candidate in df.columns:
            cl = candidate.lower()
            if "state" in cl or cl == "code":
                test = pd.to_numeric(
                    df[candidate].astype(str).str.strip().str.replace(
                        r"\.0$", "", regex=True
                    ),
                    errors="coerce",
                )
                if test.notna().sum() > 30:
                    fips_col = candidate
                    break

    if fips_col is None:
        raise ValueError(
            f"Cannot find FIPS column. Available: {list(df.columns)}"
        )
    print(f"  PERMITS: using fips_col={fips_col}")

    # Normalize state FIPS
    df["state"] = (
        df[fips_col].astype(str).str.strip()
        .str.replace(r"\.0$", "", regex=True)
        .str.zfill(2)
    )

    # Find unit columns to sum for total permits
    # The BPS file has columns like: 1-unit (with sub-columns Bldgs, Units, Value)
    # After flattening, these become something like: 1-unit_units, 2-units_units, etc.
    # We need to find all "units" sub-columns and sum them.
    unit_cols = _find_unit_columns(df)

    if unit_cols:
        print(f"  PERMITS: summing unit columns: {unit_cols}")
        for col in unit_cols:
            df[col] = pd.to_numeric(
                df[col].astype(str).str.replace(",", "").str.strip(),
                errors="coerce",
            )
        df["PERMITS"] = df[unit_cols].sum(axis=1)
    else:
        # Last resort: look for any single column that could be total
        total_col = _find_total_column(df)
        if total_col:
            print(f"  PERMITS: using single total column: {total_col}")
            df["PERMITS"] = pd.to_numeric(
                df[total_col].astype(str).str.replace(",", "").str.strip(),
                errors="coerce",
            )
        else:
            raise ValueError(
                f"Cannot identify unit columns to sum. Columns: {list(df.columns)}"
            )

    # Filter to 50 states
    df = df[df["state"].isin(STATE_FIPS.keys())].copy()

    # Deduplicate if needed
    if df["state"].duplicated().any():
        df = df.groupby("state", as_index=False)["PERMITS"].sum()

    return df[["state", "PERMITS"]].sort_values("state").reset_index(drop=True)


def _find_unit_columns(df):
    """Find columns representing housing units for each building-type category.

    BPS files have categories: 1-unit, 2-units, 3-4 units, 5+ units.
    Each has sub-columns: Bldgs, Units, Value.
    We want the "Units" sub-column for each category.

    After multi-header flattening, column names look like:
        "1-unit_units", "2-units_units", "3-4_units_units", "5+_units_units"
    Or with original single header:
        "1-unit", "2-units", "3-4 units", "5+ units" (these ARE the unit counts)
    """
    cols = list(df.columns)
    unit_cols = []

    # Pattern 1: flattened multi-header — look for columns ending in "_units"
    # but not "bldgs" or "value"
    for c in cols:
        cl = c.lower()
        if cl.endswith("_units") or cl.endswith("_units_"):
            # Exclude columns that are clearly not counts
            if "value" not in cl and "bldg" not in cl:
                unit_cols.append(c)

    if len(unit_cols) >= 3:
        return unit_cols

    # Pattern 2: single-header BPS file — the unit-count columns are named
    # "1-unit", "2-units", "3-4 units", "5+ units" directly
    unit_cols = []
    unit_patterns = ["1-unit", "2-unit", "3-4", "5+"]
    for c in cols:
        cl = c.lower().replace("_", " ").replace("-", " ")
        # Match columns like "1 unit", "2 units", "3 4 units", "5+ units"
        for pat in unit_patterns:
            pat_norm = pat.replace("-", " ")
            if pat_norm in cl and "bldg" not in cl and "val" not in cl:
                # Verify it has numeric data
                test = pd.to_numeric(
                    df[c].astype(str).str.replace(",", "").str.strip(),
                    errors="coerce",
                )
                if test.notna().sum() > 20:
                    unit_cols.append(c)
                    break

    if len(unit_cols) >= 2:
        return unit_cols

    return []


def _find_total_column(df):
    """Fallback: find a single total-units column."""
    for c in df.columns:
        cl = c.lower()
        if "total" in cl and "value" not in cl and "bldg" not in cl:
            test = pd.to_numeric(
                df[c].astype(str).str.replace(",", "").str.strip(),
                errors="coerce",
            )
            if test.notna().sum() > 20:
                return c
    return None


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

    Strategy:
    1. Try downloading the BPS state annual text/CSV file and summing
       unit columns (1-unit + 2-units + 3-4 units + 5+ units).
    2. If download fails or returns <50 states, try Census BPS API.

    Returns DataFrame with columns: state, PERMITS.
    """
    resp, url = _try_download_bps(year)
    if resp is not None:
        print(f"  PERMITS: downloaded from {url}")
        try:
            df = _parse_bps_text(resp.text, url)
            if len(df) >= 48:  # allow minor shortfall
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
