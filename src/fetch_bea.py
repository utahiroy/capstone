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
    pd.DataFrame with columns: GeoFips, GeoName, DataValue.
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

    results = payload.get("BEAAPI", {}).get("Results", {})
    data = results.get("Data", [])
    if not data:
        raise ValueError(f"No data returned for {table_name} LineCode={line_code} Year={year}")

    df = pd.DataFrame(data)
    # Keep only state-level rows (GeoFips like "XX000", length 5, not "00000" US total)
    df = df[df["GeoFips"].str.len() == 5].copy()
    df = df[df["GeoFips"] != "00000"].copy()

    # Convert DataValue to numeric (BEA returns strings, sometimes with commas)
    df["DataValue"] = df["DataValue"].str.replace(",", "").str.strip()
    df["DataValue"] = pd.to_numeric(df["DataValue"], errors="coerce")

    # Create 2-digit state FIPS for joining
    df["state"] = df["GeoFips"].str[:2]

    return df[["state", "GeoName", "DataValue"]].reset_index(drop=True)


def fetch_gdp(api_key, year=2024):
    """Fetch state GDP (all-industry total, current dollars)."""
    df = fetch_bea_regional("SAGDP2N", line_code=1, year=year, api_key=api_key)
    return df.rename(columns={"DataValue": "GDP"})
