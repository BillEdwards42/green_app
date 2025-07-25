import 'package:shared_preferences/shared_preferences.dart';

class SettingsService {
  static const String _notificationEnabledKey = 'notification_enabled';
  static const String _lastScheduledTimeKey = 'last_scheduled_time';

  static Future<void> setNotificationEnabled(bool enabled) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setBool(_notificationEnabledKey, enabled);
  }

  static Future<bool> getNotificationEnabled() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getBool(_notificationEnabledKey) ?? true; // Default to enabled
  }

  static Future<void> saveLastScheduledTime(DateTime time) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_lastScheduledTimeKey, time.toIso8601String());
  }

  static Future<DateTime?> getLastScheduledTime() async {
    final prefs = await SharedPreferences.getInstance();
    final timeString = prefs.getString(_lastScheduledTimeKey);
    if (timeString != null) {
      return DateTime.tryParse(timeString);
    }
    return null;
  }
}