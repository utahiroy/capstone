# Source Contract: Data Variables and Provenance

This document specifies the exact source, table, variable codes, formulas, and status
for every dependent and explanatory variable in the project.

**Research scope**: 50 U.S. states, 2024 cross-section only. DC, PR, and non-state geographies excluded.

---

## 1. Dependent Variables: Migration Measures

### 1.1 Data source

**Primary source**: ACS 2024 1-year estimates, via Census API.

| Table | Title | Role |
|---|---|---|
| B07001 | Geographic Mobility in Past Year by Age for Current Residence | Provides **IN-migration** counts by age (people currently in the state who moved from a different state) |
| B07401 | Geographic Mobility in Past Year by Age for Residence 1 Year Ago | Provides **OUT-migration** counts by age (people who lived in the state 1 year ago and moved to a different state) |

**API endpoint**: `https://api.census.gov/data/2024/acs/acs1`

**Universe**: Population 1 year and over in the United States.

### 1.2 Table structure: B07001

B07001 is organized as 6 mobility categories, each with a subtotal + 15 age groups (16 variables per category = 96 total variables).

**Mobility categories** (with subtotal variable codes):

| Block | Category | Subtotal code |
|---|---|---|
| Total population | All mobility statuses combined | B07001_001E |
| Same house | Did not move | B07001_017E |
| Same county | Moved within same county | B07001_033E |
| Different county, same state | Moved from different county in same state | B07001_049E |
| **Different state** | **Moved from a different U.S. state** | **B07001_065E** |
| Abroad | Moved from abroad | B07001_081E |

**Age groups within each block** (offsets from block start):

| Offset | Age group |
|---|---|
| +0 | Subtotal (all ages) |
| +1 | 1 to 4 years |
| +2 | 5 to 17 years |
| +3 | 18 and 19 years |
| +4 | 20 to 24 years |
| +5 | 25 to 29 years |
| +6 | 30 to 34 years |
| +7 | 35 to 39 years |
| +8 | 40 to 44 years |
| +9 | 45 to 49 years |
| +10 | 50 to 54 years |
| +11 | 55 to 59 years |
| +12 | 60 to 64 years |
| +13 | 65 to 69 years |
| +14 | 70 to 74 years |
| +15 | 75 years and over |

### 1.3 IN_COUNT variable mapping (from B07001 "Different state" block)

These variables count people **currently residing** in a state who moved **from a different U.S. state** in the past year.

| Project age group | ACS age brackets | ACS variable codes | Aggregation |
|---|---|---|---|
| 18-24 | 18-19, 20-24 | B07001_068E, B07001_069E | Sum |
| 25-34 | 25-29, 30-34 | B07001_070E, B07001_071E | Sum |
| 35-54 | 35-39, 40-44, 45-49, 50-54 | B07001_072E, B07001_073E, B07001_074E, B07001_075E | Sum |
| 55-64 | 55-59, 60-64 | B07001_076E, B07001_077E | Sum |
| 65+ | 65-69, 70-74, 75+ | B07001_078E, B07001_079E, B07001_080E | Sum |

**Status**: **confirmed** — variable codes verified against Census Reporter ACS 2024 1-year precomputed metadata (GitHub). All 96 B07001 variables confirmed.

### 1.4 OUT_COUNT variable mapping (from B07401 "Different state" block)

B07401 has the same structure as B07001 but from the perspective of the **state of residence 1 year ago**. The "different state" category counts people who **left** the state for a different U.S. state.

| Project age group | ACS age brackets | ACS variable codes | Aggregation |
|---|---|---|---|
| 18-24 | 18-19, 20-24 | B07401_068E, B07401_069E | Sum |
| 25-34 | 25-29, 30-34 | B07401_070E, B07401_071E | Sum |
| 35-54 | 35-39, 40-44, 45-49, 50-54 | B07401_072E, B07401_073E, B07401_074E, B07401_075E | Sum |
| 55-64 | 55-59, 60-64 | B07401_076E, B07401_077E | Sum |
| 65+ | 65-69, 70-74, 75+ | B07401_078E, B07401_079E, B07401_080E | Sum |

