import 'package:flutter/material.dart';
import 'package:flutter_local_notifications/flutter_local_notifications.dart';
import 'package:permission_handler/permission_handler.dart';
import 'package:timezone/timezone.dart' as tz;
import 'package:timezone/data/latest.dart' as tz;
import 'settings_service.dart';
import 'mock_data_service.dart';

class NotificationService {
  static final FlutterLocalNotificationsPlugin _notifications =
      FlutterLocalNotificationsPlugin();
  
  static bool _initialized = false;

  static Future<void> initialize() async {
    if (_initialized) return;
    
    // Initialize timezone data
    tz.initializeTimeZones();
    
    // Android initialization
    const AndroidInitializationSettings initializationSettingsAndroid =
        AndroidInitializationSettings('@mipmap/ic_launcher');

    // iOS initialization
    const DarwinInitializationSettings initializationSettingsIOS =
        DarwinInitializationSettings(
      requestAlertPermission: true,
      requestBadgePermission: true,
      requestSoundPermission: true,
    );

    const InitializationSettings initializationSettings =
        InitializationSettings(
      android: initializationSettingsAndroid,
      iOS: initializationSettingsIOS,
    );

    await _notifications.initialize(initializationSettings);
    _initialized = true;
  }

  static Future<bool> requestPermissions() async {
    if (await Permission.notification.isGranted) {
      return true;
    }
    
    final status = await Permission.notification.request();
    return status == PermissionStatus.granted;
  }

  static Future<bool> requestExactAlarmPermission() async {
    // For Android 12+, we need to request exact alarm permission
    final status = await Permission.scheduleExactAlarm.request();
    return status == PermissionStatus.granted;
  }

  static Future<void> scheduleDailyFetchAndNotification() async {
    if (!_initialized) await initialize();
    
    final isEnabled = await SettingsService.getNotificationEnabled();
    if (!isEnabled) return;

    // Request exact alarm permission for Android 12+
    final hasExactAlarmPermission = await requestExactAlarmPermission();
    if (!hasExactAlarmPermission) {
      debugPrint('Exact alarm permission not granted');
      return;
    }

    // Schedule daily notification at 12:10 PM
    final now = DateTime.now();
    var scheduledTime = DateTime(now.year, now.month, now.day, 12, 10);
    
    // If 12:10 PM has already passed today, schedule for tomorrow
    if (scheduledTime.isBefore(now)) {
      scheduledTime = scheduledTime.add(const Duration(days: 1));
    }

    // Also schedule a test notification in 30 seconds for immediate testing
    final testTime = now.add(const Duration(seconds: 30));
    await _scheduleTestNotification(testTime);

    await _scheduleNotificationWithRecommendation(scheduledTime);
    await SettingsService.saveLastScheduledTime(scheduledTime);
  }

  static Future<void> _scheduleTestNotification(DateTime scheduledTime) async {
    try {
      await _notifications.zonedSchedule(
        1, // test notification id
        '測試通知',
        '這是一個測試通知，如果您看到這個，表示通知功能正常運作！',
        tz.TZDateTime.from(scheduledTime, tz.local),
        const NotificationDetails(
          android: AndroidNotificationDetails(
            'green_moment_channel',
            'Green Moment Notifications',
            channelDescription: '減碳時刻提醒通知',
            importance: Importance.max,
            priority: Priority.high,
            icon: '@mipmap/ic_launcher',
          ),
          iOS: DarwinNotificationDetails(
            presentAlert: true,
            presentBadge: true,
            presentSound: true,
          ),
        ),
        androidScheduleMode: AndroidScheduleMode.exactAllowWhileIdle,
        uiLocalNotificationDateInterpretation:
            UILocalNotificationDateInterpretation.absoluteTime,
      );
      
      debugPrint('Scheduled TEST notification for $scheduledTime');
    } catch (e) {
      debugPrint('Error scheduling test notification: $e');
    }
  }

  static Future<void> _scheduleNotificationWithRecommendation(DateTime scheduledTime) async {
    try {
      // Fetch the latest recommendation data
      final appData = await MockDataService.fetchCarbonData();
      final recommendation = appData.recommendation;
      
      final title = '減碳時刻';
      final body = '今日預計減碳時刻為 ${recommendation.startTime} - ${recommendation.endTime}';
      
      await _notifications.zonedSchedule(
        0, // notification id
        title,
        body,
        tz.TZDateTime.from(scheduledTime, tz.local),
        const NotificationDetails(
          android: AndroidNotificationDetails(
            'green_moment_channel',
            'Green Moment Notifications',
            channelDescription: '減碳時刻提醒通知',
            importance: Importance.high,
            priority: Priority.high,
            icon: '@mipmap/ic_launcher',
          ),
          iOS: DarwinNotificationDetails(
            presentAlert: true,
            presentBadge: true,
            presentSound: true,
          ),
        ),
        androidScheduleMode: AndroidScheduleMode.exactAllowWhileIdle,
        uiLocalNotificationDateInterpretation:
            UILocalNotificationDateInterpretation.absoluteTime,
        matchDateTimeComponents: DateTimeComponents.time, // Repeat daily
      );
      
      debugPrint('Scheduled notification for $scheduledTime with message: $body');
    } catch (e) {
      debugPrint('Error scheduling notification: $e');
    }
  }

  static Future<void> showTestNotification() async {
    if (!_initialized) await initialize();
    
    try {
      final appData = await MockDataService.fetchCarbonData();
      final recommendation = appData.recommendation;
      
      await _notifications.show(
        999, // test notification id
        '減碳時刻 (測試)',
        '今日預計減碳時刻為 ${recommendation.startTime} - ${recommendation.endTime}',
        const NotificationDetails(
          android: AndroidNotificationDetails(
            'green_moment_channel',
            'Green Moment Notifications',
            channelDescription: '減碳時刻提醒通知',
            importance: Importance.high,
            priority: Priority.high,
            icon: '@mipmap/ic_launcher',
          ),
          iOS: DarwinNotificationDetails(
            presentAlert: true,
            presentBadge: true,
            presentSound: true,
          ),
        ),
      );
      
      debugPrint('Test notification shown');
    } catch (e) {
      debugPrint('Error showing test notification: $e');
    }
  }

  static Future<void> cancelAllNotifications() async {
    await _notifications.cancelAll();
    debugPrint('All notifications cancelled');
  }

  static Future<void> rescheduleIfEnabled() async {
    final isEnabled = await SettingsService.getNotificationEnabled();
    if (isEnabled) {
      await scheduleDailyFetchAndNotification();
    } else {
      await cancelAllNotifications();
    }
  }
}