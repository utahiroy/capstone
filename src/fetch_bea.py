"""Fetch BEA Regional data (GDP, RPP, REAL_PCPI)."""

import requests
import pandas as pd

BEA_BASE = "https://apps.bea.gov/api/data/"


def fetch_bea_regional(table_name, line_code, year, api_key, geo_fips="STATE"):
    """Fetch a BEA Regional table for all states.

    Parameters
    ----------
    table_name : str
        e.g. "SAGDP2N" for GDP, "SARPP" for RPP.
    line_code : int or str
        Line code for the specific series.
    year : int or str
        Data year.
    api_key : str
    geo_fips : str
        "STATE" for all states.

    Returns
    -------
    pd.DataFrame with columns: state, GeoName, DataValue.
    """
    params = {
        "UserID": api_key,
        "method": "GetData",
        "datasetname": "Regional",
        "TableName": table_name,
        "LineCode": str(line_code),
        "GeoFips": geo_fips,
        "Year": str(year),
        "ResultFormat": "JSON",
    }
    resp = requests.get(BEA_BASE, params=params, timeout=60)
    resp.raise_for_status()
    payload = resp.json()

    # BEA wraps everything under BEAAPI
    beaapi = payload.get("BEAAPI", {})

    # Check for API-level errors
    error = beaapi.get("Error", None)
    if error:
        raise ValueError(f"BEA API error: {error}")

    # Results can be a dict or a list depending on the response
    results = beaapi.get("Results", {})

    # Handle case where Results is a list (some BEA endpoints do this)
    if isinstance(results, list):
        if len(results) > 0:
            results = results[0]
        else:
            raise ValueError(f"BEA returned empty Results list for {table_name}")

    data = results.get("Data", [])
    if not data:
        # If year not available, try LAST5 as diagnostic
        raise ValueError(
            f"No data returned for {table_name} LineCode={line_code} Year={year}. "
            f"The {year} vintage may not yet be published for this table. "
            f"Results keys: {list(results.keys())}"
        )

    df = pd.DataFrame(data)

    # BEA GeoFips for states are 5 digits ("06000" for CA) or sometimes
    # just 2 digits ("06"). Handle both.
    if "GeoFips" not in df.columns:
        raise ValueError(f"No GeoFips column in BEA response. Columns: {list(df.columns)}")

    df["GeoFips"] = df["GeoFips"].astype(str).str.strip()

    # Filter to state-level: 5-digit codes ending in "000" (not "00000" US total),
    # or 2-digit state codes (not "00" US total)
    is_5digit_state = (df["GeoFips"].str.len() == 5) & (df["GeoFips"] != "00000")
    is_2digit_state = (df["GeoFips"].str.len() == 2) & (df["GeoFips"] != "00")
    df = df[is_5digit_state | is_2digit_state].copy()

    if df.empty:
        all_fips = payload.get("BEAAPI", {}).get("Results", {})
        raise ValueError(
            f"No state-level rows found after filtering GeoFips. "
            f"Sample GeoFips values from raw response may not match expected format."
        )

    # Normalize to 2-digit state FIPS
    df["state"] = df["GeoFips"].apply(
        lambda x: x[:2] if len(x) == 5 else x.zfill(2)
    )

    # Exclude DC (11), PR (72), and other non-state geographies
    from src.constants import STATE_FIPS
    df = df[df["state"].isin(STATE_FIPS.keys())].copy()

    # Convert DataValue to numeric (BEA returns strings, sometimes with commas,
    # and "(NA)" or "(D)" for unavailable/suppressed values)
    df["DataValue"] = (
        df["DataValue"]
        .astype(str)
        .str.replace(",", "", regex=False)
        .str.strip()
    )
    df["DataValue"] = pd.to_numeric(df["DataValue"], errors="coerce")

    return df[["state", "GeoName", "DataValue"]].reset_index(drop=True)


def fetch_gdp(api_key, year=2024, allow_fallback=False):
    """Fetch state GDP (all-industry total, current dollars).

    Parameters
    ----------
    api_key : str
    year : int
        Must match the project year (2024).
    allow_fallback : bool
        If False (default), raises an error when the requested year is
        unavailable. If True, retries with year-1 and tags the output
        with a GDP_YEAR_NOTE column. Fallback is for debugging only and
        must not be used in production pipeline runs.
    """
    try:
        df = fetch_bea_regional("SAGDP2N", line_code=1, year=year, api_key=api_key)
        if df["DataValue"].isna().all():
            raise ValueError(f"All GDP values are NA for year {year}")
        return df.rename(columns={"DataValue": "GDP"})
    except ValueError as e:
        if not allow_fallback:
            raise ValueError(
                f"GDP for {year} is unavailable from BEA. "
                f"Original error: {e}\n"
                f"This project is fixed to {year} cross-section only. "
                f"Do not substitute a different year without explicit approval."
            ) from e
        # Fallback path — debug only
        fallback_year = year - 1
        print(f"  WARNING: GDP fetch for {year} failed: {e}")
        print(f"  DEBUG FALLBACK to year {fallback_year} (allow_fallback=True)")
        df = fetch_bea_regional(
            "SAGDP2N", line_code=1, year=fallback_year, api_key=api_key
        )
        df = df.rename(columns={"DataValue": "GDP"})
        df["GDP_YEAR_NOTE"] = f"debug fallback to {fallback_year}"
        return df
