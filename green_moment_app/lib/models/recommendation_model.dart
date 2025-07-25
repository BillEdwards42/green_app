class RecommendationModel {
  final String message;
  final String startTime;
  final String endTime;

  const RecommendationModel({
    required this.message,
    required this.startTime,
    required this.endTime,
  });

  factory RecommendationModel.fromJson(Map<String, dynamic> json) {
    return RecommendationModel(
      message: json['message'] as String,
      startTime: json['start_time'] as String,
      endTime: json['end_time'] as String,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'message': message,
      'start_time': startTime,
      'end_time': endTime,
    };
  }
}