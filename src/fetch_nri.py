"""Fetch FEMA National Risk Index data and aggregate to state level.

Source: FEMA NRI v1.20 (December 2025), county-level data via OpenFEMA API.
Variable: NRI_RISK_INDEX — population-weighted mean of county-level composite
          Risk Index score (RISK_SCORE), aggregated to the state level.

IMPORTANT: State-level composite RISK_SCORE is NOT directly provided by FEMA.
This module downloads county-level data and computes a population-weighted
average. This is a PROVISIONAL implementation. The aggregation method
(population-weighted mean) is a project decision, not an official FEMA metric.

Data source: OpenFEMA REST API (no key required).
Endpoint: https://www.fema.gov/api/open/v1/NationalRiskIndexCounty
Full CSV download: append .csv to the endpoint URL.

Key columns in the county data:
  - STCOFIPS: 5-digit state+county FIPS code
  - STATE: state name
  - STATEFIPS: 2-digit state FIPS
  - COUNTY: county name
  - POPULATION: population used by NRI (from Hazus)
  - RISK_SCORE: composite overall risk score (0-100 percentile ranking)
  - RISK_RATNG: qualitative rating (Very Low to Very High)
"""

import os
import time
import requests
import pandas as pd
from src.constants import STATE_FIPS

# OpenFEMA API endpoint for NRI county-level data (no key required)
OPENFEMA_NRI_ENDPOINT = (
    "https://www.fema.gov/api/open/v1/NationalRiskIndexCounty"
)

# Fallback: legacy hazards.fema.gov download URLs
LEGACY_NRI_URLS = [
    "https://hazards.fema.gov/nri/Content/StaticDocuments/DataDownload/"
    "NRI_Table_Counties/NRI_Table_Counties.csv",
    "https://hazards.fema.gov/nri/Content/StaticDocuments/DataDownload/"
    "NRI_Table_Counties.zip",
]

# Columns to select from OpenFEMA (reduces response size)
_SELECT_COLS = "STATEFIPS,STCOFIPS,STATE,COUNTY,POPULATION,RISK_SCORE,RISK_RATNG"


def _download_via_openfema(save_path="data_raw/nri_counties_raw.csv"):
    """Download county-level NRI data via OpenFEMA paginated API.

    The OpenFEMA API returns max 1000 records per request by default.
    We use $top=10000 (max allowed) and paginate with $skip.
    """
    all_records = []
    skip = 0
    batch_size = 10000

    print(f"  Downloading NRI county data via OpenFEMA API...")

    while True:
        url = (
            f"{OPENFEMA_NRI_ENDPOINT}"
            f"?$select={_SELECT_COLS}"
            f"&$top={batch_size}"
            f"&$skip={skip}"
        )
        for attempt in range(3):
            try:
                resp = requests.get(url, timeout=120)
                if resp.status_code == 200:
                    break
                print(f"    HTTP {resp.status_code} at skip={skip}, "
                      f"attempt {attempt + 1}/3")
            except requests.exceptions.RequestException as e:
                print(f"    Request error at skip={skip}, "
                      f"attempt {attempt + 1}/3: {e}")
            if attempt < 2:
                time.sleep(2 ** (attempt + 1))
        else:
            raise RuntimeError(
                f"OpenFEMA API failed after 3 attempts at skip={skip}"
            )

        if resp.status_code != 200:
            raise RuntimeError(
                f"OpenFEMA API returned HTTP {resp.status_code}: "
                f"{resp.text[:300]}"
            )

        data = resp.json()
        # OpenFEMA wraps records under the dataset name key
        records = data.get("NationalRiskIndexCounty",
                           data.get("NationalRiskIndexCounties", []))
        if not records:
            # Try top-level if it's a list
            if isinstance(data, list):
                records = data
            else:
                break

        all_records.extend(records)
        print(f"    Fetched {len(records)} records (total: {len(all_records)})")

        if len(records) < batch_size:
            break
        skip += batch_size

    if len(all_records) < 100:
        raise RuntimeError(
            f"OpenFEMA returned only {len(all_records)} county records "
            f"(expected ~3000+)"
        )

    df = pd.DataFrame(all_records)
    df.to_csv(save_path, index=False)
    print(f"    Saved {len(df)} county records to {save_path}")
    return df


