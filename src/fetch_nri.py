"""Fetch FEMA National Risk Index data and aggregate to state level.

Source: FEMA NRI v1.20 (December 2025), county-level CSV.
Variable: NRI_RISK_INDEX — population-weighted mean of county-level composite
          Risk Index score (RISK_SCORE), aggregated to the state level.

IMPORTANT: State-level composite RISK_SCORE is NOT directly provided by FEMA.
This module downloads county-level data and computes a population-weighted
average. This is a PROVISIONAL implementation. The aggregation method
(population-weighted mean) is a project decision, not an official FEMA metric.

Data source: https://hazards.fema.gov/nri/data-resources
Download: County-level CSV from FEMA NRI data downloads.

Key columns in the county CSV:
  - STCOFIPS: 5-digit state+county FIPS code
  - STATE: state name
  - STATEFIPS: 2-digit state FIPS
  - COUNTY: county name
  - POPULATION: population used by NRI (from Hazus)
  - RISK_SCORE: composite overall risk score (0-100 percentile ranking)
  - RISK_RATNG: qualitative rating (Very Low to Very High)
  - EAL_SCORE: Expected Annual Loss score
  - SOVI_SCORE: Social Vulnerability score
  - RESL_SCORE: Community Resilience score
"""

import os
import io
import zipfile
import requests
import pandas as pd
from src.constants import STATE_FIPS

# Known download URL patterns for NRI county-level CSV
NRI_DOWNLOAD_URLS = [
    # Current version direct CSV download
    "https://hazards.fema.gov/nri/Content/StaticDocuments/DataDownload/"
    "NRI_Table_Counties/NRI_Table_Counties.csv",
    # Zipped version
    "https://hazards.fema.gov/nri/Content/StaticDocuments/DataDownload/"
    "NRI_Table_Counties.zip",
]


def _download_nri_counties(save_path="data_raw/nri_counties_raw.csv"):
    """Download county-level NRI data from FEMA.

    Tries multiple URL patterns. Returns a DataFrame.
    """
    for url in NRI_DOWNLOAD_URLS:
        try:
            print(f"  Trying NRI download: {url[:80]}...")
            resp = requests.get(url, timeout=120, stream=True)
            if resp.status_code != 200:
                print(f"    HTTP {resp.status_code}, trying next URL...")
                continue

            content_type = resp.headers.get("Content-Type", "")

            if url.endswith(".zip") or "zip" in content_type:
                # Handle ZIP file
                z = zipfile.ZipFile(io.BytesIO(resp.content))
                csv_names = [n for n in z.namelist()
                             if n.lower().endswith(".csv") and "county" in n.lower()]
                if not csv_names:
                    csv_names = [n for n in z.namelist()
                                 if n.lower().endswith(".csv")]
                if not csv_names:
                    print(f"    No CSV found in ZIP, trying next URL...")
                    continue
                csv_name = csv_names[0]
                print(f"    Extracting {csv_name} from ZIP...")
                with z.open(csv_name) as f:
                    df = pd.read_csv(f, low_memory=False)
            else:
                # Direct CSV
                df = pd.read_csv(io.StringIO(resp.text), low_memory=False)

            if len(df) > 100:
                # Save raw
                df.to_csv(save_path, index=False)
                print(f"    Downloaded NRI county data: {len(df)} rows, "
                      f"{len(df.columns)} cols")
                return df
            else:
                print(f"    Too few rows ({len(df)}), trying next URL...")

        except Exception as e:
            print(f"    Download error: {e}")
            continue

    raise RuntimeError(
        "Could not download NRI county data from any known URL. "
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

    missing = [k for k in ["statefips", "population", "risk_score"] if k not in col_map]
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