**Status**: **confirmed** — variable codes verified against Census Reporter ACS 2024 1-year precomputed metadata (GitHub). All 80 B07401 variables confirmed. Note: B07401 has no "Moved from abroad" category (it tracks the previous-residence perspective).

### 1.5 Age-group population denominator

**Critical design decision**: The denominator for migration rates (POP_AGE in the DV formula) must be **age-group-specific**, not total state population.

**Source**: ACS 2024 1-year table **B01001** (Sex by Age). Universe: Total population. Male + Female summed.

B01001 uses finer age bins than B07001, so multiple cells must be summed per project age group:

| Project age group | Male codes | Female codes | # cells |
|---|---|---|---|
| 18-24 | B01001_007E (18-19), B01001_008E (20), B01001_009E (21), B01001_010E (22-24) | B01001_031E (18-19), B01001_032E (20), B01001_033E (21), B01001_034E (22-24) | 8 |
| 25-34 | B01001_011E (25-29), B01001_012E (30-34) | B01001_035E (25-29), B01001_036E (30-34) | 4 |
| 35-54 | B01001_013E (35-39), B01001_014E (40-44), B01001_015E (45-49), B01001_016E (50-54) | B01001_037E (35-39), B01001_038E (40-44), B01001_039E (45-49), B01001_040E (50-54) | 8 |
| 55-64 | B01001_017E (55-59), B01001_018E (60-61), B01001_019E (62-64) | B01001_041E (55-59), B01001_042E (60-61), B01001_043E (62-64) | 6 |
| 65+ | B01001_020E (65-66), B01001_021E (67-69), B01001_022E (70-74), B01001_023E (75-79), B01001_024E (80-84), B01001_025E (85+) | B01001_044E (65-66), B01001_045E (67-69), B01001_046E (70-74), B01001_047E (75-79), B01001_048E (80-84), B01001_049E (85+) | 12 |

**Rationale**: B01001 provides the standard total-population age-group denominator. For ages 18+, this is functionally identical to B07001 Total (population 1 year and over) since everyone 18+ is automatically 1 year and over. B01001 is preferred because it is the canonical population-by-age table and avoids coupling the denominator to the mobility table's universe definition.

**Status**: **confirmed** — all 49 B01001 variable codes verified against Census Reporter ACS 2024 1-year precomputed metadata (GitHub).

### 1.6 DV formulas

All formulas are computed per state per age group.

| Variable | Formula | Unit |
|---|---|---|
| IN_COUNT | Sum of B07001 "different state" age bracket variables | persons |
| OUT_COUNT | Sum of B07401 "different state" age bracket variables | persons |
| NET_COUNT | IN_COUNT − OUT_COUNT | persons |
| POP_AGE | Sum of B01001 male + female age bracket variables | persons |
| IN_RATE | 1000 × IN_COUNT / POP_AGE | per 1,000 |
| OUT_RATE | 1000 × OUT_COUNT / POP_AGE | per 1,000 |
| **NET_RATE** | **1000 × (IN_COUNT − OUT_COUNT) / POP_AGE** | **per 1,000** |

### 1.7 Supplemental benchmark

| Source | Role | Table |
|---|---|---|
| Census State-to-State Migration Flows | All-ages consistency check only | ACS table series (state-to-state flows) |

This source is **not** used for the main age-group DVs.

---

## 2. Explanatory Variable: POP (Total State Population)

| Field | Value |
|---|---|
| ID | POP |
| Description | Total state population, 2024 |
| Source | ACS 2024 1-year, table B01001 (Sex by Age) |
| Dataset | ACS 2024 1-year estimates |
| Access | Census API: `https://api.census.gov/data/2024/acs/acs1?get=B01001_001E&for=state:*` |
| Variable code | B01001_001E (total population, both sexes) |
| Unit | persons |
| Formula | direct read |
| PEP alternative | Census PEP vintage 2024 (`/data/2024/pep/population`) was the original planned source but has not been implemented. ACS B01001_001E was used in smoke test and A2 pipeline. PEP may be revisited if ACS total pop proves insufficient (e.g., universe differences). For this cross-sectional analysis the difference is negligible. |
| Status | **confirmed (smoke-tested)** — ACS B01001_001E returns total population for all 50 states. |

---

## 3. Explanatory Variable: LAND_AREA

