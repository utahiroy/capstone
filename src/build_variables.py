"""Build migration DVs and IV measures from fetched data."""

import pandas as pd
from src.constants import (
    AGE_GROUPS, IN_COUNT_VARS, OUT_COUNT_VARS, POP_AGE_VARS,
    COST_BURDEN_RENTER_TOTAL, COST_BURDEN_RENTER_BURDENED,
    COST_BURDEN_OWNER_TOTAL, COST_BURDEN_OWNER_BURDENED,
    VACANCY_FOR_RENT, VACANCY_RENTED_NOT_OCC, OCCUPIED_RENTER,
    TRANSIT_WORKERS_TOTAL, TRANSIT_PUBLIC,
    BA_PLUS_TOTAL, BA_PLUS_BACHELORS, BA_PLUS_MASTERS,
    BA_PLUS_PROFESSIONAL, BA_PLUS_DOCTORATE,
)


def build_migration_dvs(df_in, df_out, df_pop):
    """Build all migration DVs from raw ACS fetches.

    Returns a DataFrame with one row per state, columns:
      state, IN_COUNT_{ag}, OUT_COUNT_{ag}, POP_AGE_{ag},
      NET_COUNT_{ag}, IN_RATE_{ag}, OUT_RATE_{ag}, NET_RATE_{ag}
    for each age group.
    """
    result = df_in[["state"]].copy()

    for ag in AGE_GROUPS:
        # IN_COUNT
        in_cols = IN_COUNT_VARS[ag]
        result[f"IN_COUNT_{ag}"] = df_in[in_cols].sum(axis=1)

        # OUT_COUNT
        out_cols = OUT_COUNT_VARS[ag]
        result[f"OUT_COUNT_{ag}"] = df_out[out_cols].sum(axis=1)

        # POP_AGE (from B01001)
        pop_cols = POP_AGE_VARS[ag]
        result[f"POP_AGE_{ag}"] = df_pop[pop_cols].sum(axis=1)

        # Derived
        result[f"NET_COUNT_{ag}"] = result[f"IN_COUNT_{ag}"] - result[f"OUT_COUNT_{ag}"]

        pop = result[f"POP_AGE_{ag}"]
        result[f"IN_RATE_{ag}"] = 1000 * result[f"IN_COUNT_{ag}"] / pop
        result[f"OUT_RATE_{ag}"] = 1000 * result[f"OUT_COUNT_{ag}"] / pop
        result[f"NET_RATE_{ag}"] = 1000 * result[f"NET_COUNT_{ag}"] / pop

    return result


def build_cost_burden(df_burden):
    """Compute COST_BURDEN_ALL from fetched B25070 + B25091 variables.

    Parameters
    ----------
    df_burden : pd.DataFrame
        Must contain all B25070 and B25091 variable columns plus 'state'.

    Returns
    -------
    pd.Series indexed like df_burden, containing COST_BURDEN_ALL (percent).
    """
    renter_burdened = df_burden[COST_BURDEN_RENTER_BURDENED].sum(axis=1)
    owner_burdened = df_burden[COST_BURDEN_OWNER_BURDENED].sum(axis=1)
    renter_total = df_burden[COST_BURDEN_RENTER_TOTAL]
    owner_total = df_burden[COST_BURDEN_OWNER_TOTAL]

    return 100 * (renter_burdened + owner_burdened) / (renter_total + owner_total)


def build_vacancy_rate(df):
    """Compute VACANCY_RATE from B25004 + B25003 variables.

    Formula: 100 * B25004_002E / (B25004_002E + B25004_003E + B25003_003E)
    """
    for_rent = df[VACANCY_FOR_RENT]
    rented_not_occ = df[VACANCY_RENTED_NOT_OCC]
    occ_renter = df[OCCUPIED_RENTER]
    return 100 * for_rent / (for_rent + rented_not_occ + occ_renter)


def build_transit_share(df):
    """Compute TRANSIT_SHARE from B08301 variables.

    Formula: 100 * B08301_010E / B08301_001E
    """
    return 100 * df[TRANSIT_PUBLIC] / df[TRANSIT_WORKERS_TOTAL]


def build_ba_plus(df):
    """Compute BA_PLUS from B15003 variables.

    Formula: 100 * (bachelor + master + professional + doctorate) / total_25plus
    """
    ba_plus_count = (
        df[BA_PLUS_BACHELORS]
        + df[BA_PLUS_MASTERS]
        + df[BA_PLUS_PROFESSIONAL]
        + df[BA_PLUS_DOCTORATE]
    )
    return 100 * ba_plus_count / df[BA_PLUS_TOTAL]


def build_pop_density(pop, land_area):
    """Compute POP_DENS = POP / LAND_AREA (persons per square mile)."""
    return pop / land_area
