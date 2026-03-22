"""Fetch EIA electricity price data."""

import time
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

    Uses EIA v2 API with api_key as query parameter and no sort params
    (sort params cause 400 Bad Request).

    Returns DataFrame with columns: state, ELEC_PRICE_TOT (cents/kWh).
    """
    # Build URL manually — bracket-notation params must not be percent-encoded
    # by requests, and sort params are omitted (they cause 400).
    url = (
        f"{EIA_BASE}"
        f"?api_key={api_key}"
        f"&frequency=annual"
        f"&data[0]=price"
        f"&facets[sectorid][]=ALL"
        f"&start={year}"
        f"&end={year}"
        f"&length=100"
    )

    max_retries = 3
    resp = None
    for attempt in range(max_retries):
        try:
            resp = requests.get(url, timeout=120)
            if resp.status_code == 200:
                break
            print(f"  EIA: HTTP {resp.status_code} (attempt {attempt + 1}/{max_retries})")
        except requests.exceptions.RequestException as e:
            print(f"  EIA request error (attempt {attempt + 1}/{max_retries}): {e}")
        if attempt < max_retries - 1:
            wait = 2 ** (attempt + 1)
            print(f"  Retrying in {wait}s...")
            time.sleep(wait)

    if resp is None or resp.status_code != 200:
        msg = resp.text[:300] if resp else "No response"
        raise RuntimeError(f"EIA API failed after {max_retries} attempts: {msg}")

    payload = resp.json()

    data = payload.get("response", {}).get("data", [])
    if not data:
        warnings = payload.get("response", {}).get("warnings", [])
        raise ValueError(
            f"No EIA electricity data returned for {year}. "
            f"Warnings: {warnings}"
        )

    rows = []
    for rec in data:
        state_abbr = rec.get("stateid", rec.get("stateId", ""))
        if state_abbr not in _ABBR_TO_FIPS:
            continue
        price = rec.get("price")
        if price is not None:
            rows.append({
                "state": _ABBR_TO_FIPS[state_abbr],
                "ELEC_PRICE_TOT": float(price),
            })

    df = pd.DataFrame(rows)
    if df.empty:
        raise ValueError(
            f"EIA returned data but no state-level prices found. "
            f"Sample record keys: {list(data[0].keys()) if data else 'N/A'}"
        )

    print(f"  ELEC_PRICE_TOT: {len(df)} states")
    if len(df) != 50:
        print(f"  WARNING: EIA returned {len(df)} states, expected 50")
    return df.sort_values("state").reset_index(drop=True)
