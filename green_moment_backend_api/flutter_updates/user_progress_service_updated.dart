import 'package:shared_preferences/shared_preferences.dart';
import 'dart:convert';
import '../models/user_progress.dart';
import '../models/usage_metrics.dart';
import '../services/api_service.dart';

class UserProgressService {
  static const String _metricsKey = 'usage_metrics';
  static const String _leagueUpgradeShownKey = 'league_upgrade_shown';
  
  final ApiService _apiService = ApiService();

  // Get current user progress from API
  Future<UserProgress> getUserProgress() async {
    try {
      // Get progress summary from API
      final progressResponse = await _apiService.get('/progress/summary');
      
      // Get current tasks from API
      final tasksResponse = await _apiService.get('/tasks/my-tasks');
      final tasks = (tasksResponse.data as List)
          .map((json) => TaskProgress.fromApi(json))
          .toList();
      
      return UserProgress(
        currentLeague: progressResponse.data['current_league'],
        lastMonthCarbonSaved: progressResponse.data['last_month_carbon_saved']?.toDouble(),
        lastCalculationDate: progressResponse.data['last_calculation_date'] != null
            ? DateTime.parse(progressResponse.data['last_calculation_date'])
            : null,
        currentMonthTasks: tasks,
        lastUpdated: DateTime.now(),
      );
    } catch (e) {
      print('Error fetching user progress: $e');
      // Return default if API fails
      return UserProgress(
        currentLeague: 'bronze',
        lastMonthCarbonSaved: null,
        lastCalculationDate: null,
        currentMonthTasks: [],
        lastUpdated: DateTime.now(),
      );
    }
  }

  // Complete a specific task via API
  Future<void> completeTask(int taskId) async {
    try {
      await _apiService.post('/tasks/complete/$taskId');
    } catch (e) {
      print('Error completing task: $e');
      throw e;
    }
  }

  // Get usage metrics (still stored locally for UI performance)
  Future<UsageMetrics> getUsageMetrics() async {
    final prefs = await SharedPreferences.getInstance();
    final metricsString = prefs.getString(_metricsKey);
    
    if (metricsString != null) {
      final json = jsonDecode(metricsString);
      return UsageMetrics.fromJson(json);
    }
    
    return UsageMetrics.empty();
  }

