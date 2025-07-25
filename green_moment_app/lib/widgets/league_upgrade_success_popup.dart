import 'package:flutter/material.dart';
import 'dart:math' as math;
import '../constants/app_colors.dart';

class LeagueUpgradeSuccessPopup extends StatefulWidget {
  final String oldLeague;
  final String newLeague;
  final VoidCallback onComplete;

  const LeagueUpgradeSuccessPopup({
    super.key,
    required this.oldLeague,
    required this.newLeague,
    required this.onComplete,
  });

  @override
  State<LeagueUpgradeSuccessPopup> createState() =>
      _LeagueUpgradeSuccessPopupState();
}

class _LeagueUpgradeSuccessPopupState extends State<LeagueUpgradeSuccessPopup>
    with TickerProviderStateMixin {
  late AnimationController _scaleController;
  late AnimationController _rotationController;
  late AnimationController _particleController;
  late Animation<double> _scaleAnimation;
  late Animation<double> _rotationAnimation;

  @override
  void initState() {
    super.initState();

    _scaleController = AnimationController(
      duration: const Duration(milliseconds: 1500),
      vsync: this,
    );

    _rotationController = AnimationController(
      duration: const Duration(seconds: 2),
      vsync: this,
    );

    _particleController = AnimationController(
      duration: const Duration(seconds: 3),
      vsync: this,
    );

    _scaleAnimation = Tween<double>(
      begin: 0.0,
      end: 1.0,
    ).animate(CurvedAnimation(
      parent: _scaleController,
      curve: Curves.elasticOut,
    ));

    _rotationAnimation = Tween<double>(
      begin: 0.0,
      end: 2 * math.pi,
    ).animate(CurvedAnimation(
      parent: _rotationController,
      curve: Curves.easeInOut,
    ));

    _startAnimation();
  }

  void _startAnimation() async {
    await Future.delayed(const Duration(milliseconds: 100));
    _scaleController.forward();
    _rotationController.forward();
    _particleController.repeat();

    await Future.delayed(const Duration(seconds: 3));
    if (mounted) {
      widget.onComplete();
    }
  }

  @override
  void dispose() {
    _scaleController.dispose();
    _rotationController.dispose();
    _particleController.dispose();
    super.dispose();
  }

  Map<String, dynamic> _getLeagueData(String league) {
    switch (league) {
      case 'bronze':
        return {
          'name': '青銅聯盟',
          'color': const Color(0xFFCD7F32),
        };
      case 'silver':
        return {
          'name': '白銀聯盟',
          'color': const Color(0xFFC0C0C0),
        };
      case 'gold':
        return {
          'name': '黃金聯盟',
          'color': const Color(0xFFFFD700),
        };
      case 'emerald':
        return {
          'name': '翡翠聯盟',
          'color': const Color(0xFF50C878),
        };
      case 'diamond':
        return {
          'name': '鑽石聯盟',
          'color': const Color(0xFF87CEEB),
        };
      default:
        return {
          'name': '青銅聯盟',
          'color': const Color(0xFFCD7F32),
        };
    }
  }

  @override
  Widget build(BuildContext context) {
    final newLeagueData = _getLeagueData(widget.newLeague);

    return Material(
      color: Colors.black87,
      child: Stack(
        children: [
          // Particles
          ...List.generate(30, (index) => _buildParticle(index)),

          // Main content
          Center(
            child: ScaleTransition(
              scale: _scaleAnimation,
              child: Container(
                padding: const EdgeInsets.all(32),
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    // Badge with rotation
                    AnimatedBuilder(
                      animation: _rotationAnimation,
                      builder: (context, child) {
                        return Transform.rotate(
                          angle: _rotationAnimation.value,
                          child: Container(
                            width: 120,
                            height: 120,
                            decoration: BoxDecoration(
                              shape: BoxShape.circle,
                              gradient: RadialGradient(
                                colors: [
                                  newLeagueData['color'],
                                  newLeagueData['color'].withValues(alpha: 0.6),
                                ],
                              ),
                              boxShadow: [
                                BoxShadow(
                                  color:
                                      newLeagueData['color'].withValues(alpha: 0.5),
                                  blurRadius: 30,
                                  spreadRadius: 10,
                                ),
                              ],
                            ),
                            child: CustomPaint(
                              painter: _ReductionSymbolPainter(),
                              size: const Size(120, 120),
                            ),
                          ),
                        );
                      },
                    ),
                    const SizedBox(height: 32),
                    Text(
                      '恭喜升級！',
                      style: TextStyle(
                        color: Colors.white,
                        fontSize: 32,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    const SizedBox(height: 16),
                    Text(
                      newLeagueData['name'],
                      style: TextStyle(
                        color: newLeagueData['color'],
                        fontSize: 40,
                        fontWeight: FontWeight.bold,
                        shadows: [
                          Shadow(
                            color: newLeagueData['color'].withValues(alpha: 0.5),
                            blurRadius: 20,
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(height: 24),
                    Text(
                      '上月碳減量達標，繼續努力！',
                      style: TextStyle(
                        color: Colors.white70,
                        fontSize: 18,
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildParticle(int index) {
    return AnimatedBuilder(
      animation: _particleController,
      builder: (context, child) {
        final progress = _particleController.value;
        final angle = (index / 30) * 2 * math.pi + (progress * 2 * math.pi);
        final radius = 150 + (progress * 200);
        final x = MediaQuery.of(context).size.width / 2 +
            radius * math.cos(angle);
        final y = MediaQuery.of(context).size.height / 2 +
            radius * math.sin(angle);

        return Positioned(
          left: x - 4,
          top: y - 4,
          child: Container(
            width: 8,
            height: 8,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              color: _getLeagueData(widget.newLeague)['color']
                  .withValues(alpha: 0.8 - progress * 0.8),
            ),
          ),
        );
      },
    );
  }
}

class LeagueUpgradeFailedPopup extends StatelessWidget {
  final String currentLeague;
  final int completedTasks;
  final VoidCallback onClose;

  const LeagueUpgradeFailedPopup({
    super.key,
    required this.currentLeague,
    required this.completedTasks,
    required this.onClose,
  });

  @override
  Widget build(BuildContext context) {
    return Dialog(
      backgroundColor: Colors.transparent,
      child: Container(
        padding: const EdgeInsets.all(24),
        decoration: BoxDecoration(
          color: AppColors.bgPrimary,
          borderRadius: BorderRadius.circular(20),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withValues(alpha: 0.2),
              blurRadius: 20,
              offset: const Offset(0, 10),
            ),
          ],
        ),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Container(
              width: 80,
              height: 80,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                color: Colors.orange.withValues(alpha: 0.1),
              ),
              child: Icon(
                Icons.timer_off,
                size: 40,
                color: Colors.orange,
              ),
            ),
            const SizedBox(height: 24),
            Text(
              '任務未完成',
              style: TextStyle(
                fontSize: 24,
                fontWeight: FontWeight.bold,
                color: AppColors.textPrimary,
              ),
            ),
            const SizedBox(height: 12),
            Text(
              '您完成了 $completedTasks/3 個任務',
              style: TextStyle(
                fontSize: 16,
                color: AppColors.textSecondary,
              ),
            ),
            const SizedBox(height: 8),
            Text(
              '繼續努力，本月再接再厲！',
              style: TextStyle(
                fontSize: 16,
                color: AppColors.textSecondary,
              ),
            ),
            const SizedBox(height: 24),
            ElevatedButton(
              onPressed: onClose,
              style: ElevatedButton.styleFrom(
                backgroundColor: AppColors.green,
                padding: const EdgeInsets.symmetric(
                  horizontal: 32,
                  vertical: 12,
                ),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(12),
                ),
              ),
              child: Text(
                '我知道了',
                style: TextStyle(
                  color: AppColors.bgPrimary,
                  fontSize: 16,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

// Custom painter for the reduction symbol in the popup
class _ReductionSymbolPainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final center = Offset(size.width / 2, size.height / 2);
    
    final symbolPaint = Paint()
      ..color = Colors.white.withValues(alpha: 0.8)
      ..style = PaintingStyle.fill;

    // Draw three circles in descending pattern
    final positions = [
      Offset(center.dx - 20, center.dy - 15),
      Offset(center.dx, center.dy),
      Offset(center.dx + 20, center.dy + 15),
    ];
    
    final sizes = [12.0, 9.0, 6.0];
    
    for (int i = 0; i < positions.length; i++) {
      // Outer glow
      final glowPaint = Paint()
        ..color = Colors.white.withValues(alpha: 0.3)
        ..maskFilter = const MaskFilter.blur(BlurStyle.normal, 5);
      canvas.drawCircle(positions[i], sizes[i] + 3, glowPaint);
      
      // Main circle
      canvas.drawCircle(positions[i], sizes[i], symbolPaint);
    }

    // Draw connecting flow line
    final path = Path();
    path.moveTo(positions[0].dx, positions[0].dy);
    
    final controlPoint1 = Offset(center.dx - 10, center.dy - 5);
    final controlPoint2 = Offset(center.dx + 10, center.dy + 5);
    
    path.cubicTo(
      controlPoint1.dx, controlPoint1.dy,
      controlPoint2.dx, controlPoint2.dy,
      positions[2].dx, positions[2].dy,
    );

    final flowPaint = Paint()
      ..color = Colors.white.withValues(alpha: 0.5)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 3
      ..strokeCap = StrokeCap.round;

    canvas.drawPath(path, flowPaint);
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}