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


def _try_eia_request(url, headers=None):
    """Make EIA request and return (response, error_info)."""
    try:
        resp = requests.get(url, headers=headers, timeout=60)
        return resp, None
    except Exception as e:
        return None, str(e)


def _parse_eia_response(payload):
    """Extract state-level electricity prices from EIA response payload."""
    data = payload.get("response", {}).get("data", [])
    if not data:
        return pd.DataFrame(columns=["state", "ELEC_PRICE_TOT"])

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

    return pd.DataFrame(rows)


def fetch_electricity_price(api_key, year=2024):
    """Fetch average retail electricity price (all sectors) by state.

    Tries multiple request strategies to handle EIA v2 API parameter encoding:
    1. Manual URL with X-API-Key header
    2. Manual URL with api_key as query param
    3. requests-encoded params with api_key as query param

    Returns DataFrame with columns: state, ELEC_PRICE_TOT (cents/kWh).
    """
    strategies = []

    # Strategy 1: Manual URL with header auth (avoids bracket encoding issues)
    url1 = (
        f"{EIA_BASE}"
        f"?frequency=annual"
        f"&data[0]=price"
        f"&facets[sectorid][]=ALL"
        f"&start={year}"
        f"&end={year}"
        f"&sort[0][column]=stateDescription"
        f"&sort[0][direction]=asc"
        f"&length=100"
    )
    strategies.append(("header_auth_manual_url", url1, {"X-API-Key": api_key}))

    # Strategy 2: Manual URL with api_key as query param
    url2 = url1 + f"&api_key={api_key}"
    strategies.append(("query_param_manual_url", url2, None))

    # Strategy 3: Simpler URL (no sort, which may cause the 400)
    url3 = (
        f"{EIA_BASE}"
        f"?api_key={api_key}"
        f"&frequency=annual"
        f"&data[0]=price"
        f"&facets[sectorid][]=ALL"
        f"&start={year}"
        f"&end={year}"
        f"&length=100"
    )
    strategies.append(("no_sort", url3, None))

    # Strategy 4: Residential sector instead of ALL (in case ALL is not valid)
    url4 = (
        f"{EIA_BASE}"
        f"?api_key={api_key}"
        f"&frequency=annual"
        f"&data[0]=price"
        f"&facets[sectorid][]=RES"
        f"&start={year}"
        f"&end={year}"
        f"&length=100"
    )
    strategies.append(("residential_sector", url4, None))

    # Strategy 5: Let requests encode (for comparison)
    strategies.append(("requests_encoded", None, None))

    for name, url, headers in strategies:
        if name == "requests_encoded":
            params = {
                "api_key": api_key,
                "frequency": "annual",
                "data[0]": "price",
                "facets[sectorid][]": "ALL",
                "start": str(year),
                "end": str(year),
                "length": "100",
            }
            try:
                resp = requests.get(EIA_BASE, params=params, timeout=60)
            except Exception as e:
                print(f"  EIA strategy '{name}': request error: {e}")
                continue
        else:
            resp, err = _try_eia_request(url, headers)
            if resp is None:
                print(f"  EIA strategy '{name}': request error: {err}")
                continue

        print(f"  EIA strategy '{name}': HTTP {resp.status_code}")

        if resp.status_code != 200:
            # Log the error response body for diagnosis
            body = resp.text[:300]
            print(f"  EIA strategy '{name}': response body: {body}")
            continue

        try:
            payload = resp.json()
        except Exception:
            print(f"  EIA strategy '{name}': response is not valid JSON")
            continue

        df = _parse_eia_response(payload)
        if len(df) > 0:
            print(f"  EIA strategy '{name}': SUCCESS, {len(df)} states")
            if len(df) != 50:
                print(f"  WARNING: EIA returned {len(df)} states, expected 50")
            return df.sort_values("state").reset_index(drop=True)
        else:
            # Log what we got
            resp_data = payload.get("response", {})
            warnings = resp_data.get("warnings", [])
            total = resp_data.get("total", 0)
            print(f"  EIA strategy '{name}': 0 parseable rows, "
                  f"total={total}, warnings={warnings}")

    raise ValueError(
        f"All EIA request strategies failed for year={year}. "
        f"Run 'python -m scripts.debug_a22b' for detailed diagnostics."
    )
