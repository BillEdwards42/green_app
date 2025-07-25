import 'package:flutter/material.dart';
import 'dart:math' as math;
import '../constants/app_colors.dart';
import '../models/carbon_intensity_model.dart';

class CarbonIntensityRing extends StatefulWidget {
  final CarbonIntensityModel? intensity;
  final bool isLoading;

  const CarbonIntensityRing({
    super.key,
    this.intensity,
    required this.isLoading,
  });

  @override
  State<CarbonIntensityRing> createState() => _CarbonIntensityRingState();
}

class _CarbonIntensityRingState extends State<CarbonIntensityRing>
    with TickerProviderStateMixin {
  late AnimationController _rotationController;
  late AnimationController _pulseController;
  late AnimationController _valueController;
  late Animation<double> _rotationAnimation;
  late Animation<double> _pulseAnimation;
  late Animation<double> _valueAnimation;
  
  double _currentDisplayValue = 0;

  @override
  void initState() {
    super.initState();
    
    // Ring rotation animation (30 seconds)
    _rotationController = AnimationController(
      duration: const Duration(seconds: 30),
      vsync: this,
    );
    _rotationAnimation = Tween<double>(begin: 0, end: 1).animate(_rotationController);
    _rotationController.repeat();
    
    // Pulse animation for glow effect
    _pulseController = AnimationController(
      duration: const Duration(milliseconds: 3000),
      vsync: this,
    );
    _pulseAnimation = Tween<double>(begin: 0.4, end: 0.8).animate(
      CurvedAnimation(parent: _pulseController, curve: Curves.easeInOut),
    );
    _pulseController.repeat(reverse: true);
    
    // Value animation controller
    _valueController = AnimationController(
      duration: const Duration(milliseconds: 2000),
      vsync: this,
    );
    _valueAnimation = Tween<double>(begin: 0, end: 1).animate(
      CurvedAnimation(parent: _valueController, curve: Curves.easeOut),
    );
  }

  @override
  void didUpdateWidget(CarbonIntensityRing oldWidget) {
    super.didUpdateWidget(oldWidget);
    
    // Trigger animation on any data update, including refresh
    if (widget.intensity != null && !widget.isLoading) {
      // Always animate from 0 to target value for consistent counting up
      _valueController.reset();
      final targetValue = widget.intensity!.gco2KWh;
      _currentDisplayValue = 0;
      _valueAnimation = Tween<double>(
        begin: 0,
        end: targetValue,
      ).animate(CurvedAnimation(parent: _valueController, curve: Curves.easeOut));
      _valueController.forward();
    }
  }

  @override
  void dispose() {
    _rotationController.dispose();
    _pulseController.dispose();
    _valueController.dispose();
    super.dispose();
  }

  Color _getColorForLevel(String? level, bool isLoading) {
    if (isLoading) return AppColors.textMuted;
    
    switch (level) {
      case 'green':
        return AppColors.green;
      case 'yellow':
        return AppColors.yellow;
      case 'red':
        return AppColors.red;
      default:
        return AppColors.textMuted;
    }
  }

  Color _getGlowColorForLevel(String? level, bool isLoading) {
    if (isLoading) return AppColors.textMuted.withValues(alpha: 0.3);
    
    switch (level) {
      case 'green':
        return AppColors.greenGlow;
      case 'yellow':
        return AppColors.yellowGlow;
      case 'red':
        return AppColors.redGlow;
      default:
        return AppColors.textMuted.withValues(alpha: 0.3);
    }
  }

  @override
  Widget build(BuildContext context) {
    final screenWidth = MediaQuery.of(context).size.width;
    final ringSize = _calculateRingSize(screenWidth);
    
    return Center(
      child: SizedBox(
        width: ringSize,
        height: ringSize,
        child: Stack(
          alignment: Alignment.center,
          children: [
            // Animated glow effect
            AnimatedBuilder(
              animation: Listenable.merge([_pulseAnimation, _valueController]),
              builder: (context, child) {
                final glowColor = _getGlowColorForLevel(
                  widget.intensity?.level, 
                  widget.isLoading,
                );
                
                return Container(
                  width: ringSize + 80,
                  height: ringSize + 80,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    boxShadow: [
                      BoxShadow(
                        color: glowColor.withValues(alpha: _pulseAnimation.value * 0.6),
                        blurRadius: 40,
                        spreadRadius: 0,
                      ),
                      BoxShadow(
                        color: glowColor.withValues(alpha: _pulseAnimation.value * 0.3),
                        blurRadius: 60,
                        spreadRadius: 10,
                      ),
                    ],
                  ),
                );
              },
            ),
            
            // Rotating outer ring
            AnimatedBuilder(
              animation: _rotationAnimation,
              builder: (context, child) {
                return Transform.rotate(
                  angle: _rotationAnimation.value * 2 * math.pi,
                  child: Container(
                    width: ringSize,
                    height: ringSize,
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      gradient: const SweepGradient(
                        colors: [
                          Colors.transparent,
                          Color(0x08FFFFFF),
                          Color(0x10FFFFFF),
                          Color(0x08FFFFFF),
                          Colors.transparent,
                        ],
                        stops: [0.0, 0.25, 0.5, 0.75, 1.0],
                      ),
                    ),
                  ),
                );
              },
            ),
            
            // Inner content container
            Container(
              width: ringSize - 20,
              height: ringSize - 20,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                gradient: const RadialGradient(
                  colors: [AppColors.surfaceLight, AppColors.surface],
                  stops: [0.0, 1.0],
                ),
                border: Border.all(color: AppColors.border, width: 1),
              ),
              child: Center(
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    // Carbon intensity value
                    AnimatedBuilder(
                      animation: _valueAnimation,
                      builder: (context, child) {
                        _currentDisplayValue = _valueAnimation.value;
                        final displayValue = widget.isLoading ? 0 : _currentDisplayValue.round();
                        final textColor = _getColorForLevel(
                          widget.intensity?.level, 
                          widget.isLoading,
                        );
                        
                        return Text(
                          '$displayValue',
                          style: TextStyle(
                            fontSize: _calculateValueFontSize(screenWidth),
                            fontWeight: FontWeight.w900,
                            color: textColor,
                            letterSpacing: -0.02,
                            height: 1.0,
                          ),
                        );
                      },
                    ),
                    
                    const SizedBox(height: 2),
                    
                    // Unit text
                    Text(
                      'gCO₂/kWh',
                      style: TextStyle(
                        fontSize: _calculateUnitFontSize(screenWidth),
                        color: AppColors.textSecondary,
                        fontWeight: FontWeight.w500,
                      ),
                    ),
                    
                    const SizedBox(height: 4),
                    
                    // Explanation text
                    Text(
                      '公克碳/一度電',
                      style: TextStyle(
                        fontSize: _calculateExplanationFontSize(screenWidth),
                        color: AppColors.textSecondary,
                        fontWeight: FontWeight.w400,
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  double _calculateRingSize(double screenWidth) {
    if (screenWidth < 360) return 320;
    if (screenWidth < 400) return 340;
    if (screenWidth < 500) return 350;
    if (screenWidth < 768) return 360;
    return 380;
  }

  double _calculateValueFontSize(double screenWidth) {
    if (screenWidth < 360) return 76;
    if (screenWidth < 400) return 84;
    if (screenWidth < 500) return 88;
    if (screenWidth < 768) return 92;
    return 100;
  }

  double _calculateUnitFontSize(double screenWidth) {
    if (screenWidth < 768) return 16;
    return 18;
  }

  double _calculateExplanationFontSize(double screenWidth) {
    if (screenWidth < 768) return 14;
    return 16;
  }
}