  // Save usage metrics locally
  Future<void> saveUsageMetrics(UsageMetrics metrics) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_metricsKey, jsonEncode(metrics.toJson()));
  }

  // Track app open and check tasks
  Future<void> trackAppOpen() async {
    final metrics = await getUsageMetrics();
    final now = DateTime.now();
    
    // Update local metrics
    final updatedMetrics = metrics.copyWith(
      totalAppOpens: metrics.totalAppOpens + 1,
      monthlyAppOpens: _isCurrentMonth(metrics.lastAppOpen) 
          ? metrics.monthlyAppOpens + 1 
          : 1,
      weeklyAppOpens: _isCurrentWeek(metrics.lastAppOpen)
          ? metrics.weeklyAppOpens + 1
          : 1,
      dailyAppOpens: _isToday(metrics.lastAppOpen)
          ? metrics.dailyAppOpens + 1
          : 1,
      firstAppOpen: metrics.firstAppOpen ?? now,
      lastAppOpen: now,
      dailyOpenTimestamps: _updateDailyTimestamps(
        metrics.dailyOpenTimestamps, 
        now,
      ),
    );
    
    await saveUsageMetrics(updatedMetrics);
    
    // Check and complete tasks via API
    await _checkAndCompleteTasks(updatedMetrics);
  }

  // Track appliance usage log
  Future<void> trackUsageLog(String applianceType, double carbonSaved) async {
    final metrics = await getUsageMetrics();
    final now = DateTime.now();
    
    final updatedAppliances = Set<String>.from(metrics.appliancesUsed)
      ..add(applianceType);
    
    final updatedMetrics = metrics.copyWith(
      totalLogs: metrics.totalLogs + 1,
      monthlyLogs: _isCurrentMonth(now) ? metrics.monthlyLogs + 1 : 1,
      weeklyLogs: _isCurrentWeek(now) ? metrics.weeklyLogs + 1 : 1,
      dailyLogs: _isToday(now) ? metrics.dailyLogs + 1 : 1,
      appliancesUsed: updatedAppliances,
      totalCarbonSaved: metrics.totalCarbonSaved + carbonSaved,
      monthlyCarbonSaved: _isCurrentMonth(now)
          ? metrics.monthlyCarbonSaved + carbonSaved
          : carbonSaved,
      firstLog: metrics.firstLog ?? now,
      dailyLogTimestamps: _updateDailyTimestamps(
        metrics.dailyLogTimestamps,
        now,
      ),
    );
    
    await saveUsageMetrics(updatedMetrics);
    
    // Check and complete tasks via API
    await _checkAndCompleteTasks(updatedMetrics);
  }

  // Track user login
  Future<void> trackLogin() async {
    final metrics = await getUsageMetrics();
    final now = DateTime.now();
    
    if (metrics.firstLogin == null) {
      final updatedMetrics = metrics.copyWith(firstLogin: now);
      await saveUsageMetrics(updatedMetrics);
      await _checkAndCompleteTasks(updatedMetrics);
    }
  }

  // Check and complete tasks based on current metrics
  Future<void> _checkAndCompleteTasks(UsageMetrics metrics) async {
    try {
      // Get current tasks from API
      final tasksResponse = await _apiService.get('/tasks/my-tasks');
      final tasks = (tasksResponse.data as List)
          .map((json) => TaskProgress.fromApi(json))
          .toList();
      
      for (final task in tasks) {
        if (!task.completed) {
          bool shouldComplete = false;
          
          switch (task.type) {
            case TaskType.firstAppOpen:
              shouldComplete = metrics.firstAppOpen != null;
              break;
            case TaskType.firstLogin:
              shouldComplete = metrics.firstLogin != null;
              break;
            case TaskType.firstApplianceLog:
              shouldComplete = metrics.firstLog != null;
              break;
            case TaskType.carbonReduction:
              shouldComplete = metrics.monthlyCarbonSaved >= (task.targetValue ?? 0);
              break;
            case TaskType.weeklyLogs:
              shouldComplete = metrics.weeklyLogs >= (task.targetValue ?? 0);
              break;
            case TaskType.weeklyAppOpens:
              shouldComplete = metrics.weeklyAppOpens >= (task.targetValue ?? 0);
              break;
            case TaskType.applianceVariety:
              shouldComplete = metrics.appliancesUsed.length >= (task.targetValue ?? 0);
              break;
            case TaskType.dailyAppOpen:
              shouldComplete = _hasOpenedEveryDay(metrics.dailyOpenTimestamps);
              break;
            case TaskType.dailyLog:
              shouldComplete = _hasLoggedEveryDay(metrics.dailyLogTimestamps);
              break;
            default:
              break;
          }
          
          if (shouldComplete) {
            await completeTask(int.parse(task.id));
          }
        }
      }
    } catch (e) {
      print('Error checking tasks: $e');
    }
  }

  // Clear all progress data (for testing/debugging)
  Future<void> clearAllProgress() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_metricsKey);
    await prefs.remove(_leagueUpgradeShownKey);
    print('🧹 All progress data cleared');
  }

  // Initialize progress for new user
  Future<void> initializeNewUserProgress() async {
    await clearAllProgress();
    
    final now = DateTime.now();
    
    // Create fresh metrics for new user
    final freshMetrics = UsageMetrics(
      totalAppOpens: 1,
      monthlyAppOpens: 1,
      weeklyAppOpens: 1,
      dailyAppOpens: 1,
      totalLogs: 0,
      monthlyLogs: 0,
      weeklyLogs: 0,
      dailyLogs: 0,
      appliancesUsed: {},
      totalCarbonSaved: 0,
      monthlyCarbonSaved: 0,
      firstAppOpen: now,
      firstLogin: now,
      firstLog: null,
      lastAppOpen: now,
      dailyOpenTimestamps: [now],
      dailyLogTimestamps: [],
    );
    
    await saveUsageMetrics(freshMetrics);
  }

  // Check if league upgrade animation should be shown
  Future<bool> shouldShowLeagueUpgrade() async {
    try {
      final response = await _apiService.get('/progress/summary');
      return response.data['should_show_league_upgrade'] ?? false;
    } catch (e) {
      return false;
    }
  }

  // Helper methods
  bool _isCurrentMonth(DateTime date) {
    final now = DateTime.now();
    return date.year == now.year && date.month == now.month;
  }

  bool _isCurrentWeek(DateTime date) {
    final now = DateTime.now();
    final weekStart = now.subtract(Duration(days: now.weekday - 1));
    return date.isAfter(weekStart);
  }

  bool _isToday(DateTime date) {
    final now = DateTime.now();
    return date.year == now.year &&
        date.month == now.month &&
        date.day == now.day;
  }

  List<DateTime> _updateDailyTimestamps(
    List<DateTime> timestamps,
    DateTime newTimestamp,
  ) {
    final updated = List<DateTime>.from(timestamps)..add(newTimestamp);
    return updated.where((ts) => _isCurrentMonth(ts)).toList();
  }

  bool _hasOpenedEveryDay(List<DateTime> timestamps) {
    if (timestamps.isEmpty) return false;
    
    final now = DateTime.now();
    final currentDay = now.day;
    
    final uniqueDays = timestamps
        .map((ts) => ts.day)
        .toSet();
    
    for (int day = 1; day <= currentDay; day++) {
      if (!uniqueDays.contains(day)) {
        return false;
      }
    }
    
    return true;
  }

  bool _hasLoggedEveryDay(List<DateTime> timestamps) {
    return _hasOpenedEveryDay(timestamps);
  }
}