# Green Moment Backend File Structure Guide

## Overview
The Green Moment backend consists of three main components:
1. **Backend API** - FastAPI service that serves carbon intensity data
2. **Data Integration Pipeline** - Collects power generation data from Taiwan
3. **Carbon Intensity Generator** - Calculates carbon intensity and forecasts

## Directory Structure

```
green_moment_backend_api/
├── app/                        # FastAPI application code
│   ├── api/                    # API endpoints
│   │   └── v1/
│   │       ├── endpoints/
│   │       │   ├── auth.py         # Authentication endpoints
│   │       │   ├── carbon.py       # Carbon intensity endpoints (/latest, /current)
│   │       │   ├── chores.py       # Chore logging endpoints
│   │       │   ├── progress.py     # User progress tracking
│   │       │   └── users.py        # User management
│   │       └── api.py          # API router aggregation
│   ├── core/                   # Core functionality
│   │   ├── config.py           # Configuration settings
│   │   ├── database.py         # Database connection
│   │   └── security.py         # JWT and security functions
│   ├── models/                 # SQLAlchemy database models
│   │   ├── carbon_intensity.py
│   │   ├── chore.py
│   │   ├── league.py
│   │   ├── user.py
│   │   └── ...
│   ├── schemas/                # Pydantic data validation schemas
│   └── main.py                 # FastAPI app initialization
│
├── scripts/                    # Carbon intensity calculation scripts
│   ├── carbon_intensity_generator.py  # Main generator (runs every X9 minute)
│   ├── carbon_calculator.py          # Carbon intensity calculations
│   ├── ml_inference.py              # ML model predictions for forecasting
│   ├── cache_manager.py             # Manages 60-minute data cache
│   └── run_generator.py             # Simple runner for testing
│
├── data/                       # Output data files
│   ├── carbon_intensity.json   # Main JSON served to Flutter app
│   ├── carbon_intensity_debug.json  # Detailed version for debugging
│   └── models/                 # ML models for each region
│       ├── model_north.h5
│       ├── model_central.h5
│       ├── model_south.h5
│       ├── model_east.h5
│       └── model_other.h5
│
├── logs/                       # Log files
│   ├── actual_carbon_intensity.csv   # Historical carbon intensity values
│   ├── carbon_calculation_log.json   # Detailed calculation breakdown
│   ├── fluctuation_log.txt          # Power plant status changes
│   ├── weather_analysis_log.txt     # Weather data logs
│   └── generator.log               # Generator runtime logs
│
├── cache/                      # Cached data
│   ├── generation_cache.pkl    # 60-minute generation data cache
│   └── scalers.pkl            # ML model scalers
│
├── migrations/                 # Database migrations (Alembic)
├── tests/                     # Test files
├── venv/                      # Python virtual environment
├── requirements.txt           # Python dependencies
└── docker-compose.yml         # Docker configuration
```

## Key Files Explained

### 1. **carbon_intensity.json** (Main Output)
This is the primary file served to the Flutter app when it calls the API.
```json
{
  "last_updated": "2025-07-30T16:39:36",
  "current_intensity": {
    "gCO2_kWh": 520,        // Carbon intensity in grams CO2/kWh
    "level": "red"          // red/yellow/green based on forecast
  },
  "forecast": [             // 144 entries for 24 hours (10-min intervals)
    {
      "time": "16:40",
      "gCO2_kWh": 484,
      "level": "yellow"
    },
    ...
  ],
  "recommendation": {       // Best time to use electricity
    "message": "電網碳密度偏高，建議避免使用大型耗電設備。",
    "start_time": "04:40 PM",
    "end_time": "06:40 PM"
  }
}
```

### 2. **carbon_calculation_log.json** (Calculation Details)
Shows exactly how carbon intensity was calculated:
```json
{
  "timestamp": "2025-07-30T16:39:35",
  "fuel_details": {
    "Coal": {
      "generation_mw": 8434.8,
      "emissions_kg": 1282089.6,
      "emission_factor": 0.912
    },
    "Storage": {
      "generation_mw": 459.1,
      "emissions_calculation": "EXCLUDED FROM CALCULATIONS",
      "note": "Storage is excluded from carbon intensity calculations"
    }
    ...
  },
  "summary": {
    "total_generation_mw": 36417.56,  // Excludes Storage
    "carbon_intensity_kg_per_kwh": 0.520187
  }
}
```

### 3. **actual_carbon_intensity.csv** (Historical Log)
Tracks all calculated carbon intensity values:
```csv
timestamp,carbon_intensity_kgco2_kwh
2025-07-30 16:29:00,0.516544
2025-07-30 16:39:34,0.520187
```

## Data Flow

1. **Every X9 minute** (09, 19, 29, 39, 49, 59):
   - `carbon_intensity_generator.py` runs
   - Fetches power generation data from Taipower API
   - Fetches weather data from CWA API
   - Calculates current carbon intensity (excluding Storage)
   - Generates 24-hour forecast using ML models
   - Saves results to `data/carbon_intensity.json`

2. **When Flutter app requests data**:
   - Calls `/api/v1/carbon/latest`
   - FastAPI reads and returns `carbon_intensity.json`

3. **Carbon Intensity Calculation**:
   ```
   Carbon Intensity = Total Emissions / Total Generation
   
   Where:
   - Total Emissions = Sum of (Generation × Emission Factor) for each fuel
   - Total Generation = Sum of all generation EXCLUDING Storage
   - Storage is excluded because it doesn't generate electricity
   ```

## Important Notes

1. **Storage (儲能) Handling**:
   - Excluded from carbon intensity calculations
   - Shown in generation_mw for transparency
   - NOT included in generation_mix percentages
   - NOT included in total_generation_mw

2. **Emission Factors** (kgCO2e/kWh):
   - Coal: 0.912
   - LNG: 0.389
   - Oil: 0.818
   - Solar/Wind/Hydro/Nuclear: 0
   - Storage: 0 (but excluded entirely)

3. **Update Frequency**:
   - Taipower updates: Every 10 minutes at X0
   - Generator runs: Every 10 minutes at X9
   - 1-minute delay ensures data availability

4. **File Relationships**:
   - `carbon_intensity.json` → Served to app
   - `carbon_intensity_debug.json` → Same data, more details
   - `carbon_calculation_log.json` → Shows the math
   - `actual_carbon_intensity.csv` → Historical tracking

## Common Operations

1. **Check generator status**:
   ```bash
   ps aux | grep carbon_intensity_generator
   ```

2. **Start generator**:
   ```bash
   cd green_moment_backend_api
   source venv/bin/activate
   python scripts/carbon_intensity_generator.py --scheduled
   ```

3. **Run verification**:
   ```bash
   python scripts/verify_storage_exclusion.py
   ```

4. **View latest calculation**:
   ```bash
   tail logs/actual_carbon_intensity.csv
   cat data/carbon_intensity.json | jq .current_intensity
   ```

## Troubleshooting

1. **Duplicate entries in CSV**: Multiple generator instances running
2. **Wrong carbon intensity**: Check if Storage is being included
3. **No forecast data**: Cache needs 6 timesteps (60 minutes) to build
4. **API returns 503**: Generator hasn't created JSON file yet