| Field | Value |
|---|---|
| ID | LAND_AREA |
| Description | Land area in square miles |
| Source | Census Bureau, State Area Measurements (2010 Census) |
| URL | https://www.census.gov/geographies/reference-files/2010/geo/state-area.html |
| Access | File download (static reference table) |
| File format | Text/CSV table |
| Variable | Land area (sq mi) column |
| Unit | square miles |
| Formula | direct read |
| Status | **confirmed** — static data, will not change |

---

## 4. Explanatory Variable: POP_DENS

| Field | Value |
|---|---|
| ID | POP_DENS |
| Description | Population density |
| Source | Derived |
| Formula | POP / LAND_AREA |
| Unit | persons per square mile |
| Status | **confirmed** — derived from POP and LAND_AREA |

---

## 5. Explanatory Variable: GDP

| Field | Value |
|---|---|
| ID | GDP |
| Description | Gross Domestic Product by state, 2024 annual |
| Source | Bureau of Economic Analysis (BEA) |
| Dataset | Regional GDP (SAGDP) |
| API | `https://apps.bea.gov/api/data/?datasetname=Regional&TableName=SAGDP1&LineCode=1&GeoFips=STATE&Year=2024&ResultFormat=JSON&UserID={key}` |
| Variable | All-industry total GDP (current dollars) |
| Unit | millions of dollars |
| Formula | direct read |
| Table candidates | SAGDP2N tried first; SAGDP1 used as working fallback. Smoke test confirmed SAGDP1 succeeds. |
| Status | **confirmed (smoke-tested)** — SAGDP2N rejected by BEA API ("Invalid Value for Parameter TableName"); SAGDP1 with LineCode=1 returned valid 2024 state GDP. Code tries both candidates in order with explicit logging. |

---

## 6. Explanatory Variable: RPP

| Field | Value |
|---|---|
| ID | RPP |
| Description | Regional Price Parities (all items), state-level |
| Source | BEA |
| Dataset | Regional Price Parities (SARPP) |
| API | `https://apps.bea.gov/api/data/?datasetname=Regional&TableName=SARPP&LineCode=1&GeoFips=STATE&Year=2024&ResultFormat=JSON&UserID={key}` |
| Variable | All-items RPP index (US = 100) |
| Unit | index (US = 100) |
| Formula | direct read |
| Status | **confirmed** — 2024 RPP released February 2026. BEA discontinued MSA-level RPP but state-level continues. |

---

## 7. Explanatory Variable: REAL_PCPI

| Field | Value |
|---|---|
| ID | REAL_PCPI |
| Description | Real per capita personal income, state-level |
| Source | BEA |
| Dataset | Regional (SARPI) |
| API | `https://apps.bea.gov/api/data/?datasetname=Regional&TableName=SARPI&LineCode={discovered}&GeoFips=STATE&Year=2024&ResultFormat=JSON&UserID={key}` |
| Variable | Per capita real personal income (chained dollars) |
| Unit | chained dollars |
| Formula | direct read |
| LineCode discovery | Runtime: `GetParameterValuesFiltered(TableName=SARPI, TargetParameter=LineCode)` → match description containing "per capita" + "personal income", excluding percent-change lines. |
| Sanity check | Median must be in $15k–$150k range (plausible per-capita). Pipeline fails loudly if violated. |
| Status | **runtime-discovered** — SARPI table covers both Real PI and Real PCE with many line codes. Hardcoded LC assumptions (LC=1, LC=3) both returned wrong series. Now uses metadata-driven discovery + sanity check. |

---

## 8. Explanatory Variable: UNEMP

| Field | Value |
|---|---|
| ID | UNEMP |
| Description | Annual average unemployment rate, 2024 |
| Source | BLS Local Area Unemployment Statistics (LAUS) |
| URL | https://www.bls.gov/lau/lastrk24.htm |
| Implementation | BLS API v2 (public, no key required): series ID `LASST{FIPS}0000000000003`, period M13 = annual average. Batched 25 series per request. |
| Access | BLS API v2 (A2 implementation) |
| Unit | percent |
| Formula | direct read |
| Status | **confirmed** — LAUS 2024 annual averages published by early 2025. A2 uses BLS API. |

---

