"""A2.2b diagnostic: Probe all 4 failing data sources and print raw response details.

Run:  python -m scripts.debug_a22b

This does NOT modify any files. It only prints diagnostic information.
"""

import io
import json
import requests
import pandas as pd

from src.config_loader import load_api_keys


def probe_laus():
    """Probe BLS LAUS API for 2 example states — print full response."""
    print("\n" + "=" * 70)
    print("  LAUS DIAGNOSTIC")
    print("=" * 70)

    LAUS_API = "https://api.bls.gov/publicAPI/v2/timeseries/data/"

    # Try both LASST and LAUST for CA (06)
    for prefix in ["LAUST", "LASST"]:
        sid = f"{prefix}060000000000003"
        payload = {
            "seriesid": [sid],
            "startyear": "2024",
            "endyear": "2024",
        }
        print(f"\n--- Trying series: {sid}")
        try:
            resp = requests.post(LAUS_API, json=payload, timeout=30)
            data = resp.json()
            print(f"  Status: {data.get('status')}")
            print(f"  Message: {data.get('message', '')}")
            for series in data.get("Results", {}).get("series", []):
                print(f"  Series ID: {series['seriesID']}")
                print(f"  Data count: {len(series.get('data', []))}")
                for obs in series.get("data", []):
                    print(f"    year={obs['year']} period={obs['period']} "
                          f"periodName={obs.get('periodName','')} value={obs['value']}")
        except Exception as e:
            print(f"  ERROR: {e}")

    # Also try with latest=true to see what's available
    print("\n--- Trying LAUST CA with latest=true, 2023-2024 range")
    payload2 = {
        "seriesid": ["LAUST060000000000003"],
        "startyear": "2023",
        "endyear": "2024",
        "latest": True,
    }
    try:
        resp = requests.post(LAUS_API, json=payload2, timeout=30)
        data = resp.json()
        print(f"  Status: {data.get('status')}")
        for series in data.get("Results", {}).get("series", []):
            print(f"  Series: {series['seriesID']}")
            for obs in series.get("data", []):
                print(f"    year={obs['year']} period={obs['period']} "
                      f"periodName={obs.get('periodName','')} value={obs['value']}")
    except Exception as e:
        print(f"  ERROR: {e}")


def probe_qcew():
    """Probe QCEW CSV API — print raw structure and filter diagnostics."""
    print("\n" + "=" * 70)
    print("  QCEW DIAGNOSTIC")
    print("=" * 70)

    url = "https://data.bls.gov/cew/data/api/2024/a/industry/10.csv"
    print(f"\n--- Fetching: {url}")
    try:
        resp = requests.get(url, timeout=120)
        print(f"  HTTP status: {resp.status_code}")
        print(f"  Content-Type: {resp.headers.get('content-type', '?')}")
        print(f"  Response length: {len(resp.text)} chars")
        print(f"  First 300 chars:\n{resp.text[:300]}")

        if resp.status_code == 200 and len(resp.text) > 100:
            df = pd.read_csv(io.StringIO(resp.text), dtype={"area_fips": str})
            print(f"\n  Raw row count: {len(df)}")
            print(f"  Columns ({len(df.columns)}): {list(df.columns)}")

            for c in ["own_code", "agglvl_code", "size_code", "area_fips"]:
                if c in df.columns:
                    print(f"\n  Column '{c}':")
                    print(f"    dtype: {df[c].dtype}")
                    print(f"    nunique: {df[c].nunique()}")
                    print(f"    unique values: {sorted(df[c].unique())[:20]}")
                    print(f"    sample: {df[c].head(5).tolist()}")

            # Step-by-step filter
            print("\n  --- Filter step-by-step ---")
            for col, val in [("own_code", 5), ("agglvl_code", 50), ("size_code", 0)]:
                if col in df.columns:
                    # Try int comparison
                    int_match = (df[col] == val).sum()
                    # Try string comparison
                    str_match = (df[col].astype(str).str.strip() == str(val)).sum()
                    print(f"  {col} == {val}: int_match={int_match}, str_match={str_match}")

            # Try with forced int conversion
            print("\n  --- Filter with forced int conversion ---")
            try:
                for c in ["own_code", "agglvl_code", "size_code"]:
                    if c in df.columns:
                        df[c] = pd.to_numeric(df[c], errors="coerce")
                mask = (df["own_code"] == 5) & (df["agglvl_code"] == 50) & (df["size_code"] == 0)
                filtered = df[mask]
                print(f"  Filtered rows: {len(filtered)}")
                if len(filtered) > 0:
                    print(f"  Sample area_fips: {filtered['area_fips'].head(5).tolist()}")
            except Exception as e:
                print(f"  Filter error: {e}")
        else:
            print("  Response is not a valid CSV or is too short")
            # Try 2023 as a comparison
            url23 = "https://data.bls.gov/cew/data/api/2023/a/industry/10.csv"
            print(f"\n--- Trying 2023 for comparison: {url23}")
            resp23 = requests.get(url23, timeout=120)
            print(f"  HTTP status: {resp23.status_code}")
            print(f"  Response length: {len(resp23.text)} chars")
    except Exception as e:
        print(f"  ERROR: {e}")


