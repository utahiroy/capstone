"""Fetch BEA Regional data (GDP, RPP, REAL_PCPI)."""

import requests
import pandas as pd

BEA_BASE = "https://apps.bea.gov/api/data/"


# ── Metadata helpers ──────────────────────────────────────────────────

def _bea_request(api_key, **extra_params):
    """Low-level BEA API call. Returns the parsed BEAAPI dict."""
    params = {
        "UserID": api_key,
        "ResultFormat": "JSON",
        **extra_params,
    }
    resp = requests.get(BEA_BASE, params=params, timeout=60)
    resp.raise_for_status()
    payload = resp.json()
    beaapi = payload.get("BEAAPI", {})
    return beaapi


def _check_bea_error(beaapi, context=""):
    """Raise if the BEAAPI response contains an error at any known path.

    BEA returns errors in at least two locations:
      1. BEAAPI.Error  (top-level)
      2. BEAAPI.Results.Error  (nested inside Results, sometimes a list)
    """
    # Path 1: top-level
    error = beaapi.get("Error")
    if error:
        raise ValueError(f"BEA API error ({context}): {error}")

    # Path 2: nested under Results
    results = beaapi.get("Results", {})
    if isinstance(results, list):
        results = results[0] if results else {}
    nested_err = results.get("Error")
    if nested_err:
        raise ValueError(f"BEA API error ({context}): {nested_err}")


def get_valid_table_names(api_key, prefix=None):
    """Query BEA for valid Regional TableName values.

    Returns list of dicts with 'Key' and 'Desc' fields, optionally
    filtered to table names starting with *prefix* (e.g. "SAGDP").
    """
    beaapi = _bea_request(
        api_key,
        method="GetParameterValues",
        datasetname="Regional",
        ParameterName="TableName",
    )
    _check_bea_error(beaapi, context="GetParameterValues/TableName")
    results = beaapi.get("Results", {})
    if isinstance(results, list):
        results = results[0] if results else {}
    values = results.get("ParamValue", [])
    if prefix:
        values = [v for v in values if v.get("Key", "").startswith(prefix)]
    return values


def get_valid_line_codes(api_key, table_name):
    """Query BEA for valid LineCode values for a given Regional table."""
    beaapi = _bea_request(
        api_key,
        method="GetParameterValuesFiltered",
        datasetname="Regional",
        TargetParameter="LineCode",
        TableName=table_name,
    )
    _check_bea_error(beaapi, context=f"GetParameterValuesFiltered/{table_name}")
    results = beaapi.get("Results", {})
    if isinstance(results, list):
        results = results[0] if results else {}
    return results.get("ParamValue", [])


# ── Data fetch ────────────────────────────────────────────────────────

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
    pd.DataFrame with columns: state, GeoName, DataValue.
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

    # BEA wraps everything under BEAAPI
    beaapi = payload.get("BEAAPI", {})

    # Check for API-level errors (top-level AND nested under Results)
    _check_bea_error(beaapi, context=f"GetData/{table_name}")

    # Results can be a dict or a list depending on the response
    results = beaapi.get("Results", {})

    # Handle case where Results is a list (some BEA endpoints do this)
    if isinstance(results, list):
        if len(results) > 0:
            results = results[0]
        else:
            raise ValueError(f"BEA returned empty Results list for {table_name}")

    data = results.get("Data", [])
    if not data:
        raise ValueError(
            f"No data returned for {table_name} LineCode={line_code} Year={year}. "
            f"The {year} vintage may not yet be published for this table. "
            f"Results keys: {list(results.keys())}"
        )

    df = pd.DataFrame(data)

    # BEA GeoFips for states are 5 digits ("06000" for CA) or sometimes
    # just 2 digits ("06"). Handle both.
    if "GeoFips" not in df.columns:
        raise ValueError(f"No GeoFips column in BEA response. Columns: {list(df.columns)}")

    df["GeoFips"] = df["GeoFips"].astype(str).str.strip()

    # Filter to state-level: 5-digit codes ending in "000" (not "00000" US total),
    # or 2-digit state codes (not "00" US total)
    is_5digit_state = (df["GeoFips"].str.len() == 5) & (df["GeoFips"] != "00000")
    is_2digit_state = (df["GeoFips"].str.len() == 2) & (df["GeoFips"] != "00")
    df = df[is_5digit_state | is_2digit_state].copy()

    if df.empty:
        all_fips = payload.get("BEAAPI", {}).get("Results", {})
        raise ValueError(
            f"No state-level rows found after filtering GeoFips. "
            f"Sample GeoFips values from raw response may not match expected format."
        )

    # Normalize to 2-digit state FIPS
    df["state"] = df["GeoFips"].apply(
        lambda x: x[:2] if len(x) == 5 else x.zfill(2)
    )

    # Exclude DC (11), PR (72), and other non-state geographies
    from src.constants import STATE_FIPS
    df = df[df["state"].isin(STATE_FIPS.keys())].copy()

    # Convert DataValue to numeric (BEA returns strings, sometimes with commas,
    # and "(NA)" or "(D)" for unavailable/suppressed values)
    df["DataValue"] = (
        df["DataValue"]
        .astype(str)
        .str.replace(",", "", regex=False)
        .str.strip()
    )
    df["DataValue"] = pd.to_numeric(df["DataValue"], errors="coerce")

    # Deduplicate: BEA may return both 5-digit and 2-digit FIPS for the same
    # state. After normalizing to 2-digit, drop duplicates (keep first non-NA).
    df = df.sort_values("DataValue", na_position="last")
    df = df.drop_duplicates(subset=["state"], keep="first")

    return df[["state", "GeoName", "DataValue"]].reset_index(drop=True)


