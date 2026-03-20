"""Fetch Census state land area reference data."""

import io
import requests
import pandas as pd

from src.constants import STATE_FIPS

# Census Bureau state area measurements (2010 Census basis)
LAND_AREA_URL = (
    "https://www2.census.gov/geo/docs/reference/state-area.csv"
)


def fetch_land_area():
    """Fetch land area in square miles for all 50 states.

    Source: Census Bureau state area measurements (2010 Census reference).
    This is a static dataset that does not change between years.

    Returns DataFrame with columns: state, LAND_AREA.
    """
    resp = requests.get(LAND_AREA_URL, timeout=60)

    if resp.status_code != 200:
        print(f"  LAND_AREA: download failed (HTTP {resp.status_code}), using hardcoded values")
        return _hardcoded_land_area()

    try:
        df = pd.read_csv(io.StringIO(resp.text))
    except Exception as e:
        print(f"  LAND_AREA: CSV parse failed ({e}), using hardcoded values")
        return _hardcoded_land_area()

    # Normalize column names
    df.columns = [c.strip() for c in df.columns]

    # Look for FIPS and land area columns
    fips_col = None
    area_col = None
    for c in df.columns:
        cl = c.lower()
        if "fips" in cl or "statefp" in cl:
            fips_col = c
        if "land" in cl and ("sq mi" in cl or "sqmi" in cl or "area" in cl):
            area_col = c

    if fips_col and area_col:
        result = pd.DataFrame({
            "state": df[fips_col].astype(str).str.zfill(2),
            "LAND_AREA": pd.to_numeric(
                df[area_col].astype(str).str.replace(",", ""), errors="coerce"
            ),
        })
        result = result[result["state"].isin(STATE_FIPS.keys())]
        if len(result) == 50:
            print(f"  LAND_AREA: loaded from Census download ({LAND_AREA_URL})")
            return result.sort_values("state").reset_index(drop=True)

    # If parsing fails, use hardcoded values
    print("  LAND_AREA: column matching failed, using hardcoded values")
    return _hardcoded_land_area()


def _hardcoded_land_area():
    """Hardcoded land area (sq mi) from Census 2010 state area measurements.

    This is a static reference dataset. Values do not change.
    """
    data = {
        "01": 50645.33, "02": 570640.95, "04": 113594.08, "05": 52035.48,
        "06": 155779.22, "08": 103641.89, "09": 4842.36, "10": 1948.54,
        "12": 53624.76, "13": 57513.49, "15": 6422.63, "16": 82643.12,
        "17": 55518.93, "18": 35826.11, "19": 55857.13, "20": 81758.72,
        "21": 39486.34, "22": 43203.90, "23": 30842.92, "24": 9707.24,
        "25": 7800.06, "26": 56538.90, "27": 79626.74, "28": 46923.27,
        "29": 68741.52, "30": 145545.80, "31": 76824.17, "32": 109781.18,
        "33": 8952.65, "34": 7354.22, "35": 121298.15, "36": 47126.40,
        "37": 48617.91, "38": 69000.80, "39": 40860.69, "40": 68594.92,
        "41": 95988.01, "42": 44742.70, "44": 1033.81, "45": 30060.70,
        "46": 75811.00, "47": 41234.90, "48": 261231.71, "49": 82169.62,
        "50": 9216.66, "51": 39490.09, "53": 66455.52, "54": 24038.21,
        "55": 54157.80, "56": 97093.14,
    }
    df = pd.DataFrame([
        {"state": k, "LAND_AREA": v} for k, v in data.items()
    ])
    return df.sort_values("state").reset_index(drop=True)