## 9. Explanatory Variables: PRIV_EMP, PRIV_ESTAB, PRIV_AVG_PAY

| Field | PRIV_EMP | PRIV_ESTAB | PRIV_AVG_PAY |
|---|---|---|---|
| Description | Private employment (annual avg) | Private establishments (annual avg) | Average annual pay (private) |
| Source | BLS QCEW | BLS QCEW | BLS QCEW (derived) |
| Download | QCEW CSV data slice API (no key required) | same | same |
| URL | `https://data.bls.gov/cew/data/api/2024/a/industry/10.csv` | same | same |
| Alt URL | https://www.bls.gov/cew/downloadable-data-files.htm (bulk download) | same | same |
| Filter: own_code | 5 (private) | 5 (private) | 5 (private) |
| Filter: industry_code | 10 (total, all industries) | 10 (total, all industries) | 10 (total, all industries) |
| Filter: area_fips | State-level FIPS (XX000) | same | same |
| Filter: agglvl_code | 50 (state, total, by ownership) | 50 | 50 |
| Filter: size_code | 0 (all sizes) | 0 (all sizes) | 0 (all sizes) |
| Column | annual_avg_emplvl | annual_avg_estabs | total_annual_wages / annual_avg_emplvl |
| Unit | persons | count | dollars |
| Formula | direct read | direct read | total_annual_wages / annual_avg_emplvl |
| Status | **confirmed** | **confirmed** | **confirmed** — derived within QCEW data |

---

## 10. Explanatory Variable: PERMITS

| Field | Value |
|---|---|
| ID | PERMITS |
| Description | Housing units authorized by building permits, 2024 annual |
| Source | Census Bureau, Building Permits Survey (BPS) |
| URL | https://www.census.gov/construction/bps/stateannual.html |
| Access | Download state annual data file (TXT or CSV) |
| Variable | Total units (all building types) |
| Unit | housing units |
| Formula | direct read |
| Status | **confirmed** — published annually |

---

## 11. Explanatory Variable: MED_RENT

| Field | Value |
|---|---|
| ID | MED_RENT |
| Description | Median gross rent |
| Source | ACS 2024 1-year |
| Table | B25064 |
| Variable | B25064_001E |
| API | `https://api.census.gov/data/2024/acs/acs1?get=B25064_001E&for=state:*` |
| Unit | dollars |
| Formula | direct read |
| Status | **confirmed** |

---

## 12. Explanatory Variable: MED_HOMEVAL

| Field | Value |
|---|---|
| ID | MED_HOMEVAL |
| Description | Median home value (owner-occupied housing units) |
| Source | ACS 2024 1-year |
| Table | B25077 |
| Variable | B25077_001E |
| API | `https://api.census.gov/data/2024/acs/acs1?get=B25077_001E&for=state:*` |
| Unit | dollars |
| Formula | direct read |
| Status | **confirmed** |

---

## 13. Explanatory Variable: COST_BURDEN_ALL

| Field | Value |
|---|---|
| ID | COST_BURDEN_ALL |
| Description | Housing cost burden: share of all households paying >= 30% of income on housing |
| Source | ACS 2024 1-year |
| Tables | B25070 (renters) + B25091 (owners by mortgage status) |
| Type | Computed from multiple variables |

**Renter cost-burdened (from B25070)**:

| Code | Label |
|---|---|
| B25070_001E | Total renter households (denominator, renters) |
| B25070_007E | 30.0 to 34.9 percent |
| B25070_008E | 35.0 to 39.9 percent |
| B25070_009E | 40.0 to 49.9 percent |
| B25070_010E | 50.0 percent or more |

Renter burden = B25070_007E + B25070_008E + B25070_009E + B25070_010E

**Owner cost-burdened (from B25091)**:

| Code | Label |
|---|---|
| B25091_001E | Total owner-occupied housing units (denominator, owners) |
| B25091_008E | With mortgage, 30.0 to 34.9 percent |
| B25091_009E | With mortgage, 35.0 to 39.9 percent |
| B25091_010E | With mortgage, 40.0 to 49.9 percent |
| B25091_011E | With mortgage, 50.0 percent or more |
| B25091_019E | Without mortgage, 30.0 to 34.9 percent |
| B25091_020E | Without mortgage, 35.0 to 39.9 percent |
| B25091_021E | Without mortgage, 40.0 to 49.9 percent |
| B25091_022E | Without mortgage, 50.0 percent or more |

