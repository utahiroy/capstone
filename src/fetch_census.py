"""Fetch ACS 2024 1-year data from the Census API."""

import requests
import pandas as pd

ACS_BASE = "https://api.census.gov/data/2024/acs/acs1"


def fetch_acs_variables(variables, api_key, state_fips_list=None):
    """Fetch a list of ACS variable codes for states.

    Parameters
    ----------
    variables : list[str]
        Variable codes (e.g. ["B07001_068E", "B07001_069E"]).
    api_key : str
        Census API key.
    state_fips_list : list[str] or None
        If None, fetch all states. Otherwise a list like ["06", "48", "36"].

    Returns
    -------
    pd.DataFrame
        Columns: "state" (FIPS), plus one column per variable.
    """
    # Census API allows up to 50 variables per call.
    var_str = ",".join(variables)
    params = {
        "get": var_str,
        "for": "state:*",
        "key": api_key,
    }
    resp = requests.get(ACS_BASE, params=params, timeout=60)
    resp.raise_for_status()
    data = resp.json()

    df = pd.DataFrame(data[1:], columns=data[0])

    # Filter to requested states if specified
    if state_fips_list is not None:
        df = df[df["state"].isin(state_fips_list)].copy()

    # Convert variable columns to numeric
    for col in variables:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    return df.reset_index(drop=True)


def fetch_all_migration_data(api_key, state_fips_list=None):
    """Fetch B07001 (in), B07401 (out), and B01001 (pop) for all age groups.

    Returns three DataFrames keyed by state FIPS.
    """
    from src.constants import IN_COUNT_VARS, OUT_COUNT_VARS, POP_AGE_VARS

    # Collect all unique variable codes per table
    in_vars = sorted({v for vs in IN_COUNT_VARS.values() for v in vs})
    out_vars = sorted({v for vs in OUT_COUNT_VARS.values() for v in vs})
    pop_vars = sorted({v for vs in POP_AGE_VARS.values() for v in vs})

    df_in = fetch_acs_variables(in_vars, api_key, state_fips_list)
    df_out = fetch_acs_variables(out_vars, api_key, state_fips_list)
    df_pop = fetch_acs_variables(pop_vars, api_key, state_fips_list)

    return df_in, df_out, df_pop


def fetch_acs_simple_vars(var_codes, api_key, state_fips_list=None):
    """Fetch simple single-variable ACS fields (e.g. MED_RENT).

    Parameters
    ----------
    var_codes : dict[str, str]
        Mapping of friendly name to ACS variable code,
        e.g. {"MED_RENT": "B25064_001E"}.

    Returns
    -------
    pd.DataFrame with columns: state, plus each friendly name.
    """
    codes = list(var_codes.values())
    df = fetch_acs_variables(codes, api_key, state_fips_list)
    rename = {v: k for k, v in var_codes.items()}
    df = df.rename(columns=rename)
    return df