def probe_permits():
    """Probe BPS text file — print exact structure."""
    print("\n" + "=" * 70)
    print("  PERMITS DIAGNOSTIC")
    print("=" * 70)

    urls = [
        ("2-digit year", "https://www2.census.gov/econ/bps/State/st24a.txt"),
        ("4-digit year", "https://www2.census.gov/econ/bps/State/st2024a.txt"),
    ]
    for label, url in urls:
        print(f"\n--- {label}: {url}")
        try:
            resp = requests.get(url, timeout=30)
            print(f"  HTTP status: {resp.status_code}")
            if resp.status_code == 200:
                lines = resp.text.split("\n")
                print(f"  Total lines: {len(lines)}")
                print("  First 15 lines:")
                for i, line in enumerate(lines[:15]):
                    print(f"    [{i}] {line[:150]}")

                # Try CSV parse
                try:
                    df = pd.read_csv(io.StringIO(resp.text), dtype=str,
                                     on_bad_lines="skip")
                    print(f"\n  CSV parse: {len(df)} rows, columns: {list(df.columns)}")
                    print(f"  First 3 rows:")
                    print(df.head(3).to_string(index=False))
                except Exception as e:
                    print(f"  CSV parse failed: {e}")

                # Try fixed-width
                try:
                    df2 = pd.read_fwf(io.StringIO(resp.text), dtype=str)
                    print(f"\n  FWF parse: {len(df2)} rows, columns: {list(df2.columns)}")
                    print(f"  First 3 rows:")
                    print(df2.head(3).to_string(index=False))
                except Exception as e:
                    print(f"  FWF parse failed: {e}")
                break  # only need one successful download
        except Exception as e:
            print(f"  ERROR: {e}")


def probe_eia():
    """Probe EIA API — print response for different parameter formats."""
    print("\n" + "=" * 70)
    print("  EIA DIAGNOSTIC")
    print("=" * 70)

    keys = load_api_keys()
    eia_key = keys.get("EIA_API_KEY", "")
    if not eia_key:
        print("  SKIPPED: No EIA_API_KEY")
        return

    # Probe 1: endpoint metadata
    url_meta = f"https://api.eia.gov/v2/electricity/retail-sales/?api_key={eia_key}"
    print(f"\n--- Probe 1: endpoint metadata")
    try:
        resp = requests.get(url_meta, timeout=30)
        print(f"  Status: {resp.status_code}")
        body = resp.text[:1000]
        print(f"  Body: {body}")
    except Exception as e:
        print(f"  ERROR: {e}")

    # Probe 2: minimal data request
    url2 = (
        f"https://api.eia.gov/v2/electricity/retail-sales/data/"
        f"?api_key={eia_key}"
        f"&frequency=annual"
        f"&data[0]=price"
        f"&facets[sectorid][]=ALL"
        f"&start=2024"
        f"&end=2024"
        f"&length=5"
    )
    print(f"\n--- Probe 2: data request with api_key param, no sort")
    try:
        resp = requests.get(url2, timeout=30)
        print(f"  Status: {resp.status_code}")
        print(f"  Body (first 500): {resp.text[:500]}")
    except Exception as e:
        print(f"  ERROR: {e}")

    # Probe 3: X-API-Key header
    url3 = (
        "https://api.eia.gov/v2/electricity/retail-sales/data/"
        "?frequency=annual"
        "&data[0]=price"
        "&facets[sectorid][]=ALL"
        "&start=2024"
        "&end=2024"
        "&length=5"
    )
    print(f"\n--- Probe 3: X-API-Key header")
    try:
        resp = requests.get(url3, headers={"X-API-Key": eia_key}, timeout=30)
        print(f"  Status: {resp.status_code}")
        print(f"  Body (first 500): {resp.text[:500]}")
    except Exception as e:
        print(f"  ERROR: {e}")

    # Probe 4: try 2023 instead of 2024
    url4 = (
        f"https://api.eia.gov/v2/electricity/retail-sales/data/"
        f"?api_key={eia_key}"
        f"&frequency=annual"
        f"&data[0]=price"
        f"&facets[sectorid][]=ALL"
        f"&start=2023"
        f"&end=2023"
        f"&length=5"
    )
    print(f"\n--- Probe 4: try 2023 data")
    try:
        resp = requests.get(url4, timeout=30)
        print(f"  Status: {resp.status_code}")
        print(f"  Body (first 500): {resp.text[:500]}")
    except Exception as e:
        print(f"  ERROR: {e}")

    # Probe 5: use requests params (let requests encode)
    print(f"\n--- Probe 5: let requests encode params")
    params = {
        "api_key": eia_key,
        "frequency": "annual",
        "data[0]": "price",
        "facets[sectorid][]": "ALL",
        "start": "2024",
        "end": "2024",
        "length": "5",
    }
    try:
        resp = requests.get(
            "https://api.eia.gov/v2/electricity/retail-sales/data/",
            params=params, timeout=30
        )
        print(f"  Encoded URL: {resp.url}")
        print(f"  Status: {resp.status_code}")
        print(f"  Body (first 500): {resp.text[:500]}")
    except Exception as e:
        print(f"  ERROR: {e}")


if __name__ == "__main__":
    probe_laus()
    probe_qcew()
    probe_permits()
    probe_eia()
    print("\n\nDone. Please share the output above so we can fix based on actual data.")
