class ApplianceModel {
  final String id;
  final String name;
  final String icon;
  final double kwhPerHour;
  final int sortOrder;

  const ApplianceModel({
    required this.id,
    required this.name,
    required this.icon,
    required this.kwhPerHour,
    required this.sortOrder,
  });

  factory ApplianceModel.fromJson(Map<String, dynamic> json) {
    return ApplianceModel(
      id: json['id'] as String,
      name: json['name'] as String,
      icon: json['icon'] as String,
      kwhPerHour: json['kwhPerHour'].toDouble(),
      sortOrder: json['sortOrder'] as int,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'name': name,
      'icon': icon,
      'kwhPerHour': kwhPerHour,
      'sortOrder': sortOrder,
    };
  }
}