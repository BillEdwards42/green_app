import 'dart:io';
import 'package:firebase_core/firebase_core.dart';
import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../config/api_config.dart';
import 'auth_service.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';

class NotificationService {
  static final NotificationService _instance = NotificationService._internal();
  factory NotificationService() => _instance;
  NotificationService._internal();

  final FirebaseMessaging _messaging = FirebaseMessaging.instance;
  final FlutterLocalNotificationsPlugin _localNotifications = FlutterLocalNotificationsPlugin();
  
  String? _deviceToken;
  bool _initialized = false;
  
  // Keys for SharedPreferences
  static const String _notificationEnabledKey = 'notification_enabled';
  static const String _scheduledTimeKey = 'notification_scheduled_time';
  static const String _deviceTokenKey = 'device_token';

  Future<void> initialize() async {
    if (_initialized) return;
    
    try {
      // Initialize Firebase
      await Firebase.initializeApp();
      
      // Initialize local notifications
      const androidSettings = AndroidInitializationSettings('@mipmap/ic_launcher');
      const iosSettings = DarwinInitializationSettings(
        requestAlertPermission: false,
        requestBadgePermission: false,
        requestSoundPermission: false,
      );
      
      const initSettings = InitializationSettings(
        android: androidSettings,
        iOS: iosSettings,
      );
      
      await _localNotifications.initialize(
        initSettings,
        onDidReceiveNotificationResponse: _onNotificationTapped,
      );
      
      // Request permissions
      await requestPermissions();
      
      // Get and save token
      await _getAndSaveToken();
      
      // Listen for token refresh
      _messaging.onTokenRefresh.listen(_handleTokenRefresh);
      
      // Handle foreground messages
      FirebaseMessaging.onMessage.listen(_handleForegroundMessage);
      
      // Handle background messages
      FirebaseMessaging.onBackgroundMessage(_firebaseMessagingBackgroundHandler);
      
      _initialized = true;
      print('NotificationService initialized successfully');
    } catch (e) {
      print('Error initializing NotificationService: $e');
    }
  }

  Future<bool> requestPermissions() async {
    final settings = await _messaging.requestPermission(
      alert: true,
      badge: true,
      sound: true,
    );
    
    return settings.authorizationStatus == AuthorizationStatus.authorized;
  }

  Future<void> _getAndSaveToken() async {
    try {
      print('🔑 Getting FCM token...');
      _deviceToken = await _messaging.getToken();
      
      if (_deviceToken != null) {
        print('🔑 Got FCM token: ${_deviceToken!.substring(0, 50)}...');
        // Save locally
        final prefs = await SharedPreferences.getInstance();
        await prefs.setString(_deviceTokenKey, _deviceToken!);
        
        // Send to backend if authenticated
        await _registerTokenWithBackend(_deviceToken!);
      } else {
        print('❌ FCM token is null');
      }
    } catch (e) {
      print('❌ Error getting FCM token: $e');
    }
  }
  
  // Call this when user logs in to ensure fresh token
  Future<void> refreshToken() async {
    await _getAndSaveToken();
  }

  Future<void> _handleTokenRefresh(String newToken) async {
    _deviceToken = newToken;
    
    // Save locally
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_deviceTokenKey, newToken);
    
