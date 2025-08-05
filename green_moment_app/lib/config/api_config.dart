class ApiConfig {
  // For Android Emulator connecting to localhost
  // The Android emulator uses 10.0.2.2 to access the host machine's localhost
  static const String androidEmulatorUrl = 'http://10.0.2.2:8000/api/v1';
  
  // For physical device on same network (your computer's actual IP)
  // Update this with your computer's current IP address
  static const String localNetworkUrl = 'http://192.168.0.199:8000/api/v1';
  
  // Alternative emulator URLs to try
  static const String alternativeEmulatorUrl = 'http://127.0.0.1:8000/api/v1';
  
  // For production (will be updated after deployment)
  static const String productionUrl = 'https://api.greenmoment.com/api/v1';
  
  // Toggle between environments
  static const bool isProduction = false;
  static const bool useEmulator = false; // Set to false for physical device
  static const bool useAlternativeEmulator = true; // Set to true if 10.0.2.2 doesn't work
  
  // Current environment URL
  static String get baseUrl {
    if (isProduction) {
      return productionUrl;
    }
    
    if (useEmulator) {
      // Try your actual IP first if 10.0.2.2 doesn't work
      return useAlternativeEmulator ? localNetworkUrl : androidEmulatorUrl;
    } else {
      return localNetworkUrl;
    }
  }
  
  // Request timeout
  static const Duration timeout = Duration(seconds: 30);
  
  // API endpoints
  static const String authGoogle = '/auth/google';
  static const String authAnonymous = '/auth/anonymous';
  static const String authVerify = '/auth/verify';
  
  static const String userProfile = '/users/profile';
  static const String userUsername = '/users/username';
  
  static const String carbonCurrent = '/carbon/current';
  static const String carbonForecast = '/carbon/forecast';
  static const String carbonHistorical = '/carbon/historical';
  static const String carbonLatest = '/carbon/latest';  // New endpoint for combined data
  
  static const String choresLog = '/chores/log';
  static const String choresEstimate = '/chores/estimate';
  static const String choresHistory = '/chores/history';
  
  static const String progressSummary = '/progress/summary';
  static const String progressTasks = '/progress/tasks';
  static const String progressLeague = '/progress/league';
}