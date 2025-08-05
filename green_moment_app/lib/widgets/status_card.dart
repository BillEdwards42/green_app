import 'package:flutter/material.dart';
import '../constants/app_colors.dart';
import '../models/carbon_intensity_model.dart';
import '../models/recommendation_model.dart';
import 'notification_settings.dart';

class StatusCard extends StatefulWidget {
  final CarbonIntensityModel? intensity;
  final RecommendationModel? recommendation;
  final bool isLoading;
  final VoidCallback onForecastTap;

  const StatusCard({
    super.key,
    this.intensity,
    this.recommendation,
    required this.isLoading,
    required this.onForecastTap,
  });

  @override
  State<StatusCard> createState() => _StatusCardState();
}

class _StatusCardState extends State<StatusCard> {

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      constraints: const BoxConstraints(maxWidth: 360),
      margin: const EdgeInsets.symmetric(horizontal: 0),
      decoration: BoxDecoration(
        color: AppColors.surface,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppColors.border),
        boxShadow: const [
          BoxShadow(
            color: Color(0x26000000),
            blurRadius: 12,
            offset: Offset(0, 4),
          ),
        ],
      ),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Status header
            Row(
              children: [
                // Status icon
                Container(
                  width: 32,
                  height: 32,
                  decoration: BoxDecoration(
                    gradient: _getStatusGradient(widget.intensity?.level, widget.isLoading),
                    borderRadius: BorderRadius.circular(10),
                    boxShadow: [
                      BoxShadow(
                        color: _getStatusShadowColor(widget.intensity?.level, widget.isLoading),
                        blurRadius: 8,
                        offset: const Offset(0, 2),
                      ),
                    ],
                  ),
                  child: const Icon(
                    Icons.eco,
                    color: Colors.white,
                    size: 18,
                  ),
                ),
                
                const SizedBox(width: 12),
                
                // Status info
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        _getStatusTitle(widget.intensity?.level, widget.isLoading),
                        style: const TextStyle(
                          fontSize: 16,
                          fontWeight: FontWeight.w700,
                          color: AppColors.textPrimary,
                          letterSpacing: -0.01,
                        ),
                      ),
                      const SizedBox(height: 2),
                      Text(
                        _getStatusDescription(widget.intensity?.level, widget.isLoading),
                        style: const TextStyle(
                          fontSize: 12,
                          color: AppColors.textSecondary,
                          height: 1.4,
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
            
            // Divider
            Container(
              height: 1,
              margin: const EdgeInsets.symmetric(vertical: 12),
              decoration: const BoxDecoration(
                gradient: LinearGradient(
                  colors: [
                    Colors.transparent,
                    AppColors.border,
                    Colors.transparent,
                  ],
                ),
              ),
            ),
            
            // Action section with enhanced design
            Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // Simple text layout for 最佳用電時段
                Padding(
                  padding: const EdgeInsets.only(left: 4, bottom: 8),
                  child: Text(
                    '最佳用電時段',
                    style: TextStyle(
                      fontSize: 12,
                      color: AppColors.textSecondary,
                      fontWeight: FontWeight.w500,
                    ),
                  ),
                ),
                
                // Time display
                Padding(
                  padding: const EdgeInsets.only(left: 4, bottom: 8),
                  child: widget.isLoading
                      ? Row(
                          children: [
                            SizedBox(
                              width: 12,
                              height: 12,
                              child: CircularProgressIndicator(
                                strokeWidth: 2,
                                valueColor: AlwaysStoppedAnimation<Color>(AppColors.accent),
                              ),
                            ),
                            const SizedBox(width: 6),
                            Text(
                              '更新中...',
                              style: TextStyle(
                                fontSize: 16,
                                fontWeight: FontWeight.w600,
                                color: AppColors.textSecondary,
                              ),
                            ),
                          ],
                        )
                      : Text(
                          widget.recommendation != null
                              ? '${widget.recommendation!.startTime} - ${widget.recommendation!.endTime}'
                              : '-- : -- - -- : --',
                          style: TextStyle(
                            fontSize: 20,
                            fontWeight: FontWeight.w700,
                            color: widget.recommendation != null 
                                ? AppColors.accent
                                : AppColors.textMuted.withValues(alpha: 0.5),
                            letterSpacing: -0.5,
                          ),
                        ),
                ),
                
                const SizedBox(height: 10),
                
                // Notification settings
                const NotificationSettings(),
                
                const SizedBox(height: 10),
                
                // Forecast button
                GestureDetector(
                  onTap: widget.isLoading ? null : widget.onForecastTap,
                  child: Container(
                    height: 38,
                    width: double.infinity,
                    padding: const EdgeInsets.symmetric(horizontal: 16),
                    decoration: BoxDecoration(
                      color: widget.isLoading 
                          ? AppColors.textMuted.withValues(alpha: 0.1)
                          : const Color(0x0AFFFFFF),
                      border: Border.all(
                        color: widget.isLoading 
                            ? AppColors.textMuted.withValues(alpha: 0.2)
                            : const Color(0x14FFFFFF),
                      ),
                      borderRadius: BorderRadius.circular(10),
                    ),
                    child: Center(
                      child: Row(
                        mainAxisAlignment: MainAxisAlignment.center,
                        mainAxisSize: MainAxisSize.min,
                        children: [
                        Text(
                          '查看24小時詳細預測',
                          style: TextStyle(
                            fontSize: 13,
                            fontWeight: FontWeight.w600,
                            color: widget.isLoading 
                                ? AppColors.textMuted
                                : AppColors.textSecondary,
                          ),
                        ),
                        const SizedBox(width: 4),
                        Icon(
                          Icons.arrow_forward_ios,
                          size: 12,
                          color: widget.isLoading 
                              ? AppColors.textMuted
                              : AppColors.textSecondary,
                        ),
                      ],
                      ),
                    ),
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  LinearGradient _getStatusGradient(String? level, bool isLoading) {
    if (isLoading) {
      return const LinearGradient(
        colors: [AppColors.textMuted, AppColors.textMuted],
      );
    }
    
    switch (level) {
      case 'green':
        return const LinearGradient(
          colors: [AppColors.green, Color(0xFF22C55E)],
        );
      case 'yellow':
        return const LinearGradient(
          colors: [AppColors.yellow, Color(0xFFFBBF24)],
        );
      case 'red':
        return const LinearGradient(
          colors: [AppColors.red, Color(0xFFF87171)],
        );
      default:
        return const LinearGradient(
          colors: [AppColors.textMuted, AppColors.textMuted],
        );
    }
  }

  Color _getStatusShadowColor(String? level, bool isLoading) {
    if (isLoading) {
      return AppColors.textMuted.withValues(alpha: 0.3);
    }
    
    switch (level) {
      case 'green':
        return AppColors.green.withValues(alpha: 0.3);
      case 'yellow':
        return AppColors.yellow.withValues(alpha: 0.3);
      case 'red':
        return AppColors.red.withValues(alpha: 0.3);
      default:
        return AppColors.textMuted.withValues(alpha: 0.3);
    }
  }

  String _getStatusTitle(String? level, bool isLoading) {
    if (isLoading) return '載入中';
    
    switch (level) {
      case 'green':
        return '低碳排放時段';
      case 'yellow':
        return '中碳排放時段';
      case 'red':
        return '高碳排放時段';
      default:
        return '載入中';
    }
  }

  String _getStatusDescription(String? level, bool isLoading) {
    if (isLoading) return '正在獲取最新資料...';
    
    switch (level) {
      case 'green':
        return '電網碳強度偏低，建議使用大型家電。';
      case 'yellow':
        return '電網碳密度適中，建議優先使用必要電器。';
      case 'red':
        return '電網碳密度偏高，建議避免使用大型耗電設備。';
      default:
        return '正在載入資料...';
    }
  }
}