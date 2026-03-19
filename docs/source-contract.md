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

**Status**: **confirmed** — variable codes verified against Census Reporter metadata (ACS 2022 1-year; structure is identical across ACS vintages).

### 1.4 OUT_COUNT variable mapping (from B07401 "Different state" block)

B07401 has the same structure as B07001 but from the perspective of the **state of residence 1 year ago**. The "different state" category counts people who **left** the state for a different U.S. state.

| Project age group | ACS age brackets | ACS variable codes | Aggregation |
|---|---|---|---|
| 18-24 | 18-19, 20-24 | B07401_068E, B07401_069E | Sum |
| 25-34 | 25-29, 30-34 | B07401_070E, B07401_071E | Sum |
| 35-54 | 35-39, 40-44, 45-49, 50-54 | B07401_072E, B07401_073E, B07401_074E, B07401_075E | Sum |
| 55-64 | 55-59, 60-64 | B07401_076E, B07401_077E | Sum |
| 65+ | 65-69, 70-74, 75+ | B07401_078E, B07401_079E, B07401_080E | Sum |

**Status**: **confirmed** — variable codes verified. Note: B07401 has 80 variables (no "Moved from abroad" category, as it tracks the previous-residence perspective).

### 1.5 Age-group population denominator

**Critical design decision**: The denominator for migration rates (POP in the DV formula) must be **age-group-specific**, not total state population.

**Source**: B07001 "Total" block (all mobility statuses combined), which represents the full population 1 year and over by age group for each state.

| Project age group | ACS variable codes | Aggregation |
|---|---|---|
| 18-24 | B07001_004E (18-19), B07001_005E (20-24) | Sum |
| 25-34 | B07001_006E (25-29), B07001_007E (30-34) | Sum |
| 35-54 | B07001_008E (35-39), B07001_009E (40-44), B07001_010E (45-49), B07001_011E (50-54) | Sum |
| 55-64 | B07001_012E (55-59), B07001_013E (60-64) | Sum |
| 65+ | B07001_014E (65-69), B07001_015E (70-74), B07001_016E (75+) | Sum |

**Rationale**: Using B07001 Total ensures that the denominator comes from the same universe (population 1 year and over) as the migration numerators. This avoids denominator-numerator mismatch.

**Status**: **confirmed** — variable codes verified against Census Reporter metadata.

### 1.6 DV formulas

All formulas are computed per state per age group.

| Variable | Formula | Unit |
|---|---|---|
| IN_COUNT | Sum of B07001 "different state" age bracket variables | persons |
| OUT_COUNT | Sum of B07401 "different state" age bracket variables | persons |
| NET_COUNT | IN_COUNT − OUT_COUNT | persons |
| POP_AGE | Sum of B07001 "Total" age bracket variables | persons |
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
| Description | Total state population estimate, 2024 |
| Source | Census Population Estimates Program (PEP) |
| Dataset | Vintage 2024 State Population Estimates |
| Access | Census API: `https://api.census.gov/data/2024/pep/population` |
| Variable code | POP_2024 (or equivalent vintage-2024 variable) |
| Unit | persons |
| Formula | direct read |
| Status | **needs review** — verify exact API endpoint and variable name for vintage 2024 PEP |

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
| API | `https://apps.bea.gov/api/data/?datasetname=Regional&TableName=SAGDP2N&LineCode=1&GeoFips=STATE&Year=2024&ResultFormat=JSON&UserID={key}` |
| Variable | All-industry total GDP (current dollars) |
| Unit | millions of dollars |
| Formula | direct read |
| Status | **confirmed** — BEA API well-documented; 2024 annual GDP typically available by mid-2025 |

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
| API | `https://apps.bea.gov/api/data/?datasetname=Regional&TableName=SARPI&LineCode=1&GeoFips=STATE&Year=2024&ResultFormat=JSON&UserID={key}` |
| Variable | Real per capita personal income (chained dollars) |
| Unit | dollars |
| Formula | direct read |
| Status | **confirmed** — 2024 data released February 2026 alongside RPP. LineCode for real per capita PI needs runtime discovery via BEA GetParameterValuesFiltered. |

---

## 8. Explanatory Variable: UNEMP

| Field | Value |
|---|---|
| ID | UNEMP |
| Description | Annual average unemployment rate, 2024 |
| Source | BLS Local Area Unemployment Statistics (LAUS) |
| URL | https://www.bls.gov/lau/lastrk24.htm |
| Alternative | BLS API v2: series ID `LAUST{FIPS}0000000000003` (not seasonally adjusted, unemployment rate). Annual average = period M13. Up to 50 series per request. |
| Access | HTML table parse or BLS API |
| Unit | percent |
| Formula | direct read |
| Status | **confirmed** — LAUS 2024 annual averages are published by early 2025 |

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

**Status**: **needs review** — B25091 variable positions for the "without mortgage" subcategory offsets should be verified against the 2024 group definition. The structure shown above matches 2019–2023 ACS vintages.

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
| Description | Median travel time to work (minutes) |
| Source | ACS 2024 1-year |
| Table | Subject table S0801 |
| Variable | S0801_C01_046E (Total — Median travel time to work, minutes) |
| API | `https://api.census.gov/data/2024/acs/acs1/subject?get=S0801_C01_046E&for=state:*` |
| Unit | minutes |
| Formula | direct read |
| Status | **needs review** — subject table variable codes can shift between ACS vintages. The code S0801_C01_046E is based on recent vintages and must be verified against `https://api.census.gov/data/2024/acs/acs1/subject/groups/S0801.json`. If unavailable, a **mean** can be computed from B08013_001E / B08301_001E (aggregate travel time / total workers), but this changes the variable definition and would require approval. |

