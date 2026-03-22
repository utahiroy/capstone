"""Fetch state-level violent crime rate from FBI Crime Data Explorer API.

Source: FBI Uniform Crime Reporting (UCR) program, via CDE API.
Variable: CRIME_VIOLENT_RATE — estimated violent crime rate per 100,000 population.

Violent crime definition (FBI): murder and nonnegligent manslaughter, rape,
robbery, aggravated assault.

API endpoint: https://api.usa.gov/crime/fbi/sapi/api/estimates/states/{state_abbr}
Requires: DATA_GOV_API_KEY (free from https://api.data.gov/signup/)

The estimates endpoint returns one record per year per state with fields including:
  - year, state_abbr, state_id, population
  - violent_crime (count)
  - homicide, rape_legacy, rape_revised, robbery, aggravated_assault (counts)

If the API is unreliable, this module also supports loading from a local CSV
placed at data_raw/fbi_crime_state_2024.csv with columns:
  state_abbr, violent_crime, population
"""

import time
import requests
import pandas as pd

FBI_API_BASE = "https://api.usa.gov/crime/fbi/sapi"

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


def _fetch_state_estimates(api_key, state_abbr, year=2024, max_retries=3):
    """Fetch estimated crime data for one state from CDE API."""
    url = f"{FBI_API_BASE}/api/estimates/states/{state_abbr}/{year}/{year}"
    params = {"api_key": api_key}

    for attempt in range(max_retries):
        try:
            resp = requests.get(url, params=params, timeout=30)
            if resp.status_code == 200:
                data = resp.json()
                if isinstance(data, dict) and "results" in data:
                    return data["results"]
                elif isinstance(data, list):
                    return data
                else:
                    return [data] if data else []
            elif resp.status_code == 429:
                wait = 2 ** (attempt + 1)
                print(f"    Rate limited for {state_abbr}, waiting {wait}s...")
                time.sleep(wait)
            else:
                print(f"    {state_abbr}: HTTP {resp.status_code}")
                return []
        except requests.exceptions.RequestException as e:
            if attempt < max_retries - 1:
                wait = 2 ** (attempt + 1)
                print(f"    {state_abbr} request error, retrying in {wait}s: {e}")
                time.sleep(wait)
            else:
                print(f"    {state_abbr} failed after {max_retries} attempts: {e}")
                return []
    return []


def fetch_crime_violent_rate(api_key, year=2024):
    """Fetch state-level violent crime rate from FBI CDE API.

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
    rows = []
    failed_states = []

    for abbr, fips in sorted(STATE_ABBR_TO_FIPS.items()):
        results = _fetch_state_estimates(api_key, abbr, year)

        if not results:
            failed_states.append(abbr)
            continue

        # Find the record for the target year
        record = None
        for r in results:
            if isinstance(r, dict) and r.get("year") == year:
                record = r
                break
        if record is None and results:
            record = results[-1] if isinstance(results[-1], dict) else None

        if record is None:
            failed_states.append(abbr)
            continue

        violent = record.get("violent_crime")
        pop = record.get("population")

        if violent is not None and pop is not None and pop > 0:
            rate = 100000 * violent / pop
            rows.append({
                "state": fips,
                "CRIME_VIOLENT_RATE": round(rate, 1),
                "CRIME_VIOLENT_COUNT": violent,
                "CRIME_POPULATION": pop,
                "CRIME_SOURCE": "FBI_CDE_API",
            })
        else:
            failed_states.append(abbr)

    if failed_states:
        print(f"  WARNING: Failed to get crime data for {len(failed_states)} states: "
              f"{', '.join(failed_states)}")

    df = pd.DataFrame(rows)

    if len(df) == 0:
        raise RuntimeError("FBI CDE API returned no data. Check API key and endpoint.")

    # Sanity check
    med_rate = df["CRIME_VIOLENT_RATE"].median()
    if not (50 <= med_rate <= 800):
        raise ValueError(
            f"CRIME_VIOLENT_RATE sanity check failed: median = {med_rate:.1f} "
            f"per 100k (expected 50–800)."
        )

    print(f"  FBI CDE: {len(df)}/50 states, median rate = {med_rate:.1f} per 100k")
    return df


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
