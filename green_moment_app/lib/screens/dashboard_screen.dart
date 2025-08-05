import 'package:flutter/material.dart';
import 'dart:math' as math;
import '../constants/app_colors.dart';
import '../widgets/background_pattern.dart';
import '../models/user_progress.dart';
import '../services/user_progress_service.dart';
import '../services/auth_service.dart';
import '../widgets/league_upgrade_success_popup.dart';
import '../widgets/animated_menu_toggle.dart';
import '../widgets/account_settings_modal.dart';
import '../services/notification_service.dart';
import 'package:shared_preferences/shared_preferences.dart';

class DashboardScreen extends StatefulWidget {
  const DashboardScreen({super.key});

  @override
  State<DashboardScreen> createState() => DashboardScreenState();
}

// Make state public so it can be accessed from main screen
class DashboardScreenState extends State<DashboardScreen>
    with SingleTickerProviderStateMixin, WidgetsBindingObserver {
  final UserProgressService _progressService = UserProgressService();
  UserProgress? _userProgress;
  bool _isLoading = true;
  late AnimationController _animationController;
  late Animation<double> _pulseAnimation;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    _animationController = AnimationController(
      duration: const Duration(seconds: 2),
      vsync: this,
    )..repeat(reverse: true);
    
    _pulseAnimation = Tween<double>(
      begin: 0.95,
      end: 1.05,
    ).animate(CurvedAnimation(
      parent: _animationController,
      curve: Curves.easeInOut,
    ));
    
    _loadUserProgress();
    _checkForLeagueUpgrade();
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (state == AppLifecycleState.resumed) {
      _loadUserProgress();
    }
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    _animationController.dispose();
    super.dispose();
  }

  Future<void> _loadUserProgress() async {
    try {
      final progress = await _progressService.getUserProgress();
      setState(() {
        _userProgress = progress;
        _isLoading = false;
      });
    } catch (e) {
      setState(() {
        _isLoading = false;
      });
    }
  }

  Future<void> _checkForLeagueUpgrade() async {
    final shouldShow = await _progressService.shouldShowLeagueUpgrade();
    if (shouldShow && mounted) {
      // Get the league info from progress
      final progress = await _progressService.getUserProgress();
      if (progress != null && progress.shouldShowLeagueUpgrade) {
        // Mark as shown
        await _progressService.markLeagueUpgradeShown();
        
        // Show the upgrade popup
        if (mounted) {
          showDialog(
            context: context,
            barrierDismissible: false,
            builder: (context) => LeagueUpgradeSuccessPopup(
              oldLeague: _getLeagueBefore(progress.currentLeague),
              newLeague: progress.currentLeague,
              onClose: () {
                Navigator.of(context).pop();
                // Reload progress to update UI
                _loadUserProgress();
              },
            ),
          );
        }
      }
    }
  }
  
  String _getLeagueBefore(String currentLeague) {
    const leagues = ['bronze', 'silver', 'gold', 'emerald', 'diamond'];
    final index = leagues.indexOf(currentLeague);
    return index > 0 ? leagues[index - 1] : currentLeague;
  }

  // Public method to refresh data from external sources
  void refreshData() {
    _loadUserProgress();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.bgPrimary,
      body: Stack(
        children: [
          const Positioned.fill(
            child: BackgroundPattern(),
          ),
          SafeArea(
            child: _isLoading
                ? Center(
                    child: CircularProgressIndicator(
                      color: AppColors.green,
                    ),
                  )
                : Stack(
                    children: [
                      SingleChildScrollView(
                        physics: const BouncingScrollPhysics(),
                        child: Padding(
                          padding: const EdgeInsets.symmetric(horizontal: 20.0),
                          child: Column(
                            crossAxisAlignment: CrossAxisAlignment.stretch,
                            children: [
                              const SizedBox(height: 50),
                              _buildUserGreeting(),
                              const SizedBox(height: 24),
                              _buildMonthlySavingsCard(),
                          const SizedBox(height: 32),
                          _buildLeagueSection(),
                          const SizedBox(height: 24),
                          _buildTasksSection(),
                          const SizedBox(height: 20),
                          _buildFooterNote(),
                          const SizedBox(height: 20),
                          // DEBUG: FCM Token Display Button
                          _buildDebugTokenButton(),
                          const SizedBox(height: 32),
                            ],
                          ),
                        ),
                      ),
                      // Menu toggle
                      Positioned(
                        top: 10,
                        right: 20,
                        child: AnimatedMenuToggle(
                          onSettingsTap: _showAccountSettings,
                          onRankingTap: _showHelpDialog,
                        ),
                      ),
                    ],
                  ),
          ),
        ],
      ),
    );
  }

  Widget _buildUserGreeting() {
    final authService = AuthService();
    final username = authService.username ?? '用戶';
    
    return Container(
      alignment: Alignment.centerLeft,
      child: IntrinsicHeight(
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.center,
          children: [
            // Active indicator with pulse animation
            AnimatedBuilder(
              animation: _pulseAnimation,
              builder: (context, child) {
                return Container(
                  width: 8,
                  height: 8,
                  margin: const EdgeInsets.only(right: 16),
                  decoration: BoxDecoration(
                    color: AppColors.green,
                    shape: BoxShape.circle,
                    boxShadow: [
                      BoxShadow(
                        color: AppColors.green.withValues(alpha: 0.6),
                        blurRadius: 16 * _pulseAnimation.value,
                        spreadRadius: 4 * _pulseAnimation.value,
                      ),
                    ],
                  ),
                );
              },
            ),
            // Greeting text
            RichText(
              text: TextSpan(
                style: TextStyle(
                  fontSize: 26,
                  height: 1.2,
                ),
                children: [
                  TextSpan(
                    text: '你好，',
                    style: TextStyle(
                      color: AppColors.textSecondary,
                      fontWeight: FontWeight.w300,
                    ),
                  ),
                  TextSpan(
                    text: username,
                    style: TextStyle(
                      color: AppColors.textPrimary,
                      fontWeight: FontWeight.w600,
                      letterSpacing: 0.5,
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildMonthlySavingsCard() {
    final hasSavings = _userProgress?.lastMonthCarbonSaved != null;
    
    return Container(
      height: 200,
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: hasSavings
              ? [
                  AppColors.green,
                  AppColors.green.withValues(alpha: 0.85),
                ]
              : [
                  AppColors.textPrimary.withValues(alpha: 0.15),
                  AppColors.textPrimary.withValues(alpha: 0.08),
                ],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(24),
        boxShadow: [
          BoxShadow(
            color: hasSavings
                ? AppColors.green.withValues(alpha: 0.25)
                : Colors.black.withValues(alpha: 0.08),
            blurRadius: 20,
            offset: const Offset(0, 8),
          ),
        ],
      ),
      child: Stack(
        children: [
          // Decorative circles
          Positioned(
            right: -30,
            top: -30,
            child: Container(
              width: 120,
              height: 120,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                color: AppColors.bgPrimary.withValues(alpha: 0.1),
              ),
            ),
          ),
          Positioned(
            left: -20,
            bottom: -20,
            child: Container(
              width: 80,
              height: 80,
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                color: AppColors.bgPrimary.withValues(alpha: 0.08),
              ),
            ),
          ),
          // Content
          Padding(
            padding: const EdgeInsets.all(28.0),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  '上月碳減量',
                  style: TextStyle(
                    color: hasSavings
                        ? AppColors.bgPrimary.withValues(alpha: 0.9)
                        : AppColors.textSecondary,
                    fontSize: 16,
                    fontWeight: FontWeight.w500,
                    letterSpacing: 0.5,
                  ),
                ),
                const SizedBox(height: 12),
                Row(
                  crossAxisAlignment: CrossAxisAlignment.end,
                  children: [
                    Text(
                      hasSavings
                          ? _userProgress!.lastMonthCarbonSaved!
                              .toStringAsFixed(0)
                          : '計算中',
                      style: TextStyle(
                        color: hasSavings
                            ? AppColors.bgPrimary
                            : AppColors.textPrimary,
                        fontSize: 48,
                        fontWeight: FontWeight.w700,
                        height: 1,
                      ),
                    ),
                    if (hasSavings) ...[
                      const SizedBox(width: 8),
                      Padding(
                        padding: const EdgeInsets.only(bottom: 8.0),
                        child: Text(
                          '公克',
                          style: TextStyle(
                            color: AppColors.bgPrimary.withValues(alpha: 0.8),
                            fontSize: 20,
                            fontWeight: FontWeight.w500,
                          ),
                        ),
                      ),
                    ],
                  ],
                ),
                if (!hasSavings) ...[
                  const SizedBox(height: 8),
                  Text(
                    '每月1日更新',
                    style: TextStyle(
                      color: AppColors.textSecondary,
                      fontSize: 14,
                      fontWeight: FontWeight.w400,
                    ),
                  ),
                ],
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildLeagueSection() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.center,
      children: [
        AnimatedBuilder(
          animation: _pulseAnimation,
          builder: (context, child) {
            return Transform.scale(
              scale: _pulseAnimation.value,
              child: _buildLeagueBadge(
                  _userProgress?.currentLeague ?? 'bronze'),
            );
          },
        ),
        const SizedBox(height: 20),
        Text(
          _getLeagueData(_userProgress?.currentLeague ?? 'bronze')['name'],
          style: TextStyle(
            fontSize: 24,
            fontWeight: FontWeight.w700,
            color: AppColors.textPrimary,
            letterSpacing: 1.0,
          ),
        ),
      ],
    );
  }

  Widget _buildLeagueBadge(String league) {
    final leagueData = _getLeagueData(league);
    
    return Container(
      width: 100,
      height: 100,
      child: CustomPaint(
        painter: LeagueBadgePainter(
          primaryColor: leagueData['colors'][0],
          secondaryColor: leagueData['colors'][1],
          league: league,
        ),
        child: Container(),
      ),
    );
  }

  Map<String, dynamic> _getLeagueData(String league) {
    switch (league) {
      case 'bronze':
        return {
          'name': '青銅聯盟',
          'colors': [const Color(0xFFCD7F32), const Color(0xFF8B5A2B)],
        };
      case 'silver':
        return {
          'name': '白銀聯盟',
          'colors': [const Color(0xFFE5E5E5), const Color(0xFFA8A8A8)],
        };
      case 'gold':
        return {
          'name': '黃金聯盟',
          'colors': [const Color(0xFFFFD700), const Color(0xFFFFB300)],
        };
      case 'emerald':
        return {
          'name': '翡翠聯盟',
          'colors': [const Color(0xFF50C878), const Color(0xFF2E8B57)],
        };
      case 'diamond':
        return {
          'name': '鑽石聯盟',
          'colors': [const Color(0xFFE0F2FF), const Color(0xFF87CEEB)],
        };
      default:
        return {
          'name': '青銅聯盟',
          'colors': [const Color(0xFFCD7F32), const Color(0xFF8B5A2B)],
        };
    }
  }

  Widget _buildTasksSection() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          '本月任務',
          style: TextStyle(
            fontSize: 20,
            fontWeight: FontWeight.w600,
            color: AppColors.textPrimary,
            letterSpacing: 0.5,
          ),
        ),
        const SizedBox(height: 16),
        ...(_userProgress?.currentMonthTasks ?? [])
            .asMap()
            .entries
            .map((entry) => _buildTaskCard(
                  entry.value.description,
                  entry.value.completed,
                  entry.key,
                ))
            .toList(),
      ],
    );
  }

  Widget _buildTaskCard(String description, bool completed, int index) {
    return AnimatedContainer(
      duration: Duration(milliseconds: 300 + (index * 100)),
      curve: Curves.easeOutCubic,
      margin: const EdgeInsets.only(bottom: 12),
      decoration: BoxDecoration(
        color: completed
            ? AppColors.green.withValues(alpha: 0.08)
            : AppColors.textPrimary.withValues(alpha: 0.04),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: completed
              ? AppColors.green.withValues(alpha: 0.3)
              : AppColors.textPrimary.withValues(alpha: 0.08),
          width: 1,
        ),
      ),
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          borderRadius: BorderRadius.circular(16),
          onTap: () {},
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 18),
            child: Row(
              children: [
                Expanded(
                  child: Text(
                    description,
                    style: TextStyle(
                      fontSize: 16,
                      color: completed
                          ? AppColors.textPrimary
                          : AppColors.textSecondary,
                      fontWeight: completed ? FontWeight.w500 : FontWeight.w400,
                      letterSpacing: 0.3,
                    ),
                  ),
                ),
                AnimatedContainer(
                  duration: const Duration(milliseconds: 300),
                  width: 28,
                  height: 28,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    color: completed
                        ? AppColors.green
                        : Colors.transparent,
                    border: Border.all(
                      color: completed
                          ? AppColors.green
                          : AppColors.textPrimary.withValues(alpha: 0.2),
                      width: 2,
                    ),
                  ),
                  child: completed
                      ? Icon(
                          Icons.check,
                          color: AppColors.bgPrimary,
                          size: 16,
                        )
                      : null,
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildFooterNote() {
    return Container(
      padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 20),
      decoration: BoxDecoration(
        color: AppColors.textPrimary.withValues(alpha: 0.04),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(
            Icons.info_outline,
            size: 16,
            color: AppColors.textSecondary,
          ),
          const SizedBox(width: 8),
          Text(
            '聯盟升級於每月1日進行',
            style: TextStyle(
              fontSize: 14,
              color: AppColors.textSecondary,
              fontWeight: FontWeight.w400,
            ),
          ),
        ],
      ),
    );
  }

  void _showAccountSettings() {
    showDialog(
      context: context,
      builder: (context) => const AccountSettingsModal(),
    );
  }

  void _showHelpDialog() {
    showDialog(
      context: context,
      builder: (context) => Dialog(
        backgroundColor: AppColors.bgPrimary,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(20),
        ),
        child: Container(
          constraints: const BoxConstraints(maxWidth: 400),
          child: SingleChildScrollView(
            child: Padding(
              padding: const EdgeInsets.all(24.0),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Icon(
                        Icons.emoji_events,
                        color: AppColors.green,
                        size: 28,
                      ),
                      const SizedBox(width: 12),
                      Text(
                        '聯盟系統說明',
                        style: TextStyle(
                          fontSize: 24,
                          fontWeight: FontWeight.bold,
                          color: AppColors.textPrimary,
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 20),
                  Text(
                    '完成每個聯盟的3個任務來晉級到下一個聯盟。開始減少碳排放吧！',
                    style: TextStyle(
                      fontSize: 16,
                      color: AppColors.textSecondary,
                      height: 1.5,
                    ),
                  ),
                  const SizedBox(height: 24),
                  _buildLeagueHelpItem(
                    '青銅聯盟',
                    const Color(0xFFCD7F32),
                  ),
                  const SizedBox(height: 12),
                  _buildLeagueHelpItem(
                    '白銀聯盟',
                    const Color(0xFFC0C0C0),
                  ),
                  const SizedBox(height: 12),
                  _buildLeagueHelpItem(
                    '黃金聯盟',
                    const Color(0xFFFFD700),
                  ),
                  const SizedBox(height: 12),
                  _buildLeagueHelpItem(
                    '翡翠聯盟',
                    const Color(0xFF50C878),
                  ),
                  const SizedBox(height: 12),
                  _buildLeagueHelpItem(
                    '鑽石聯盟',
                    const Color(0xFF87CEEB),
                  ),
                  const SizedBox(height: 24),
                  Container(
                    padding: const EdgeInsets.all(16),
                    decoration: BoxDecoration(
                      color: AppColors.green.withValues(alpha: 0.1),
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: Row(
                      children: [
                        Icon(
                          Icons.info_outline,
                          color: AppColors.green,
                          size: 20,
                        ),
                        const SizedBox(width: 12),
                        Expanded(
                          child: Text(
                            '每月1日系統會根據您的任務完成情況決定是否晉級',
                            style: TextStyle(
                              fontSize: 14,
                              color: AppColors.textPrimary,
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(height: 20),
                  Center(
                    child: TextButton(
                      onPressed: () => Navigator.of(context).pop(),
                      style: TextButton.styleFrom(
                        padding: const EdgeInsets.symmetric(
                          horizontal: 32,
                          vertical: 12,
                        ),
                      ),
                      child: Text(
                        '我知道了',
                        style: TextStyle(
                          color: AppColors.green,
                          fontSize: 16,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildLeagueHelpItem(String name, Color color) {
    return Row(
      children: [
        Container(
          width: 50,
          height: 50,
          decoration: BoxDecoration(
            shape: BoxShape.circle,
            gradient: RadialGradient(
              colors: [color, color.withValues(alpha: 0.7)],
            ),
          ),
          child: CustomPaint(
            painter: _MiniLeagueBadgePainter(color),
          ),
        ),
        const SizedBox(width: 16),
        Text(
          name,
          style: TextStyle(
            fontSize: 18,
            fontWeight: FontWeight.w600,
            color: AppColors.textPrimary,
          ),
        ),
      ],
    );
  }

  // DEBUG: Method to show FCM token
  Widget _buildDebugTokenButton() {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.orange.withValues(alpha: 0.1),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(
          color: Colors.orange.withValues(alpha: 0.3),
          width: 1,
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            '🔧 DEBUG: FCM Token',
            style: TextStyle(
              color: Colors.orange,
              fontWeight: FontWeight.bold,
              fontSize: 16,
            ),
          ),
          const SizedBox(height: 8),
          ElevatedButton(
            onPressed: _showFCMToken,
            style: ElevatedButton.styleFrom(
              backgroundColor: Colors.orange,
              foregroundColor: Colors.white,
            ),
            child: const Text('Show FCM Token'),
          ),
        ],
      ),
    );
  }

  Future<void> _showFCMToken() async {
    // Get FCM token from SharedPreferences
    final prefs = await SharedPreferences.getInstance();
    final token = prefs.getString('device_token') ?? 'No token found';
    
    // Show dialog with token
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        backgroundColor: AppColors.bgPrimary,
        title: const Text(
          'FCM Token',
          style: TextStyle(color: AppColors.textPrimary),
        ),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Copy this token for testing:',
              style: TextStyle(color: AppColors.textSecondary),
            ),
            const SizedBox(height: 8),
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: Colors.black,
                borderRadius: BorderRadius.circular(8),
              ),
              child: SelectableText(
                token,
                style: const TextStyle(
                  color: Colors.green,
                  fontFamily: 'monospace',
                  fontSize: 12,
                ),
              ),
            ),
            const SizedBox(height: 16),
            Text(
              'Token length: ${token.length}',
              style: TextStyle(
                color: AppColors.textSecondary,
                fontSize: 12,
              ),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Close'),
          ),
        ],
      ),
    );
  }
}

// Custom painter for the league badge
class LeagueBadgePainter extends CustomPainter {
  final Color primaryColor;
  final Color secondaryColor;
  final String league;

  LeagueBadgePainter({
    required this.primaryColor,
    required this.secondaryColor,
    required this.league,
  });

  @override
  void paint(Canvas canvas, Size size) {
    final center = Offset(size.width / 2, size.height / 2);
    final radius = size.width / 2;

    // Create gradient paint with subtle texture
    final gradientPaint = Paint()
      ..shader = RadialGradient(
        colors: [primaryColor, secondaryColor],
        stops: const [0.2, 1.0],
        center: const Alignment(-0.3, -0.3),
      ).createShader(Rect.fromCircle(center: center, radius: radius));

    // Draw main circle with subtle shadow
    final shadowPaint = Paint()
      ..color = Colors.black.withValues(alpha: 0.2)
      ..maskFilter = const MaskFilter.blur(BlurStyle.normal, 3);
    
    canvas.drawCircle(
      Offset(center.dx + 1, center.dy + 2), 
      radius - 2, 
      shadowPaint
    );
    
    // Draw main badge circle
    canvas.drawCircle(center, radius, gradientPaint);

    // Draw inner ring for depth
    final innerRingPaint = Paint()
      ..shader = LinearGradient(
        colors: [
          Colors.white.withValues(alpha: 0.15),
          Colors.white.withValues(alpha: 0.05),
        ],
        begin: Alignment.topLeft,
        end: Alignment.bottomRight,
      ).createShader(Rect.fromCircle(center: center, radius: radius - 8))
      ..style = PaintingStyle.stroke
      ..strokeWidth = 1.5;
    
    canvas.drawCircle(center, radius - 8, innerRingPaint);

    // Draw sophisticated carbon reduction symbol
    _drawCarbonReductionSymbol(canvas, center, size);

    // League-specific enhancements
    if (league == 'diamond') {
      _drawDiamondSparkles(canvas, center, radius);
    } else if (league == 'gold' || league == 'emerald') {
      _drawPremiumAccents(canvas, center, radius);
    }
  }

  void _drawCarbonReductionSymbol(Canvas canvas, Offset center, Size size) {
    // Create a sophisticated descending pattern representing reduction
    final symbolPaint = Paint()
      ..color = Colors.white.withValues(alpha: 0.25)
      ..style = PaintingStyle.fill;

    // Draw three circles in descending pattern
    final positions = [
      Offset(center.dx - 12, center.dy - 8),
      Offset(center.dx, center.dy),
      Offset(center.dx + 12, center.dy + 8),
    ];
    
    final sizes = [8.0, 6.0, 4.0];
    
    for (int i = 0; i < positions.length; i++) {
      // Outer glow
      final glowPaint = Paint()
        ..color = Colors.white.withValues(alpha: 0.1)
        ..maskFilter = const MaskFilter.blur(BlurStyle.normal, 3);
      canvas.drawCircle(positions[i], sizes[i] + 2, glowPaint);
      
      // Main circle
      canvas.drawCircle(positions[i], sizes[i], symbolPaint);
    }

    // Draw connecting flow line
    final path = Path();
    path.moveTo(positions[0].dx, positions[0].dy);
    
    // Create smooth curve through points
    final controlPoint1 = Offset(center.dx - 6, center.dy - 2);
    final controlPoint2 = Offset(center.dx + 6, center.dy + 2);
    
    path.cubicTo(
      controlPoint1.dx, controlPoint1.dy,
      controlPoint2.dx, controlPoint2.dy,
      positions[2].dx, positions[2].dy,
    );

    final flowPaint = Paint()
      ..color = Colors.white.withValues(alpha: 0.15)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 2
      ..strokeCap = StrokeCap.round;

    canvas.drawPath(path, flowPaint);

    // Add subtle arrow at the end
    final arrowPaint = Paint()
      ..color = Colors.white.withValues(alpha: 0.2)
      ..style = PaintingStyle.fill;

    final arrowPath = Path();
    final arrowTip = Offset(positions[2].dx + 3, positions[2].dy + 3);
    arrowPath.moveTo(arrowTip.dx, arrowTip.dy);
    arrowPath.lineTo(arrowTip.dx - 4, arrowTip.dy - 2);
    arrowPath.lineTo(arrowTip.dx - 2, arrowTip.dy - 4);
    arrowPath.close();
    
    canvas.drawPath(arrowPath, arrowPaint);
  }

  void _drawDiamondSparkles(Canvas canvas, Offset center, double radius) {
    final sparklePaint = Paint()
      ..color = Colors.white.withValues(alpha: 0.4)
      ..strokeWidth = 1.5;
    
    for (int i = 0; i < 8; i++) {
      final angle = i * 45 * (math.pi / 180);
      final innerRadius = radius - 15;
      final outerRadius = radius - 5;
      
      canvas.drawLine(
        Offset(
          center.dx + innerRadius * math.cos(angle),
          center.dy + innerRadius * math.sin(angle),
        ),
        Offset(
          center.dx + outerRadius * math.cos(angle),
          center.dy + outerRadius * math.sin(angle),
        ),
        sparklePaint,
      );
    }
  }

  void _drawPremiumAccents(Canvas canvas, Offset center, double radius) {
    final accentPaint = Paint()
      ..color = Colors.white.withValues(alpha: 0.1)
      ..style = PaintingStyle.fill;

    // Draw subtle dots at cardinal points
    for (int i = 0; i < 4; i++) {
      final angle = i * 90 * (math.pi / 180);
      final dotRadius = radius - 12;
      final x = center.dx + dotRadius * math.cos(angle);
      final y = center.dy + dotRadius * math.sin(angle);
      canvas.drawCircle(Offset(x, y), 2, accentPaint);
    }
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}

// Mini badge painter for the help dialog
class _MiniLeagueBadgePainter extends CustomPainter {
  final Color color;

  _MiniLeagueBadgePainter(this.color);

  @override
  void paint(Canvas canvas, Size size) {
    final center = Offset(size.width / 2, size.height / 2);
    
    // Draw the simplified carbon reduction symbol
    final symbolPaint = Paint()
      ..color = Colors.white.withValues(alpha: 0.7)
      ..style = PaintingStyle.fill;

    // Three descending circles
    final positions = [
      Offset(center.dx - 6, center.dy - 4),
      Offset(center.dx, center.dy),
      Offset(center.dx + 6, center.dy + 4),
    ];
    
    final sizes = [4.0, 3.0, 2.0];
    
    for (int i = 0; i < positions.length; i++) {
      canvas.drawCircle(positions[i], sizes[i], symbolPaint);
    }

    // Connecting line
    final path = Path();
    path.moveTo(positions[0].dx, positions[0].dy);
    path.quadraticBezierTo(
      center.dx, center.dy,
      positions[2].dx, positions[2].dy,
    );

    final flowPaint = Paint()
      ..color = Colors.white.withValues(alpha: 0.5)
      ..style = PaintingStyle.stroke
      ..strokeWidth = 1
      ..strokeCap = StrokeCap.round;

    canvas.drawPath(path, flowPaint);
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}