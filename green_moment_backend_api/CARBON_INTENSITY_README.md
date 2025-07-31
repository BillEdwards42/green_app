# Carbon Intensity System Documentation

## Overview

This system generates real-time carbon intensity data and 24-hour forecasts for Taiwan's electricity grid using ML models trained on historical generation data.

## Architecture

```
[Data Pipeline] → [Generator Script @ X9] → [carbon_intensity.json] → [FastAPI] → [Flutter App]
                                          ↓
                              [actual_carbon_intensity.csv]
```

## Components

### 1. Carbon Intensity Generator (`scripts/carbon_intensity_generator.py`)
- Main orchestrator that runs every X9 minute (09, 19, 29, 39, 49, 59)
- Reads latest generation data from integrated CSV files
- Calculates current national carbon intensity
- Manages rolling 6-timestep cache for ML predictions
- Generates 24-hour forecast when cache is ready
- Outputs JSON file and logs

### 2. Cache Manager (`scripts/cache_manager.py`)
- Maintains rolling 6-timestep cache using pickle
- Each region needs 6 timesteps (1 hour) before ML predictions can run
- Persistent across script restarts

### 3. Carbon Calculator (`scripts/carbon_calculator.py`)
- Applies emission factors to calculate carbon intensity
- Emission factors (kgCO2e/kWh):
  - Nuclear: 0
  - Coal: 0.912
  - LNG: 0.389
  - Wind/Solar/Hydro: 0
  - Others: varies

### 4. ML Inference Service (`scripts/ml_inference.py`)
- Loads pre-trained LSTM models for 5 regions
- Preprocesses data to match training format
- Generates 144 timestep (24hr) predictions

### 5. API Endpoints (`app/api/v1/endpoints/carbon.py`)
- `GET /api/v1/carbon/latest` - Complete JSON with current + forecast
- `GET /api/v1/carbon/current` - Current intensity only
- `GET /api/v1/carbon/forecast` - 24hr forecast only
- `GET /api/v1/carbon/status` - Generator status

## Setup & Usage

### 1. Install ML Dependencies
```bash
pip install -r requirements_ml.txt
```

### 2. Run Generator

**Option A: Manual Test (Run Once)**
```bash
python scripts/carbon_intensity_generator.py --once
```

**Option B: Scheduled Mode (Every X9 minute)**
```bash
python scripts/carbon_intensity_generator.py --scheduled
```

**Option C: Interactive Runner**
```bash
python scripts/run_generator.py
```

### 3. Check Output
- JSON output: `data/carbon_intensity.json`
- Actual carbon log: `logs/actual_carbon_intensity.csv`
- Fluctuation log: `logs/fluctuation_log.txt`
- Weather analysis: `logs/weather_analysis_log.txt`

### 4. Test API
Start FastAPI server:
```bash
uvicorn app.main:app --reload
```

Test endpoints:
```bash
curl http://localhost:8000/api/v1/carbon/latest
curl http://localhost:8000/api/v1/carbon/status
```

## JSON Output Format

```json
{
  "last_updated": "2025-07-27T15:09:00+08:00",
  "status": "complete",
  "current": {
    "carbon_intensity": 0.456,
    "timestamp": "2025-07-27T15:00:00+08:00",
    "total_generation_mw": 35678.5,
    "generation_mix": {
      "Nuclear": 10.5,
      "Coal": 35.2,
      "LNG": 40.1,
      ...
    }
  },
  "forecast": {
    "available": true,
    "start_time": "2025-07-27T15:10:00+08:00",
    "values": [0.445, 0.442, ...],  // 144 values
    "timestamps": [...]              // 144 timestamps
  },
  "errors": []
}
```

## Cache Building Process

On first run:
1. Minute 0-50: Cache building (forecast unavailable)
2. Minute 60+: Full functionality with ML forecasts

The system shows progress: "Building cache: 4/6 timesteps"

## Logs

### Fluctuation Log
Tracks generator additions/removals between runs:
```
Timestamp: 2025-07-27 15:09:00
Generators ADDED:
  - Solar in South region: 1234.56 MW
Status: COMPLETE - No changes
```

### Weather Analysis Log
Shows weather data status per region:
```
North Region:
  - AirTemperature: 28.5
  - WindSpeed: 3.2
  - SunshineDuration: NULL
```

## Troubleshooting

1. **"Carbon intensity data not available"**
   - Generator hasn't run yet
   - Run: `python scripts/carbon_intensity_generator.py --once`

2. **"Building cache: X/6 timesteps"**
   - Normal during first hour
   - Wait for 6 runs (60 minutes) for full functionality

3. **Model loading errors**
   - Ensure models extracted: `unzip trained_models.zip -d data/models/`
   - Check TensorFlow installation

## Production Deployment

For cloud deployment:
1. Replace `schedule` library with cloud scheduler (Cloud Functions, etc.)
2. Use cloud storage for JSON output
3. Implement proper logging and monitoring
4. Add error alerting
5. Consider using managed ML services for model hosting