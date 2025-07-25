import 'package:flutter/material.dart';

class AppAnimations {
  // Animation durations
  static const Duration logoRotationDuration = Duration(milliseconds: 1000);
  static const Duration progressBarFadeDuration = Duration(milliseconds: 500);
  static const Duration progressTextFadeDuration = Duration(milliseconds: 300);
  static const Duration progressFillDuration = Duration(milliseconds: 1800);
  static const Duration fadeOutDuration = Duration(milliseconds: 400);
  static const Duration pulseAnimationDuration = Duration(milliseconds: 2000);
  static const Duration shimmerDuration = Duration(milliseconds: 2000);
  
  // Animation curves
  static const Curve logoRotationCurve = Curves.easeOutBack;
  static const Curve progressFillCurve = Curves.easeInOut;
  static const Curve fadeInCurve = Curves.easeOut;
  static const Curve fadeOutCurve = Curves.easeIn;
  static const Curve pulseCurve = Curves.easeInOut;
  
  // Logo animation values
  static const double logoInitialScale = 0.5;
  static const double logoFinalScale = 1.0;
  static const double logoInitialRotation = -180.0;
  static const double logoFinalRotation = 0.0;
  static const double logoInitialOpacity = 0.0;
  static const double logoFinalOpacity = 1.0;
  
  // Pulse animation values
  static const double pulseMinScale = 1.0;
  static const double pulseMaxScale = 1.05;
  static const double pulseMinGlow = 0.3;
  static const double pulseMaxGlow = 0.5;
  
  // Progress bar values
  static const double progressBarHeight = 6.0;
  static const double progressBarWidth = 240.0;
  static const BorderRadius progressBarBorderRadius = BorderRadius.all(Radius.circular(3.0));
  static const double progressBarBackgroundOpacity = 0.1;
  
  // Logo dimensions and styling
  static const double logoSize = 80.0;
  static const double logoGlowBlurRadius = 24.0;
  static const double logoGlowSpreadRadius = 0.0;
  static const Offset logoGlowOffset = Offset(0, 8);
  
  // Layout spacing
  static const double loadingContentGap = 32.0;
  static const double progressContainerGap = 16.0;
  static const double progressContainerWidth = 240.0;
}