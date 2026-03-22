"""Fetch state-level violent crime rate from FBI Crime Data Explorer API.

Source: FBI Uniform Crime Reporting (UCR) program, via CDE API.
Variable: CRIME_VIOLENT_RATE — estimated violent crime rate per 100,000 population.

Violent crime definition (FBI): murder and nonnegligent manslaughter, rape,
robbery, aggravated assault.

API endpoints tried (in order):
  1. CDE v2: https://api.usa.gov/crime/fbi/cde/estimate/state/{abbr}/violent-crime
     (current as of July 2025 endpoint migration)
  2. SAPI v1: https://api.usa.gov/crime/fbi/sapi/api/estimates/states/{abbr}/{year}/{year}
     (legacy, may return 403 after July 2025 changes)
  3. CSV fallback: data_raw/fbi_crime_state_2024.csv

Requires: DATA_GOV_API_KEY (free from https://api.data.gov/signup/)
"""

import time
import requests
import pandas as pd

# 50-state abbreviations mapped to FIPS (excludes DC)
STATE_ABBR_TO_FIPS = {
    "AL": "01", "AK": "02", "AZ": "04", "AR": "05", "CA": "06",
    "CO": "08", "CT": "09", "DE": "10", "FL": "12", "GA": "13",
    "HI": "15", "ID": "16", "IL": "17", "IN": "18", "IA": "19",
    "KS": "20", "KY": "21", "LA": "22", "ME": "23", "MD": "24",
    "MA": "25", "MI": "26", "MN": "27", "MS": "28", "MO": "29",
    "MT": "30", "NE": "31", "NV": "32", "NH": "33", "NJ": "34",
    "NM": "35", "NY": "36", "NC": "37", "ND": "38", "OH": "39",
    "OK": "40", "OR": "41", "PA": "42", "RI": "44", "SC": "45",
    "SD": "46", "TN": "47", "TX": "48", "UT": "49", "VT": "50",
    "VA": "51", "WA": "53", "WV": "54", "WI": "55", "WY": "56",
}

FIPS_TO_ABBR = {v: k for k, v in STATE_ABBR_TO_FIPS.items()}


def _try_cde_endpoint(api_key, year=2024, max_retries=3):
    """Try the newer CDE estimate endpoint (post-July 2025 migration).

    Fetches all 50 states using per-state calls.
    CDE endpoint: /cde/estimate/state/{abbr}/violent-crime?from={year}&to={year}
    Returns list of dicts or raises RuntimeError.
    """
    rows = []
    failed = []
    base = "https://api.usa.gov/crime/fbi/cde"

    for abbr, fips in sorted(STATE_ABBR_TO_FIPS.items()):
        url = f"{base}/estimate/state/{abbr}/violent-crime"
        params = {"from": year, "to": year, "API_KEY": api_key}

        success = False
        for attempt in range(max_retries):
            try:
                resp = requests.get(url, params=params, timeout=30)
                if resp.status_code == 200:
                    data = resp.json()
                    # CDE returns a list or dict with yearly records
                    records = data if isinstance(data, list) else data.get("results", [data])
                    for rec in records:
                        if not isinstance(rec, dict):
                            continue
                        rec_year = rec.get("year") or rec.get("data_year")
                        if rec_year and int(rec_year) != year:
                            continue
                        violent = rec.get("violent_crime") or rec.get("value")
                        pop = rec.get("population")
                        if violent is not None and pop is not None and pop > 0:
                            rows.append({
                                "state": fips,
                                "CRIME_VIOLENT_RATE": round(100000 * violent / pop, 1),
                                "CRIME_VIOLENT_COUNT": violent,
                                "CRIME_POPULATION": pop,
                                "CRIME_SOURCE": "FBI_CDE_API",
                            })
                            success = True
                            break
                    if success:
                        break
                    # Got 200 but couldn't extract data — try next year match
                    if not success and records:
                        # Maybe no year filter needed, take first valid record
                        rec = records[-1] if isinstance(records[-1], dict) else None
                        if rec:
                            violent = rec.get("violent_crime") or rec.get("value")
                            pop = rec.get("population")
                            if violent is not None and pop is not None and pop > 0:
                                rows.append({
                                    "state": fips,
                                    "CRIME_VIOLENT_RATE": round(100000 * violent / pop, 1),
                                    "CRIME_VIOLENT_COUNT": violent,
                                    "CRIME_POPULATION": pop,
                                    "CRIME_SOURCE": "FBI_CDE_API",
                                })
                                success = True
                    break
                elif resp.status_code == 429:
                    wait = 2 ** (attempt + 1)
                    print(f"    Rate limited for {abbr}, waiting {wait}s...")
                    time.sleep(wait)
                elif resp.status_code in (403, 404):
                    # Endpoint doesn't work — bail out of this method entirely
                    raise RuntimeError(
                        f"CDE endpoint returned {resp.status_code} for {abbr}"
                    )
                else:
                    break
            except requests.exceptions.RequestException as e:
                if attempt < max_retries - 1:
                    time.sleep(2 ** (attempt + 1))
                else:
                    failed.append(abbr)

        if not success:
            failed.append(abbr)

    if len(rows) < 25:
        raise RuntimeError(
            f"CDE endpoint: only {len(rows)}/50 states returned data"
        )

    if failed:
        print(f"  CDE: {len(failed)} states failed: {', '.join(failed[:10])}")
    return rows


