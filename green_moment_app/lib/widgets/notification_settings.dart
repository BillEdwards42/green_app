import 'package:flutter/material.dart';
import '../constants/app_colors.dart';
import '../services/notification_service.dart';
import '../services/auth_service.dart';

class NotificationSettings extends StatefulWidget {
  const NotificationSettings({super.key});

  @override
  State<NotificationSettings> createState() => _NotificationSettingsState();
}

class _NotificationSettingsState extends State<NotificationSettings> {
  final NotificationService _notificationService = NotificationService();
  final AuthService _authService = AuthService();
  
  bool _notificationEnabled = true;
  TimeOfDay _scheduledTime = const TimeOfDay(hour: 9, minute: 0);
  bool _isLoading = true;

  @override
  void initState() {
    super.initState();
    _loadSettings();
  }

  Future<void> _loadSettings() async {
    if (!_authService.isAuthenticated) {
      setState(() => _isLoading = false);
      return;
    }

    // Load settings from local storage/backend
    final enabled = await _notificationService.isNotificationEnabled();
    final timeStr = await _notificationService.getScheduledTime();
    
    // Parse time string (HH:MM format)
    final parts = timeStr.split(':');
    final hour = int.tryParse(parts[0]) ?? 9;
    final minute = parts.length > 1 ? int.tryParse(parts[1]) ?? 0 : 0;
    
    setState(() {
      _notificationEnabled = enabled;
      _scheduledTime = TimeOfDay(hour: hour, minute: minute);
      _isLoading = false;
    });
  }

  void _toggleNotifications(bool value) async {
    if (!_authService.isAuthenticated) {
      _showAuthRequiredDialog();
      return;
    }

    setState(() {
      _notificationEnabled = value;
    });
    
    if (value) {
      // Request permissions first
      final granted = await _notificationService.requestPermissions();
      if (!granted) {
        setState(() {
          _notificationEnabled = false;
        });
        _showPermissionDeniedDialog();
        return;
      }
    }
    
    // Update backend
    await _notificationService.setNotificationEnabled(value);
  }

