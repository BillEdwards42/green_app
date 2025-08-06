import 'package:flutter/material.dart';
import '../constants/app_colors.dart';
import '../models/app_data_model.dart';
import '../services/api_service.dart';
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
    with TickerProviderStateMixin, WidgetsBindingObserver {
  AppDataModel? _appData;
  bool _isRefreshing = false;
  bool _isModalOpen = false;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
    _initializeApp();
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    super.dispose();
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (state == AppLifecycleState.resumed) {
      // Refresh data when app comes back from background
      _refreshData();
    }
  }

  Future<void> _initializeApp() async {
    // Load initial data
    await _loadInitialData();
  }

  Future<void> _loadInitialData() async {
    setState(() => _isRefreshing = true);
    try {
      final data = await ApiService.fetchCarbonData();
      if (mounted) {
        setState(() {
          _appData = data;
          _isRefreshing = false;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() => _isRefreshing = false);
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('無法連接到伺服器: ${e.toString()}'),
            duration: const Duration(seconds: 3),
          ),
        );
      }
    }
  }

  Future<void> _refreshData() async {
    if (_isRefreshing) return;
    
    setState(() => _isRefreshing = true);
    try {
      final data = await ApiService.fetchCarbonData();
      if (mounted) {
        setState(() {
          _appData = data;
          _isRefreshing = false;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() => _isRefreshing = false);
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('無法更新資料: ${e.toString()}'),
            duration: const Duration(seconds: 3),
          ),
        );
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
                child: SingleChildScrollView(
                  padding: const EdgeInsets.symmetric(horizontal: 16.0),
                  child: Column(
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
                      ),
                      
                      const SizedBox(height: 20),
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