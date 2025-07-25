import 'dart:convert';
import 'package:http/http.dart' as http;

class NetworkTestService {
  /// Test network connectivity to different endpoints
  static Future<void> testConnectivity() async {
    final endpoints = [
      'http://10.0.2.2:8000/api/v1/auth/google',
      'http://192.168.0.199:8000/api/v1/auth/google', // Your actual IP
      'http://127.0.0.1:8000/api/v1/auth/google',
      'https://httpbin.org/get', // External test to verify internet works
    ];

    for (final endpoint in endpoints) {
      print('🔗 Testing: $endpoint');
      try {
        final response = await http.post(
          Uri.parse(endpoint),
          headers: {'Content-Type': 'application/json'},
          body: jsonEncode({'google_token': 'test'}),
        ).timeout(const Duration(seconds: 5));
        
        print('✅ Success: ${response.statusCode}');
      } catch (e) {
        print('❌ Failed: $e');
      }
      print('---');
    }
  }
}