class UserProgress {
  final String currentLeague;
  final double? lastMonthCarbonSaved;
  final DateTime? lastCalculationDate;
  final List<TaskProgress> currentMonthTasks;
  final DateTime lastUpdated;

  UserProgress({
    required this.currentLeague,
    this.lastMonthCarbonSaved,
    this.lastCalculationDate,
    required this.currentMonthTasks,
    required this.lastUpdated,
  });

  factory UserProgress.fromJson(Map<String, dynamic> json) {
    return UserProgress(
      currentLeague: json['currentLeague'] ?? 'bronze',
      lastMonthCarbonSaved: json['lastMonthCarbonSaved']?.toDouble(),
      lastCalculationDate: json['lastCalculationDate'] != null
          ? DateTime.parse(json['lastCalculationDate'])
          : null,
      currentMonthTasks: (json['currentMonthTasks'] as List<dynamic>?)
              ?.map((task) => TaskProgress.fromJson(task))
              .toList() ??
          [],
      lastUpdated: DateTime.parse(json['lastUpdated']),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'currentLeague': currentLeague,
      'lastMonthCarbonSaved': lastMonthCarbonSaved,
      'lastCalculationDate': lastCalculationDate?.toIso8601String(),
      'currentMonthTasks': currentMonthTasks.map((task) => task.toJson()).toList(),
      'lastUpdated': lastUpdated.toIso8601String(),
    };
  }
}

class TaskProgress {
  final String id;
  final String description;
  final bool completed;
  final TaskType type;

  TaskProgress({
    required this.id,
    required this.description,
    required this.completed,
    required this.type,
  });

  factory TaskProgress.fromJson(Map<String, dynamic> json) {
    return TaskProgress(
      id: json['id'],
      description: json['description'],
      completed: json['completed'] ?? false,
      type: TaskType.values.firstWhere(
        (e) => e.toString() == 'TaskType.${json['type']}',
        orElse: () => TaskType.other,
      ),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'description': description,
      'completed': completed,
      'type': type.toString().split('.').last,
    };
  }
}

enum TaskType {
  firstAppOpen,
  firstLogin,
  firstApplianceLog,
  carbonReduction,
  weeklyLogs,
  weeklyAppOpens,
  applianceVariety,
  dailyAppOpen,
  dailyLog,
  other,
}

class LeagueRequirements {
  static const Map<String, List<Map<String, dynamic>>> requirements = {
    'bronze_to_silver': [
      {'type': TaskType.firstAppOpen, 'description': '第一次打開app'},
      {'type': TaskType.firstLogin, 'description': '第一次登入'},
      {'type': TaskType.firstApplianceLog, 'description': '第一次紀錄家電使用'},
    ],
    'silver_to_gold': [
      {'type': TaskType.carbonReduction, 'description': '排碳減少30公克', 'target': 30},
      {'type': TaskType.weeklyLogs, 'description': '每週紀錄3次或以上', 'target': 3},
      {'type': TaskType.weeklyAppOpens, 'description': '每週app開啟超過5次', 'target': 5},
    ],
    'gold_to_emerald': [
      {'type': TaskType.carbonReduction, 'description': '排碳減少100公克', 'target': 100},
      {'type': TaskType.weeklyLogs, 'description': '每週紀錄5次或以上', 'target': 5},
      {'type': TaskType.applianceVariety, 'description': '紀錄過超過或等於5種的不同家電使用', 'target': 5},
    ],
    'emerald_to_diamond': [
      {'type': TaskType.carbonReduction, 'description': '排碳減少500公克', 'target': 500},
      {'type': TaskType.dailyAppOpen, 'description': 'app每天至少開啟一次'},
      {'type': TaskType.dailyLog, 'description': '每天至少紀錄一次'},
    ],
  };

  static String getNextLeague(String currentLeague) {
    switch (currentLeague) {
      case 'bronze':
        return 'silver';
      case 'silver':
        return 'gold';
      case 'gold':
        return 'emerald';
      case 'emerald':
        return 'diamond';
      case 'diamond':
        return 'diamond'; // Max level
      default:
        return 'bronze';
    }
  }

  static List<Map<String, dynamic>> getTasksForLeague(String currentLeague) {
    switch (currentLeague) {
      case 'bronze':
        return requirements['bronze_to_silver']!;
      case 'silver':
        return requirements['silver_to_gold']!;
      case 'gold':
        return requirements['gold_to_emerald']!;
      case 'emerald':
        return requirements['emerald_to_diamond']!;
      case 'diamond':
        return []; // Max level, no more tasks
      default:
        return requirements['bronze_to_silver']!;
    }
  }
}