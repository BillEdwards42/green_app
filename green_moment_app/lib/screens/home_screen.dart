import 'package:flutter/material.dart';
import '../constants/app_colors.dart';
import '../models/app_data_model.dart';
import '../services/mock_data_service.dart';
import '../services/notification_service.dart';
import '../services/settings_service.dart';
import '../widgets/app_header.dart';
import '../widgets/carbon_intensity_ring.dart';
import '../widgets/status_card.dart';
import '../widgets/forecast_modal.dart';
import '../widgets/background_pattern.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen>
    with TickerProviderStateMixin {
  AppDataModel? _appData;
  bool _isRefreshing = false;
  bool _isModalOpen = false;
  bool _notificationEnabled = true;

  @override
  void initState() {
    super.initState();
    _initializeApp();
  }

  Future<void> _initializeApp() async {
    // Initialize notification service
    await NotificationService.initialize();
    await NotificationService.requestPermissions();
    
    // Load notification settings
    final enabled = await SettingsService.getNotificationEnabled();
    setState(() {
      _notificationEnabled = enabled;
    });
    
    // Schedule notifications if enabled
    if (enabled) {
      await NotificationService.scheduleDailyFetchAndNotification();
    }
    
    // Load initial data
    await _loadInitialData();
  }

  Future<void> _loadInitialData() async {
    setState(() => _isRefreshing = true);
    try {
      final data = await MockDataService.fetchCarbonData();
      if (mounted) {
        setState(() {
          _appData = data;
          _isRefreshing = false;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() => _isRefreshing = false);
      }
    }
  }

  Future<void> _refreshData() async {
    if (_isRefreshing) return;
    
    setState(() => _isRefreshing = true);
    try {
      final data = await MockDataService.fetchCarbonData();
      if (mounted) {
        setState(() {
          _appData = data;
          _isRefreshing = false;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() => _isRefreshing = false);
      }
    }
  }

  void _openForecastModal() {
    if (_appData?.forecast != null) {
      setState(() => _isModalOpen = true);
    }
  }

  void _closeForecastModal() {
    setState(() => _isModalOpen = false);
  }

  Future<void> _onNotificationToggle(bool enabled) async {
    setState(() {
      _notificationEnabled = enabled;
    });
    
    await SettingsService.setNotificationEnabled(enabled);
    await NotificationService.rescheduleIfEnabled();
    
    // Show a test notification if enabled
    if (enabled) {
      await NotificationService.showTestNotification();
    }
  }

  @override
  Widget build(BuildContext context) {
    return Stack(
      children: [
        // Background pattern
        const Positioned.fill(
          child: BackgroundPattern(),
        ),
        
        // Main content
        SafeArea(
          child: Column(
            children: [
              // Header
              AppHeader(
                timeText: _appData?.formattedLastUpdated ?? '載入中...',
                isRefreshing: _isRefreshing,
                onRefresh: _refreshData,
              ),
              
              // Main content
              Expanded(
                child: Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 16.0),
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.start,
                    children: [
                      const SizedBox(height: 40),
                      
                      // Carbon intensity ring
                      CarbonIntensityRing(
                        intensity: _appData?.currentIntensity,
                        isLoading: _isRefreshing,
                      ),
                      
                      const SizedBox(height: 24),
                      
                      // Status card
                      StatusCard(
                        intensity: _appData?.currentIntensity,
                        recommendation: _appData?.recommendation,
                        isLoading: _isRefreshing,
                        onForecastTap: _openForecastModal,
                        notificationEnabled: _notificationEnabled,
                        onNotificationToggle: _onNotificationToggle,
                      ),
                    ],
                  ),
                ),
              ),
            ],
          ),
        ),
        
        // Forecast modal
        if (_isModalOpen && _appData != null)
          ForecastModal(
            currentIntensity: _appData!.currentIntensity,
            forecastData: _appData!.forecast,
            lastUpdated: _appData!.formattedLastUpdated,
            onClose: _closeForecastModal,
          ),
      ],
    );
  }
}