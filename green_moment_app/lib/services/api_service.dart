import 'dart:convert';
import 'package:http/http.dart' as http;
import '../config/api_config.dart';
import '../models/app_data_model.dart';
import '../models/carbon_intensity_model.dart';
import '../models/forecast_data_model.dart';
import '../models/recommendation_model.dart';

class ApiService {
  static final Map<String, String> _headers = {
    'Content-Type': 'application/json',
  };

  // For authenticated requests
  static Map<String, String> _authHeaders(String? token) {
    return {
      ..._headers,
      if (token != null) 'Authorization': 'Bearer $token',
    };
  }

  /// Fetch current carbon data and forecast
  static Future<AppDataModel> fetchCarbonData() async {
    try {
      // First, try to get the latest data which includes current and forecast
      final response = await http.get(
        Uri.parse('${ApiConfig.baseUrl}${ApiConfig.carbonLatest}'),
        headers: _headers,
      ).timeout(ApiConfig.timeout);

      if (response.statusCode == 200) {
        final data = json.decode(response.body);
        return AppDataModel.fromJson(data);
      } else {
        print('API Error: Status ${response.statusCode}');
        throw Exception('Failed to fetch carbon data: Status ${response.statusCode}');
      }
    } catch (e) {
      print('API Error: $e');
      throw Exception('Failed to connect to server: $e');
    }
  }

  /// Anonymous authentication
  static Future<Map<String, dynamic>> authenticateAnonymous() async {
    try {
      final response = await http.post(
        Uri.parse('${ApiConfig.baseUrl}${ApiConfig.authAnonymous}'),
        headers: _headers,
      ).timeout(ApiConfig.timeout);

      if (response.statusCode == 200) {
        return json.decode(response.body);
      } else {
        throw Exception('Failed to authenticate');
      }
    } catch (e) {
      print('Auth Error: $e');
      // Return mock token for development
      return {
        'access_token': 'mock_anonymous_token',
        'user_id': 'anonymous_user_${DateTime.now().millisecondsSinceEpoch}',
      };
    }
  }

  /// Google authentication
  static Future<Map<String, dynamic>> authenticateGoogle(String googleToken) async {
    try {
      final response = await http.post(
        Uri.parse('${ApiConfig.baseUrl}${ApiConfig.authGoogle}'),
        headers: _headers,
        body: json.encode({'token': googleToken}),
      ).timeout(ApiConfig.timeout);

      if (response.statusCode == 200) {
        return json.decode(response.body);
      } else {
        throw Exception('Failed to authenticate with Google');
      }
    } catch (e) {
      print('Google Auth Error: $e');
      throw e;
    }
  }

  /// Estimate carbon savings for a chore
  static Future<Map<String, dynamic>> estimateCarbon({
    required String applianceId,
    required DateTime startTime,
    required double durationHours,
    String? token,
  }) async {
    try {
      final response = await http.post(
        Uri.parse('${ApiConfig.baseUrl}${ApiConfig.choresEstimate}'),
        headers: _authHeaders(token),
        body: json.encode({
          'appliance_id': applianceId,
          'start_time': startTime.toIso8601String(),
          'duration_hours': durationHours,
        }),
      ).timeout(ApiConfig.timeout);

      if (response.statusCode == 200) {
        return json.decode(response.body);
      } else {
        throw Exception('Failed to estimate carbon savings');
      }
    } catch (e) {
      print('Estimate Error: $e');
      // Return mock estimation for development
      return {
        'carbon_saved': durationHours * 0.35 * 100, // Mock calculation
        'carbon_emitted': durationHours * 0.35 * 300,
        'peak_carbon_emitted': durationHours * 0.35 * 500,
      };
    }
  }

  /// Log a completed chore
  static Future<Map<String, dynamic>> logChore({
    required String applianceId,
    required DateTime startTime,
    required double durationHours,
    required String token,
  }) async {
    try {
      final response = await http.post(
        Uri.parse('${ApiConfig.baseUrl}${ApiConfig.choresLog}'),
        headers: _authHeaders(token),
        body: json.encode({
          'appliance_id': applianceId,
          'start_time': startTime.toIso8601String(),
          'duration_hours': durationHours,
        }),
      ).timeout(ApiConfig.timeout);

      if (response.statusCode == 200) {
        return json.decode(response.body);
      } else {
        throw Exception('Failed to log chore');
      }
    } catch (e) {
      print('Log Chore Error: $e');
      throw e;
    }
  }

  /// Get user progress summary
  static Future<Map<String, dynamic>> getProgressSummary(String token) async {
    try {
      final response = await http.get(
        Uri.parse('${ApiConfig.baseUrl}${ApiConfig.progressSummary}'),
        headers: _authHeaders(token),
      ).timeout(ApiConfig.timeout);

      if (response.statusCode == 200) {
        return json.decode(response.body);
      } else {
        throw Exception('Failed to get progress summary');
      }
    } catch (e) {
      print('Progress Error: $e');
      // Return mock progress for development
      return {
        'total_carbon_saved': 15.5,
        'chores_count': 23,
        'current_league': 'silver',
        'points': 155,
        'days_active': 14,
      };
    }
  }
}