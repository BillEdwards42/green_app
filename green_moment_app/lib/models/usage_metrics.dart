class UsageMetrics {
  final int totalAppOpens;
  final int monthlyAppOpens;
  final int weeklyAppOpens;
  final int dailyAppOpens;
  final int totalLogs;
  final int monthlyLogs;
  final int weeklyLogs;
  final int dailyLogs;
  final Set<String> appliancesUsed;
  final double totalCarbonSaved;
  final double monthlyCarbonSaved;
  final DateTime? firstAppOpen;
  final DateTime? firstLogin;
  final DateTime? firstLog;
  final DateTime lastAppOpen;
  final List<DateTime> dailyOpenTimestamps;
  final List<DateTime> dailyLogTimestamps;

  UsageMetrics({
    required this.totalAppOpens,
    required this.monthlyAppOpens,
    required this.weeklyAppOpens,
    required this.dailyAppOpens,
    required this.totalLogs,
    required this.monthlyLogs,
    required this.weeklyLogs,
    required this.dailyLogs,
    required this.appliancesUsed,
    required this.totalCarbonSaved,
    required this.monthlyCarbonSaved,
    this.firstAppOpen,
    this.firstLogin,
    this.firstLog,
    required this.lastAppOpen,
    required this.dailyOpenTimestamps,
    required this.dailyLogTimestamps,
  });

  factory UsageMetrics.empty() {
    return UsageMetrics(
      totalAppOpens: 0,
      monthlyAppOpens: 0,
      weeklyAppOpens: 0,
      dailyAppOpens: 0,
      totalLogs: 0,
      monthlyLogs: 0,
      weeklyLogs: 0,
      dailyLogs: 0,
      appliancesUsed: {},
      totalCarbonSaved: 0,
      monthlyCarbonSaved: 0,
      lastAppOpen: DateTime.now(),
      dailyOpenTimestamps: [],
      dailyLogTimestamps: [],
    );
  }

  factory UsageMetrics.fromJson(Map<String, dynamic> json) {
    return UsageMetrics(
      totalAppOpens: json['totalAppOpens'] ?? 0,
      monthlyAppOpens: json['monthlyAppOpens'] ?? 0,
      weeklyAppOpens: json['weeklyAppOpens'] ?? 0,
      dailyAppOpens: json['dailyAppOpens'] ?? 0,
      totalLogs: json['totalLogs'] ?? 0,
      monthlyLogs: json['monthlyLogs'] ?? 0,
      weeklyLogs: json['weeklyLogs'] ?? 0,
      dailyLogs: json['dailyLogs'] ?? 0,
      appliancesUsed: Set<String>.from(json['appliancesUsed'] ?? []),
      totalCarbonSaved: (json['totalCarbonSaved'] ?? 0).toDouble(),
      monthlyCarbonSaved: (json['monthlyCarbonSaved'] ?? 0).toDouble(),
      firstAppOpen: json['firstAppOpen'] != null
          ? DateTime.parse(json['firstAppOpen'])
          : null,
      firstLogin: json['firstLogin'] != null
          ? DateTime.parse(json['firstLogin'])
          : null,
      firstLog: json['firstLog'] != null
          ? DateTime.parse(json['firstLog'])
          : null,
      lastAppOpen: DateTime.parse(json['lastAppOpen']),
      dailyOpenTimestamps: (json['dailyOpenTimestamps'] as List<dynamic>?)
              ?.map((ts) => DateTime.parse(ts))
              .toList() ??
          [],
      dailyLogTimestamps: (json['dailyLogTimestamps'] as List<dynamic>?)
              ?.map((ts) => DateTime.parse(ts))
              .toList() ??
          [],
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'totalAppOpens': totalAppOpens,
      'monthlyAppOpens': monthlyAppOpens,
      'weeklyAppOpens': weeklyAppOpens,
      'dailyAppOpens': dailyAppOpens,
      'totalLogs': totalLogs,
      'monthlyLogs': monthlyLogs,
      'weeklyLogs': weeklyLogs,
      'dailyLogs': dailyLogs,
      'appliancesUsed': appliancesUsed.toList(),
      'totalCarbonSaved': totalCarbonSaved,
      'monthlyCarbonSaved': monthlyCarbonSaved,
      'firstAppOpen': firstAppOpen?.toIso8601String(),
      'firstLogin': firstLogin?.toIso8601String(),
      'firstLog': firstLog?.toIso8601String(),
      'lastAppOpen': lastAppOpen.toIso8601String(),
      'dailyOpenTimestamps': dailyOpenTimestamps
          .map((ts) => ts.toIso8601String())
          .toList(),
      'dailyLogTimestamps': dailyLogTimestamps
          .map((ts) => ts.toIso8601String())
          .toList(),
    };
  }

  UsageMetrics copyWith({
    int? totalAppOpens,
    int? monthlyAppOpens,
    int? weeklyAppOpens,
    int? dailyAppOpens,
    int? totalLogs,
    int? monthlyLogs,
    int? weeklyLogs,
    int? dailyLogs,
    Set<String>? appliancesUsed,
    double? totalCarbonSaved,
    double? monthlyCarbonSaved,
    DateTime? firstAppOpen,
    DateTime? firstLogin,
    DateTime? firstLog,
    DateTime? lastAppOpen,
    List<DateTime>? dailyOpenTimestamps,
    List<DateTime>? dailyLogTimestamps,
  }) {
    return UsageMetrics(
      totalAppOpens: totalAppOpens ?? this.totalAppOpens,
      monthlyAppOpens: monthlyAppOpens ?? this.monthlyAppOpens,
      weeklyAppOpens: weeklyAppOpens ?? this.weeklyAppOpens,
      dailyAppOpens: dailyAppOpens ?? this.dailyAppOpens,
      totalLogs: totalLogs ?? this.totalLogs,
      monthlyLogs: monthlyLogs ?? this.monthlyLogs,
      weeklyLogs: weeklyLogs ?? this.weeklyLogs,
      dailyLogs: dailyLogs ?? this.dailyLogs,
      appliancesUsed: appliancesUsed ?? this.appliancesUsed,
      totalCarbonSaved: totalCarbonSaved ?? this.totalCarbonSaved,
      monthlyCarbonSaved: monthlyCarbonSaved ?? this.monthlyCarbonSaved,
      firstAppOpen: firstAppOpen ?? this.firstAppOpen,
      firstLogin: firstLogin ?? this.firstLogin,
      firstLog: firstLog ?? this.firstLog,
      lastAppOpen: lastAppOpen ?? this.lastAppOpen,
      dailyOpenTimestamps: dailyOpenTimestamps ?? this.dailyOpenTimestamps,
      dailyLogTimestamps: dailyLogTimestamps ?? this.dailyLogTimestamps,
    );
  }
}