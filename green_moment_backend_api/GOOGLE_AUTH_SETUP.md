# Google OAuth Setup Guide

## Prerequisites
- Google Cloud Platform account
- Green Moment project created in GCP

## Steps to Configure Google OAuth

### 1. Create OAuth 2.0 Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Select your project
3. Navigate to **APIs & Services** > **Credentials**
4. Click **Create Credentials** > **OAuth client ID**
5. Choose **Application type**: 
   - For Android: Select "Android"
   - For iOS: Select "iOS" 
   - For testing: Select "Web application"

### 2. Configure OAuth Consent Screen

1. Go to **APIs & Services** > **OAuth consent screen**
2. Choose **External** (unless using G Suite)
3. Fill in required fields:
   - App name: "Green Moment"
   - User support email: Your email
   - Developer contact: Your email
4. Add scopes: `email`, `profile`
5. Add test users for development

### 3. Android Configuration

For Android app:
1. Package name: `com.example.green_moment_take_2`
2. SHA-1 certificate fingerprint:
   ```bash
   # Debug keystore (for development)
   keytool -list -v -keystore ~/.android/debug.keystore -alias androiddebugkey -storepass android -keypass android
   
   # Look for SHA1 fingerprint
   ```

### 4. Update Backend Configuration

Add to your `.env` file:
```env
GOOGLE_CLIENT_ID=your-client-id-here.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret-here
```

### 5. Update Flutter Configuration

1. For Android, add to `android/app/google-services.json`:
   - Download from Firebase Console or create manually
   
2. Update `android/app/build.gradle`:
   ```gradle
   android {
       defaultConfig {
           applicationId "com.example.green_moment_take_2"
       }
   }
   ```

### 6. Testing Notes

- For local testing, you may need to add `http://localhost:8000` to authorized redirect URIs
- Test users must be added to OAuth consent screen during development
- Production requires app verification for public access

## Common Issues

1. **"Invalid token" error**: 
   - Check GOOGLE_CLIENT_ID matches between Flutter and backend
   - Ensure SHA-1 fingerprint is correct for Android

2. **"Redirect URI mismatch"**:
   - Add all possible redirect URIs in Google Console
   
3. **"Access blocked" error**:
   - Add test users in OAuth consent screen
   - Check app is not in production mode during testing