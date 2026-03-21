# Implementation-Specific Source Notes

This document records non-obvious implementation choices made during data
ingestion (Phase A2).  Each entry explains what was done and why, so that a
reviewer can assess whether the choice materially affects results.

---

## 1. LAND_AREA — Census State Area (fallback to hardcoded values)

**Intended source:** Census Bureau state area reference file
**URL tried:** `https://www2.census.gov/geo/docs/reference/state-area.csv`

**Fallback logic:**
If the HTTP download fails, column names cannot be matched, or CSV parsing
errors occur, the code falls back to a hardcoded dictionary of 50-state land
areas (square miles) sourced from Census 2010 state area measurements.

**Why this is acceptable:**
Land area is a fixed geographic statistic that changes only with boundary
revisions.  The Census 2010 values are the same figures published in the
2020-vintage reference files.  No meaningful precision is lost.

**Verification:** Compare any state's value against the Census "State Area
Measurements" page to confirm alignment.

---

## 2. UNEMP — BLS LAUS Annual Average

**Source:** BLS Local Area Unemployment Statistics (LAUS), public API v2
**Series pattern:** `LAUST{FIPS}0000000000003` (unemployment rate)

**Monthly-average method:**

1. **Preferred:** Use period code `M13` if present.  M13 is the BLS-computed
   annual average and is the official published rate.
2. **Fallback:** If M13 is not yet available for the target year, compute a
   simple arithmetic mean of all available monthly values (M01–M12).
3. **Partial-year:** If fewer than 12 months are available, the mean is
   computed over whatever months exist.  This situation is logged but not
   treated as a fatal error.

**Seasonality note:** The code first tries unadjusted (SA code = U) series.
Seasonally adjusted (SA code = S) series are tried only if unadjusted returns
no data.  For annual averages this distinction is minor, but it is recorded
here for transparency.

**Rounding:** Final rate is rounded to 1 decimal place.

---

## 3. QCEW — BLS Quarterly Census of Employment and Wages (State-Level Extraction)

**Source:** BLS QCEW annual data API
**URL pattern:** `https://data.bls.gov/cew/data/api/{year}/a/industry/10.csv`
(Industry code 10 = all industries/total; frequency = annual)

**State-level extraction rule:**

| Filter         | Value                                             |
|----------------|---------------------------------------------------|
| `own_code`     | `5` (private sector only)                         |
| `size_code`    | `0` (all establishment sizes); fallback: no filter|
| `area_fips`    | Pattern `XX000` (statewide total)                 |
| Deduplication  | If multiple `agglvl_code` rows per state, keep lowest (most aggregated) |

**Derived variables:**

| Variable       | Computation                                  |
|----------------|----------------------------------------------|
| `PRIV_EMP`     | `annual_avg_emplvl` (direct read)            |
| `PRIV_ESTAB`   | `annual_avg_estabs` (direct read)            |
| `PRIV_AVG_PAY` | `total_annual_wages / PRIV_EMP`              |

**Note:** `PRIV_AVG_PAY` is a derived proxy for average annual pay.  The
official BLS "average annual pay" column is sometimes labeled differently
across vintages, so dividing total wages by employment ensures a consistent
definition.

---

## 4. PERMITS — Census Building Permits Survey (Summed-Unit Definition)

**Source:** Census Bureau Building Permits Survey (BPS), state annual file
**URL patterns tried (in order):**
1. `https://www2.census.gov/econ/bps/State/st{yyyy}a.txt`
2. `https://www2.census.gov/econ/bps/State/st{yy}a.txt`
3. `https://www2.census.gov/econ/bps/State/st_annual_{yyyy}.csv`

**Fallback:** Census BPS JSON API (`category_code=TOTAL`)

**Column structure:**
The text file has a 2-row header.  Data rows begin with a 6-digit survey code
(e.g., `202499` = year 2024, annual).  The parser skips all header rows and
assigns canonical column names based on the known BPS layout:

```
survey, fips, region, division, state_name,
1unit_bldgs, 1unit_units, 1unit_value,
2unit_bldgs, 2unit_units, 2unit_value,
34unit_bldgs, 34unit_units, 34unit_value,
5plus_bldgs, 5plus_units, 5plus_value,
[optional _rep columns...]
```

**Summed-unit definition:**

```
PERMITS = 1unit_units + 2unit_units + 34unit_units + 5plus_units
```

This sums **housing units authorized** (not buildings, not valuation) across
all four structure-type categories.  The `_rep` (reporting/revision) columns
are excluded from the sum.

**Rationale:** The four primary unit columns represent the canonical total of
housing units authorized by building permits.  The `_rep` columns are revision
companion fields that track reporting adjustments and should not be added to
the primary counts.

---

## 5. REAL_PCPI — BEA SARPI Runtime LineCode Discovery

**Source:** BEA Regional API, table `SARPI`

**Problem history:**
The SARPI table covers both Real Personal Income (PI) and Real Personal
Consumption Expenditures (PCE) by state.  It has many line codes — not just
3.  Two hardcoded attempts failed:

1. `LineCode=1` → returned total real personal income (millions of chained $).
   Values: mean ~$401k, max ~$2.5M.  This is aggregate state PI, not per capita.
2. `LineCode=3` → returned another aggregate series (possibly real PCE or
   another PI subcomponent).  Values: mean ~$321k, max ~$1.9M.  Still not
   per capita.

**Current approach — runtime metadata discovery:**

1. Call `GetParameterValuesFiltered(TableName=SARPI, TargetParameter=LineCode)`
   to retrieve all available line codes with descriptions.
2. Log every discovered line code and description to the build log.
3. Match the line whose description contains both `"per capita"` and
   `"personal income"` (case-insensitive), excluding any percent-change lines.
4. Fetch only that line code.
5. **Sanity check:** verify that the median state value is in the range
   $15,000–$150,000.  If outside this range, the pipeline fails with a clear
   error message identifying the mismatch.

**Why runtime discovery:**
BEA may reorder or renumber line codes across table vintages.  By matching
on the human-readable description rather than a hardcoded integer, the
pipeline is robust to such renumbering.

---

*Last updated: Phase A3 (REAL_PCPI runtime discovery fix).*
