# Research Brief: Life-Stage Interstate Migration Across the 50 U.S. States

## 1. Research objective

This project studies how interstate migration patterns differ across life stages in the United States.

The core objective is to identify which state-level characteristics are associated with age-group-specific interstate net migration in 2024.

The project is not trying to prove strict causality. It is a state-level cross-sectional analysis focused on statistical association, interpretability, and spatial pattern discovery.

---

## 2. Core research question

Which state-level characteristics are most strongly associated with interstate net migration rates for different age groups in the 50 U.S. states in 2024?

### Sub-questions
- Do migration drivers differ by age group?
- Are younger and older populations attracted to different types of states?
- Which variables matter most for each life stage?
- How different are total-count and per-1,000-population views?

---

## 3. Geographic and temporal scope

- Geography: 50 U.S. states only
- Exclude: DC, Puerto Rico, and all non-state geographies
- Year: 2024 only
- Design: cross-section only

---

## 4. Age groups

Use these age groups exactly:

- 18-24
- 25-34
- 35-54
- 55-64
- 65+

These age groups are fixed for the project.

---

## 5. Dependent variables

## 5.1 Main dependent variable

For each age group and state, the primary DV is:

**Interstate net migration rate per 1,000 population**

Formula:

`NET_RATE = 1000 * (IN_COUNT - OUT_COUNT) / POP`

Where:
- `IN_COUNT` = number of people in the age group who moved into the state from a different U.S. state
- `OUT_COUNT` = number of people in the age group who moved out of the state to a different U.S. state
- `POP` = state population for that age group

### Main DV names
- `NET_RATE_18_24`
- `NET_RATE_25_34`
- `NET_RATE_35_54`
- `NET_RATE_55_64`
- `NET_RATE_65_PLUS`

## 5.2 Supplemental DVs

Also construct:

- `IN_COUNT`
- `OUT_COUNT`
- `NET_COUNT = IN_COUNT - OUT_COUNT`
- `IN_RATE`
- `OUT_RATE`

Use the rate-based DV as the main analysis target.
Use the count-based DV only as a supplemental perspective.

---

## 6. Migration data source policy

### Main source logic
Use ACS 2024 1-year migration-related tables to construct age-group-specific in/out/net state migration measures.

### Supplemental benchmark
Use the Census State-to-State Migration Flows series only as:
- an all-ages benchmark
- a consistency check
- a supplemental comparison reference

Do not use the all-ages state-to-state flows table as the main age-group-specific DV source.

---

## 7. Explanatory variables

The explanatory variable set is fixed at 22 variables.

| No | ID | Variable | Category | Source | Note |
|---|---|---|---|---|---|
| 1 | POP | Population | Size | Census PopEst | 2024 state estimate |
| 2 | LAND_AREA | Land area (sq mi) | Size | Census State Area | fixed geographic statistic |
| 3 | POP_DENS | Population density | Size | derived from POP / LAND_AREA | derived |
| 4 | GDP | Gross Domestic Product (state) | Macro | BEA GDP by State | 2024 annual |
| 5 | RPP | Regional Price Parities | Cost | BEA RPP | 2024 |
| 6 | REAL_PCPI | Real per capita personal income | Income | BEA Real PI (States) | 2024 |
| 7 | UNEMP | Unemployment rate (annual avg) | Labor | BLS LAUS | 2024 |
| 8 | PRIV_EMP | Private employment (annual avg) | Labor | BLS QCEW | private ownership |
| 9 | PRIV_ESTAB | Private establishments (annual avg) | Labor | BLS QCEW | private ownership |
| 10 | PRIV_AVG_PAY | Avg annual pay proxy | Wages | BLS QCEW | total wages / employment |
| 11 | PERMITS | Housing units authorized (annual) | Housing | Census BPS | 2024 |
| 12 | MED_RENT | Median gross rent | Housing | ACS 2024 1y API | 2024 |
| 13 | MED_HOMEVAL | Median home value | Housing | ACS 2024 1y API | 2024 |
| 14 | COST_BURDEN_ALL | Housing cost burden (>=30%) all households | Housing | ACS 2024 1y API | derived owners + renters combined |
| 15 | VACANCY_RATE | Rental vacancy rate | Housing | ACS 2024 1y API | fixed definition required |
| 16 | COMMUTE_MED | Median travel time to work | Transport | ACS 2024 1y API | 2024 |
| 17 | TRANSIT_SHARE | Public transportation share (commute) | Transport | ACS 2024 1y API | 2024 |
| 18 | BA_PLUS | Bachelor’s degree or higher (%) | Education | ACS 2024 1y API | 25+ population |
| 19 | UNINSURED | Uninsured rate | Health | ACS 2024 1y Subject/API | likely Subject table |
| 20 | ELEC_PRICE_TOT | Electricity price, total average | Energy | EIA | 2024 |
| 21 | CRIME_VIOLENT_RATE | Violent crime rate (per 100k) | Safety | FBI CDE | 2024 |
| 22 | NRI_RISK_INDEX | National Risk Index overall risk | Safety | FEMA NRI / OpenFEMA | state-level composite |