**Formula**:
```
renter_burdened = B25070_007E + B25070_008E + B25070_009E + B25070_010E
owner_burdened  = B25091_008E + B25091_009E + B25091_010E + B25091_011E
              + B25091_019E + B25091_020E + B25091_021E + B25091_022E
COST_BURDEN_ALL = 100 * (renter_burdened + owner_burdened) / (B25070_001E + B25091_001E)
```

**Unit**: percent

**Status**: **confirmed** — all B25070 and B25091 variable codes verified against Census Reporter ACS 2024 1-year precomputed metadata (GitHub). B25070: 11 variables (001–011). B25091: 23 variables (001–023). Codes 008–011 (with mortgage >=30%) and 019–022 (without mortgage >=30%) confirmed.

---

## 14. Explanatory Variable: VACANCY_RATE

| Field | Value |
|---|---|
| ID | VACANCY_RATE |
| Description | Rental vacancy rate |
| Source | ACS 2024 1-year |
| Tables | B25004 (vacancy status) + B25003 (tenure) |

**Variables**:
- B25004_002E = Vacant units "For rent"
- B25004_003E = Vacant units "Rented, not occupied"
- B25003_003E = Occupied units, renter-occupied

**Formula**:
```
VACANCY_RATE = 100 * B25004_002E / (B25004_002E + B25004_003E + B25003_003E)
```

**Unit**: percent

**Note**: This is the standard ACS-based rental vacancy rate formula. It differs from the CPS Housing Vacancy Survey definition but is the appropriate measure when using ACS data.

**Status**: **confirmed**

---

## 15. Explanatory Variable: COMMUTE_MED

| Field | Value |
|---|---|
| ID | COMMUTE_MED |
| Description | Approximate grouped median travel time to work (minutes) |
| Source | ACS 2024 1-year |
| Table | B08303 (Travel Time to Work) |
| Variables | B08303_001E (total), B08303_002E–B08303_013E (12 time bins) |
| API | `https://api.census.gov/data/2024/acs/acs1?get=B08303_001E,...,B08303_013E&for=state:*` |
| Unit | minutes |
| Formula | Grouped-median interpolation: `L + [(N/2 - F) / f] * C` |
| Status | **verified** — S0801_C01_046E was confirmed as MEAN travel time (not median). Grouped median from B08303 bins is the correct implementation for COMMUTE_MED. |

**Note on S0801_C01_046E**: This subject table variable provides **mean** travel time to work, not median. Using it would change the variable definition from the research design. The B08303 grouped-median approach preserves the intended definition.

---

## 16. Explanatory Variable: TRANSIT_SHARE

| Field | Value |
|---|---|
| ID | TRANSIT_SHARE |
| Description | Public transportation share of commuters |
| Source | ACS 2024 1-year |
| Table | B08301 (Means of Transportation to Work) |
| Variables | B08301_010E (public transportation; taxi/ride-hailing is separate sibling B08301_016E), B08301_001E (total workers 16+) |

**Formula**:
```
TRANSIT_SHARE = 100 * B08301_010E / B08301_001E
```

**Unit**: percent

**Status**: **confirmed**

---

## 17. Explanatory Variable: BA_PLUS

| Field | Value |
|---|---|
| ID | BA_PLUS |
| Description | Percentage with bachelor's degree or higher, population 25+ |
| Source | ACS 2024 1-year |
| Table | B15003 (Educational Attainment, 25+) |
| Variables | B15003_022E (bachelor's), B15003_023E (master's), B15003_024E (professional), B15003_025E (doctorate), B15003_001E (total 25+) |

**Formula**:
```
BA_PLUS = 100 * (B15003_022E + B15003_023E + B15003_024E + B15003_025E) / B15003_001E
```

**Unit**: percent

**Status**: **confirmed**

---

## 18. Explanatory Variable: UNINSURED

