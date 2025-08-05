# Flutter Task Migration Guide

This guide explains how to migrate the Flutter app from local task storage to cloud-based API storage.

## Key Changes Required

### 1. Remove Local Task Storage from `user_progress_service.dart`

The current implementation stores tasks in SharedPreferences. This needs to be completely removed.

**Remove these methods:**
- `_createTasksForLeague()` - Tasks come from API
- `_updateTaskProgress()` - Task completion tracked via API
- Task checking logic in `trackAppOpen()` and `trackUsageLog()`

**Update `getUserProgress()` to fetch from API:**

```dart
Future<UserProgress> getUserProgress() async {
  try {
    final response = await _apiService.get('/api/v1/progress/summary');
    
    // Get current tasks from API
    final tasksResponse = await _apiService.get('/api/v1/tasks/my-tasks');
    final tasks = (tasksResponse.data['tasks'] as List)
        .map((json) => TaskProgress.fromApi(json))
        .toList();
    
    return UserProgress(
      currentLeague: response.data['current_league'],
      lastMonthCarbonSaved: response.data['last_month_carbon_saved']?.toDouble(),
      lastCalculationDate: response.data['last_calculation_date'] != null
          ? DateTime.parse(response.data['last_calculation_date'])
          : null,
      currentMonthTasks: tasks,
      lastUpdated: DateTime.now(),
    );
  } catch (e) {
    // Handle error
    throw e;
  }
}
```

### 2. Update Task Completion Logic

Instead of local task checking, use API endpoints:

```dart
class TaskService {
  final ApiService _apiService;
  
  TaskService(this._apiService);
  
  // Complete a specific task
  Future<void> completeTask(int taskId) async {
    await _apiService.post('/api/v1/tasks/complete/$taskId');
  }
  
  // Get current tasks
  Future<List<TaskProgress>> getCurrentTasks() async {
    final response = await _apiService.get('/api/v1/tasks/my-tasks');
    return (response.data as List)
        .map((json) => TaskProgress.fromApi(json))
        .toList();
  }
}
```

### 3. Update TaskProgress Model

Add factory method to create from API response:

```dart
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
  
  factory TaskProgress.fromApi(Map<String, dynamic> json) {
    return TaskProgress(
      id: json['task_id'].toString(),
      description: json['name'],
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
}
```

### 4. Task Completion Triggers

Update these methods to trigger API calls:

**When app opens:**
```dart
Future<void> trackAppOpen() async {
  // Still track metrics locally for UI
  final metrics = await getUsageMetrics();
  // ... update metrics ...
  await saveUsageMetrics(updatedMetrics);
  
  // Check and complete tasks via API
  await _checkAndCompleteTasks();
}

Future<void> _checkAndCompleteTasks() async {
  final tasks = await TaskService(_apiService).getCurrentTasks();
  
  for (final task in tasks) {
    if (!task.completed) {
      bool shouldComplete = false;
      
      switch (task.type) {
        case TaskType.firstAppOpen:
          shouldComplete = true; // App is open
          break;
        case TaskType.weeklyAppOpens:
          final metrics = await getUsageMetrics();
          shouldComplete = metrics.weeklyAppOpens >= (task.targetValue ?? 0);
          break;
        // ... other task types
      }
      
      if (shouldComplete) {
        await TaskService(_apiService).completeTask(int.parse(task.id));
      }
    }
  }
}
```

### 5. Remove Monthly Reset Logic

Remove `checkMonthlyUpdate()` - the backend handles this automatically.

### 6. Update Dashboard Screen

Fetch fresh data from API on screen load:

```dart
Future<void> _loadUserProgress() async {
  try {
    setState(() => _isLoading = true);
    
    // Get fresh data from API
    final progress = await _progressService.getUserProgress();
    
    setState(() {
      _userProgress = progress;
      _isLoading = false;
    });
  } catch (e) {
    setState(() => _isLoading = false);
    // Handle error
  }
}
```

## Migration Steps

1. **Run database migration** on backend:
   ```bash
   alembic upgrade head
   python3 scripts/seed_league_tasks.py
   ```

2. **Update Flutter code** as described above

3. **Test thoroughly**:
   - Task loading from API
   - Task completion
   - League progression
   - Carbon tracking

## Important Notes

- Tasks are now league-specific and assigned by the backend
- Task completion is tracked in real-time via API
- Monthly resets happen automatically on the backend
- Users always see their last month's carbon saved
- No more local/cloud sync issues!

## API Endpoints Summary

- `GET /api/v1/tasks/my-tasks` - Get user's current tasks
- `POST /api/v1/tasks/complete/{task_id}` - Mark task complete
- `GET /api/v1/progress/summary` - Get overall progress/league info