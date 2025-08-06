import 'package:flutter/material.dart';
import 'dart:math' as math;
import '../constants/app_colors.dart';

class LeagueUpgradeAnimation extends StatefulWidget {
  final String oldLeague;
  final String newLeague;
  final VoidCallback onComplete;

  const LeagueUpgradeAnimation({
    super.key,
    required this.oldLeague,
    required this.newLeague,
    required this.onComplete,
  });

  @override
  State<LeagueUpgradeAnimation> createState() => _LeagueUpgradeAnimationState();
}

class _LeagueUpgradeAnimationState extends State<LeagueUpgradeAnimation>
    with TickerProviderStateMixin {
  late AnimationController _scaleController;
  late AnimationController _fadeController;
  late AnimationController _particleController;
  late Animation<double> _scaleAnimation;
  late Animation<double> _fadeAnimation;

  @override
  void initState() {
    super.initState();
    
    _scaleController = AnimationController(
      duration: const Duration(milliseconds: 1500),
      vsync: this,
    );
    
    _fadeController = AnimationController(
      duration: const Duration(milliseconds: 500),
      vsync: this,
    );
    
    _particleController = AnimationController(
      duration: const Duration(seconds: 3),
      vsync: this,
    );
    
    _scaleAnimation = Tween<double>(
      begin: 0.0,
      end: 1.2,
    ).animate(CurvedAnimation(
      parent: _scaleController,
      curve: Curves.elasticOut,
    ));
    
    _fadeAnimation = Tween<double>(
      begin: 0.0,
      end: 1.0,
    ).animate(CurvedAnimation(
      parent: _fadeController,
      curve: Curves.easeIn,
    ));
    
    _startAnimation();
  }

  void _startAnimation() async {
    await Future.delayed(const Duration(milliseconds: 300));
    _fadeController.forward();
    _scaleController.forward();
    _particleController.repeat();
    
    await Future.delayed(const Duration(seconds: 3));
    if (mounted) {
      widget.onComplete();
    }
  }

  @override
  void dispose() {
    _scaleController.dispose();
    _fadeController.dispose();
    _particleController.dispose();
    super.dispose();
  }

  Map<String, dynamic> _getLeagueData(String league) {
    switch (league) {
      case 'bronze':
        return {
          'name': '銅聯盟',
          'color': const Color(0xFFCD7F32),
          'icon': Icons.shield_outlined,
        };
      case 'silver':
        return {
          'name': '銀聯盟',
          'color': const Color(0xFFC0C0C0),
          'icon': Icons.shield_outlined,
        };
      case 'gold':
        return {
          'name': '金聯盟',
          'color': const Color(0xFFFFD700),
          'icon': Icons.shield,
        };
      case 'emerald':
        return {
          'name': '翡翠聯盟',
          'color': const Color(0xFF50C878),
          'icon': Icons.shield,
        };
      case 'diamond':
        return {
          'name': '鑽石聯盟',
          'color': const Color(0xFFB9F2FF),
          'icon': Icons.stars,
        };
      default:
        return {
          'name': '銅聯盟',
          'color': const Color(0xFFCD7F32),
          'icon': Icons.shield_outlined,
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
          // Particle effects would go here
          // For now, simple colored circles as placeholders
          ...List.generate(20, (index) => _buildParticle(index)),
          
          Center(
            child: FadeTransition(
              opacity: _fadeAnimation,
              child: ScaleTransition(
                scale: _scaleAnimation,
                child: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: [
                    Container(
                      width: 150,
                      height: 150,
                      decoration: BoxDecoration(
                        shape: BoxShape.circle,
                        color: newLeagueData['color'],
                        boxShadow: [
                          BoxShadow(
                            color: newLeagueData['color'].withValues(alpha: 0.5),
                            blurRadius: 30,
                            spreadRadius: 10,
                          ),
                        ],
                      ),
                      child: Icon(
                        newLeagueData['icon'],
                        color: Colors.white,
                        size: 80,
                      ),
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
                        fontSize: 48,
                        fontWeight: FontWeight.bold,
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
        final angle = (index / 20) * 2 * 3.14159;
        final radius = 100 + (progress * 200);
        final x = MediaQuery.of(context).size.width / 2 + radius * math.cos(angle);
        final y = MediaQuery.of(context).size.height / 2 + radius * math.sin(angle);
        
        return Positioned(
          left: x,
          top: y,
          child: Container(
            width: 8,
            height: 8,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              color: AppColors.green.withValues(alpha: 1 - progress),
            ),
          ),
        );
      },
    );
  }
}