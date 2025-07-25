import 'dart:convert';
import 'package:flutter/services.dart';
import '../models/app_data_model.dart';

class MockDataService {
  static Future<AppDataModel> fetchCarbonData() async {
    // Simulate network delay
    await Future.delayed(const Duration(milliseconds: 1500));
    
    // Load mock data from JSON file
    final mockData = await _loadMockDataFromJson();
    return AppDataModel.fromJson(mockData);
  }

  static Future<Map<String, dynamic>> _loadMockDataFromJson() async {
    final String jsonString = await rootBundle.loadString('assets/mock-data.json');
    return json.decode(jsonString) as Map<String, dynamic>;
  }
}