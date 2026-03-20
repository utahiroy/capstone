"""Fetch EIA electricity price data."""

import requests
import pandas as pd

from src.constants import STATE_FIPS

# State abbreviation to FIPS mapping (needed because EIA uses abbreviations)
_FIPS_TO_ABBR = {
    "01": "AL", "02": "AK", "04": "AZ", "05": "AR", "06": "CA",
    "08": "CO", "09": "CT", "10": "DE", "12": "FL", "13": "GA",
    "15": "HI", "16": "ID", "17": "IL", "18": "IN", "19": "IA",
    "20": "KS", "21": "KY", "22": "LA", "23": "ME", "24": "MD",
    "25": "MA", "26": "MI", "27": "MN", "28": "MS", "29": "MO",
    "30": "MT", "31": "NE", "32": "NV", "33": "NH", "34": "NJ",
    "35": "NM", "36": "NY", "37": "NC", "38": "ND", "39": "OH",
    "40": "OK", "41": "OR", "42": "PA", "44": "RI", "45": "SC",
    "46": "SD", "47": "TN", "48": "TX", "49": "UT", "50": "VT",
    "51": "VA", "53": "WA", "54": "WV", "55": "WI", "56": "WY",
}
_ABBR_TO_FIPS = {v: k for k, v in _FIPS_TO_ABBR.items()}

EIA_BASE = "https://api.eia.gov/v2/electricity/retail-sales/data/"


def fetch_electricity_price(api_key, year=2024):
    """Fetch average retail electricity price (all sectors) by state.

    Returns DataFrame with columns: state, ELEC_PRICE_TOT (cents/kWh).
    """
    params = {
        "api_key": api_key,
        "frequency": "annual",
        "data[0]": "price",
        "facets[sectorid][]": "ALL",
        "start": str(year),
        "end": str(year),
        "sort[0][column]": "stateDescription",
        "sort[0][direction]": "asc",
        "length": "100",
    }
    resp = requests.get(EIA_BASE, params=params, timeout=60)
    resp.raise_for_status()
    payload = resp.json()

    data = payload.get("response", {}).get("data", [])
    if not data:
        raise ValueError(
            f"No EIA electricity data returned for {year}. "
            f"Response: {payload.get('response', {}).get('warnings', payload)}"
        )

    rows = []
    for rec in data:
        state_abbr = rec.get("stateid", "")
        # Skip US total and non-state entries
        if state_abbr not in _ABBR_TO_FIPS:
            continue
        price = rec.get("price")
        if price is not None:
            rows.append({
                "state": _ABBR_TO_FIPS[state_abbr],
                "ELEC_PRICE_TOT": float(price),
            })

    df = pd.DataFrame(rows)
    if len(df) != 50:
        print(f"  WARNING: EIA returned {len(df)} states, expected 50")
    return df.sort_values("state").reset_index(drop=True)