---

## 16. Explanatory Variable: TRANSIT_SHARE

| Field | Value |
|---|---|
| ID | TRANSIT_SHARE |
| Description | Public transportation share of commuters |
| Source | ACS 2024 1-year |
| Table | B08301 (Means of Transportation to Work) |
| Variables | B08301_010E (public transportation, excl. taxicab), B08301_001E (total workers 16+) |

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

**Fallback** (if subject table unavailable):
- Table B27010 (Types of Health Insurance Coverage by Age)
- Uninsured = B27010_017E + B27010_033E + B27010_050E + B27010_066E
- Total = B27010_001E
- UNINSURED = 100 * (sum of uninsured) / total

**Unit**: percent

**Status**: **needs review** — S2701 variable code must be verified for 2024 vintage. Fallback B27010 codes must also be verified. Subject table codes are less stable across vintages than detail table codes.

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
| API | FBI CDE API: `https://api.usa.gov/crime/fbi/sapi/api/estimates/states/{state_abbr}/?api_key={key}` |
| Alt API key | Free key from https://api.data.gov/signup/ |
| Fallback | Bulk CSV/Excel download from https://cde.ucr.cjis.gov/LATEST/webapp/#/pages/downloads |
| Unit | per 100,000 |
| Formula | direct read (pre-computed rate) or compute from counts + population |
| Status | **needs review** — FBI released 2024 data (95.6% population coverage) but CDE API documentation is incomplete and unreliable. State-level rates may need to be computed from count data. Fallback: bulk download. If API fails, escalate for approval on alternative source (e.g., BJS). |

---

## 21. Explanatory Variable: NRI_RISK_INDEX

| Field | Value |
|---|---|
| ID | NRI_RISK_INDEX |
| Description | FEMA National Risk Index, overall composite risk score, state-level |
| Source | FEMA / OpenFEMA |
| URL | https://www.fema.gov/about/openfema/data-sets/national-risk-index-data |
| Access | CSV download from https://hazards.fema.gov/nri/data-resources |
| Version | v1.20 (December 2025) — latest available |
| Variable | RISK_SCORE (composite overall risk) |
| Unit | index score |
| Geographic level | **County and tract only** — state-level composite Risk Index is NOT directly provided |
| State alternative | State-level Expected Annual Loss (EAL) IS provided directly |
| Formula | Option A: aggregate county RISK_SCORE to state (population-weighted average) — requires methodological decision. Option B: use state-level EAL as proxy — simpler but different construct. |
| Status | **needs review — METHODOLOGICAL DECISION REQUIRED** — (1) Use county-to-state aggregation of RISK_SCORE (what aggregation method?), or (2) substitute state-level EAL as the variable. This changes the variable definition and requires explicit approval. |

---

## 22. Summary of source status

### Confirmed (ready to implement)

| # | Variable | Source |
|---|---|---|
| DV | IN_COUNT (all age groups) | ACS B07001 "Different state" block — verified |
| DV | OUT_COUNT (all age groups) | ACS B07401 "Different state" block — verified |
| DV | POP_AGE denominator | ACS B07001 "Total" block — verified |
| 3 | LAND_AREA | Census state area reference (static) |
| 4 | POP_DENS | Derived (POP / LAND_AREA) |
| 5 | GDP | BEA SAGDP2N — 2024 available |
| 6 | RPP | BEA SARPP — 2024 released Feb 2026 |
| 7 | REAL_PCPI | BEA SARPI — 2024 released Feb 2026 |
| 8 | UNEMP | BLS LAUS 2024 |
| 9 | PRIV_EMP | BLS QCEW 2024 |
| 10 | PRIV_ESTAB | BLS QCEW 2024 |
| 11 | PRIV_AVG_PAY | BLS QCEW 2024 (derived) |
| 12 | PERMITS | Census BPS 2024 |
| 13 | MED_RENT | ACS B25064 |
| 14 | MED_HOMEVAL | ACS B25077 |
| 16 | VACANCY_RATE | ACS B25004 + B25003 |
| 17 | TRANSIT_SHARE | ACS B08301 |
| 18 | BA_PLUS | ACS B15003 |
| 20 | ELEC_PRICE_TOT | EIA API v2 — 2024 data available |

### Needs review (minor — verify at implementation)

| # | Variable | Issue |
|---|---|---|
| 1 | POP | Census PEP 2024 API endpoint/variable name needs verification |
| 15 | COST_BURDEN_ALL | B25091 without-mortgage offsets need verification for 2024 vintage |
| 16 | COMMUTE_MED | Subject table S0801 variable code needs verification |
| 19 | UNINSURED | S2701 variable code needs verification; B27010 fallback available |

### Needs review (methodological decision required)

| # | Variable | Issue |
|---|---|---|
| 21 | CRIME_VIOLENT_RATE | 2024 data exists but FBI CDE API is unreliable. May need bulk download. |
| 22 | NRI_RISK_INDEX | **State-level composite not directly available.** Must either (a) aggregate county-level RISK_SCORE (requires choosing aggregation method) or (b) substitute state-level Expected Annual Loss (EAL). Requires approval. |
