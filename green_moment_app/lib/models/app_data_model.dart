import 'carbon_intensity_model.dart';
import 'forecast_data_model.dart';
import 'recommendation_model.dart';

class AppDataModel {
  final DateTime lastUpdated;
  final CarbonIntensityModel currentIntensity;
  final List<ForecastDataModel> forecast;
  final RecommendationModel recommendation;

  const AppDataModel({
    required this.lastUpdated,
    required this.currentIntensity,
    required this.forecast,
    required this.recommendation,
  });

  factory AppDataModel.fromJson(Map<String, dynamic> json) {
    return AppDataModel(
      lastUpdated: DateTime.parse(json['last_updated']),
      currentIntensity: CarbonIntensityModel.fromJson(json['current_intensity']),
      forecast: (json['forecast'] as List)
          .map((item) => ForecastDataModel.fromJson(item))
          .toList(),
      recommendation: RecommendationModel.fromJson(json['recommendation']),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'last_updated': lastUpdated.toIso8601String(),
      'current_intensity': currentIntensity.toJson(),
      'forecast': forecast.map((item) => item.toJson()).toList(),
      'recommendation': recommendation.toJson(),
    };
  }

  String get formattedLastUpdated {
    // Round down to nearest 10 minutes to show X0 time
    final roundedMinute = (lastUpdated.minute ~/ 10) * 10;
    return '${lastUpdated.month}/${lastUpdated.day} ${lastUpdated.hour.toString().padLeft(2, '0')}:${roundedMinute.toString().padLeft(2, '0')} 即時碳強度';
  }
}