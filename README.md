# Life-Stage Interstate Migration Across the 50 U.S. States

A reproducible state-level research project analyzing how interstate migration patterns differ by age group across the 50 U.S. states in 2024, and which state-level characteristics are statistically associated with those differences.

## Research question

Which state-level characteristics are most strongly associated with interstate net migration rates for different age groups (18–24, 25–34, 35–54, 55–64, 65+) in the 50 U.S. states in 2024?

## Repository structure

```
capstone/
├── config/              # API keys (not committed)
├── data_raw/            # Unmodified source downloads
├── data_interim/        # Cleaned intermediate tables
├── data_processed/      # Final analysis-ready tables
├── docs/
│   ├── research-brief.md        # Full research specification
│   ├── source-contract.md       # Data source definitions
│   ├── source-notes.md          # Implementation-specific notes
│   ├── variable-dictionary.csv  # Variable reference table
│   └── local-execution-guide.md # Setup and run instructions
├── outputs/
│   ├── tables/          # Summary tables, correlation matrices
│   ├── figures/         # Charts and maps
│   └── logs/            # Pipeline run logs
├── scripts/
│   ├── build_dataset.py     # A2: Full 50-state dataset build
│   ├── validate_a2.py       # A2: Validation checks
│   ├── descriptive_a3.py    # A3: Descriptive statistics
│   └── spearman_a4.py       # A4: Spearman rank correlation screening
├── src/
│   ├── constants.py         # FIPS codes, age groups, variable codes
│   ├── config_loader.py     # API key loader
│   ├── build_variables.py   # Derived variable construction
│   ├── fetch_census.py      # ACS migration and IV data
│   ├── fetch_bea.py         # GDP, RPP, REAL_PCPI (BEA API)
│   ├── fetch_bls.py         # UNEMP (LAUS), QCEW (private sector)
│   ├── fetch_eia.py         # Electricity price (EIA API)
│   ├── fetch_permits.py     # Building permits (Census BPS)
│   ├── fetch_land_area.py   # Land area (Census reference)
│   ├── fetch_commute.py     # COMMUTE_MED (ACS B08303 grouped median)
│   ├── fetch_uninsured.py   # UNINSURED (ACS S2701 / B27010 fallback)
│   ├── fetch_crime.py       # CRIME_VIOLENT_RATE (FBI CDE API + CSV fallback)
│   └── fetch_nri.py         # NRI_RISK_INDEX (OpenFEMA API + CSV fallback)
└── requirements.txt
```

## Setup

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Copy `config/api_keys.py.template` to `config/api_keys.py` and add your API keys:

- **CENSUS_API_KEY** (required) — [request here](https://api.census.gov/data/key_signup.html)
- **BEA_API_KEY** (required) — [request here](https://apps.bea.gov/api/signup/)
- **EIA_API_KEY** (required) — [request here](https://www.eia.gov/opendata/register.php)
- **DATA_GOV_API_KEY** (optional, for CRIME_VIOLENT_RATE) — [request here](https://api.data.gov/signup/). If unavailable, place a manual CSV at `data_raw/fbi_crime_state_2024.csv`.

## Pipeline

Run the phases in order:

```bash
# A2: Build the 50-state analysis-ready dataset
python -m scripts.build_dataset

# A2: Validate (50 rows, no missing values, all columns present)
python -m scripts.validate_a2

# A3: Descriptive statistics, distributions, outliers
python -m scripts.descriptive_a3

# A4: Spearman rank correlation screening
python -m scripts.spearman_a4
```

## Data

**Dependent variables** — age-group-specific interstate net migration rates per 1,000 population, constructed from ACS 2024 1-year tables B07001 (in-migration), B07401 (out-migration), and B01001 (population by age).

**Explanatory variables** (22 IVs):

| Category | Variables |
|---|---|
| Size | POP, LAND_AREA, POP_DENS |
| Macro/Income | GDP, RPP, REAL_PCPI |
| Labor | UNEMP, PRIV_EMP, PRIV_ESTAB, PRIV_AVG_PAY |
| Housing | PERMITS, MED_RENT, MED_HOMEVAL, COST_BURDEN_ALL, VACANCY_RATE |
| Transport | COMMUTE_MED, TRANSIT_SHARE |
| Education | BA_PLUS |
| Health | UNINSURED |
| Energy | ELEC_PRICE_TOT |
| Safety | CRIME_VIOLENT_RATE, NRI_RISK_INDEX |

See `docs/variable-dictionary.csv` for full definitions, sources, and formulas.

**Provisional data notes:**
- CRIME_VIOLENT_RATE: FBI CDE API with CSV manual fallback (`data_raw/fbi_crime_state_2024.csv`). API endpoint not yet validated live; the successful pipeline run used the CSV fallback.
- NRI_RISK_INDEX: FEMA NRI v1.20 (December 2025 vintage) via OpenFEMA API, with local CSV fallback (`data_raw/nri_counties_raw.csv`). Uses project-defined population-weighted county-to-state aggregation. **This is a documented methodological exception to the 2024-only cross-section design** — see `docs/deferred-iv-validation-memo.md` section 4.

## Methodology

1. Descriptive statistics
2. Spearman rank correlation screening
3. Single-variable OLS
4. Multiple OLS
5. Mapping and residual visualization

Models are estimated separately by age group. See `docs/research-brief.md` for the full analytical design.

## Scope constraints

- Geography: 50 U.S. states only (DC and territories excluded)
- Time: 2024 cross-section only
- Design: statistical association, not causal identification
