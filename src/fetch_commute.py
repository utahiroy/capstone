"""Fetch ACS B08303 travel-time-to-work bins and compute grouped-median commute time.

Source: ACS 2024 1-year, table B08303 (Travel Time to Work).
Variable: COMMUTE_MED — approximate grouped median travel time (minutes).

Method: Linear interpolation within the bin containing the N/2-th observation.
Formula: median = L + [(N/2 - F) / f] * C
  L = lower bound of median bin
  N = total count of workers
  F = cumulative count in bins BEFORE the median bin
  f = count in the median bin
  C = width of the median bin

Note: S0801_C01_046E provides MEAN travel time, not median.
      This module deliberately uses grouped-median interpolation from B08303
      to produce COMMUTE_MED as specified in the research design.
"""

import pandas as pd
from src.fetch_census import fetch_acs_variables

# B08303 bin variable codes and their boundaries (minutes)
# Each tuple: (var_code, lower_bound, upper_bound)
B08303_BINS = [
    ("B08303_002E", 0, 5),       # Less than 5 minutes
    ("B08303_003E", 5, 10),      # 5 to 9 minutes
    ("B08303_004E", 10, 15),     # 10 to 14 minutes
    ("B08303_005E", 15, 20),     # 15 to 19 minutes
    ("B08303_006E", 20, 25),     # 20 to 24 minutes
    ("B08303_007E", 25, 30),     # 25 to 29 minutes
    ("B08303_008E", 30, 35),     # 30 to 34 minutes
    ("B08303_009E", 35, 40),     # 35 to 39 minutes (was 35-44 in older vintages)
    ("B08303_010E", 40, 45),     # 40 to 44 minutes
    ("B08303_011E", 45, 60),     # 45 to 59 minutes
    ("B08303_012E", 60, 90),     # 60 to 89 minutes
    ("B08303_013E", 90, 120),    # 90 or more minutes (upper bound = 120 assumed)
]

B08303_TOTAL = "B08303_001E"


def _grouped_median(counts, bins):
    """Compute grouped median from bin counts using linear interpolation.

    Parameters
    ----------
    counts : list[float]
        Count in each bin (same order as bins).
    bins : list[tuple[float, float]]
        (lower, upper) boundary for each bin.

    Returns
    -------
    float
        Estimated grouped median.
    """
    N = sum(counts)
    if N <= 0:
        return float("nan")

    target = N / 2.0
    cum = 0.0
    for i, (count, (lo, hi)) in enumerate(zip(counts, bins)):
        if cum + count >= target:
            # Median falls in this bin
            f = count
            F = cum
            C = hi - lo
            L = lo
            if f == 0:
                return float("nan")
            return L + ((target - F) / f) * C
        cum += count

    # Should not reach here; return midpoint of last bin
    return (bins[-1][0] + bins[-1][1]) / 2.0


def fetch_commute_med(api_key, state_fips_list):
    """Fetch B08303 bins and compute COMMUTE_MED for each state.

    Parameters
    ----------
    api_key : str
        Census API key.
    state_fips_list : list[str]
        List of 2-digit FIPS codes.

    Returns
    -------
    pd.DataFrame
        Columns: state, COMMUTE_MED
    """
    all_vars = [B08303_TOTAL] + [b[0] for b in B08303_BINS]
    df = fetch_acs_variables(all_vars, api_key, state_fips_list)

    bin_codes = [b[0] for b in B08303_BINS]
    bin_bounds = [(b[1], b[2]) for b in B08303_BINS]

    medians = []
    for _, row in df.iterrows():
        counts = [row[code] for code in bin_codes]
        med = _grouped_median(counts, bin_bounds)
        medians.append(med)

    result = pd.DataFrame({
        "state": df["state"],
        "COMMUTE_MED": medians,
    })

    # Sanity check: median should be 5–60 minutes for any US state
    med_val = result["COMMUTE_MED"].median()
    if not (5 <= med_val <= 60):
        raise ValueError(
            f"COMMUTE_MED sanity check failed: median of state medians = {med_val:.1f} min "
            f"(expected 5–60). Check B08303 data."
        )

    return result
