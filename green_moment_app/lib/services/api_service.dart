import 'dart:convert';
import 'package:http/http.dart' as http;
import '../config/api_config.dart';
import '../models/app_data_model.dart';
import '../models/carbon_intensity_model.dart';
import '../models/forecast_data_model.dart';
import '../models/recommendation_model.dart';
import 'auth_service.dart';

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

  // Instance methods for the updated user_progress_service
  final AuthService _authService = AuthService();

  // Generic GET request
  Future<ApiResponse> get(String endpoint) async {
    try {
      final token = _authService.token;
      final response = await http.get(
        Uri.parse('${ApiConfig.baseUrl}$endpoint'),
        headers: _authHeaders(token),
      ).timeout(ApiConfig.timeout);

      if (response.statusCode == 200) {
        return ApiResponse(
          data: json.decode(response.body),
          statusCode: response.statusCode,
        );
      } else if (response.statusCode == 401) {
        print('API GET: Token expired or invalid. Status: 401');
        throw Exception('GET $endpoint failed: 401 Unauthorized - Please login again');
      } else {
        print('API GET: Unexpected status code: ${response.statusCode}');
        print('Response body: ${response.body}');
        throw Exception('GET $endpoint failed: ${response.statusCode}');
      }
    } catch (e) {
      print('API GET Error: $e');
      throw e;
    }
  }

  // Generic POST request
  Future<ApiResponse> post(String endpoint, {Map<String, dynamic>? body}) async {
    try {
      final token = _authService.token;
      final response = await http.post(
        Uri.parse('${ApiConfig.baseUrl}$endpoint'),
        headers: _authHeaders(token),
        body: body != null ? json.encode(body) : null,
      ).timeout(ApiConfig.timeout);

      if (response.statusCode == 200 || response.statusCode == 201) {
        return ApiResponse(
          data: response.body.isNotEmpty ? json.decode(response.body) : null,
          statusCode: response.statusCode,
        );
      } else {
        throw Exception('POST $endpoint failed: ${response.statusCode}');
      }
    } catch (e) {
      print('API POST Error: $e');
      throw e;
    }
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
    required String applianceType,
    required DateTime startTime,
    required int durationMinutes,
    required String token,
  }) async {
    try {
      final response = await http.post(
        Uri.parse('${ApiConfig.baseUrl}${ApiConfig.choresLog}'),
        headers: _authHeaders(token),
        body: json.encode({
          'appliance_type': applianceType,
          'start_time': startTime.toIso8601String(),
          'duration_minutes': durationMinutes,
        }),
      ).timeout(ApiConfig.timeout);

      if (response.statusCode == 200) {
        return json.decode(response.body);
      } else {
        print('Chore log failed - Status: ${response.statusCode}');
        print('Response body: ${response.body}');
        throw Exception('Failed to log chore: ${response.body}');
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

// Simple response wrapper for instance methods
class ApiResponse {
  final dynamic data;
  final int statusCode;

  ApiResponse({
    required this.data,
    required this.statusCode,
  });
}