---

## 8. Canonical source URLs

Use these URLs as the primary source anchors unless a source has moved and the equivalent official page must be updated.

| ID | URL |
|---|---|
| POP | https://www.census.gov/data/tables/time-series/demo/popest/2020s-state-total.html |
| LAND_AREA | https://www.census.gov/geographies/reference-files/2010/geo/state-area.html |
| GDP | https://www.bea.gov/data/gdp/gdp-state |
| RPP | https://www.bea.gov/data/prices-inflation/regional-price-parities-state-and-metro-area |
| REAL_PCPI | https://www.bea.gov/data/income-saving/real-personal-income-states |
| UNEMP | https://www.bls.gov/lau/lastrk24.htm |
| PRIV_EMP | https://www.bls.gov/cew/downloadable-data-files.htm |
| PRIV_ESTAB | https://www.bls.gov/cew/downloadable-data-files.htm |
| PRIV_AVG_PAY | https://www.bls.gov/cew/downloadable-data-files.htm |
| PERMITS | https://www.census.gov/construction/bps/stateannual.html |
| MED_RENT | https://api.census.gov/data/2024/acs/acs1.html |
| MED_HOMEVAL | https://api.census.gov/data/2024/acs/acs1.html |
| COST_BURDEN_ALL | https://api.census.gov/data/2024/acs/acs1.html |
| VACANCY_RATE | https://api.census.gov/data/2024/acs/acs1.html |
| COMMUTE_MED | https://api.census.gov/data/2024/acs/acs1.html |
| TRANSIT_SHARE | https://api.census.gov/data/2024/acs/acs1.html |
| BA_PLUS | https://api.census.gov/data/2024/acs/acs1.html |
| UNINSURED | https://api.census.gov/data/2024/acs/acs1/subject.html |
| ELEC_PRICE_TOT | https://www.eia.gov/electricity/sales_revenue_price/ |
| CRIME_VIOLENT_RATE | https://cde.ucr.cjis.gov/ |
| NRI_RISK_INDEX | https://www.fema.gov/about/openfema/data-sets/national-risk-index-data |

---

## 9. Analytical workflow

Use this sequence unless explicitly revised.

### Step 1: data ingestion
- download or query all agreed sources
- standardize state identifiers
- keep raw source files intact
- create a joined state-level master table

### Step 2: variable engineering
- build age-group migration measures
- build derived explanatory variables
- create final analysis-ready tables
- document formulas

### Step 3: descriptive analysis
- summary statistics
- basic distribution checks
- identify obvious anomalies

### Step 4: nonparametric screening
- Spearman rank correlation by age group
- rank variables by absolute rho

### Step 5: single-variable regression
- compare candidate variables using Adjusted R²

### Step 6: multiple regression
- estimate age-group-specific models
- compare models using:
  - Adjusted R²
  - AIC
  - BIC
  - theoretical sign plausibility
  - acceptable multicollinearity

### Step 7: mapping and interpretation
- map each age group’s `NET_RATE`
- map key explanatory variables
- map residuals from selected models
- identify spatial patterns and outliers

---

## 10. Model selection rules

Use these rules exactly unless a deliberate methodological change is approved:

- variable screening: absolute Spearman rho
- single-variable comparison: Adjusted R²
- multiple regression comparison:
  - Adjusted R²
  - AIC / BIC
  - sign plausibility
  - no extreme multicollinearity

Do not select models by p-value alone.
Do not describe correlations as causal effects.

---

## 11. Reliability and quality policy

This is an academic departmental research project, not a formal production econometrics audit.

Therefore:
- rely on official ACS and other official sources as the base policy
- do not apply overly aggressive exclusion rules
- do basic quality control:
  - missingness checks
  - join validation
  - age-group aggregation validation
  - obvious outlier review
  - formula verification

---

## 12. GIS and output goals

The project should produce both statistical and spatial outputs.

Minimum expected outputs:
- analysis-ready state table
- age-group-specific DV tables
- Spearman tables
- single-regression summary tables
- multiple-regression comparison tables
- choropleth maps by age group
- residual maps
- concise methodological notes

---

## 13. Out of scope

Do not expand the project into these unless explicitly instructed:

- DC or Puerto Rico analysis
- multi-year time-series analysis
- Mann-Kendall as a core method
- pooled age-group interaction models as the main design
- PUMS-based state-to-state OD matrix as the main design
- causal identification strategies such as IV, DID, or panel FE
- climate-score variables that are subjective or weakly defined

---

## 14. Working interpretation hypothesis

Interpret results with the expectation that migration drivers differ by life stage.

Possible broad tendencies:
- 18-24: education, urban access, transport, rent, labor conditions
- 25-34: wages, jobs, living costs, housing affordability
- 35-54: housing, burden, safety, education environment
- 55-64: cost, insurance, safety, disaster risk
- 65+: cost, housing, insurance, safety, disaster risk, utilities

These are interpretation priors, not fixed truths.
Data results take priority.
