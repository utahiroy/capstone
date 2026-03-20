# Local Execution Guide

## Prerequisites

- Python 3.10+
- API keys for Census, BEA (minimum for smoke test)

## Setup

```bash
cd capstone

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt

# Set up API keys
cp config/api_keys.py.template config/api_keys.py
# Edit config/api_keys.py and paste your keys
```

## API Key Sources

| Key | Sign-up URL |
|---|---|
| CENSUS_API_KEY | https://api.census.gov/data/key_signup.html |
| BEA_API_KEY | https://apps.bea.gov/api/signup/ |
| EIA_API_KEY | https://www.eia.gov/opendata/register.php |
| FBI_API_KEY | https://api.data.gov/signup/ |

Only Census and BEA keys are needed for the smoke test.

## Running the Smoke Test

```bash
# From the project root:
python -m scripts.smoke_test
```

The smoke test fetches data for 3 states (California, Texas, New York) and validates:
- All 7 migration DVs per age group (IN_COUNT, OUT_COUNT, POP_AGE, NET_COUNT, IN_RATE, OUT_RATE, NET_RATE)
- 4 IVs (POP, GDP, MED_RENT, COST_BURDEN_ALL)
- Formula consistency checks

Output files are saved to `smoke_test_outputs/`.

## Directory Structure

```
capstone/
├── config/              # API keys (gitignored)
├── data_raw/            # Unmodified downloads
├── data_interim/        # Cleaned intermediates
├── data_processed/      # Analysis-ready tables
├── docs/                # Research specs and notes
├── outputs/
│   ├── tables/          # Regression and summary tables
│   ├── figures/         # Charts and maps
│   └── logs/            # Run logs
├── scripts/             # Executable pipeline scripts
├── smoke_test_outputs/  # Smoke test results (separate from full run)
└── src/                 # Reusable Python modules
```
