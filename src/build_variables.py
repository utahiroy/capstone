"""Build migration DVs and IV measures from fetched data."""

import pandas as pd
from src.constants import (
    AGE_GROUPS, IN_COUNT_VARS, OUT_COUNT_VARS, POP_AGE_VARS,
    COST_BURDEN_RENTER_TOTAL, COST_BURDEN_RENTER_BURDENED,
    COST_BURDEN_OWNER_TOTAL, COST_BURDEN_OWNER_BURDENED,
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
