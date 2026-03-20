"""Project-wide constants: FIPS codes, age-group mappings, variable code lookups."""

# 50 US states only (exclude DC=11, PR=72)
STATE_FIPS = {
    "01": "Alabama", "02": "Alaska", "04": "Arizona", "05": "Arkansas",
    "06": "California", "08": "Colorado", "09": "Connecticut", "10": "Delaware",
    "12": "Florida", "13": "Georgia", "15": "Hawaii", "16": "Idaho",
    "17": "Illinois", "18": "Indiana", "19": "Iowa", "20": "Kansas",
    "21": "Kentucky", "22": "Louisiana", "23": "Maine", "24": "Maryland",
    "25": "Massachusetts", "26": "Michigan", "27": "Minnesota", "28": "Mississippi",
    "29": "Missouri", "30": "Montana", "31": "Nebraska", "32": "Nevada",
    "33": "New Hampshire", "34": "New Jersey", "35": "New Mexico", "36": "New York",
    "37": "North Carolina", "38": "North Dakota", "39": "Ohio", "40": "Oklahoma",
    "41": "Oregon", "42": "Pennsylvania", "44": "Rhode Island", "45": "South Carolina",
    "46": "South Dakota", "47": "Tennessee", "48": "Texas", "49": "Utah",
    "50": "Vermont", "51": "Virginia", "53": "Washington", "54": "West Virginia",
    "55": "Wisconsin", "56": "Wyoming",
}

AGE_GROUPS = ["18_24", "25_34", "35_54", "55_64", "65_PLUS"]

# ── B07001: IN-migration ("Moved from different state" block, starts at 065) ──
# Verified against Census Reporter ACS 2024 1-year precomputed metadata.
IN_COUNT_VARS = {
    "18_24": ["B07001_068E", "B07001_069E"],           # 18-19, 20-24
    "25_34": ["B07001_070E", "B07001_071E"],           # 25-29, 30-34
    "35_54": ["B07001_072E", "B07001_073E",            # 35-39, 40-44
              "B07001_074E", "B07001_075E"],            # 45-49, 50-54
    "55_64": ["B07001_076E", "B07001_077E"],           # 55-59, 60-64
    "65_PLUS": ["B07001_078E", "B07001_079E",          # 65-69, 70-74
                "B07001_080E"],                         # 75+
}

# ── B07401: OUT-migration ("Moved to different state" block, starts at 065) ──
OUT_COUNT_VARS = {
    "18_24": ["B07401_068E", "B07401_069E"],
    "25_34": ["B07401_070E", "B07401_071E"],
    "35_54": ["B07401_072E", "B07401_073E",
              "B07401_074E", "B07401_075E"],
    "55_64": ["B07401_076E", "B07401_077E"],
    "65_PLUS": ["B07401_078E", "B07401_079E",
                "B07401_080E"],
}

# ── B01001: Age-group population denominator (Sex by Age, male + female) ──
# Verified against Census Reporter ACS 2024 1-year precomputed metadata.
POP_AGE_VARS = {
    "18_24": [
        # Male: 18-19, 20, 21, 22-24
        "B01001_007E", "B01001_008E", "B01001_009E", "B01001_010E",
        # Female: 18-19, 20, 21, 22-24
        "B01001_031E", "B01001_032E", "B01001_033E", "B01001_034E",
    ],
    "25_34": [
        "B01001_011E", "B01001_012E",  # Male 25-29, 30-34
        "B01001_035E", "B01001_036E",  # Female 25-29, 30-34
    ],
    "35_54": [
        "B01001_013E", "B01001_014E", "B01001_015E", "B01001_016E",  # Male
        "B01001_037E", "B01001_038E", "B01001_039E", "B01001_040E",  # Female
    ],
    "55_64": [
        "B01001_017E", "B01001_018E", "B01001_019E",  # Male 55-59, 60-61, 62-64
        "B01001_041E", "B01001_042E", "B01001_043E",  # Female
    ],
    "65_PLUS": [
        "B01001_020E", "B01001_021E", "B01001_022E",  # Male 65-66, 67-69, 70-74
        "B01001_023E", "B01001_024E", "B01001_025E",  # Male 75-79, 80-84, 85+
        "B01001_044E", "B01001_045E", "B01001_046E",  # Female 65-66, 67-69, 70-74
        "B01001_047E", "B01001_048E", "B01001_049E",  # Female 75-79, 80-84, 85+
    ],
}

# ── Smoke-test IV variable codes (ACS detail tables) ──
# MED_RENT: B25064_001E
# COST_BURDEN_ALL components:
COST_BURDEN_RENTER_TOTAL = "B25070_001E"
COST_BURDEN_RENTER_BURDENED = [
    "B25070_007E", "B25070_008E", "B25070_009E", "B25070_010E",
]
COST_BURDEN_OWNER_TOTAL = "B25091_001E"
COST_BURDEN_OWNER_BURDENED = [
    "B25091_008E", "B25091_009E", "B25091_010E", "B25091_011E",  # with mortgage
    "B25091_019E", "B25091_020E", "B25091_021E", "B25091_022E",  # without mortgage
]
