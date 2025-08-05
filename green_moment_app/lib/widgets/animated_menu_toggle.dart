import 'package:flutter/material.dart';
import '../constants/app_colors.dart';

class AnimatedMenuToggle extends StatefulWidget {
  final VoidCallback onSettingsTap;
  final VoidCallback onRankingTap;

  const AnimatedMenuToggle({
    super.key,
    required this.onSettingsTap,
    required this.onRankingTap,
  });

  @override
  State<AnimatedMenuToggle> createState() => _AnimatedMenuToggleState();
}

class _AnimatedMenuToggleState extends State<AnimatedMenuToggle>
    with SingleTickerProviderStateMixin {
  bool isExpanded = false;
  late AnimationController _controller;
  late Animation<double> _rotationAnimation;
  late Animation<double> _menuAnimation;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      duration: const Duration(milliseconds: 300),
      vsync: this,
    );
    
    _rotationAnimation = Tween<double>(
      begin: 0.0,
      end: 0.0, // No rotation to keep X as X
    ).animate(CurvedAnimation(
      parent: _controller,
      curve: Curves.easeInOut,
    ));

    _menuAnimation = CurvedAnimation(
      parent: _controller,
      curve: Curves.easeOutCubic,
    );
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  void _toggleMenu() {
    setState(() {
      isExpanded = !isExpanded;
      if (isExpanded) {
        _controller.forward();
      } else {
        _controller.reverse();
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.end,
      children: [
        // Toggle Button
        GestureDetector(
          onTap: _toggleMenu,
          child: Container(
            width: 40,
            height: 40,
            decoration: BoxDecoration(
              color: AppColors.surface,
              borderRadius: BorderRadius.circular(20),
              border: Border.all(
                color: AppColors.border,
                width: 1,
              ),
              boxShadow: const [
                BoxShadow(
                  color: Color(0x1A000000),
                  blurRadius: 4,
                  offset: Offset(0, 2),
                ),
              ],
            ),
            child: Center(
              child: AnimatedBuilder(
                animation: _rotationAnimation,
                builder: (context, child) {
                  return Transform.rotate(
                    angle: _rotationAnimation.value * 2 * 3.14159,
                    child: AnimatedSwitcher(
                      duration: const Duration(milliseconds: 200),
                      child: isExpanded
                          ? Icon(
                              Icons.close,
                              key: const ValueKey('close'),
                              color: AppColors.textSecondary,
                              size: 20,
                            )
                          : Icon(
                              Icons.more_vert,
                              key: const ValueKey('menu'),
                              color: AppColors.textSecondary,
                              size: 20,
                            ),
                    ),
                  );
                },
              ),
            ),
          ),
        ),
        
        // Animated Menu
        AnimatedBuilder(
          animation: _menuAnimation,
          builder: (context, child) {
            return ClipRect(
              child: Align(
                alignment: Alignment.topCenter,
                heightFactor: _menuAnimation.value,
                child: child,
              ),
            );
          },
          child: Container(
            margin: const EdgeInsets.only(top: 8),
            decoration: BoxDecoration(
              color: AppColors.surface,
              borderRadius: BorderRadius.circular(16),
              border: Border.all(
                color: AppColors.border,
                width: 1,
              ),
              boxShadow: const [
                BoxShadow(
                  color: Color(0x1A000000),
                  blurRadius: 4,
                  offset: Offset(0, 2),
                ),
              ],
            ),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                _buildMenuItem(
                  icon: Icons.settings,
                  label: '帳號設定',
                  onTap: () {
                    _toggleMenu();
                    widget.onSettingsTap();
                  },
                ),
                Container(
                  height: 1,
                  margin: const EdgeInsets.symmetric(horizontal: 16),
                  color: AppColors.border,
                ),
                _buildMenuItem(
                  icon: Icons.help_outline,
                  label: '排行說明',
                  onTap: () {
                    _toggleMenu();
                    widget.onRankingTap();
                  },
                ),
              ],
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildMenuItem({
    required IconData icon,
    required String label,
    required VoidCallback onTap,
  }) {
    return Material(
      color: Colors.transparent,
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(8),
        child: Container(
          padding: const EdgeInsets.symmetric(
            horizontal: 16,
            vertical: 12,
          ),
          child: Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(
                icon,
                size: 20,
                color: AppColors.textSecondary,
              ),
              const SizedBox(width: 12),
              Text(
                label,
                style: const TextStyle(
                  color: AppColors.textPrimary,
                  fontSize: 14,
                  fontWeight: FontWeight.w500,
                ),
              ),
              const SizedBox(width: 16),
            ],
          ),
        ),
      ),
    );
  }
}