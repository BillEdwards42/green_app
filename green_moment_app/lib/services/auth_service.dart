import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import '../config/api_config.dart';
import 'user_progress_service.dart';
import 'notification_service.dart';

class AuthService {
  static const String _tokenKey = 'auth_token';
  static const String _userIdKey = 'user_id';
  static const String _usernameKey = 'username';
  static const String _isAnonymousKey = 'is_anonymous';
  static const String _emailKey = 'email';
  static const String _createdAtKey = 'created_at';
  static const String _currentLeagueKey = 'current_league';

  // Singleton pattern
  static final AuthService _instance = AuthService._internal();
  factory AuthService() => _instance;
  AuthService._internal();

  String? _token;
  int? _userId;
  String? _username;
  bool _isAnonymous = false;
  String? _email;
  String? _createdAt;
  String? _currentLeague;
  String? _lastErrorMessage;

  // Getters
  bool get isAuthenticated => _token != null;
  String? get token => _token;
  int? get userId => _userId;
  String? get username => _username;
  bool get isAnonymous => _isAnonymous;
  String? get email => _email;
  String? get lastErrorMessage => _lastErrorMessage;
  
  Map<String, dynamic>? get currentUser => isAuthenticated ? {
    'user_id': _userId,
    'username': _username,
    'email': _email,
    'is_anonymous': _isAnonymous,
    'created_at': _createdAt,
    'current_league': _currentLeague,
  } : null;

  /// Initialize auth service - call this at app startup
  Future<void> initialize() async {
    print('🔄 AuthService.initialize() called');
    final prefs = await SharedPreferences.getInstance();
    _token = prefs.getString(_tokenKey);
    _userId = prefs.getInt(_userIdKey);
    _username = prefs.getString(_usernameKey);
    _isAnonymous = prefs.getBool(_isAnonymousKey) ?? false;
    _email = prefs.getString(_emailKey);
    _createdAt = prefs.getString(_createdAtKey);
    _currentLeague = prefs.getString(_currentLeagueKey);
    
    print('🔑 Loaded token from prefs: ${_token?.substring(0, 20)}...');
    print('👤 User ID: $_userId, Username: $_username');

    // Verify token if exists
    if (_token != null) {
      print('🔍 Verifying token...');
      final isValid = await _verifyToken();
      print('✅ Token valid: $isValid');
      if (!isValid) {
        print('❌ Token invalid, logging out');
        await signOut();
      } else {
        // Refresh user profile data
        await getUserProfile();
      }
    }
  }

  /// Google Sign-In
  Future<bool> signInWithGoogle(String googleToken, {String? username}) async {
    _lastErrorMessage = null; // Clear previous error
    
    try {
      print('🔐 Attempting Google sign-in...');
      print('🔗 API URL: ${ApiConfig.baseUrl}/auth/google');
      // Prepare request body
      final requestBody = <String, dynamic>{
        'google_token': googleToken,
      };
      
      // Only add username if it's not null and not empty
      if (username != null && username.trim().isNotEmpty) {
        requestBody['username'] = username.trim();
      }
      
      print('📝 Request body: ${jsonEncode(requestBody)}');
      
      final response = await http.post(
        Uri.parse('${ApiConfig.baseUrl}/auth/google'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode(requestBody),
      ).timeout(const Duration(seconds: 30));

      print('📡 Response status: ${response.statusCode}');
      print('📄 Response body: ${response.body}');

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        print('✅ Sign-in successful, saving auth data...');
        await _saveAuthData(
          token: data['access_token'],
          userId: data['user_id'],
          username: data['username'],
          isAnonymous: data['is_anonymous'],
        );
        
        // Load notification settings and refresh FCM token after successful sign-in
        try {
          final notificationService = NotificationService();
          await notificationService.loadSettingsFromBackend();
          await notificationService.refreshToken();
        } catch (e) {
          print('Failed to load notification settings: $e');
        }
        
        return true;
      } else {
        try {
          final errorData = jsonDecode(response.body);
          _lastErrorMessage = errorData['detail'] ?? '登入失敗';
          print('❌ Google sign-in failed: ${_lastErrorMessage}');
        } catch (jsonError) {
          _lastErrorMessage = 'HTTP ${response.statusCode}: 服務器錯誤';
          print('❌ Google sign-in failed with status ${response.statusCode}: ${response.body}');
        }
        return false;
      }
    } catch (e) {
      _lastErrorMessage = '網絡連線失敗，請檢查網絡設定';
      print('💥 Google sign-in error: $e');
      return false;
    }
  }

