# Flutter App Update Notes

## Changes After Database Migration

The backend now stores chores with simplified fields. The Flutter app should continue to work as-is because:

1. **API Response Structure Unchanged** (mostly):
   - `duration_hours` changed to `duration_minutes` in responses
   - All other fields in request/response remain the same

2. **No Carbon Calculations in Real-Time**:
   - The app can still show immediate feedback using local calculations
   - Actual carbon savings will be calculated monthly on the backend
   - Consider showing "Estimated Savings" label in the UI

## Required Flutter Updates:

1. **Update API Service** (`lib/services/api_service.dart`):
   ```dart
   // In logChore method, change line ~101:
   // OLD:
   'duration_hours': durationHours,
   
   // NEW:
   'duration_minutes': (durationHours * 60).round(),
   ```

   Or update the method signature to accept minutes:
   ```dart
   static Future<Map<String, dynamic>> logChore({
     required String applianceType,
     required DateTime startTime,
     required int durationMinutes,  // Changed from double durationHours
   }) async {
     // ...
     body: jsonEncode({
       'appliance_type': applianceType,
       'start_time': startTime.toIso8601String(),
       'duration_minutes': durationMinutes,
     }),
   }
   ```

2. **Update Logger Screen** (`lib/screens/logger_screen.dart`):
   - When calling logChore, pass duration in minutes
   - Local calculations can remain unchanged

3. **Update Response Models** (if using strongly typed models):
   ```dart
   // In chore response model
   final int durationMinutes; // Changed from double durationHours
   ```

3. **Add Monthly Summary View** (future feature):
   - New endpoint will be available: `/api/v1/progress/monthly-summary`
   - Shows actual carbon saved after monthly calculation
   - Compare with real-time estimates

## Testing After Migration:

1. Log a new chore - should work normally
2. View chore history - check duration display
3. Verify all appliance types still work
4. Check that start/end times are correct

The migration is backward-compatible for the core functionality!