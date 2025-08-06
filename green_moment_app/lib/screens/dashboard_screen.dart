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

// Simple data class for daily carbon data
class DailyCarbonData {
  final DateTime date;
  final double carbon;
  
  DailyCarbonData({required this.date, required this.carbon});
  
  factory DailyCarbonData.fromJson(Map<String, dynamic> json) {
    return DailyCarbonData(
      date: DateTime.parse(json['date']),
      carbon: (json['carbon'] ?? 0.0).toDouble(),
    );
  }
}

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
  
  // Carbon tracking data
  double _yesterdayCarbon = 0.0;
  double _monthlyCarbon = 0.0;
  double _monthlyTarget = 0.0;

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
        _monthlyTarget = _getMonthlyTarget(progress.currentLeague);
      });
      await _loadCarbonData();
      setState(() {
        _isLoading = false;
      });
    } catch (e) {
      setState(() {
        _isLoading = false;
      });
    }
  }
  
  Future<void> _loadCarbonData() async {
    try {
      // Get carbon data from progress response
      final progressData = await _progressService.apiService.get('/progress/summary');
      
      if (progressData.data != null) {
        setState(() {
          _monthlyCarbon = (progressData.data['current_month_co2e_saved_g'] ?? 0.0).toDouble();
          // Monthly target is already set in _loadUserProgress
        });
      }
      
      // Get yesterday's carbon from daily carbon progress
      final yesterday = DateTime.now().subtract(const Duration(days: 1));
      final yesterdayStr = '${yesterday.year}-${yesterday.month.toString().padLeft(2, '0')}-${yesterday.day.toString().padLeft(2, '0')}';
      
      try {
        final dailyProgress = await _progressService.apiService.get('/progress/daily-carbon?date=$yesterdayStr');
        if (dailyProgress.data != null) {
          setState(() {
            _yesterdayCarbon = (dailyProgress.data['carbon_saved'] ?? 0.0).toDouble();
          });
        }
      } catch (e) {
        print('Error loading yesterday carbon: $e');
        setState(() {
          _yesterdayCarbon = 0.0;
        });
      }
    } catch (e) {
      print('Error loading carbon data: $e');
    }
  }
  
  double _getMonthlyTarget(String league) {
    switch (league) {
      case 'bronze':
        return 30.0;  // Target to reach Silver
      case 'silver':
        return 300.0;  // Target to reach Gold
      case 'gold':
        return 500.0;  // Target to reach Emerald
      case 'emerald':
        return 1000.0;  // Target to reach Diamond
      case 'diamond':
        return double.infinity;  // Max level - no further promotion
      default:
        return 30.0;
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
              onComplete: () {
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
                              _buildLeagueAndMonthlySection(),
                          const SizedBox(height: 20),
                          _buildCarbonSummarySection(),
                          const SizedBox(height: 20),
                          _buildFooterNote(),
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

  Widget _buildLeagueAndMonthlySection() {
    final progress = _userProgress?.currentLeague == 'diamond' 
        ? 1.0  // Diamond league always shows full progress
        : (_monthlyTarget > 0 ? (_monthlyCarbon / _monthlyTarget).clamp(0.0, 1.0) : 0.0);
    final leagueData = _getLeagueData(_userProgress?.currentLeague ?? 'bronze');
    
    // Get current month name
    final now = DateTime.now();
    final monthNames = ['', '一月', '二月', '三月', '四月', '五月', '六月', 
                       '七月', '八月', '九月', '十月', '十一月', '十二月'];
    final currentMonthName = monthNames[now.month];
    
    return Container(
      padding: const EdgeInsets.all(24),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
          colors: [
            AppColors.green.withValues(alpha: 0.08),
            AppColors.green.withValues(alpha: 0.04),
          ],
        ),
        borderRadius: BorderRadius.circular(24),
        border: Border.all(
          color: AppColors.green.withValues(alpha: 0.15),
          width: 1,
        ),
      ),
      child: Row(
        children: [
          // League Badge
          AnimatedBuilder(
            animation: _pulseAnimation,
            builder: (context, child) {
              return Transform.scale(
                scale: _pulseAnimation.value,
                child: Container(
                  width: 80,
                  height: 80,
                  decoration: BoxDecoration(
                    shape: BoxShape.circle,
                    gradient: RadialGradient(
                      colors: [
                        leagueData['colors'][0],
                        leagueData['colors'][1],
                      ],
                    ),
                    boxShadow: [
                      BoxShadow(
                        color: leagueData['colors'][0].withValues(alpha: 0.4),
                        blurRadius: 15,
                        spreadRadius: 2,
                      ),
                    ],
                  ),
                  child: Center(
                    child: _buildLeagueIcon(_userProgress?.currentLeague ?? 'bronze'),
                  ),
                ),
              );
            },
          ),
          const SizedBox(width: 20),
          // Monthly Progress
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          '${currentMonthName}目前碳減量',
                          style: TextStyle(
                            fontSize: 16,
                            fontWeight: FontWeight.bold,
                            color: AppColors.textPrimary,
                            letterSpacing: 0.5,
                          ),
                        ),
                        const SizedBox(height: 2),
                        Text(
                          leagueData['name'],
                          style: TextStyle(
                            fontSize: 12,
                            fontWeight: FontWeight.w500,
                            color: AppColors.textSecondary,
                          ),
                        ),
                      ],
                    ),
                    Text(
                      _userProgress?.currentLeague == 'diamond' 
                        ? 'MAX' 
                        : '${(progress * 100).toInt()}%',
                      style: TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.w600,
                        color: AppColors.green,
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 8),
                Row(
                  crossAxisAlignment: CrossAxisAlignment.end,
                  children: [
                    Text(
                      _monthlyCarbon.toStringAsFixed(0),
                      style: TextStyle(
                        fontSize: 28,
                        fontWeight: FontWeight.bold,
                        color: AppColors.green,
                        height: 1,
                      ),
                    ),
                    Padding(
                      padding: const EdgeInsets.only(bottom: 4, left: 4),
                      child: Text(
                        _userProgress?.currentLeague == 'diamond' 
                          ? 'g / max' 
                          : 'g / ${_monthlyTarget.toStringAsFixed(0)} g',
                        style: TextStyle(
                          fontSize: 14,
                          fontWeight: FontWeight.w500,
                          color: AppColors.textSecondary,
                        ),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 12),
                ClipRRect(
                  borderRadius: BorderRadius.circular(6),
                  child: LinearProgressIndicator(
                    value: progress,
                    minHeight: 10,
                    backgroundColor: AppColors.textPrimary.withValues(alpha: 0.1),
                    valueColor: AlwaysStoppedAnimation<Color>(AppColors.green),
                  ),
                ),
                if (_monthlyCarbon > 0) ...[
                  const SizedBox(height: 12),
                  GestureDetector(
                    onTap: _showTreeCalculationInfo,
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Text(
                          '🌳 ${(_monthlyCarbon / 1000 / 25).toStringAsFixed(2)} 棵樹',
                          style: TextStyle(
                            fontSize: 13,
                            color: AppColors.green,
                            fontWeight: FontWeight.w500,
                          ),
                        ),
                        const SizedBox(width: 4),
                        Icon(
                          Icons.info_outline,
                          size: 14,
                          color: AppColors.green.withValues(alpha: 0.7),
                        ),
                      ],
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
  
  Widget _buildLeagueIcon(String league) {
    IconData icon;
    switch (league) {
      case 'bronze':
        icon = Icons.eco;
        break;
      case 'silver':
        icon = Icons.star_half;
        break;
      case 'gold':
        icon = Icons.star;
        break;
      case 'emerald':
        icon = Icons.diamond;
        break;
      case 'diamond':
        icon = Icons.workspace_premium;
        break;
      default:
        icon = Icons.eco;
    }
    
    return Icon(
      icon,
      color: Colors.white,
      size: 40,
    );
  }
  
  Widget _buildCarbonSummarySection() {
    return Column(
      children: [
        // Title for the section
        Padding(
          padding: const EdgeInsets.only(bottom: 16),
          child: Row(
            children: [
              Icon(
                Icons.analytics_outlined,
                color: AppColors.textPrimary,
                size: 20,
              ),
              const SizedBox(width: 8),
              Text(
                '碳減量數據',
                style: TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.w600,
                  color: AppColors.textPrimary,
                  letterSpacing: 0.5,
                ),
              ),
            ],
          ),
        ),
        // Two cards side by side
        LayoutBuilder(
          builder: (context, constraints) {
            // On smaller screens, stack vertically
            if (constraints.maxWidth < 500) {
              return Column(
                children: [
                  _buildMonthlySummaryCard(),
                  const SizedBox(height: 12),
                  _buildYesterdayCard(),
                ],
              );
            }
            // On larger screens, show side by side
            return Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Expanded(child: _buildMonthlySummaryCard()),
                const SizedBox(width: 12),
                Expanded(child: _buildYesterdayCard()),
              ],
            );
          },
        ),
      ],
    );
  }
  
  Widget _buildMonthlySummaryCard() {
    final lastMonthCarbon = _userProgress?.lastMonthCarbonSaved ?? 0.0;
    final lastMonthCarbonKg = lastMonthCarbon / 1000.0;
    
    final now = DateTime.now();
    final lastMonth = now.month == 1 
        ? DateTime(now.year - 1, 12) 
        : DateTime(now.year, now.month - 1);
    final monthNames = ['', '一月', '二月', '三月', '四月', '五月', '六月', 
                       '七月', '八月', '九月', '十月', '十一月', '十二月'];
    final lastMonthName = monthNames[lastMonth.month];
    
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: AppColors.bgSecondary.withValues(alpha: 0.7),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(
          color: AppColors.textPrimary.withValues(alpha: 0.1),
          width: 1,
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(
                Icons.history,
                color: AppColors.textSecondary,
                size: 18,
              ),
              const SizedBox(width: 6),
              Text(
                lastMonthName,
                style: TextStyle(
                  fontSize: 14,
                  fontWeight: FontWeight.w600,
                  color: AppColors.textPrimary,
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          Text(
            lastMonthCarbonKg.toStringAsFixed(2),
            style: TextStyle(
              fontSize: 32,
              fontWeight: FontWeight.bold,
              color: lastMonthCarbon > 0 ? AppColors.green : AppColors.textSecondary,
              height: 1.1,
            ),
          ),
          Text(
            'kg CO₂e',
            style: TextStyle(
              fontSize: 14,
              color: AppColors.textSecondary,
              fontWeight: FontWeight.w500,
            ),
          ),
          if (lastMonthCarbon > 0) ...[
            const SizedBox(height: 12),
            GestureDetector(
              onTap: _showTreeCalculationInfo,
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Text(
                    '🌳 ${(lastMonthCarbon / 1000 / 25).toStringAsFixed(2)} 棵樹',
                    style: TextStyle(
                      fontSize: 12,
                      color: AppColors.green,
                      fontWeight: FontWeight.w500,
                    ),
                  ),
                  const SizedBox(width: 4),
                  Icon(
                    Icons.info_outline,
                    size: 12,
                    color: AppColors.green.withValues(alpha: 0.7),
                  ),
                ],
              ),
            ),
          ],
        ],
      ),
    );
  }
  
  Widget _buildYesterdayCard() {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: AppColors.bgSecondary.withValues(alpha: 0.7),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(
          color: AppColors.textPrimary.withValues(alpha: 0.1),
          width: 1,
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(
                Icons.calendar_today,
                color: AppColors.textSecondary,
                size: 18,
              ),
              const SizedBox(width: 6),
              Text(
                '昨日',
                style: TextStyle(
                  fontSize: 14,
                  fontWeight: FontWeight.w600,
                  color: AppColors.textPrimary,
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          Text(
            _yesterdayCarbon.toStringAsFixed(1),
            style: TextStyle(
              fontSize: 32,
              fontWeight: FontWeight.bold,
              color: _yesterdayCarbon > 0 ? AppColors.green : AppColors.textSecondary,
              height: 1.1,
            ),
          ),
          Text(
            'g CO₂e',
            style: TextStyle(
              fontSize: 14,
              color: AppColors.textSecondary,
              fontWeight: FontWeight.w500,
            ),
          ),
          if (_yesterdayCarbon > 0) ...[
            const SizedBox(height: 12),
            GestureDetector(
              onTap: _showTreeCalculationInfo,
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Text(
                    '🌳 ${(_yesterdayCarbon / 1000 / 25).toStringAsFixed(2)} 棵樹',
                    style: TextStyle(
                      fontSize: 12,
                      color: AppColors.green,
                      fontWeight: FontWeight.w500,
                    ),
                  ),
                  const SizedBox(width: 4),
                  Icon(
                    Icons.info_outline,
                    size: 12,
                    color: AppColors.green.withValues(alpha: 0.7),
                  ),
                ],
              ),
            ),
          ],
        ],
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

  // Removed task section - no longer needed in carbon-only system

  Widget _buildFooterNote() {
    // Get current month name
    final now = DateTime.now();
    final monthNames = ['', '一月', '二月', '三月', '四月', '五月', '六月', 
                       '七月', '八月', '九月', '十月', '十一月', '十二月'];
    final currentMonthName = monthNames[now.month];
    
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppColors.textPrimary.withValues(alpha: 0.04),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Column(
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(
                Icons.info_outline,
                size: 16,
                color: AppColors.textSecondary,
              ),
              const SizedBox(width: 8),
              Text(
                '聯盟升級基於每月碳減量達成',
                style: TextStyle(
                  fontSize: 14,
                  color: AppColors.textSecondary,
                  fontWeight: FontWeight.w400,
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),
          Text(
            '${currentMonthName}碳減量與昨日碳減量均在每日12AM更新昨日之進度',
            style: TextStyle(
              fontSize: 12,
              color: AppColors.textSecondary.withValues(alpha: 0.8),
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
                    '達成每月碳減量目標即可晉級到下一個聯盟。開始減少碳排放吧！',
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
                    '起始聯盟',
                  ),
                  const SizedBox(height: 12),
                  _buildLeagueHelpItem(
                    '白銀聯盟',
                    const Color(0xFFC0C0C0),
                    '目標: 100g CO₂e/月',
                  ),
                  const SizedBox(height: 12),
                  _buildLeagueHelpItem(
                    '黃金聯盟',
                    const Color(0xFFFFD700),
                    '目標: 500g CO₂e/月',
                  ),
                  const SizedBox(height: 12),
                  _buildLeagueHelpItem(
                    '翡翠聯盟',
                    const Color(0xFF50C878),
                    '目標: 700g CO₂e/月',
                  ),
                  const SizedBox(height: 12),
                  _buildLeagueHelpItem(
                    '鑽石聯盟',
                    const Color(0xFF87CEEB),
                    '目標: 1000g CO₂e/月',
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
                            '每月1日系統會根據您的碳減量達成情況決定是否晉級',
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
  
  IconData _getLeagueIconData(String leagueName) {
    if (leagueName.contains('青銅')) return Icons.eco;
    if (leagueName.contains('白銀')) return Icons.star_half;
    if (leagueName.contains('黃金')) return Icons.star;
    if (leagueName.contains('翡翠')) return Icons.diamond;
    if (leagueName.contains('鑽石')) return Icons.workspace_premium;
    return Icons.eco;
  }

  Widget _buildLeagueHelpItem(String name, Color color, String target) {
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
          child: Center(
            child: Icon(
              _getLeagueIconData(name),
              color: Colors.white,
              size: 24,
            ),
          ),
        ),
        const SizedBox(width: 16),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                name,
                style: TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.w600,
                  color: AppColors.textPrimary,
                ),
              ),
              Text(
                target,
                style: TextStyle(
                  fontSize: 12,
                  color: AppColors.textSecondary,
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }

  void _showTreeCalculationInfo() {
    showDialog(
      context: context,
      builder: (context) => Dialog(
        backgroundColor: AppColors.bgPrimary,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(20),
        ),
        child: Container(
          constraints: const BoxConstraints(maxWidth: 350),
          padding: const EdgeInsets.all(24),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Text(
                    '🌳',
                    style: TextStyle(fontSize: 28),
                  ),
                  const SizedBox(width: 12),
                  Text(
                    '樹木減碳計算說明',
                    style: TextStyle(
                      fontSize: 20,
                      fontWeight: FontWeight.bold,
                      color: AppColors.textPrimary,
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 16),
              Container(
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: AppColors.bgSecondary.withValues(alpha: 0.5),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      '計算基準',
                      style: TextStyle(
                        fontSize: 14,
                        fontWeight: FontWeight.w600,
                        color: AppColors.textPrimary,
                      ),
                    ),
                    const SizedBox(height: 8),
                    Text(
                      '• 一棵樹每年吸收約 25 公斤 CO₂e\n'
                      '• 1 kg CO₂e = 種植 0.04 棵樹\n'
                      '• 此為科學研究平均值',
                      style: TextStyle(
                        fontSize: 13,
                        color: AppColors.textSecondary,
                        height: 1.5,
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 16),
              Text(
                '實際吸收量會因樹種、樹齡、地理位置等因素而有所不同。',
                style: TextStyle(
                  fontSize: 12,
                  color: AppColors.textSecondary,
                  fontStyle: FontStyle.italic,
                ),
              ),
              const SizedBox(height: 20),
              Center(
                child: TextButton(
                  onPressed: () => Navigator.pop(context),
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
    );
  }
}