class CarbonIntensityModel {
  final double gco2KWh;
  final String level;

  const CarbonIntensityModel({
    required this.gco2KWh,
    required this.level,
  });

  factory CarbonIntensityModel.fromJson(Map<String, dynamic> json) {
    return CarbonIntensityModel(
      gco2KWh: (json['gCO2_kWh'] ?? json['gCO2e_kWh'] ?? 0).toDouble(),
      level: json['level'] as String,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'gCO2e_kWh': gco2KWh,
      'level': level,
    };
  }
}