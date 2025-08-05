import 'package:flutter/material.dart';
import 'dart:math' as math;
import '../constants/app_colors.dart';
import '../models/forecast_data_model.dart';

class ForecastChart extends StatefulWidget {
  final List<ForecastDataModel> forecastData;
  final double currentValue;

  const ForecastChart({
    super.key,
    required this.forecastData,
    required this.currentValue,
  });

  @override
  State<ForecastChart> createState() => _ForecastChartState();
}

class _ForecastChartState extends State<ForecastChart>
    with SingleTickerProviderStateMixin {
  late AnimationController _animationController;
  late ScrollController _scrollController;
  late Animation<double> _animation;

  @override
  void initState() {
    super.initState();
    
    _animationController = AnimationController(
      duration: const Duration(milliseconds: 1200),
      vsync: this,
    );
    
    _scrollController = ScrollController();
    
    _animation = Tween<double>(begin: 0.0, end: 1.0).animate(
      CurvedAnimation(parent: _animationController, curve: Curves.easeOut),
    );
    
    _animationController.forward();
    
    // Removed auto-scroll to keep chart at the left edge
  }

  @override
  void dispose() {
    _animationController.dispose();
    _scrollController.dispose();
    super.dispose();
  }


  @override
  Widget build(BuildContext context) {
    if (widget.forecastData.isEmpty) {
      return const Center(
        child: Text(
          'No forecast data available',
          style: TextStyle(color: AppColors.textSecondary),
        ),
      );
    }

    // Set fixed range for y-axis
    const double minValue = 450.0;
    const double maxValue = 600.0;
    const double range = maxValue - minValue;
    
    return Column(
      children: [
        // Current status
        Container(
          width: double.infinity,
          padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 16),
          margin: const EdgeInsets.only(bottom: 12),
          decoration: BoxDecoration(
            color: AppColors.surface,
            borderRadius: BorderRadius.circular(8),
            border: Border.all(color: AppColors.border),
          ),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Text(
                '${DateTime.now().month}/${DateTime.now().day} ${DateTime.now().hour.toString().padLeft(2, '0')}:${DateTime.now().minute.toString().padLeft(2, '0')}：',
                style: const TextStyle(
                  fontSize: 14,
                  color: AppColors.textSecondary,
                ),
              ),
              Text(
                '${widget.currentValue.round()}',
                style: const TextStyle(
                  fontSize: 14,
                  fontWeight: FontWeight.w700,
                  color: AppColors.textPrimary,
                ),
              ),
              const Text(
                ' gCO₂/kWh',
                style: TextStyle(
                  fontSize: 14,
                  color: AppColors.textSecondary,
                ),
              ),
            ],
          ),
        ),
        
        // Chart
        Expanded(
          child: Container(
            decoration: BoxDecoration(
              border: Border.all(color: AppColors.border),
              borderRadius: BorderRadius.circular(8),
            ),
            child: Row(
              children: [
                // Y-axis
                Container(
                  width: 40,
                  decoration: const BoxDecoration(
                    border: Border(right: BorderSide(color: AppColors.border)),
                  ),
                  child: Padding(
                    padding: const EdgeInsets.only(top: 40, bottom: 42.8),
                    child: Column(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        _buildYAxisLabel('600'),
                        _buildYAxisLabel('550'),
                        _buildYAxisLabel('500'),
                        _buildYAxisLabel('450'),
                      ],
                    ),
                  ),
                ),
                
                // Chart bars
                Expanded(
                  child: SingleChildScrollView(
                    controller: _scrollController,
                    scrollDirection: Axis.horizontal,
                    child: AnimatedBuilder(
                      animation: _animation,
                      builder: (context, child) {
                        return LayoutBuilder(
                          builder: (context, constraints) {
                            // Calculate available height for bars (subtract padding)
                            final chartHeight = constraints.maxHeight - 80; // 40 top + 40 bottom padding
                            
                            return Container(
                              height: double.infinity,
                              padding: const EdgeInsets.symmetric(vertical: 40, horizontal: 8),
                              child: Row(
                                crossAxisAlignment: CrossAxisAlignment.end,
                                children: widget.forecastData.asMap().entries.map((entry) {
                                  final index = entry.key;
                                  final data = entry.value;
                                  final isCurrentHour = _isCurrentHour(data.time);
                                  
                                  return AnimatedContainer(
                                    duration: Duration(milliseconds: 50 + (index * 15)),
                                    margin: const EdgeInsets.symmetric(horizontal: 1.5),
                                    child: Column(
                                      mainAxisAlignment: MainAxisAlignment.end,
                                      children: [
                                        // Bar
                                        Container(
                                          width: 14,
                                          height: math.max(0, ((data.gco2KWh - minValue) / range) * chartHeight * _animation.value),
                                      decoration: BoxDecoration(
                                        gradient: _getBarGradient(data.level),
                                        borderRadius: const BorderRadius.vertical(top: Radius.circular(6)),
                                        boxShadow: isCurrentHour ? [
                                          BoxShadow(
                                            color: AppColors.accent.withValues(alpha: 0.4),
                                            blurRadius: 8,
                                            offset: const Offset(0, 0),
                                          ),
                                        ] : [
                                          const BoxShadow(
                                            color: Color(0x33000000),
                                            blurRadius: 2,
                                            offset: Offset(0, -2),
                                          ),
                                        ],
                                      ),
                                    ),
                                    
                                    const SizedBox(height: 8),
                                    
                                    // Time label (only show on the hour)
                                    if (data.time.endsWith(':00'))
                                      Container(
                                        constraints: const BoxConstraints(minHeight: 16),
                                        child: Text(
                                          data.time.substring(0, 2),
                                          style: TextStyle(
                                            fontSize: 10,
                                            color: isCurrentHour 
                                                ? AppColors.accent 
                                                : AppColors.textMuted,
                                            fontWeight: isCurrentHour 
                                                ? FontWeight.w600 
                                                : FontWeight.w500,
                                          ),
                                        ),
                                      )
                                    else
                                      const SizedBox(height: 16),
                                  ],
                                ),
                              );
                            }).toList(),
                              ),
                            );
                          },
                        );
                      },
                    ),
                  ),
                ),
              ],
            ),
          ),
        ),
        
        // Legend
        Container(
          margin: const EdgeInsets.only(top: 16),
          padding: const EdgeInsets.all(12),
          decoration: BoxDecoration(
            color: AppColors.surface,
            borderRadius: BorderRadius.circular(12),
            border: Border.all(color: AppColors.border),
          ),
          child: const Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              _LegendItem(color: AppColors.green, label: '低碳排'),
              SizedBox(width: 24),
              _LegendItem(color: AppColors.yellow, label: '中碳排'),
              SizedBox(width: 24),
              _LegendItem(color: AppColors.red, label: '高碳排'),
            ],
          ),
        ),
      ],
    );
  }

  Widget _buildYAxisLabel(String value) {
    return Padding(
      padding: const EdgeInsets.only(right: 8.0),
      child: Text(
        value,
        style: const TextStyle(
          fontSize: 10,
          color: AppColors.textMuted,
          fontWeight: FontWeight.w500,
        ),
      ),
    );
  }

  LinearGradient _getBarGradient(String level) {
    switch (level) {
      case 'green':
        return const LinearGradient(
          begin: Alignment.bottomCenter,
          end: Alignment.topCenter,
          colors: [Color(0xFF059669), Color(0xFF34D399)],
        );
      case 'yellow':
        return const LinearGradient(
          begin: Alignment.bottomCenter,
          end: Alignment.topCenter,
          colors: [Color(0xFFD97706), Color(0xFFFBBF24)],
        );
      case 'red':
        return const LinearGradient(
          begin: Alignment.bottomCenter,
          end: Alignment.topCenter,
          colors: [Color(0xFFDC2626), Color(0xFFF87171)],
        );
      default:
        return const LinearGradient(
          colors: [AppColors.textMuted, AppColors.textMuted],
        );
    }
  }

  bool _isCurrentHour(String time) {
    // Since this is forecast data, we should not highlight any bars as "current"
    // The forecast shows future predictions, not the current hour
    return false;
  }
}

class _LegendItem extends StatelessWidget {
  final Color color;
  final String label;

  const _LegendItem({
    required this.color,
    required this.label,
  });

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Container(
          width: 10,
          height: 10,
          decoration: BoxDecoration(
            color: color,
            borderRadius: BorderRadius.circular(5),
            boxShadow: const [
              BoxShadow(
                color: Color(0x33000000),
                blurRadius: 4,
                offset: Offset(0, 2),
              ),
            ],
          ),
        ),
        const SizedBox(width: 8),
        Text(
          label,
          style: const TextStyle(
            fontSize: 13,
            color: AppColors.textSecondary,
            fontWeight: FontWeight.w500,
          ),
        ),
      ],
    );
  }
}