# Candidate table names for all-industry GDP, in preference order.
# SAGDP2N = "GDP by state (NAICS)"; SAGDP1 = "GDP summary".
# Both use LineCode=1 for all-industry total.
_GDP_TABLE_CANDIDATES = ["SAGDP2N", "SAGDP1"]


def fetch_gdp(api_key, year=2024, allow_fallback=False):
    """Fetch state GDP (all-industry total, current dollars).

    Tries each candidate GDP table name in order. If a table name is
    rejected by BEA ("Invalid Value for Parameter TableName"), the next
    candidate is attempted. Any other error is raised immediately.

    Parameters
    ----------
    api_key : str
    year : int
        Must match the project year (2024).
    allow_fallback : bool
        If False (default), raises on year-unavailability.
        If True (debug only), retries with year-1.
    """
    errors_by_table = {}

    for table_name in _GDP_TABLE_CANDIDATES:
        try:
            print(f"  Trying GDP table: {table_name}, LineCode=1, Year={year}")
            df = fetch_bea_regional(
                table_name, line_code=1, year=year, api_key=api_key
            )
            if df["DataValue"].isna().all():
                raise ValueError(f"All GDP values are NA for year {year}")
            print(f"  OK: GDP fetched from table {table_name}")
            return df.rename(columns={"DataValue": "GDP"})
        except ValueError as e:
            err_str = str(e)
            errors_by_table[table_name] = err_str
            # If the table name itself is invalid, try the next candidate
            if "Invalid" in err_str and "TableName" in err_str:
                print(f"  Table {table_name} rejected by BEA, trying next candidate...")
                continue
            # For any other error (year unavailable, no data, etc.), stop
            break

    # All candidates failed — build a diagnostic message
    diag_lines = [
        f"GDP fetch failed for year={year}.",
        "Errors by table candidate:",
    ]
    for tbl, err in errors_by_table.items():
        diag_lines.append(f"  {tbl}: {err}")

    # Run metadata discovery to help the user diagnose
    try:
        valid_tables = get_valid_table_names(api_key, prefix="SAGDP")
        if valid_tables:
            table_list = ", ".join(
                f"{v['Key']} ({v.get('Desc', '?')})" for v in valid_tables
            )
            diag_lines.append(f"Valid SAGDP tables from BEA: {table_list}")

            # For the first valid SAGDP table, show valid line codes
            first_valid = valid_tables[0]["Key"]
            line_codes = get_valid_line_codes(api_key, first_valid)
            if line_codes:
                lc_list = ", ".join(
                    f"{lc['Key']}={lc.get('Desc', '?')}" for lc in line_codes[:5]
                )
                diag_lines.append(
                    f"Sample LineCodes for {first_valid}: {lc_list}"
                )
        else:
            diag_lines.append("No SAGDP tables found via GetParameterValues.")
    except Exception as disc_err:
        diag_lines.append(f"Metadata discovery also failed: {disc_err}")

    full_msg = "\n".join(diag_lines)
    print(full_msg)

    if not allow_fallback:
        raise ValueError(full_msg)

    # Debug-only year fallback — only if the error was year-related
    last_table = list(errors_by_table.keys())[-1]
    fallback_year = year - 1
    print(f"  DEBUG FALLBACK: retrying {last_table} with year={fallback_year}")
    df = fetch_bea_regional(
        last_table, line_code=1, year=fallback_year, api_key=api_key
    )
    df = df.rename(columns={"DataValue": "GDP"})
    df["GDP_YEAR_NOTE"] = f"debug fallback to {fallback_year}"
    return df


def fetch_rpp(api_key, year=2024):
    """Fetch Regional Price Parities (all items) for all states.

    Returns DataFrame with columns: state, GeoName, RPP.
    """
    print(f"  Fetching RPP (SARPP, LineCode=1, Year={year})")
    df = fetch_bea_regional("SARPP", line_code=1, year=year, api_key=api_key)
    if df["DataValue"].isna().all():
        raise ValueError(f"All RPP values are NA for year {year}")
    return df.rename(columns={"DataValue": "RPP"})


def fetch_real_pcpi(api_key, year=2024):
    """Fetch Real Per Capita Personal Income for all states.

    BEA SARPI table line codes:
        LineCode=1: Real personal income (millions of chained dollars) — TOTAL
        LineCode=2: Population (persons)
        LineCode=3: Per capita real personal income (chained dollars) — PER CAPITA

    We use LineCode=3 directly. Expected values ~$40k–$80k per state.

    Returns DataFrame with columns: state, GeoName, REAL_PCPI.
    """
    lc = 3  # Per capita real personal income
    print(f"  Fetching REAL_PCPI (SARPI, LineCode={lc}, Year={year})")
    try:
        df = fetch_bea_regional(
            "SARPI", line_code=lc, year=year, api_key=api_key
        )
        if df["DataValue"].isna().all():
            raise ValueError(f"All REAL_PCPI values are NA for year {year}")
        print(f"  OK: REAL_PCPI fetched with LineCode={lc}")
        return df.rename(columns={"DataValue": "REAL_PCPI"})
    except ValueError:
        pass

    # Fallback: metadata discovery to diagnose
    try:
        line_codes = get_valid_line_codes(api_key, "SARPI")
        lc_info = ", ".join(
            f"{lc['Key']}={lc.get('Desc', '?')}" for lc in line_codes[:10]
        )
        raise ValueError(
            f"SARPI LineCode=3 failed for Year={year}. "
            f"Valid LineCodes: {lc_info}"
        )
    except Exception as e:
        raise ValueError(
            f"SARPI fetch failed for Year={year}. Error: {e}"
        ) from e