  /// Anonymous Sign-In
  Future<bool> signInAnonymously(String username) async {
    _lastErrorMessage = null; // Clear previous error
    
    try {
      print('👤 Attempting anonymous sign-in...');
      print('🔗 API URL: ${ApiConfig.baseUrl}/auth/anonymous');
      print('📝 Request body: {"username": "$username"}');
      
      final response = await http.post(
        Uri.parse('${ApiConfig.baseUrl}/auth/anonymous'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({'username': username}),
      ).timeout(const Duration(seconds: 10));

      print('📡 Response status: ${response.statusCode}');
      print('📄 Response body: ${response.body}');

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        print('✅ Anonymous sign-in successful, saving auth data...');
        await _saveAuthData(
          token: data['access_token'],
          userId: data['user_id'],
          username: data['username'],
          isAnonymous: data['is_anonymous'],
        );
        
        // Load notification settings and refresh FCM token after successful sign-in
        try {
          final notificationService = NotificationService();
          await notificationService.loadSettingsFromBackend();
          await notificationService.refreshToken();
        } catch (e) {
          print('Failed to load notification settings: $e');
        }
        
        return true;
      } else {
        try {
          final errorData = jsonDecode(response.body);
          _lastErrorMessage = errorData['detail'] ?? '建立帳戶失敗';
          print('❌ Anonymous sign-in failed: ${_lastErrorMessage}');
        } catch (jsonError) {
          _lastErrorMessage = 'HTTP ${response.statusCode}: 服務器錯誤';
          print('❌ Anonymous sign-in failed with status ${response.statusCode}: ${response.body}');
        }
        return false;
      }
    } catch (e) {
      _lastErrorMessage = '網絡連線失敗，請檢查網絡設定';
      print('💥 Anonymous sign-in error: $e');
      return false;
    }
  }

  /// Verify current token
  Future<bool> _verifyToken() async {
    if (_token == null) return false;

    try {
      final response = await http.post(
        Uri.parse('${ApiConfig.baseUrl}/auth/verify'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({'token': _token}),
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        print('🔍 Token verify response: $data');
        // The response has 'valid' at the root level
        return data['valid'] == true;
      }
      return false;
    } catch (e) {
      print('Token verification error: $e');
      return false;
    }
  }

  /// Update username
  Future<bool> updateUsername(String newUsername) async {
    if (_token == null) return false;

    try {
      final response = await http.put(
        Uri.parse('${ApiConfig.baseUrl}/users/username'),
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer $_token',
        },
        body: jsonEncode({'username': newUsername}),
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        if (data['success'] == true) {
          _username = data['username'];
          final prefs = await SharedPreferences.getInstance();
          await prefs.setString(_usernameKey, _username!);
          return true;
        }
      }
      return false;
    } catch (e) {
      print('Username update error: \$e');
      return false;
    }
  }

  /// Get user profile
  Future<Map<String, dynamic>?> getUserProfile() async {
    if (_token == null) return null;

    try {
      final response = await http.get(
        Uri.parse('${ApiConfig.baseUrl}${ApiConfig.userProfile}'),
        headers: {'Authorization': 'Bearer $_token'},
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        
        // Update stored user data
        _email = data['email'];
        _createdAt = data['created_at'];
        _currentLeague = data['current_league'];
        
        // Save to preferences
        final prefs = await SharedPreferences.getInstance();
        if (_email != null) await prefs.setString(_emailKey, _email!);
        if (_createdAt != null) await prefs.setString(_createdAtKey, _createdAt!);
        if (_currentLeague != null) await prefs.setString(_currentLeagueKey, _currentLeague!);
        
        return data;
      }
      return null;
    } catch (e) {
      print('Get profile error: $e');
      return null;
    }
  }

  /// Sign out
  Future<void> signOut() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_tokenKey);
    await prefs.remove(_userIdKey);
    await prefs.remove(_usernameKey);
    await prefs.remove(_isAnonymousKey);
    await prefs.remove(_emailKey);
    await prefs.remove(_createdAtKey);
    await prefs.remove(_currentLeagueKey);

    _token = null;
    _userId = null;
    _username = null;
    _isAnonymous = false;
    _email = null;
    _createdAt = null;
    _currentLeague = null;
    
    // Clear all user progress data when logging out
    final progressService = UserProgressService();
    await progressService.clearAllProgress();
  }
  
  /// Delete account
  Future<bool> deleteAccount() async {
    if (_token == null) return false;
    
    try {
      final response = await http.delete(
        Uri.parse('${ApiConfig.baseUrl}/users/me'),
        headers: {'Authorization': 'Bearer $_token'},
      );
      
      if (response.statusCode == 200 || response.statusCode == 204) {
        // Account deleted successfully, sign out locally
        await signOut();
        return true;
      }
      return false;
    } catch (e) {
      print('Delete account error: $e');
      return false;
    }
  }

  /// Save authentication data
  Future<void> _saveAuthData({
    required String token,
    required int userId,
    required String username,
    required bool isAnonymous,
  }) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_tokenKey, token);
    await prefs.setInt(_userIdKey, userId);
    await prefs.setString(_usernameKey, username);
    await prefs.setBool(_isAnonymousKey, isAnonymous);

    _token = token;
    _userId = userId;
    _username = username;
    _isAnonymous = isAnonymous;
    
    print('💾 Auth data saved - Token: ${token.substring(0, 20)}..., UserId: $userId');
  }

  /// Get authorization header for API calls
  Map<String, String> getAuthHeaders() {
    if (_token == null) return {};
    return {'Authorization': 'Bearer $_token'};
  }
}