# Task API Integration Guide

This guide explains how to integrate the new task API endpoints in your Flutter app for cloud-only task storage.

## Overview

Previously, tasks were stored locally in the Flutter app, causing sync issues with the backend. Now, all task data should be stored in the cloud database and accessed via API endpoints.

## Required Changes in Flutter App

### 1. Remove Local Task Storage

Remove any code that stores tasks in:
- SharedPreferences
- Local SQLite database
- Any other local storage mechanism

### 2. API Endpoints

Base URL: `https://your-api-domain.com/api/v1`

#### Get User's Tasks
```dart
GET /tasks/my-tasks
Authorization: Bearer {token}

Response:
[
  {
    "id": 1,
    "task_id": 1,
    "name": "完成5次家電使用記錄",
    "description": "記錄5次在綠色時段使用家電的行為",
    "points": 100,
    "completed": false,
    "completed_at": null,
    "points_earned": 0
  },
  // ... more tasks
]
```

#### Complete a Task
```dart
POST /tasks/complete/{task_id}
Authorization: Bearer {token}

Response:
{
  "message": "Task completed successfully",
  "points_earned": 100,
  "total_tasks_completed": 1
}
```

#### Uncomplete a Task (for testing)
```dart
POST /tasks/uncomplete/{task_id}
Authorization: Bearer {token}

Response:
{
  "message": "Task marked as incomplete",
  "total_tasks_completed": 0
}
```

### 3. Flutter Implementation Example

```dart
class TaskService {
  final ApiService _apiService;
  
  Future<List<UserTask>> getMyTasks() async {
    final response = await _apiService.get('/tasks/my-tasks');
    return (response.data as List)
        .map((json) => UserTask.fromJson(json))
        .toList();
  }
  
  Future<void> completeTask(int taskId) async {
    await _apiService.post('/tasks/complete/$taskId');
    // Refresh task list after completion
    await getMyTasks();
  }
  
  Future<void> uncompleteTask(int taskId) async {
    await _apiService.post('/tasks/uncomplete/$taskId');
    // Refresh task list
    await getMyTasks();
  }
}
```

### 4. Task Model

```dart
class UserTask {
  final int id;
  final int taskId;
  final String name;
  final String description;
  final int points;
  final bool completed;
  final DateTime? completedAt;
  final int pointsEarned;
  
  UserTask({
    required this.id,
    required this.taskId,
    required this.name,
    required this.description,
    required this.points,
    required this.completed,
    this.completedAt,
    required this.pointsEarned,
  });
  
  factory UserTask.fromJson(Map<String, dynamic> json) {
    return UserTask(
      id: json['id'],
      taskId: json['task_id'],
      name: json['name'],
      description: json['description'],
      points: json['points'],
      completed: json['completed'],
      completedAt: json['completed_at'] != null
          ? DateTime.parse(json['completed_at'])
          : null,
      pointsEarned: json['points_earned'],
    );
  }
}
```

### 5. UI Updates

1. **Remove local task completion logic** - Don't update task state locally
2. **Always fetch from API** - Call `getMyTasks()` when entering the tasks screen
3. **Show loading states** - While API calls are in progress
4. **Handle errors** - Network failures, unauthorized access, etc.

### 6. Task Types

The system includes 3 standard tasks that reset monthly:

1. **完成5次家電使用記錄** (100 points)
   - Record 5 appliance usage sessions during green periods
   
2. **累積減碳1公斤** (150 points)
   - Accumulate 1kg of carbon savings through smart electricity usage
   
3. **連續7天查看碳密度預報** (100 points)
   - Open the app to check carbon intensity forecast for 7 consecutive days

### 7. Important Notes

- Tasks are automatically created for each user when they first access `/tasks/my-tasks`
- Tasks reset on the 1st of each month
- Task completion affects league promotion
- The backend tracks `current_month_tasks_completed` on the User model
- All 3 tasks must be completed to qualify for league promotion

## Migration Steps

1. **Run the cleanup script** on the backend:
   ```bash
   python3 scripts/cleanup_and_migrate_tasks.py
   ```

2. **Update Flutter app** to use API endpoints instead of local storage

3. **Test thoroughly**:
   - Task loading
   - Task completion
   - Monthly reset
   - League promotion eligibility

## Error Handling

Handle these common scenarios:
- No tasks exist (backend will auto-create them)
- Network failures
- Task already completed
- Invalid task ID

## Questions?

If you encounter any issues during integration, check:
1. API authentication is working
2. Tasks exist in the database (run `seed_tasks.py` if needed)
3. User has UserTask entries for the current month