def _download_via_openfema_csv(save_path="data_raw/nri_counties_raw.csv"):
    """Download full NRI county CSV via OpenFEMA bulk download.

    Appending .csv to the endpoint URL triggers a full download.
    """
    url = f"{OPENFEMA_NRI_ENDPOINT}.csv"
    print(f"  Downloading NRI county CSV from OpenFEMA (bulk)...")

    for attempt in range(3):
        try:
            resp = requests.get(url, timeout=300, stream=True)
            if resp.status_code == 200:
                with open(save_path, "wb") as f:
                    for chunk in resp.iter_content(chunk_size=1024 * 1024):
                        f.write(chunk)
                df = pd.read_csv(save_path, low_memory=False)
                if len(df) > 100:
                    print(f"    Downloaded {len(df)} county records")
                    return df
                print(f"    Too few rows ({len(df)})")
            else:
                print(f"    HTTP {resp.status_code} (attempt {attempt + 1}/3)")
        except requests.exceptions.RequestException as e:
            print(f"    Download error (attempt {attempt + 1}/3): {e}")
        if attempt < 2:
            time.sleep(2 ** (attempt + 1))

    raise RuntimeError("OpenFEMA CSV bulk download failed after 3 attempts")


def _download_nri_counties(save_path="data_raw/nri_counties_raw.csv"):
    """Download county-level NRI data. Tries multiple methods in order."""
    # Method 1: OpenFEMA paginated JSON API
    try:
        return _download_via_openfema(save_path)
    except Exception as e:
        print(f"  OpenFEMA JSON API failed: {e}")

    # Method 2: OpenFEMA bulk CSV download
    try:
        return _download_via_openfema_csv(save_path)
    except Exception as e:
        print(f"  OpenFEMA CSV download failed: {e}")

    # Method 3: Legacy hazards.fema.gov URLs (may not work)
    import io
    import zipfile
    for url in LEGACY_NRI_URLS:
        try:
            print(f"  Trying legacy URL: {url[:80]}...")
            resp = requests.get(url, timeout=120)
            if resp.status_code != 200:
                continue
            content_type = resp.headers.get("Content-Type", "")
            if url.endswith(".zip") or "zip" in content_type:
                z = zipfile.ZipFile(io.BytesIO(resp.content))
                csv_names = [n for n in z.namelist()
                             if n.lower().endswith(".csv")]
                if csv_names:
                    with z.open(csv_names[0]) as f:
                        df = pd.read_csv(f, low_memory=False)
                    if len(df) > 100:
                        df.to_csv(save_path, index=False)
                        return df
            else:
                df = pd.read_csv(io.StringIO(resp.text), low_memory=False)
                if len(df) > 100:
                    df.to_csv(save_path, index=False)
                    return df
        except Exception as e:
            print(f"    Legacy download error: {e}")

    raise RuntimeError(
        "Could not download NRI county data from any source. "
        "Place a county-level CSV at data_raw/nri_counties_raw.csv manually."
    )


def _find_columns(df):
    """Identify key column names (case-insensitive matching).

    Returns dict with keys: statefips, population, risk_score, stcofips.
    """
    col_map = {}
    cols_upper = {c.upper(): c for c in df.columns}

    for target, candidates in [
        ("statefips", ["STATEFIPS", "STATE_FIPS", "STFIPS"]),
        ("stcofips", ["STCOFIPS", "COUNTYID", "FIPS", "NRI_ID"]),
        ("population", ["POPULATION", "POP", "BUILDVALUE"]),
        ("risk_score", ["RISK_SCORE", "RISKSCORE", "RISK_VALUE"]),
    ]:
        for cand in candidates:
            if cand in cols_upper:
                col_map[target] = cols_upper[cand]
                break

    missing = [k for k in ["statefips", "population", "risk_score"]
               if k not in col_map]
    if missing:
        raise ValueError(
            f"NRI data missing expected columns: {missing}. "
            f"Available columns: {sorted(df.columns[:30])}"
        )
    return col_map


