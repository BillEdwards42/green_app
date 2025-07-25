# 🚀 Quick Start Guide - Green Moment Backend

## Step 1: Start the Backend (2 minutes)

```bash
# Navigate to backend directory
cd /home/bill/StudioProjects/green_moment_backend_api

# Copy environment file
cp .env.example .env

# Start everything with Docker
docker-compose up -d

# Wait ~30 seconds for services to start, then verify
docker-compose ps
```

✅ You should see all services "Up" and healthy.

## Step 2: Test the Backend (1 minute)

```bash
# Run the test script
python test_endpoints.py
```

✅ You should see mostly green checkmarks. The endpoints return placeholder data for now.

## Step 3: Open API Documentation

Open your browser and go to:
- 📚 **http://localhost:8000/api/v1/docs**

This shows all available endpoints you can test.

## Step 4: Connect Your Flutter App

### For Android Emulator:
Your app is already configured! The emulator can access your backend at `10.0.2.2:8000`.

### For Physical Device:
1. Find your computer's IP address:
   ```bash
   # Linux/Mac
   hostname -I | awk '{print $1}'
   
   # Windows (in PowerShell)
   (Get-NetIPAddress -AddressFamily IPv4 -InterfaceAlias "Wi-Fi").IPAddress
   ```

2. Update `lib/config/api_config.dart` in your Flutter app:
   ```dart
   static const String localNetworkUrl = 'http://YOUR_IP:8000/api/v1';
   static const bool useEmulator = false; // Change to false
   ```

## Step 5: Test in Android Studio

1. Run your Flutter app
2. Watch the backend logs:
   ```bash
   docker-compose logs -f api
   ```
3. You should see requests coming in when the app tries to fetch data

## 🎯 What's Working Now?

- ✅ Backend is running
- ✅ All endpoints respond (with placeholder data)
- ✅ Database is ready
- ✅ Redis cache is running
- ✅ API documentation is available
- ✅ Flutter app can connect

## 🔧 Troubleshooting

### "Connection refused" in Flutter app
- Make sure Docker containers are running: `docker-compose ps`
- For physical device: Check you're on the same Wi-Fi network
- Check firewall isn't blocking port 8000

### "docker-compose: command not found"
Install Docker Desktop from https://www.docker.com/products/docker-desktop/

### Backend won't start
```bash
# Stop everything and restart
docker-compose down
docker-compose up -d
```

## 📱 Next Steps

1. **Test with real data**: The endpoints currently return mock data. As we implement them, they'll connect to your carbon intensity data.

2. **Add Google Sign-In**: 
   - Get credentials from [Google Cloud Console](https://console.cloud.google.com/)
   - Add to `.env` file
   - Update Flutter app with Google Sign-In package

3. **Deploy to cloud**: When ready, see `DEPLOYMENT.md` for cloud deployment options.

## 🆘 Need Help?

- Check logs: `docker-compose logs -f api`
- API docs: http://localhost:8000/api/v1/docs
- All guides are in this directory:
  - `TESTING_GUIDE.md` - Detailed testing instructions
  - `DEPLOYMENT.md` - Cloud deployment guide
  - `README.md` - Project overview