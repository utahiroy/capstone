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

## 6. COMMUTE_MED — Grouped Median from ACS B08303

**Source:** ACS 2024 1-year, detail table B08303 (Travel Time to Work)
**Variables:** B08303_001E (total workers), B08303_002E–B08303_013E (12 time bins)

**Why not S0801_C01_046E:**
The subject table variable S0801_C01_046E was validated and confirmed to
provide **mean** travel time to work, not **median**.  The research design
specifies median.  Using mean would silently change the variable definition.

**Method:**
Grouped-median interpolation from 12 Census-defined time bins.  Standard
formula: `L + [(N/2 - F) / f] * C`.  Upper bound of the final bin
(90+ minutes) assumed to be 120 minutes.

**Sanity check:** Median of state medians must be 5–60 minutes.

---

## 7. UNINSURED — ACS Subject Table S2701 with B27010 Fallback

**Primary source:** ACS 2024 1-year subject table S2701
**Variable:** S2701_C05_001E (percent uninsured, total population)
**API endpoint:** `/data/2024/acs/acs1/subject` (different from detail table base)

**Cross-check logic:**
When S2701 succeeds, the direct percentage is cross-checked against a
recomputed value (S2701_C04_001E / S2701_C01_001E * 100).  If the max
discrepancy exceeds 1.0 percentage point, a warning is logged.

**Fallback:** Detail table B27010 (Types of Health Insurance by Age).
All B27010 uninsured codes (017, 033, 050, 066) verified against Census
Reporter ACS 2024 1-year metadata.

---

## 8. CRIME_VIOLENT_RATE — FBI CDE API (Provisional)

**Source:** FBI Crime Data Explorer, UCR estimated state-level data
**Key:** DATA_GOV_API_KEY (free from https://api.data.gov/signup/)

**Endpoint cascade (tried in order):**

1. **CDE endpoint (current, post-July 2025):**
   `https://api.usa.gov/crime/fbi/cde/estimate/state/{abbr}/violent-crime?from={year}&to={year}&API_KEY={key}`
   The FBI migrated endpoints in July 2025.  The CDE base is the current
   public path.

2. **SAPI endpoint (legacy fallback):**
   `https://api.usa.gov/crime/fbi/sapi/api/estimates/states/{abbr}/{year}/{year}?api_key={key}`
   This was the original public API path.  It returned HTTP 403 during
   the prior pipeline run (likely due to the July 2025 migration).

3. **CSV fallback:**
   If both API methods fail, place a CSV at `data_raw/fbi_crime_state_2024.csv`
   with columns `state_abbr, violent_crime, population` (or pre-computed
   `state, CRIME_VIOLENT_RATE`).

**Extraction:**
The API is called once per state (50 calls).  Each call returns a JSON
response.  The code handles multiple response formats: list of records,
dict with `results` key, and varying field names (`violent_crime` or
`value`; `year` or `data_year`).

**Rate formula:** `CRIME_VIOLENT_RATE = 100000 * violent_crime / population`

**Retry logic:** Up to 3 attempts per state with exponential backoff on
rate limits (HTTP 429) and transient errors.  If a 403 or 404 is received,
the entire endpoint method is abandoned and the next method is tried.

**Why provisional:** The CDE endpoint URL pattern is based on documented
migration notices and working examples from other CDE endpoints, but the
exact response JSON structure for the estimates endpoint has not been
validated against live data in a successful pipeline run.

---

## 9. NRI_RISK_INDEX — FEMA County-to-State Aggregation (Provisional)

**Source:** FEMA National Risk Index v1.20 (December 2025), county-level data

**Retrieval cascade (tried in order):**

1. **OpenFEMA paginated JSON API (primary):**
   `https://www.fema.gov/api/open/v1/NationalRiskIndexCounty?$select=STATEFIPS,STCOFIPS,STATE,COUNTY,POPULATION,RISK_SCORE,RISK_RATNG&$top=10000&$skip=N`
   No API key required.  Paginated with `$top`/`$skip` (max 10,000 per call).

2. **OpenFEMA bulk CSV download:**
   `https://www.fema.gov/api/open/v1/NationalRiskIndexCounty.csv`
   Full download, no pagination needed.

3. **Legacy hazards.fema.gov URLs (fallback):**
   `https://hazards.fema.gov/nri/Content/StaticDocuments/DataDownload/NRI_Table_Counties/NRI_Table_Counties.csv`
   These URLs were guessed and failed in the prior pipeline run.

4. **Local CSV fallback:**
   If all downloads fail, place a county-level CSV at
   `data_raw/nri_counties_raw.csv` manually.

**Key columns used:**
- `STATEFIPS` — 2-digit state FIPS
- `POPULATION` — county population from Hazus
- `RISK_SCORE` — composite overall risk score (0–100 percentile among counties)

**Aggregation method:**
Population-weighted mean:
`NRI_RISK_INDEX = sum(county_pop * county_RISK_SCORE) / sum(county_pop)`

Counties with missing RISK_SCORE or zero population are excluded.

**Vintage exception:**
NRI v1.20 was released December 2025.  This is a documented exception to the
project's 2024-only cross-section design.  Justification: the NRI is not
published annually; it is an irregularly updated composite index based on
multi-year hazard records and Census 2020 population.  NRI scores change slowly
and are a reasonable proxy for 2024 conditions.  The prior version (v1.19.0)
was released March 2023.  This exception must be disclosed in the final report.

**Why provisional:**
1. FEMA does not provide a direct state-level composite Risk Index.
2. The population-weighted mean is a project decision.
3. Averaging county percentile ranks produces a meaningful measure of
   "average risk exposure" but is not a true state-level percentile.
4. Alternative aggregation methods (unweighted mean, EAL-based) could
   produce different rankings.
5. The OpenFEMA API response structure has not been validated in a
   successful pipeline run.

**Caching:** Downloaded county CSV is saved to `data_raw/nri_counties_raw.csv`
and reused on subsequent runs.  Delete the cached file to force re-download.

---

*Last updated: Phase A2 deferred-IV implementation (COMMUTE_MED, UNINSURED, CRIME_VIOLENT_RATE, NRI_RISK_INDEX).*
