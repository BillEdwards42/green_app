class ApplianceModel {
  final String id;
  final String name;
  final String icon;
  final double kw;
  final int sortOrder;

  const ApplianceModel({
    required this.id,
    required this.name,
    required this.icon,
    required this.kw,
    required this.sortOrder,
  });

  factory ApplianceModel.fromJson(Map<String, dynamic> json) {
    return ApplianceModel(
      id: json['id'] as String,
      name: json['name'] as String,
      icon: json['icon'] as String,
      kw: json['kw'].toDouble(),
      sortOrder: json['sortOrder'] as int,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'name': name,
      'icon': icon,
      'kw': kw,
      'sortOrder': sortOrder,
    };
  }
}