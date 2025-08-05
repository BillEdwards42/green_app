import 'package:flutter/material.dart';

class AppColors {
  // Background colors matching prototype
  static const Color bgPrimary = Color(0xFF070F27);
  static const Color bgSecondary = Color(0xFF0D1935);
  
  // Surface colors
  static const Color surface = Color(0x08FFFFFF);
  static const Color surfaceLight = Color(0x0FFFFFFF);
  
  // Text colors
  static const Color textPrimary = Color(0xFFFFFFFF);
  static const Color textSecondary = Color(0xFF94A3B8);
  static const Color textMuted = Color(0xFF64748B);
  
  // Primary colors
  static const Color primary = Color(0xFF10B981);  // Main brand color (green)
  static const Color primaryLight = Color(0xFF34D399);
  static const Color primaryDark = Color(0xFF059669);
  
  // Status colors
  static const Color green = Color(0xFF10B981);
  static const Color greenGlow = Color(0x6610B981);
  static const Color yellow = Color(0xFFF59E0B);
  static const Color yellowGlow = Color(0x66F59E0B);
  static const Color red = Color(0xFFEF4444);
  static const Color redGlow = Color(0x66EF4444);
  static const Color error = Color(0xFFEF4444);  // Alias for red, used in forms
  
  // Accent colors
  static const Color accent = Color(0xFF6366F1);
  static const Color accentLight = Color(0xFF818CF8);
  
  // Border and shadows
  static const Color border = Color(0x14FFFFFF);
  
  // Gradients
  static const RadialGradient loadingBackground = RadialGradient(
    center: Alignment.center,
    radius: 1.0,
    stops: [0.0, 0.7],
    colors: [bgSecondary, bgPrimary],
  );
  
  static const LinearGradient progressGradient = LinearGradient(
    begin: Alignment.centerLeft,
    end: Alignment.centerRight,
    colors: [accent, accentLight],
  );
  
  static const LinearGradient shimmerGradient = LinearGradient(
    begin: Alignment.centerLeft,
    end: Alignment.centerRight,
    colors: [
      Colors.transparent,
      Color(0x4DFFFFFF),
      Colors.transparent,
    ],
  );
}