# Validation Memo: Four Deferred Explanatory Variables

**Date**: 2026-03-22
**Variables**: COMMUTE_MED, UNINSURED, CRIME_VIOLENT_RATE, NRI_RISK_INDEX
**Scope**: 50 U.S. states, 2024 cross-section

---

## Summary

| Variable | Status | Source | Method |
|---|---|---|---|
| COMMUTE_MED | **Verified** | ACS 2024 1-year B08303 | Grouped-median interpolation from travel-time bins |
| UNINSURED | **Verified** | ACS 2024 1-year S2701 (primary) / B27010 (fallback) | Direct percent read or computed from counts |
| CRIME_VIOLENT_RATE | **Provisional** | FBI CDE API (estimates endpoint) | API call per state; CSV manual fallback available |
| NRI_RISK_INDEX | **Provisional** | FEMA NRI v1.20 county-level CSV | Population-weighted mean of county RISK_SCORE |

---

## 1. COMMUTE_MED — Verified Implementation

### Variable definition
Approximate grouped median travel time to work (minutes) for workers 16+.

### Source validated
- **Table**: ACS 2024 1-year, B08303 (Travel Time to Work)
- **API endpoint**: `https://api.census.gov/data/2024/acs/acs1` (standard detail table)
- **Variables**: B08303_001E (total), B08303_002E through B08303_013E (12 bins)

### Why NOT S0801_C01_046E
The subject table variable S0801_C01_046E provides **mean** travel time to work, not median. The research design specifies median. Using mean would change the variable definition.

### Method
Grouped-median interpolation using the standard formula:

```
median = L + [(N/2 - F) / f] * C
```

Where:
- L = lower bound of the median bin
- N = total count of workers
- F = cumulative count in bins before the median bin
- f = count in the median bin
- C = width of the median bin

### Bin boundaries used

| Variable | Range (minutes) |
|---|---|
| B08303_002E | 0–5 |
| B08303_003E | 5–10 |
| B08303_004E | 10–15 |
| B08303_005E | 15–20 |
| B08303_006E | 20–25 |
| B08303_007E | 25–30 |
| B08303_008E | 30–35 |
| B08303_009E | 35–40 |
| B08303_010E | 40–45 |
| B08303_011E | 45–60 |
| B08303_012E | 60–90 |
| B08303_013E | 90–120 (upper bound assumed) |

### Sanity check
Median of state medians must be 5–60 minutes.

### Unit
Minutes.

### Implementation file
`src/fetch_commute.py`

---

## 2. UNINSURED — Verified Implementation

### Variable definition
Percent of civilian noninstitutionalized population without health insurance coverage.

### Primary source validated
- **Table**: ACS 2024 1-year subject table S2701 (Health Insurance Coverage Status)
- **API endpoint**: `https://api.census.gov/data/2024/acs/acs1/subject`
- **Variable**: S2701_C05_001E (percent uninsured, total population)
  - C05 = "Percent Uninsured" column
  - 001 = total population row

### Cross-check
Recomputed from S2701_C04_001E (uninsured count) / S2701_C01_001E (total population). Maximum allowed difference: 1.0 percentage point.

### Fallback source validated
- **Table**: ACS 2024 1-year detail table B27010 (Types of Health Insurance by Age)
- **Variables**: B27010_017E + B27010_033E + B27010_050E + B27010_066E (no insurance by age group)
- **Denominator**: B27010_001E (total)
- **Formula**: `UNINSURED = 100 * sum_uninsured / total`
- All B27010 codes verified against Census Reporter ACS 2024 1-year metadata.

### Sanity check
Median state rate must be 2–25%.

### Unit
Percent.

### Implementation file
`src/fetch_uninsured.py`

---

## 3. CRIME_VIOLENT_RATE — Provisional Implementation

### Variable definition
Estimated violent crime rate per 100,000 population. Violent crime = murder and nonnegligent manslaughter + rape + robbery + aggravated assault (FBI definition).

### Source
- **Agency**: FBI Crime Data Explorer (CDE)
- **API**: `https://api.usa.gov/crime/fbi/sapi/api/estimates/states/{state_abbr}/{year}/{year}`
- **Key**: DATA_GOV_API_KEY (free from https://api.data.gov/signup/)
- **Data year**: 2024

### Why provisional
1. The FBI CDE API has been documented as unreliable (timeouts, rate limits).
2. The API returns SRS-estimated data. With the FBI's transition from SRS to NIBRS, the estimates methodology is evolving.
3. 2024 data covers 95.6% of the U.S. population (not 100%).
4. If the API fails, a manual CSV fallback is available at `data_raw/fbi_crime_state_2024.csv`.

### Formula
If the API returns `violent_crime` (count) and `population`:
```
CRIME_VIOLENT_RATE = 100,000 * violent_crime / population
```

### Sanity check
Median state rate must be 50–800 per 100,000.

### Unit
Per 100,000 population.

### Implementation file
`src/fetch_crime.py`

---

## 4. NRI_RISK_INDEX — Provisional Implementation

### Variable definition
Population-weighted mean of county-level composite Risk Index score, aggregated to state level.

### Source
- **Agency**: FEMA National Risk Index, v1.20 (December 2025)
- **Download**: County-level CSV from https://hazards.fema.gov/nri/data-resources
- **Geographic level**: County (3,000+ records nationwide)

### Why provisional
1. **FEMA does not provide a direct state-level composite Risk Index score.** The NRI provides county and Census tract level scores only.
2. The aggregation method (population-weighted mean) is a **project decision**, not an official FEMA metric.
3. Alternative approaches include:
   - Unweighted mean of county scores
   - State-level Expected Annual Loss (EAL) — different construct
   - Maximum county score per state
4. RISK_SCORE is a percentile ranking (0–100) relative to all counties. Averaging percentile ranks is a simplification; the resulting state-level number is NOT a true percentile among states.

### Aggregation formula
```
NRI_RISK_INDEX_state = sum(county_population * county_RISK_SCORE) / sum(county_population)
```

For each state, only counties with non-missing RISK_SCORE and positive population are included.

### Key NRI CSV columns used
- `STATEFIPS`: 2-digit state FIPS
- `POPULATION`: county population (from Hazus)
- `RISK_SCORE`: composite overall risk score (0–100)

### Sanity check
- At least 45 of 50 states must be present after aggregation
- RISK_SCORE values must be in 0–100 range

### Unit
Index score (weighted average of county percentile rankings).

### Implementation file
`src/fetch_nri.py`

---

## Implementation Status Summary

### Verified implementations
- **COMMUTE_MED**: Grouped median from ACS B08303 bins. Standard statistical method. No methodological ambiguity.
- **UNINSURED**: Direct percent from ACS S2701 subject table with cross-check, or computed from B27010 detail table as fallback.

### Provisional implementations
- **CRIME_VIOLENT_RATE**: FBI CDE API is the correct source, but API reliability is uncertain. Manual CSV fallback is available. The data itself (2024 UCR estimates) is the standard source for this variable.
- **NRI_RISK_INDEX**: Population-weighted county aggregation is a project-defined method. The resulting variable measures something different from FEMA's official county-level RISK_SCORE. This should be interpreted as "average natural hazard risk exposure of the state's population" rather than "state risk ranking."

### Unresolved ambiguities
None that block implementation, but:
1. CRIME_VIOLENT_RATE API may fail at runtime; manual data entry from the UCR summary report would be needed.
2. NRI_RISK_INDEX aggregation method could be revisited (e.g., EAL-based instead of RISK_SCORE-based).
