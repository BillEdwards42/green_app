// Add this factory method to the TaskProgress class in user_progress.dart

class TaskProgress {
  final String id;
  final String description;
  final bool completed;
  final TaskType type;
  final int? targetValue;

  TaskProgress({
    required this.id,
    required this.description,
    required this.completed,
    required this.type,
    this.targetValue,
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
      targetValue: json['target_value'],
    );
  }

  // Add this new factory method for API responses
  factory TaskProgress.fromApi(Map<String, dynamic> json) {
    return TaskProgress(
      id: json['task_id'].toString(),
      description: json['name'],  // API returns 'name' not 'description'
      completed: json['completed'],
      type: _mapTaskType(json['task_type']),
      targetValue: json['target_value'],
    );
  }
  
  static TaskType _mapTaskType(String type) {
    switch (type) {
      case 'firstAppOpen':
        return TaskType.firstAppOpen;
      case 'firstLogin':
        return TaskType.firstLogin;
      case 'firstApplianceLog':
        return TaskType.firstApplianceLog;
      case 'carbonReduction':
        return TaskType.carbonReduction;
      case 'weeklyLogs':
        return TaskType.weeklyLogs;
      case 'weeklyAppOpens':
        return TaskType.weeklyAppOpens;
      case 'applianceVariety':
        return TaskType.applianceVariety;
      case 'dailyAppOpen':
        return TaskType.dailyAppOpen;
      case 'dailyLog':
        return TaskType.dailyLog;
      default:
        return TaskType.other;
    }
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'description': description,
      'completed': completed,
      'type': type.toString().split('.').last,
      'target_value': targetValue,
    };
  }
}