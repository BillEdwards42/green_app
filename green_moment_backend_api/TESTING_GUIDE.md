# Backend Testing Guide for Green Moment

## Overview
This guide helps you test the backend API with your Flutter app in Android Studio and prepare for cloud deployment.

## Step 1: Local Backend Setup

### 1.1 Quick Start with Docker
```bash
cd /home/bill/StudioProjects/green_moment_backend_api

# Copy environment file
cp .env.example .env

# Start all services
docker-compose up -d

# Check if services are running
docker-compose ps

# View logs
docker-compose logs -f api
```

### 1.2 Without Docker (Manual Setup)
```bash
# Install PostgreSQL and Redis locally
sudo apt install postgresql redis-server

# Create database
createdb green_moment

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Start the API
uvicorn app.main:app --reload --host 0.0.0.0
```

## Step 2: Test API is Working

### 2.1 Check API Health
Open browser or use curl:
```bash
# Root endpoint
curl http://localhost:8000/

# API docs (Swagger UI)
open http://localhost:8000/api/v1/docs
```

### 2.2 Test with Postman or cURL
```bash
# Test carbon intensity endpoint
curl http://localhost:8000/api/v1/carbon/current

# Test auth endpoint
curl -X POST http://localhost:8000/api/v1/auth/anonymous
```

## Step 3: Connect Flutter App to Local Backend

### 3.1 Find Your Computer's IP Address
```bash
# Linux/Mac
ifconfig | grep inet

# Windows
ipconfig

# Look for your local network IP (usually 192.168.x.x)
```

### 3.2 Update Flutter App Configuration

Create a config file in your Flutter app:

**lib/config/api_config.dart**
```dart
class ApiConfig {
  // For Android Emulator connecting to localhost
  static const String androidEmulatorUrl = 'http://10.0.2.2:8000/api/v1';
  
  // For physical device on same network (replace with your IP)
  static const String localNetworkUrl = 'http://192.168.1.100:8000/api/v1';
  
  // For production (will be updated later)
  static const String productionUrl = 'https://api.greenmoment.com/api/v1';
  
  // Current environment
  static String get baseUrl {
    // Change this based on your testing needs
    return androidEmulatorUrl; // or localNetworkUrl
  }
}
```

### 3.3 Update MockDataService to Use Real API

**lib/services/api_service.dart** (new file)
```dart
import 'dart:convert';
import 'package:http/http.dart' as http;
import '../config/api_config.dart';
import '../models/app_data_model.dart';

class ApiService {
  static Future<AppDataModel> fetchCarbonData() async {
    try {
      final response = await http.get(
        Uri.parse('${ApiConfig.baseUrl}/carbon/forecast'),
        headers: {'Content-Type': 'application/json'},
      ).timeout(const Duration(seconds: 10));

      if (response.statusCode == 200) {
        return AppDataModel.fromJson(json.decode(response.body));
      } else {
        throw Exception('Failed to load carbon data');
      }
    } catch (e) {
      print('API Error: $e');
      // Fallback to mock data
      return MockDataService.fetchCarbonData();
    }
  }
}
```

### 3.4 Add HTTP Package to Flutter
Update **pubspec.yaml**:
```yaml
dependencies:
  http: ^1.1.0
```

## Step 4: Android Studio Testing Setup

### 4.1 Configure Android Emulator
1. Open Android Studio
2. Open AVD Manager
3. Create/Start an emulator
4. The emulator can access your localhost backend at `10.0.2.2:8000`

### 4.2 Physical Device Testing
1. Connect device via USB
2. Enable Developer Mode and USB Debugging
3. Ensure device is on same Wi-Fi network
4. Use your computer's IP address in the API config

### 4.3 Network Permission (Android)
Ensure **android/app/src/main/AndroidManifest.xml** has:
```xml
<uses-permission android:name="android.permission.INTERNET" />
```

For Android 9+ (API 28+), add to allow HTTP in debug:
**android/app/src/debug/AndroidManifest.xml**
```xml
<application android:usesCleartextTraffic="true">
    <!-- Allows HTTP in debug mode -->
</application>
```

## Step 5: Testing Checklist

### Backend Health Checks
- [ ] Docker containers running: `docker-compose ps`
- [ ] API responds: `curl http://localhost:8000/`
- [ ] Database connected: Check logs for errors
- [ ] Redis working: `docker exec green_moment_redis redis-cli ping`

### Flutter App Checks
- [ ] App builds without errors
- [ ] Network requests reach backend (check backend logs)
- [ ] Data displays in app
- [ ] Error handling works (stop backend, test app behavior)

## Step 6: Common Issues & Solutions

### Issue: Connection Refused
**Solution**: Check firewall, ensure backend is running on 0.0.0.0 not 127.0.0.1

### Issue: CORS Errors
**Solution**: Backend already configured for CORS, ensure your app URL is in BACKEND_CORS_ORIGINS

### Issue: Database Connection Failed
**Solution**: 
```bash
# Check PostgreSQL is running
docker-compose logs db

# Recreate database
docker-compose down -v
docker-compose up -d
```

### Issue: Android Emulator Can't Connect
**Solution**: Use `10.0.2.2` instead of `localhost` or `127.0.0.1`

## Step 7: Monitor Backend

### View Logs
```bash
# All services
docker-compose logs -f

# Just API
docker-compose logs -f api

# Database queries (if DEBUG=True)
docker-compose logs -f api | grep SQL
```

### Test Endpoints Manually
Use the Swagger UI at http://localhost:8000/api/v1/docs to:
1. Test each endpoint
2. See request/response formats
3. Understand API structure

## Next Steps: Cloud Deployment

Once local testing is successful, you can deploy to:

1. **Google Cloud Platform (GCP)**
   - Cloud Run for the API
   - Cloud SQL for PostgreSQL
   - Memorystore for Redis

2. **AWS**
   - ECS/Fargate for the API
   - RDS for PostgreSQL
   - ElastiCache for Redis

3. **Railway/Render**
   - Simpler deployment
   - Built-in PostgreSQL and Redis
   - Good for getting started

See DEPLOYMENT.md for detailed cloud deployment instructions.