| Field | Value |
|---|---|
| ID | UNINSURED |
| Description | Uninsured rate, civilian noninstitutionalized population |
| Source | ACS 2024 1-year |
| Table | Subject table S2701 (preferred) or detail table B27010 |
| Primary variable | S2701_C05_001E (uninsured percentage, total) |
| API | `https://api.census.gov/data/2024/acs/acs1/subject?get=S2701_C05_001E&for=state:*` |

**Cross-check**: Recomputed from S2701_C04_001E (count) / S2701_C01_001E (total). Max allowed difference: 1.0 pp.

**Fallback** (if subject table unavailable):
- Table B27010 (Types of Health Insurance Coverage by Age)
- Uninsured = B27010_017E + B27010_033E + B27010_050E + B27010_066E
- Total = B27010_001E
- UNINSURED = 100 * (sum of uninsured) / total

**Unit**: percent

**Status**: **verified** — S2701_C05_001E confirmed as percent uninsured for ACS 2024 1-year. C05 = Percent Uninsured column, 001 = total population row. Subject table API endpoint: `/data/2024/acs/acs1/subject`. Fallback B27010 codes also confirmed.

---

## 19. Explanatory Variable: ELEC_PRICE_TOT

| Field | Value |
|---|---|
| ID | ELEC_PRICE_TOT |
| Description | Average retail price of electricity, total (all sectors) |
| Source | EIA (Energy Information Administration) |
| URL | https://www.eia.gov/electricity/sales_revenue_price/ |
| Alternative | EIA API v2: `https://api.eia.gov/v2/electricity/retail-sales/data/?api_key={key}&frequency=annual&data[0]=price&facets[sectorid][]=ALL&facets[stateid][]={ST}&start=2024&end=2024` |
| Unit | cents per kWh |
| Formula | direct read |
| Status | **confirmed** — 2024 EIA-861 data available. API endpoint: `/v2/electricity/retail-sales/data/` with facets `sectorid=ALL`, `frequency=annual`. Omit `stateid` facet to get all states. |

---

## 20. Explanatory Variable: CRIME_VIOLENT_RATE

| Field | Value |
|---|---|
| ID | CRIME_VIOLENT_RATE |
| Description | Violent crime rate per 100,000 population |
| Source | FBI Crime Data Explorer (CDE) |
| URL | https://cde.ucr.cjis.gov/ |
| Primary API (CDE, current) | `https://api.usa.gov/crime/fbi/cde/estimate/state/{abbr}/violent-crime?from={year}&to={year}&API_KEY={key}` |
| Legacy API (SAPI, fallback) | `https://api.usa.gov/crime/fbi/sapi/api/estimates/states/{abbr}/{year}/{year}?api_key={key}` |
| CSV fallback | `data_raw/fbi_crime_state_2024.csv` (manually prepared) |
| API key | DATA_GOV_API_KEY — free from https://api.data.gov/signup/ |
| Unit | per 100,000 |
| Formula | `100000 * violent_crime / population` |
| Status | **provisional** — In July 2025, the FBI migrated API endpoints; the legacy SAPI path returned HTTP 403. Code now tries CDE endpoint first, then SAPI, then CSV fallback. The successful local pipeline run used the CSV fallback. The CDE endpoint response format has not been validated against live data. 2024 data covers 95.6% of U.S. population. |

---

## 21. Explanatory Variable: NRI_RISK_INDEX

| Field | Value |
|---|---|
| ID | NRI_RISK_INDEX |
| Description | FEMA National Risk Index, overall composite risk score, state-level |
| Source | FEMA / OpenFEMA |
| Primary API | OpenFEMA REST API (no key): `https://www.fema.gov/api/open/v1/NationalRiskIndexCounty` (paginated JSON or `.csv` bulk) |
| Legacy URL | https://hazards.fema.gov/nri/data-resources (download links failed in prior run) |
| Local fallback | `data_raw/nri_counties_raw.csv` (manually placed county-level CSV) |
| Version | v1.20 (December 2025) — latest available |
| Variable | RISK_SCORE (composite overall risk) |
| Unit | index score (weighted average of county percentile rankings) |
| Geographic level | **County and tract only** — state-level composite Risk Index is NOT directly provided by FEMA |
| State alternative | State-level Expected Annual Loss (EAL) IS provided directly (different construct, not used) |
| Formula | Population-weighted mean of county RISK_SCORE: `sum(county_pop * county_RISK_SCORE) / sum(county_pop)` |
| Vintage exception | **NRI v1.20 (Dec 2025) is a methodological exception to the project's 2024-only design.** The NRI is not published annually. The prior version (v1.19.0) was released March 2023. NRI uses multi-year underlying data (Census 2020 population, historical hazard records) and scores change slowly, making v1.20 a reasonable proxy for 2024 conditions. This must be disclosed in the final report. |
| Status | **provisional** — Implemented as population-weighted mean of county-level composite RISK_SCORE. This is a project-defined aggregation, not an official FEMA state-level metric. RISK_SCORE is a 0–100 percentile ranking among all U.S. counties. The successful local pipeline run used a manually placed local CSV. The OpenFEMA API response structure has not been validated in a successful pipeline run. |

