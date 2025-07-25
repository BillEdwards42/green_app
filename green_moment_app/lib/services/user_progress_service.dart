import 'package:shared_preferences/shared_preferences.dart';
import 'dart:convert';
import '../models/user_progress.dart';
import '../models/usage_metrics.dart';

class UserProgressService {
  static const String _progressKey = 'user_progress';
  static const String _metricsKey = 'usage_metrics';
  static const String _leagueUpgradeShownKey = 'league_upgrade_shown';

  // Get current user progress
  Future<UserProgress> getUserProgress() async {
    final prefs = await SharedPreferences.getInstance();
    final progressString = prefs.getString(_progressKey);
    
    if (progressString != null) {
      final json = jsonDecode(progressString);
      return UserProgress.fromJson(json);
    }
    
    // Return default progress for new users
    return _createDefaultProgress();
  }

  // Save user progress
  Future<void> saveUserProgress(UserProgress progress) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_progressKey, jsonEncode(progress.toJson()));
  }

  // Get usage metrics
  Future<UsageMetrics> getUsageMetrics() async {
    final prefs = await SharedPreferences.getInstance();
    final metricsString = prefs.getString(_metricsKey);
    
    if (metricsString != null) {
      final json = jsonDecode(metricsString);
      return UsageMetrics.fromJson(json);
    }
    
    return UsageMetrics.empty();
  }

  // Save usage metrics
  Future<void> saveUsageMetrics(UsageMetrics metrics) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_metricsKey, jsonEncode(metrics.toJson()));
  }

  // Track app open
  Future<void> trackAppOpen() async {
    final metrics = await getUsageMetrics();
    final now = DateTime.now();
    
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
    await _updateTaskProgress(metrics, updatedMetrics);
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
    await _updateTaskProgress(metrics, updatedMetrics);
  }

  // Clear all progress data (for testing/debugging)
  Future<void> clearAllProgress() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_progressKey);
    await prefs.remove(_metricsKey);
    await prefs.remove(_leagueUpgradeShownKey);
    print('🧹 All progress data cleared');
  }

  // Track user login
  Future<void> trackLogin() async {
    final metrics = await getUsageMetrics();
    final now = DateTime.now();
    
    if (metrics.firstLogin == null) {
      final updatedMetrics = metrics.copyWith(firstLogin: now);
      await saveUsageMetrics(updatedMetrics);
      await _updateTaskProgress(metrics, updatedMetrics);
    }
  }

  // Initialize progress for new user (clears ALL previous data)
  Future<void> initializeNewUserProgress() async {
    // Clear all existing data first
    await clearAllProgress();
    
    final now = DateTime.now();
    
    // Create completely fresh metrics for new user
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
      firstLog: null,  // Must be earned by actually logging usage
      lastAppOpen: now,
      dailyOpenTimestamps: [now],
      dailyLogTimestamps: [],
    );
    
    await saveUsageMetrics(freshMetrics);
    
    // Create fresh progress for new user
    final freshProgress = _createDefaultProgress();
    await saveUserProgress(freshProgress);
    
    // Update tasks based on fresh metrics
    await _updateTaskProgress(UsageMetrics.empty(), freshMetrics);
  }

  // Check and update league on month change
  Future<bool> checkMonthlyUpdate() async {
    final progress = await getUserProgress();
    final now = DateTime.now();
    
    // Check if it's a new month
    if (!_isCurrentMonth(progress.lastUpdated)) {
      // Calculate last month's carbon savings
      final metrics = await getUsageMetrics();
      final lastMonthSaved = metrics.monthlyCarbonSaved;
      
      // Check if all tasks are completed for league upgrade
      final allTasksCompleted = progress.currentMonthTasks
          .every((task) => task.completed);
      
      String newLeague = progress.currentLeague;
      if (allTasksCompleted && progress.currentLeague != 'diamond') {
        newLeague = LeagueRequirements.getNextLeague(progress.currentLeague);
      }
      
      // Create new tasks for the new month
      final newTasks = _createTasksForLeague(newLeague);
      
      // Update progress
      final newProgress = UserProgress(
        currentLeague: newLeague,
        lastMonthCarbonSaved: lastMonthSaved,
        lastCalculationDate: now,
        currentMonthTasks: newTasks,
        lastUpdated: now,
      );
      
      await saveUserProgress(newProgress);
      
      // Reset monthly metrics
      final resetMetrics = metrics.copyWith(
        monthlyAppOpens: 0,
        monthlyLogs: 0,
        monthlyCarbonSaved: 0,
        weeklyAppOpens: 0,
        weeklyLogs: 0,
        dailyAppOpens: 0,
        dailyLogs: 0,
        dailyOpenTimestamps: [],
        dailyLogTimestamps: [],
      );
      
      await saveUsageMetrics(resetMetrics);
      
      return newLeague != progress.currentLeague; // League changed
    }
    
    return false;
  }

  // Check if league upgrade animation should be shown
  Future<bool> shouldShowLeagueUpgrade() async {
    final prefs = await SharedPreferences.getInstance();
    final shownThisMonth = prefs.getBool(_leagueUpgradeShownKey) ?? false;
    
    if (!shownThisMonth) {
      final leagueChanged = await checkMonthlyUpdate();
      if (leagueChanged) {
        await prefs.setBool(_leagueUpgradeShownKey, true);
        return true;
      }
    }
    
    // Reset the flag on new month
    final progress = await getUserProgress();
    if (!_isCurrentMonth(progress.lastUpdated)) {
      await prefs.setBool(_leagueUpgradeShownKey, false);
    }
    
    return false;
  }

  // Helper methods
  UserProgress _createDefaultProgress() {
    return UserProgress(
      currentLeague: 'bronze',
      lastMonthCarbonSaved: null,
      lastCalculationDate: null,
      currentMonthTasks: _createTasksForLeague('bronze'),
      lastUpdated: DateTime.now(),
    );
  }

  List<TaskProgress> _createTasksForLeague(String league) {
    final requirements = LeagueRequirements.getTasksForLeague(league);
    return requirements.map((req) {
      return TaskProgress(
        id: req['type'].toString(),
        description: req['description'],
        completed: false,
        type: req['type'],
      );
    }).toList();
  }

  Future<void> _updateTaskProgress(
    UsageMetrics oldMetrics,
    UsageMetrics newMetrics,
  ) async {
    final progress = await getUserProgress();
    final updatedTasks = <TaskProgress>[];
    
    for (final task in progress.currentMonthTasks) {
      bool completed = task.completed;
      
      // Check task completion based on type
      switch (task.type) {
        case TaskType.firstAppOpen:
          completed = newMetrics.firstAppOpen != null;
          break;
        case TaskType.firstLogin:
          completed = newMetrics.firstLogin != null;
          break;
        case TaskType.firstApplianceLog:
          completed = newMetrics.firstLog != null;
          break;
        case TaskType.carbonReduction:
          final target = _getTaskTarget(progress.currentLeague, task.type);
          completed = newMetrics.monthlyCarbonSaved >= target;
          break;
        case TaskType.weeklyLogs:
          final target = _getTaskTarget(progress.currentLeague, task.type);
          completed = newMetrics.weeklyLogs >= target;
          break;
        case TaskType.weeklyAppOpens:
          final target = _getTaskTarget(progress.currentLeague, task.type);
          completed = newMetrics.weeklyAppOpens >= target;
          break;
        case TaskType.applianceVariety:
          final target = _getTaskTarget(progress.currentLeague, task.type);
          completed = newMetrics.appliancesUsed.length >= target;
          break;
        case TaskType.dailyAppOpen:
          completed = _hasOpenedEveryDay(newMetrics.dailyOpenTimestamps);
          break;
        case TaskType.dailyLog:
          completed = _hasLoggedEveryDay(newMetrics.dailyLogTimestamps);
          break;
        default:
          break;
      }
      
      updatedTasks.add(TaskProgress(
        id: task.id,
        description: task.description,
        completed: completed,
        type: task.type,
      ));
    }
    
    final updatedProgress = UserProgress(
      currentLeague: progress.currentLeague,
      lastMonthCarbonSaved: progress.lastMonthCarbonSaved,
      lastCalculationDate: progress.lastCalculationDate,
      currentMonthTasks: updatedTasks,
      lastUpdated: DateTime.now(),
    );
    
    await saveUserProgress(updatedProgress);
  }

  int _getTaskTarget(String league, TaskType type) {
    final requirements = LeagueRequirements.getTasksForLeague(league);
    final task = requirements.firstWhere(
      (req) => req['type'] == type,
      orElse: () => {'target': 0},
    );
    return task['target'] ?? 0;
  }

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
    // Keep only current month timestamps
    return updated.where((ts) => _isCurrentMonth(ts)).toList();
  }

  bool _hasOpenedEveryDay(List<DateTime> timestamps) {
    if (timestamps.isEmpty) return false;
    
    final now = DateTime.now();
    final daysInMonth = DateTime(now.year, now.month + 1, 0).day;
    final currentDay = now.day;
    
    // Check if we have timestamps for each day up to today
    final uniqueDays = timestamps
        .map((ts) => ts.day)
        .toSet();
    
    // For current month, check days up to today
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