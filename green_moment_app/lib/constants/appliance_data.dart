import '../models/appliance_model.dart';

class ApplianceData {
  static const List<ApplianceModel> appliances = [
    // Sorted by kWh descending (except EV charging at bottom)
    ApplianceModel(
      id: 'microwave',
      name: '微波爐',
      icon: '🍲',
      kw: 1.2,
      sortOrder: 1,
    ),
    ApplianceModel(
      id: 'dryer',
      name: '烘衣機',
      icon: '👔',
      kw: 1.2,
      sortOrder: 2,
    ),
    ApplianceModel(
      id: 'air_conditioner',
      name: '冷氣機',
      icon: '❄️',
      kw: 0.9,
      sortOrder: 3,
    ),
    ApplianceModel(
      id: 'washing_machine',
      name: '洗衣機',
      icon: '🧺',
      kw: 0.42,
      sortOrder: 4,
    ),
    ApplianceModel(
      id: 'tv',
      name: '電視',
      icon: '📺',
      kw: 0.14,
      sortOrder: 5,
    ),
    ApplianceModel(
      id: 'fan',
      name: '電扇',
      icon: '💨',
      kw: 0.06,
      sortOrder: 6,
    ),
    // EV charging always at bottom
    ApplianceModel(
      id: 'ev_fast_charge',
      name: '電動車快充',
      icon: '⚡',
      kw: 50.0,
      sortOrder: 100,
    ),
    ApplianceModel(
      id: 'ev_slow_charge',
      name: '電動車慢充',
      icon: '🔌',
      kw: 9.0,
      sortOrder: 101,
    ),
  ];

  static List<ApplianceModel> getSortedAppliances() {
    return List<ApplianceModel>.from(appliances)
      ..sort((a, b) => a.sortOrder.compareTo(b.sortOrder));
  }

  static ApplianceModel? getApplianceById(String id) {
    try {
      return appliances.firstWhere((appliance) => appliance.id == id);
    } catch (e) {
      return null;
    }
  }
}