def aggregate_nri_to_state(df_counties):
    """Aggregate county-level NRI RISK_SCORE to state level.

    Method: Population-weighted mean of county RISK_SCORE.
    Formula: state_score = sum(county_pop * county_risk) / sum(county_pop)

    Parameters
    ----------
    df_counties : pd.DataFrame
        County-level NRI data with STATEFIPS, POPULATION, RISK_SCORE columns.

    Returns
    -------
    pd.DataFrame
        Columns: state, NRI_RISK_INDEX, NRI_COUNTY_COUNT, NRI_POP_COVERAGE
    """
    col_map = _find_columns(df_counties)

    df = df_counties.copy()
    df["_statefips"] = df[col_map["statefips"]].astype(str).str.zfill(2)
    df["_pop"] = pd.to_numeric(df[col_map["population"]], errors="coerce")
    df["_risk"] = pd.to_numeric(df[col_map["risk_score"]], errors="coerce")

    # Filter to 50 states only
    df = df[df["_statefips"].isin(STATE_FIPS.keys())].copy()

    # Drop rows with missing risk scores or zero population
    df = df.dropna(subset=["_risk", "_pop"])
    df = df[df["_pop"] > 0]

    # Population-weighted aggregation
    df["_weighted_risk"] = df["_pop"] * df["_risk"]

    state_agg = df.groupby("_statefips").agg(
        total_pop=("_pop", "sum"),
        weighted_risk_sum=("_weighted_risk", "sum"),
        county_count=("_risk", "count"),
    ).reset_index()

    state_agg["NRI_RISK_INDEX"] = (
        state_agg["weighted_risk_sum"] / state_agg["total_pop"]
    ).round(2)

    result = pd.DataFrame({
        "state": state_agg["_statefips"],
        "NRI_RISK_INDEX": state_agg["NRI_RISK_INDEX"],
        "NRI_COUNTY_COUNT": state_agg["county_count"].astype(int),
        "NRI_POP_COVERAGE": state_agg["total_pop"].astype(int),
    })

    # Sanity check: all 50 states should be present
    if len(result) < 45:
        raise ValueError(
            f"NRI aggregation produced only {len(result)} states (expected ~50). "
            f"Check STATEFIPS column."
        )

    # Sanity check: risk scores should be 0-100
    if result["NRI_RISK_INDEX"].max() > 100 or result["NRI_RISK_INDEX"].min() < 0:
        print(f"  WARNING: NRI_RISK_INDEX out of 0-100 range: "
              f"min={result['NRI_RISK_INDEX'].min():.1f}, "
              f"max={result['NRI_RISK_INDEX'].max():.1f}")

    return result


def fetch_nri_risk_index():
    """Download NRI county data and aggregate to state-level NRI_RISK_INDEX.

    Returns
    -------
    pd.DataFrame
        Columns: state, NRI_RISK_INDEX, NRI_COUNTY_COUNT, NRI_POP_COVERAGE
    """
    raw_path = "data_raw/nri_counties_raw.csv"

    # Check for cached raw file
    if os.path.exists(raw_path):
        print(f"  Using cached NRI data from {raw_path}")
        df = pd.read_csv(raw_path, low_memory=False)
    else:
        df = _download_nri_counties(raw_path)

    result = aggregate_nri_to_state(df)
    print(f"  NRI aggregated: {len(result)} states, "
          f"median score = {result['NRI_RISK_INDEX'].median():.1f}")
    return result
