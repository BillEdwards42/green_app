class CarbonIntensityModel {
  final double gco2KWh;
  final String level;

  const CarbonIntensityModel({
    required this.gco2KWh,
    required this.level,
  });

  factory CarbonIntensityModel.fromJson(Map<String, dynamic> json) {
    return CarbonIntensityModel(
      gco2KWh: json['gCO2_kWh'].toDouble(),
      level: json['level'] as String,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'gCO2_kWh': gco2KWh,
      'level': level,
    };
  }
}