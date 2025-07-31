# Green Moment Backend Test Plan

## Current Test: Local Backend Integration with Carbon Intensity ML Pipeline

### Test Overview
This test validates the complete data flow from Taipower/CWA APIs through ML predictions to the Flutter app, ensuring accurate carbon intensity calculations and forecasting.

### System Architecture Being Tested
```
Taipower API → Carbon Generator → Cache (6 timesteps) → ML Models → JSON → FastAPI → Flutter App
     ↓                   ↓                                    ↓
Real-time data    Carbon calculations              24hr predictions
```

### Test Components

#### 1. **Carbon Intensity Generator** (Terminal 3)
- **Runs**: Every X9 minute (09, 19, 29, 39, 49, 59)
- **Fetches**: 
  - Generation data from Taipower API (MW per fuel type)
  - Weather data from CWA API (temperature, wind, sunshine, precipitation)
- **Calculates**: Current carbon intensity (kgCO2e/kWh)
- **Stores**: 
  - Cache: Raw MW values + weather + datetime
  - JSON: Carbon intensity + percentages + MW values
  - CSV log: Historical carbon intensity values

#### 2. **ML Model Input Sequence** (After preprocessing)
Based on training script analysis, the input order is:
1. **Datetime features**: Year, Month, Day, DayOfWeek, Hour, Minute
2. **Weather features** (except for 'Other' region):
   - AirTemperature
   - WindSpeed  
   - SunshineDuration
   - Precipitation
3. **Fuel generation** (MW):
   - Nuclear, Coal, Co-Gen, IPP-Coal, LNG, IPP-LNG
   - Oil, Diesel, Hydro, Wind, Solar, Other_Renewable, Storage

**Note**: Total_Generation and Timestamp are dropped before model input.

#### 3. **Data Validation Points**

##### At Each X9 Run:
- [ ] Taipower data timestamp matches expected (X0 minute)
- [ ] MW values sum to total_generation_mw
- [ ] Carbon intensity calculation: 0.4-0.6 kgCO2e/kWh range
- [ ] Weather data has reasonable values (temp: 15-35°C, etc.)

##### After 6 Timesteps (Cache Full):
- [ ] ML models load without 'mse' errors (warning only)
- [ ] 144 forecast points generated (24 hours × 6 per hour)
- [ ] Forecast carbon intensities in reasonable range
- [ ] No crashes or exceptions

### Current Test Status
- **Backend API**: ✅ Running on port 8000
- **Carbon Generator**: ✅ Running, fetching from APIs
- **Cache Status**: 🔄 Building (X/6 timesteps)
- **ML Predictions**: ⏳ Waiting for 6 timesteps

### Test Success Criteria
1. **Data Accuracy**:
   - Carbon intensity matches expected range
   - MW values match Taipower official data
   - Weather data is current and region-specific

2. **System Stability**:
   - No crashes over 2+ hours
   - Consistent X9 minute execution
   - Proper error handling

3. **API Response**:
   - `/api/v1/carbon/latest` returns valid JSON
   - Contains both current and forecast (after 1 hour)
   - Updates every 10 minutes

4. **Flutter App Integration**:
   - App displays current carbon intensity
   - Shows generation mix percentages
   - Updates automatically

### Next Steps After This Test

#### Phase 1: Flutter App Testing (Immediate)
1. **Configure Flutter app** for local backend:
   - Update `api_config.dart` with correct IP
   - Test on Android emulator first
   - Then test on physical device via USB

2. **Verify app functionality**:
   - Carbon intensity gauge displays correctly
   - 24-hour forecast chart (after ML predictions)
   - Chore logging and savings calculation

#### Phase 2: Production Preparation
1. **Data Pipeline on Server**:
   - Set up cron jobs for integrated pipeline
   - Ensure CSV files update every 10 minutes
   - Monitor data quality

2. **Cloud Deployment**:
   - Choose cloud provider (AWS/GCP/Azure)
   - Deploy FastAPI with Docker
   - Set up PostgreSQL and Redis
   - Configure HTTPS/SSL

3. **Production Carbon Generator**:
   - Deploy as cloud function or scheduled task
   - Set up monitoring and alerts
   - Implement error recovery

#### Phase 3: App Store Release
1. **Backend Production URL**:
   - Update Flutter app to use production API
   - Implement proper error handling
   - Add offline mode

2. **Google Play Store**:
   - Build release APK/AAB
   - Prepare store listing
   - Submit for review

3. **Apple App Store**:
   - Build iOS version
   - Test on iOS devices
   - Submit for review

### Monitoring Commands

```bash
# Check current carbon intensity
curl -s http://localhost:8000/api/v1/carbon/latest | jq '.current'

# Monitor cache building
watch -n 60 'curl -s http://localhost:8000/api/v1/carbon/latest | jq ".forecast.reason"'

# View generator logs
tail -f logs/actual_carbon_intensity.csv

# Check cache contents
python3 -c "import pickle; cache = pickle.load(open('cache/generation_cache.pkl','rb')); print(f'Cache timesteps: {len(cache.get(\"North\", []))}/6')"
```

### Known Issues
1. **ML Model Warnings**: "Could not locate function 'mse'" - harmless, models still work
2. **First Cache Entry**: May have incorrect timestamp if started at non-X9 minute
3. **Weather API**: Occasional null values for some stations

### Test Duration
- **Minimum**: 1 hour (to see ML predictions)
- **Recommended**: 2-3 hours (to verify stability)
- **Full validation**: 24 hours (complete forecast cycle)