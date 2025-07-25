import 'package:flutter/material.dart';
import '../constants/app_colors.dart';
import '../widgets/custom_bottom_nav.dart';
import 'home_screen.dart';
import 'logger_screen.dart';
import 'dashboard_screen.dart';

class MainScreen extends StatefulWidget {
  const MainScreen({super.key});

  @override
  State<MainScreen> createState() => _MainScreenState();
}

class _MainScreenState extends State<MainScreen> {
  int _currentIndex = 1; // Start with home screen (middle tab)
  final GlobalKey<DashboardScreenState> _dashboardKey = GlobalKey<DashboardScreenState>();

  late final List<Widget> _screens;

  @override
  void initState() {
    super.initState();
    _screens = [
      const LoggerScreen(),
      const HomeScreen(),
      DashboardScreen(key: _dashboardKey),
    ];
  }

  void _onNavTap(int index) {
    setState(() {
      _currentIndex = index;
    });
    
    // Refresh dashboard when switching to it
    if (index == 2) {  // Dashboard is at index 2
      _dashboardKey.currentState?.refreshData();
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.bgPrimary,
      body: IndexedStack(
        index: _currentIndex,
        children: _screens,
      ),
      bottomNavigationBar: CustomBottomNav(
        currentIndex: _currentIndex,
        onTap: _onNavTap,
      ),
    );
  }
}