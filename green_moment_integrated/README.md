# Green Moment Integrated Backend

This integrated backend system combines power generation data collection and real-time weather monitoring for Taiwan's electricity grid analysis.

## Overview

The system consists of two main components:
1. **Live Pipeline** - Collects power generation data from Taipower every 10 minutes
2. **Weather Fetch** - Collects weather data and integrates it with generation data

## File Structure

```
green_moment_integrated/
├── stru_data/                    # Regional CSV files (output)
│   ├── North.csv
│   ├── South.csv
│   ├── Central.csv
│   ├── East.csv
│   ├── Islands.csv
│   ├── Other.csv
│   └── electricity_demand.csv
├── logs/                         # Log files
│   ├── pipeline_runs.log
│   ├── weather_fetch.log
│   ├── fluctuation_log.txt
│   └── 10min_weather_log.csv
├── config/                       # Configuration files
│   ├── plant_to_region_map.csv
│   └── .env
├── live_pipeline_integrated.py   # Main generation data pipeline
├── fetch_weather_integrated.py   # Weather data integration
├── verify_integrated_output.py   # Data verification script
└── requirements.txt
```

## Data Structure

Each regional CSV file contains:
- **Timestamp**: 10-minute intervals
- **Fuel Types**: Nuclear, Coal, LNG, Wind, Solar, etc. (as columns)
- **Total_Generation**: Sum of all fuel types
- **Weather Data**: AirTemperature, WindSpeed, SunshineDuration

Example CSV structure:
```
Timestamp,Nuclear,Coal,LNG,Wind,Solar,...,Total_Generation,AirTemperature,WindSpeed,SunshineDuration
2024-01-15 10:00:00,500.0,1200.5,800.3,250.2,300.1,...,3765.1,25.3,3.2,0.8
```

## Setup

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure API Key**:
   - Copy `config/.env.example` to `config/.env`
   - Add your CWA API key

3. **Set Up Cron Jobs**:
   ```bash
   # Generation data (runs at X9 minutes to capture X0 data)
   9,19,29,39,49,59 * * * * /path/to/python /path/to/live_pipeline_integrated.py
   
   # Weather data (runs every 10 minutes)
   */10 * * * * /path/to/python /path/to/fetch_weather_integrated.py
   ```

## Usage

### Manual Execution

```bash
# Run generation pipeline
python live_pipeline_integrated.py

# Run weather integration
python fetch_weather_integrated.py

# Verify output and view reports
python verify_integrated_output.py
```

### Data Verification

The verification script provides:
- Current generation mix by fuel type
- Data completeness check (generation + weather)
- Regional weather summary
- Timestamp synchronization status
- Recent fluctuation reports

## Key Features

### Data Integration
- **File Locking**: Prevents conflicts when both scripts access same files
- **Timestamp Synchronization**: Aligns weather data with generation timestamps
- **Graceful Handling**: Continues operation if one data source fails

### Regional Organization
- **6 Regions**: North, Central, South, East, Islands, Other
- **Plant Mapping**: 3-layer logic (CSV mapping → keyword inference → default)
- **Weather Stations**: Regional grouping for accurate weather averages

### Robustness
- **Error Recovery**: Handles API failures gracefully
- **Data Validation**: Checks for completeness and consistency  
- **Logging**: Comprehensive logging for debugging and monitoring

## Cron Job Timing

- **Generation Pipeline**: Runs at X9 minutes (09, 19, 29, 39, 49, 59)
  - Captures X0 minute data with 1-minute delay for API availability
- **Weather Integration**: Runs every 10 minutes (00, 10, 20, 30, 40, 50)
  - Real-time weather data, rounded to nearest 10-minute interval

## API Endpoints Used

- **Taipower Generation**: `genary.json`
- **Taipower Demand**: `loadpara.json` 
- **CWA Weather**: `O-A0003-001` (Real-time observations)

## Data Retention

- **Generation Data**: Indefinite (for historical analysis)
- **Weather Logs**: Individual station data for debugging
- **Fluctuation Logs**: Plant additions/removals between runs

## Migration from Legacy System

This integrated system replaces the previous structure where:
- Each fuel type had separate CSV files
- Weather data was stored separately
- 6-hour weather intervals were used instead of 10-minute

The new structure provides:
- Single CSV per region (more efficient)
- Integrated weather + generation data
- Higher temporal resolution (10-minute weather data)
- Better synchronization between data sources