---

## 22. Summary of source status

**Verification method**: Census Reporter ACS 2024 1-year precomputed metadata on GitHub (mirrors Census Bureau table shells). All ACS detail table codes verified against this source. ACS 2024 1-year dataset confirmed available.

### Confirmed (ready to implement)

| # | Variable | Source | Verification |
|---|---|---|---|
| DV | IN_COUNT (all age groups) | ACS B07001 "Different state" block | 96 vars verified, ACS 2024 1-yr |
| DV | OUT_COUNT (all age groups) | ACS B07401 "Different state" block | 80 vars verified, ACS 2024 1-yr |
| DV | POP_AGE denominator | **ACS B01001** (Sex by Age, male+female) | 49 vars verified, ACS 2024 1-yr |
| 1 | POP | ACS B01001_001E (total population) | Smoke-tested; PEP deferred |
| 3 | LAND_AREA | Census state area reference (static) | unchanged |
| 4 | POP_DENS | Derived (POP / LAND_AREA) | unchanged |
| 5 | GDP | BEA SAGDP1 (LineCode=1) — 2024 smoke-tested | SAGDP2N rejected by API; SAGDP1 confirmed working |
| 6 | RPP | BEA SARPP — 2024 released Feb 2026 | unchanged |
| 7 | REAL_PCPI | BEA SARPI — 2024 released Feb 2026 | unchanged |
| 8 | UNEMP | BLS LAUS 2024 | unchanged |
| 9 | PRIV_EMP | BLS QCEW 2024 | unchanged |
| 10 | PRIV_ESTAB | BLS QCEW 2024 | unchanged |
| 11 | PRIV_AVG_PAY | BLS QCEW 2024 (derived) | unchanged |
| 12 | PERMITS | Census BPS 2024 | unchanged |
| 13 | MED_RENT | ACS B25064 | unchanged |
| 14 | MED_HOMEVAL | ACS B25077 | unchanged |
| 15 | COST_BURDEN_ALL | ACS B25070 + B25091 | **newly verified** — B25091 codes confirmed |
| 16 | VACANCY_RATE | ACS B25004 + B25003 | codes verified, ACS 2024 1-yr |
| 17 | TRANSIT_SHARE | ACS B08301 | codes verified; taxi/ride-hailing is separate sibling |
| 18 | BA_PLUS | ACS B15003 | codes verified, ACS 2024 1-yr |
| 20 | ELEC_PRICE_TOT | EIA API v2 — 2024 data available | unchanged |

### Verified (newly implemented)

| # | Variable | Resolution |
|---|---|---|
| 16 | COMMUTE_MED | Grouped median from ACS B08303 bins. S0801_C01_046E confirmed as mean (not median). |
| 19 | UNINSURED | S2701_C05_001E confirmed as percent uninsured. B27010 fallback also confirmed. |

### Provisional (implemented with caveats)

| # | Variable | Caveat |
|---|---|---|
| 21 | CRIME_VIOLENT_RATE | FBI CDE API (CDE endpoint primary, SAPI legacy fallback, CSV manual fallback). Successful run used CSV fallback. CDE response format not yet validated live. |
| 22 | NRI_RISK_INDEX | Pop-weighted mean of county RISK_SCORE via OpenFEMA API (local CSV fallback). Project-defined aggregation. **NRI v1.20 (Dec 2025) is a vintage exception to 2024-only design.** |