def _try_sapi_endpoint(api_key, year=2024, max_retries=3):
    """Try the legacy SAPI estimate endpoint.

    Endpoint: /sapi/api/estimates/states/{abbr}/{year}/{year}
    """
    rows = []
    failed = []
    base = "https://api.usa.gov/crime/fbi/sapi"

    for abbr, fips in sorted(STATE_ABBR_TO_FIPS.items()):
        url = f"{base}/api/estimates/states/{abbr}/{year}/{year}"
        params = {"api_key": api_key}

        success = False
        for attempt in range(max_retries):
            try:
                resp = requests.get(url, params=params, timeout=30)
                if resp.status_code == 200:
                    data = resp.json()
                    results = (data.get("results", data)
                               if isinstance(data, dict) else data)
                    if isinstance(results, list):
                        for rec in results:
                            if not isinstance(rec, dict):
                                continue
                            violent = rec.get("violent_crime")
                            pop = rec.get("population")
                            if violent is not None and pop is not None and pop > 0:
                                rows.append({
                                    "state": fips,
                                    "CRIME_VIOLENT_RATE": round(100000 * violent / pop, 1),
                                    "CRIME_VIOLENT_COUNT": violent,
                                    "CRIME_POPULATION": pop,
                                    "CRIME_SOURCE": "FBI_SAPI_API",
                                })
                                success = True
                                break
                    break
                elif resp.status_code == 429:
                    time.sleep(2 ** (attempt + 1))
                elif resp.status_code in (403, 404):
                    raise RuntimeError(
                        f"SAPI endpoint returned {resp.status_code} for {abbr}"
                    )
                else:
                    break
            except requests.exceptions.RequestException:
                if attempt < max_retries - 1:
                    time.sleep(2 ** (attempt + 1))
                else:
                    failed.append(abbr)

        if not success:
            failed.append(abbr)

    if len(rows) < 25:
        raise RuntimeError(
            f"SAPI endpoint: only {len(rows)}/50 states returned data"
        )
    return rows


def fetch_crime_violent_rate(api_key, year=2024):
    """Fetch state-level violent crime rate from FBI CDE API.

    Tries CDE endpoint first, then SAPI legacy endpoint.

    Parameters
    ----------
    api_key : str
        data.gov API key.
    year : int
        Target year (default 2024).

    Returns
    -------
    pd.DataFrame
        Columns: state (FIPS), CRIME_VIOLENT_RATE, CRIME_VIOLENT_COUNT,
                 CRIME_POPULATION, CRIME_SOURCE
    """
    # Try CDE endpoint first (current as of July 2025)
    for method_name, method_fn in [
        ("CDE", lambda: _try_cde_endpoint(api_key, year)),
        ("SAPI", lambda: _try_sapi_endpoint(api_key, year)),
    ]:
        try:
            print(f"  Trying {method_name} endpoint...")
            rows = method_fn()
            df = pd.DataFrame(rows)
            med_rate = df["CRIME_VIOLENT_RATE"].median()
            if not (50 <= med_rate <= 800):
                print(f"  WARNING: {method_name} median rate = {med_rate:.1f} "
                      f"(outside 50-800 range), trying next method")
                continue
            print(f"  {method_name}: {len(df)}/50 states, "
                  f"median rate = {med_rate:.1f} per 100k")
            return df
        except Exception as e:
            print(f"  {method_name} failed: {e}")
            continue

    raise RuntimeError(
        "FBI API: both CDE and SAPI endpoints failed. "
        "Place a CSV at data_raw/fbi_crime_state_2024.csv as fallback."
    )


def load_crime_from_csv(csv_path="data_raw/fbi_crime_state_2024.csv"):
    """Load crime data from a manually prepared CSV (fallback).

    Expected columns: state_abbr, violent_crime, population
    OR: state (FIPS), CRIME_VIOLENT_RATE

    Returns
    -------
    pd.DataFrame with columns: state, CRIME_VIOLENT_RATE, CRIME_SOURCE
    """
    df = pd.read_csv(csv_path)

    if "CRIME_VIOLENT_RATE" in df.columns and "state" in df.columns:
        df["CRIME_SOURCE"] = "manual_csv"
        return df[["state", "CRIME_VIOLENT_RATE", "CRIME_SOURCE"]]

    if "state_abbr" in df.columns:
        df["state"] = df["state_abbr"].map(STATE_ABBR_TO_FIPS)
        df = df.dropna(subset=["state"])
        df["CRIME_VIOLENT_RATE"] = 100000 * df["violent_crime"] / df["population"]
        df["CRIME_VIOLENT_RATE"] = df["CRIME_VIOLENT_RATE"].round(1)
        df["CRIME_SOURCE"] = "manual_csv"
        return df[["state", "CRIME_VIOLENT_RATE", "CRIME_SOURCE"]]

    raise ValueError(f"Unrecognized CSV format in {csv_path}")
