class ForecastDataModel {
  final String time;
  final double gco2KWh;
  final String level;

  const ForecastDataModel({
    required this.time,
    required this.gco2KWh,
    required this.level,
  });

  factory ForecastDataModel.fromJson(Map<String, dynamic> json) {
    return ForecastDataModel(
      time: json['time'] as String,
      gco2KWh: json['gCO2_kWh'].toDouble(),
      level: json['level'] as String,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'time': time,
      'gCO2_kWh': gco2KWh,
      'level': level,
    };
  }
}