  void _showAuthRequiredDialog() {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        backgroundColor: AppColors.bgPrimary,
        title: const Text('需要登入', style: TextStyle(color: AppColors.textPrimary)),
        content: const Text('請先登入以使用通知功能', style: TextStyle(color: AppColors.textSecondary)),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('確定'),
          ),
        ],
      ),
    );
  }

  void _showPermissionDeniedDialog() {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        backgroundColor: AppColors.bgPrimary,
        title: const Text('需要通知權限', style: TextStyle(color: AppColors.textPrimary)),
        content: const Text('請在設定中允許通知權限以接收減碳提醒', style: TextStyle(color: AppColors.textSecondary)),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('確定'),
          ),
        ],
      ),
    );
  }

  Future<void> _showTimePickerDialog() async {
    if (!_authService.isAuthenticated) {
      _showAuthRequiredDialog();
      return;
    }

    final TimeOfDay? picked = await showTimePicker(
      context: context,
      initialTime: _scheduledTime,
      helpText: '選擇通知時間\n(將調整至最接近的10分鐘)',
      builder: (BuildContext context, Widget? child) {
        return Theme(
          data: Theme.of(context).copyWith(
            colorScheme: const ColorScheme.light(
              primary: AppColors.accent,
              onPrimary: Colors.white,
              onSurface: Colors.white,
              surface: AppColors.bgPrimary,
              onSurfaceVariant: Colors.white,
            ),
            dialogBackgroundColor: AppColors.bgPrimary,
            timePickerTheme: TimePickerThemeData(
              backgroundColor: AppColors.bgPrimary,
              hourMinuteShape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(12),
                side: const BorderSide(color: Colors.white24),
              ),
              dayPeriodShape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(8),
                side: const BorderSide(color: Colors.white24),
              ),
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(16),
              ),
              hourMinuteTextStyle: const TextStyle(
                fontSize: 40,
                fontWeight: FontWeight.w600,
                color: Colors.white,
              ),
              dayPeriodTextStyle: const TextStyle(
                fontSize: 14,
                fontWeight: FontWeight.w600,
                color: Colors.white,
              ),
              helpTextStyle: const TextStyle(
                fontSize: 16,
                fontWeight: FontWeight.w600,
                color: Colors.white70,
              ),
              dialHandColor: AppColors.accent,
              dialTextStyle: const TextStyle(
                fontSize: 14,
                fontWeight: FontWeight.w500,
                color: Colors.white70,
              ),
              dialTextColor: Colors.white,
              entryModeIconColor: Colors.white,
              hourMinuteTextColor: Colors.white,
              dayPeriodTextColor: Colors.white,
              dialBackgroundColor: Colors.white.withOpacity(0.12),
              hourMinuteColor: Colors.white.withOpacity(0.12),
              dayPeriodColor: Colors.white.withOpacity(0.12),
            ),
          ),
          child: child!,
        );
      },
    );

    if (picked != null && picked != _scheduledTime) {
      // Round to nearest 10-minute increment
      int roundedMinute = (picked.minute / 10).round() * 10;
      if (roundedMinute == 60) {
        roundedMinute = 0;
      }
      
      final adjustedTime = TimeOfDay(hour: picked.hour, minute: roundedMinute);
      
      // Show confirmation if time was adjusted
      if (picked.minute != roundedMinute) {
        await showDialog(
          context: context,
          builder: (BuildContext context) {
            return AlertDialog(
              backgroundColor: AppColors.bgPrimary,
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(16),
              ),
              title: const Text(
                '時間已調整',
                style: TextStyle(
                  color: Colors.white,
                  fontSize: 18,
                  fontWeight: FontWeight.w600,
                ),
              ),
              content: Text(
                '您選擇的 ${picked.hour.toString().padLeft(2, '0')}:${picked.minute.toString().padLeft(2, '0')} '
                '已調整為 ${adjustedTime.hour.toString().padLeft(2, '0')}:${adjustedTime.minute.toString().padLeft(2, '0')}',
                style: const TextStyle(
                  color: Colors.white70,
                  fontSize: 14,
                ),
              ),
              actions: [
                TextButton(
                  onPressed: () => Navigator.of(context).pop(),
                  child: const Text(
                    '確定',
                    style: TextStyle(color: AppColors.accent),
                  ),
                ),
              ],
            );
          },
        );
      }
      
      setState(() {
        _scheduledTime = adjustedTime;
      });
      
      // Update backend with 24-hour format
      final timeStr = '${adjustedTime.hour.toString().padLeft(2, '0')}:${adjustedTime.minute.toString().padLeft(2, '0')}';
      await _notificationService.setScheduledTime(timeStr);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      height: 48,
      padding: const EdgeInsets.symmetric(horizontal: 16),
      decoration: BoxDecoration(
        color: const Color(0x0AFFFFFF),
        border: Border.all(
          color: const Color(0x14FFFFFF),
        ),
        borderRadius: BorderRadius.circular(10),
      ),
      child: Row(
        children: [
          // Bell icon
          Icon(
            Icons.notifications_outlined,
            size: 16,
            color: _isLoading || !_notificationEnabled
                ? AppColors.textMuted
                : AppColors.textSecondary,
          ),
          const SizedBox(width: 8),
          
          // Text
          Text(
            '減碳時刻',
            style: TextStyle(
              fontSize: 13,
              fontWeight: FontWeight.w600,
              color: _isLoading || !_notificationEnabled
                  ? AppColors.textMuted
                  : AppColors.textSecondary,
            ),
          ),
          
          const Spacer(),
          
          // Clock button (only visible when enabled)
          if (_notificationEnabled)
            GestureDetector(
              onTap: _showTimePickerDialog,
              child: Container(
                padding: const EdgeInsets.all(6),
                margin: const EdgeInsets.only(right: 8),
                decoration: BoxDecoration(
                  color: Colors.white.withValues(alpha: 0.1),
                  borderRadius: BorderRadius.circular(6),
                ),
                child: Icon(
                  Icons.access_time,
                  size: 14,
                  color: Colors.white,
                ),
              ),
            ),
          
          // Toggle switch
          Transform.scale(
            scale: 0.7,
            child: Switch(
              value: _notificationEnabled,
              onChanged: _isLoading ? null : _toggleNotifications,
              activeColor: AppColors.accent,
              activeTrackColor: AppColors.accent.withValues(alpha: 0.3),
              inactiveThumbColor: AppColors.textMuted,
              inactiveTrackColor: AppColors.textMuted.withValues(alpha: 0.2),
              materialTapTargetSize: MaterialTapTargetSize.shrinkWrap,
            ),
          ),
        ],
      ),
    );
  }
}