    // Update backend
    await _registerTokenWithBackend(newToken);
  }

  Future<void> _registerTokenWithBackend(String token) async {
    print('📤 Attempting to register FCM token with backend...');
    final authService = AuthService();
    if (!authService.isAuthenticated) {
      print('❌ Not authenticated, skipping FCM token registration');
      return;
    }
    
    try {
      final deviceId = await _getDeviceId();
      
      final response = await http.post(
        Uri.parse('${ApiConfig.baseUrl}/notifications/device-token'),
        headers: {
          'Content-Type': 'application/json',
          ...authService.getAuthHeaders(),
        },
        body: jsonEncode({
          'token': token,
          'platform': Platform.isAndroid ? 'android' : 'ios',
          'device_id': deviceId,
          'app_version': '1.0.0', // TODO: Get from package info
        }),
      );
      
      if (response.statusCode == 200) {
        print('Device token registered successfully');
      } else {
        print('Failed to register device token: ${response.statusCode}');
      }
    } catch (e) {
      print('Error registering device token: $e');
    }
  }

  Future<String> _getDeviceId() async {
    // For Android, we can use a unique ID
    // For iOS, we'll use a generated UUID stored in SharedPreferences
    final prefs = await SharedPreferences.getInstance();
    
    String? deviceId = prefs.getString('device_unique_id');
    if (deviceId == null) {
      deviceId = DateTime.now().millisecondsSinceEpoch.toString();
      await prefs.setString('device_unique_id', deviceId);
    }
    
    return deviceId;
  }

  // Handle foreground messages
  void _handleForegroundMessage(RemoteMessage message) {
    print('Foreground message received: ${message.messageId}');
    
    // Show local notification
    _showLocalNotification(message);
  }

  Future<void> _showLocalNotification(RemoteMessage message) async {
    const androidDetails = AndroidNotificationDetails(
      'daily_recommendations',
      '每日減碳提醒',
      channelDescription: '每日最佳用電時段提醒',
      importance: Importance.high,
      priority: Priority.high,
    );
    
    const iosDetails = DarwinNotificationDetails(
      presentAlert: true,
      presentBadge: true,
      presentSound: true,
    );
    
    const details = NotificationDetails(
      android: androidDetails,
      iOS: iosDetails,
    );
    
    await _localNotifications.show(
      message.hashCode,
      null, // No title as requested
      message.notification?.body ?? message.data['body'],
      details,
      payload: jsonEncode(message.data),
    );
  }

  void _onNotificationTapped(NotificationResponse response) {
    // Handle notification tap
    if (response.payload != null) {
      final data = jsonDecode(response.payload!);
      print('Notification tapped with data: $data');
      // TODO: Navigate to appropriate screen
    }
  }

  // Notification settings management
  Future<bool> isNotificationEnabled() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getBool(_notificationEnabledKey) ?? true; // Default enabled
  }

  Future<void> setNotificationEnabled(bool enabled) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool(_notificationEnabledKey, enabled);
    
    // Update backend
    await _updateBackendSettings(enabled: enabled);
  }

  Future<String> getScheduledTime() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString(_scheduledTimeKey) ?? '09:00'; // Default 9:00
  }

  Future<void> setScheduledTime(String time) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_scheduledTimeKey, time);
    
    // Update backend
    await _updateBackendSettings(scheduledTime: time);
  }

  Future<void> _updateBackendSettings({bool? enabled, String? scheduledTime}) async {
    final authService = AuthService();
    if (!authService.isAuthenticated) return;
    
    try {
      final body = <String, dynamic>{};
      if (enabled != null) body['enabled'] = enabled;
      if (scheduledTime != null) body['scheduled_time'] = scheduledTime;
      
      final response = await http.put(
        Uri.parse('${ApiConfig.baseUrl}/notifications/settings'),
        headers: {
          'Content-Type': 'application/json',
          ...authService.getAuthHeaders(),
        },
        body: jsonEncode(body),
      );
      
      if (response.statusCode == 200) {
        print('Notification settings updated successfully');
      } else {
        print('Failed to update notification settings: ${response.statusCode}');
      }
    } catch (e) {
      print('Error updating notification settings: $e');
    }
  }

  // Load settings from backend
  Future<void> loadSettingsFromBackend() async {
    final authService = AuthService();
    if (!authService.isAuthenticated) return;
    
    try {
      final response = await http.get(
        Uri.parse('${ApiConfig.baseUrl}/notifications/settings'),
        headers: authService.getAuthHeaders(),
      );
      
      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        final prefs = await SharedPreferences.getInstance();
        
        await prefs.setBool(_notificationEnabledKey, data['enabled'] ?? true);
        await prefs.setString(_scheduledTimeKey, data['scheduled_time'] ?? '09:00');
        
        print('Notification settings loaded from backend');
      }
    } catch (e) {
      print('Error loading notification settings: $e');
    }
  }
}

// Background message handler (must be top-level function)
@pragma('vm:entry-point')
Future<void> _firebaseMessagingBackgroundHandler(RemoteMessage message) async {
  await Firebase.initializeApp();
  print('Background message received: ${message.messageId}');
  // Handle background message if needed
}