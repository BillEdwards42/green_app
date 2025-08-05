import 'package:flutter/material.dart';
import '../constants/app_colors.dart';
import '../constants/appliance_data.dart';
import '../models/appliance_model.dart';
import '../models/forecast_data_model.dart';
import '../services/api_service.dart';
import '../services/auth_service.dart';
import '../services/user_progress_service.dart';
import '../widgets/background_pattern.dart';

class LoggerScreen extends StatefulWidget {
  const LoggerScreen({super.key});

  @override
  State<LoggerScreen> createState() => _LoggerScreenState();
}

class _LoggerScreenState extends State<LoggerScreen> {
  final UserProgressService _progressService = UserProgressService();
  final AuthService _authService = AuthService();
  ApplianceModel? _selectedAppliance;
  Duration _selectedDuration = const Duration(hours: 1);
  List<ForecastDataModel>? _forecastData;
  DateTime? _lastFetchTime;
  double? _predictedSavings;
  double? _averageCarbonIntensity;
  double? _peakCarbonIntensity;
  bool _isDropdownOpen = false;
  int _consecutiveLogCount = 0;
  
  // Get max duration based on appliance
  Duration _getMaxDuration() {
    if (_selectedAppliance == null) return const Duration(hours: 8);
    
    switch (_selectedAppliance!.id) {
      case 'microwave':
        return const Duration(minutes: 30);
      case 'tv':
      case 'air_conditioner':
      case 'fan':
      case 'ev_fast_charge':
      case 'ev_slow_charge':
        return const Duration(hours: 8);
      default:
        return const Duration(hours: 4);
    }
  }
  
  // Get quick selection durations based on appliance
  List<MapEntry<String, Duration>> _getQuickDurations() {
    if (_selectedAppliance == null) {
      return [
        const MapEntry('30分', Duration(minutes: 30)),
        const MapEntry('1時', Duration(hours: 1)),
        const MapEntry('2時', Duration(hours: 2)),
        const MapEntry('4時', Duration(hours: 4)),
      ];
    }
    
    switch (_selectedAppliance!.id) {
      case 'microwave':
        return [
          const MapEntry('10分', Duration(minutes: 10)),
          const MapEntry('15分', Duration(minutes: 15)),
          const MapEntry('20分', Duration(minutes: 20)),
          const MapEntry('30分', Duration(minutes: 30)),
        ];
      case 'tv':
      case 'air_conditioner':
      case 'fan':
        return [
          const MapEntry('1時', Duration(hours: 1)),
          const MapEntry('2時', Duration(hours: 2)),
          const MapEntry('4時', Duration(hours: 4)),
          const MapEntry('8時', Duration(hours: 8)),
        ];
      case 'ev_fast_charge':
        return [
          const MapEntry('30分', Duration(minutes: 30)),
          const MapEntry('1時', Duration(hours: 1)),
          const MapEntry('2時', Duration(hours: 2)),
          const MapEntry('3時', Duration(hours: 3)),
        ];
      case 'ev_slow_charge':
        return [
          const MapEntry('2時', Duration(hours: 2)),
          const MapEntry('4時', Duration(hours: 4)),
          const MapEntry('6時', Duration(hours: 6)),
          const MapEntry('8時', Duration(hours: 8)),
        ];
      default:
        return [
          const MapEntry('30分', Duration(minutes: 30)),
          const MapEntry('1時', Duration(hours: 1)),
          const MapEntry('2時', Duration(hours: 2)),
          const MapEntry('4時', Duration(hours: 4)),
        ];
    }
  }

  @override
  void initState() {
    super.initState();
    _loadForecastData();
  }

  Future<void> _loadForecastData() async {
    final appData = await ApiService.fetchCarbonData();
    setState(() {
      _forecastData = appData.forecast;
      _lastFetchTime = DateTime.now();
    });
  }
  
  bool _isDataStale() {
    if (_lastFetchTime == null) return true;
    // Consider data stale if older than 10 minutes
    final now = DateTime.now();
    final difference = now.difference(_lastFetchTime!);
    return difference.inMinutes > 10;
  }

  void _calculateSavings() async {
    if (_selectedAppliance == null || _forecastData == null) return;
    
    // Don't calculate if duration is 0
    if (_selectedDuration.inMinutes == 0) {
      setState(() {
        _predictedSavings = null;
        _averageCarbonIntensity = null;
        _peakCarbonIntensity = null;
      });
      return;
    }
    
    // Check if data is stale and refresh if needed
    if (_isDataStale()) {
      await _loadForecastData();
    }

    // Get current hour and minute
    final now = DateTime.now();
    final currentHour = now.hour;
    final currentMinute = now.minute;
    
    // Find the starting index in forecast data
    int startIndex = 0;
    for (int i = 0; i < _forecastData!.length; i++) {
      final parts = _forecastData![i].time.split(':');
      final forecastHour = int.parse(parts[0]);
      final forecastMinute = int.parse(parts[1]);
      
      if (forecastHour == currentHour && forecastMinute >= currentMinute - 5) {
        startIndex = i;
        break;
      } else if (forecastHour > currentHour) {
        startIndex = i;
        break;
      }
    }
    
    // Calculate how many 10-minute intervals we need
    final intervals = (_selectedDuration.inMinutes / 10).ceil();
    
    // Calculate average intensity for the selected duration starting now
    double totalIntensity = 0;
    int count = 0;
    
    for (int i = startIndex; i < _forecastData!.length && count < intervals; i++) {
      totalIntensity += _forecastData![i].gco2KWh;
      count++;
    }
    
    // If we don't have enough data, use what we have
    final avgIntensity = count > 0 ? totalIntensity / count : _forecastData![startIndex].gco2KWh;
    
    // Find worst continuous period
    final worstIntensity = _findWorstContinuousPeriod(_selectedDuration);
    
    // Calculate emissions
    final durationHours = _selectedDuration.inMinutes / 60.0;
    final predictedEmission = avgIntensity * _selectedAppliance!.kw * durationHours;
    final worstEmission = worstIntensity * _selectedAppliance!.kw * durationHours;
    final savings = worstEmission - predictedEmission;
    
    setState(() {
      _predictedSavings = savings > 0 ? savings : 0;
      _averageCarbonIntensity = avgIntensity;
      _peakCarbonIntensity = worstIntensity;
    });
  }

  double _findWorstContinuousPeriod(Duration duration) {
    if (_forecastData == null || _forecastData!.isEmpty) return 0;
    
    double maxAvgIntensity = 0;
    final intervals = (duration.inMinutes / 10).ceil();
    
    // Make sure we have enough data points
    if (intervals > _forecastData!.length) {
      // If duration is longer than available data, use all data
      double sum = 0;
      for (final data in _forecastData!) {
        sum += data.gco2KWh;
      }
      return sum / _forecastData!.length;
    }
    
    // Find the worst continuous period
    for (int i = 0; i <= _forecastData!.length - intervals; i++) {
      double sum = 0;
      for (int j = 0; j < intervals; j++) {
        sum += _forecastData![i + j].gco2KWh;
      }
      final avg = sum / intervals;
      if (avg > maxAvgIntensity) {
        maxAvgIntensity = avg;
      }
    }
    
    return maxAvgIntensity;
  }


  void _startLogging() async {
    if (_selectedAppliance == null || _predictedSavings == null) return;
    
    // Ensure data is fresh before logging
    if (_isDataStale()) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('更新資料中...'),
          duration: Duration(seconds: 1),
        ),
      );
      await _loadForecastData();
      // Recalculate with fresh data
      _calculateSavings();
      return;
    }
    
    try {
      // Get auth token
      await _authService.initialize(); // Ensure auth service is initialized
      final token = _authService.token;
      print('Auth token in logger: $token');
      if (token == null) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('請先登入'),
            backgroundColor: AppColors.red,
          ),
        );
        return;
      }
      
      // Call backend API to log chore
      await ApiService.logChore(
        applianceType: _selectedAppliance!.id,
        startTime: DateTime.now(),
        durationMinutes: _selectedDuration.inMinutes,
        token: token,
      );
      
      // Track usage in progress service (for local UI updates)
      await _progressService.trackUsageLog(
        _selectedAppliance!.id,
        _predictedSavings!,
      );
      
      // Increment consecutive log count
      _consecutiveLogCount++;
      
      // Check if warning should be shown
      if (_consecutiveLogCount >= 5) {
        _showWarningDialog();
      }
      
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('已開始記錄 ${_selectedAppliance!.name}'),
          backgroundColor: AppColors.green,
          duration: const Duration(seconds: 2),
        ),
      );
      
      // Reset form
      setState(() {
        _selectedAppliance = null;
        _selectedDuration = const Duration(hours: 1);
        _predictedSavings = null;
        _averageCarbonIntensity = null;
        _peakCarbonIntensity = null;
      });
    } catch (e) {
      print('Failed to log chore: $e');
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('記錄失敗，請稍後再試'),
          backgroundColor: AppColors.red,
        ),
      );
    }
  }
  
  void _showWarningDialog() {
    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (BuildContext context) {
        return Dialog(
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(16),
          ),
          backgroundColor: AppColors.bgSecondary,
          child: Container(
            padding: const EdgeInsets.all(24),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                Container(
                  width: 60,
                  height: 60,
                  decoration: BoxDecoration(
                    color: AppColors.yellow.withValues(alpha: 0.1),
                    shape: BoxShape.circle,
                  ),
                  child: Icon(
                    Icons.warning_amber_rounded,
                    size: 32,
                    color: AppColors.yellow,
                  ),
                ),
                const SizedBox(height: 20),
                Text(
                  '友善提醒',
                  style: TextStyle(
                    fontSize: 20,
                    fontWeight: FontWeight.w700,
                    color: AppColors.textPrimary,
                  ),
                ),
                const SizedBox(height: 16),
                Text(
                  '在減碳時刻做更多家事當然很好！\n注意不要為了增加減碳而謊報使用喔！',
                  textAlign: TextAlign.center,
                  style: TextStyle(
                    fontSize: 16,
                    height: 1.5,
                    color: AppColors.textSecondary,
                  ),
                ),
                const SizedBox(height: 24),
                SizedBox(
                  width: double.infinity,
                  child: ElevatedButton(
                    onPressed: () {
                      Navigator.of(context).pop();
                      // Reset counter after showing warning
                      setState(() {
                        _consecutiveLogCount = 0;
                      });
                    },
                    style: ElevatedButton.styleFrom(
                      backgroundColor: AppColors.accent,
                      foregroundColor: AppColors.textPrimary,
                      padding: const EdgeInsets.symmetric(vertical: 14),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(12),
                      ),
                    ),
                    child: const Text(
                      '我了解了',
                      style: TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ),
                ),
              ],
            ),
          ),
        );
      },
    );
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
            child: SingleChildScrollView(
              padding: const EdgeInsets.all(16.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  const SizedBox(height: 20),
                  Text(
                    '記錄用電',
                    style: TextStyle(
                      fontSize: 28,
                      fontWeight: FontWeight.w700,
                      color: AppColors.textPrimary,
                      letterSpacing: 2.0,
                    ),
                    textAlign: TextAlign.center,
                  ),
                  const SizedBox(height: 8),
                  Text(
                    '現在開始減碳之旅',
                    style: TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.w400,
                      color: AppColors.textSecondary,
                      letterSpacing: 0.5,
                    ),
                    textAlign: TextAlign.center,
                  ),
                  const SizedBox(height: 40),
                  
                  // Step 1: Appliance Selection
                  _buildApplianceSelector(),
                  
                  const SizedBox(height: 24),
                  
                  // Step 2: Duration Input
                  _buildDurationInput(),
                  
                  const SizedBox(height: 24),
                  
                  // Step 3: Carbon Savings Preview
                  if (_predictedSavings != null)
                    _buildSavingsPreview(),
                  
                  const SizedBox(height: 32),
                  
                  // Start Button
                  _buildStartButton(),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildApplianceSelector() {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: AppColors.surface,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppColors.border),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            '選擇家電',
            style: TextStyle(
              fontSize: 18,
              fontWeight: FontWeight.w600,
              color: AppColors.textPrimary,
            ),
          ),
          const SizedBox(height: 16),
          // Custom dropdown implementation
          GestureDetector(
            onTap: () {
              setState(() {
                _isDropdownOpen = !_isDropdownOpen;
              });
            },
            child: Container(
              decoration: BoxDecoration(
                color: AppColors.bgSecondary,
                borderRadius: BorderRadius.circular(12),
                border: Border.all(
                  color: _isDropdownOpen ? AppColors.accent : AppColors.border,
                ),
              ),
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
              child: Row(
                children: [
                  if (_selectedAppliance != null) ...[
                    Text(
                      _selectedAppliance!.icon,
                      style: const TextStyle(fontSize: 24),
                    ),
                    const SizedBox(width: 12),
                  ],
                  Expanded(
                    child: Text(
                      _selectedAppliance?.name ?? '請選擇家電',
                      style: TextStyle(
                        color: _selectedAppliance != null 
                            ? AppColors.textPrimary 
                            : AppColors.textSecondary,
                        fontSize: 16,
                      ),
                    ),
                  ),
                  if (_selectedAppliance != null)
                    Text(
                      '${_selectedAppliance!.kw} kW',
                      style: TextStyle(
                        color: AppColors.textSecondary,
                        fontSize: 14,
                      ),
                    ),
                  const SizedBox(width: 8),
                  Icon(
                    _isDropdownOpen ? Icons.arrow_drop_up : Icons.arrow_drop_down,
                    color: AppColors.textSecondary,
                  ),
                ],
              ),
            ),
          ),
          if (_isDropdownOpen) ...[
            const SizedBox(height: 8),
            Container(
              constraints: const BoxConstraints(maxHeight: 300),
              decoration: BoxDecoration(
                color: AppColors.bgSecondary,
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: AppColors.border),
                boxShadow: [
                  BoxShadow(
                    color: Colors.black.withValues(alpha: 0.1),
                    blurRadius: 8,
                    offset: const Offset(0, 4),
                  ),
                ],
              ),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  // Collapse button
                  Container(
                    decoration: BoxDecoration(
                      border: Border(bottom: BorderSide(color: AppColors.border)),
                    ),
                    child: Material(
                      color: Colors.transparent,
                      child: InkWell(
                        onTap: () {
                          setState(() {
                            _isDropdownOpen = false;
                          });
                        },
                        borderRadius: const BorderRadius.vertical(top: Radius.circular(12)),
                        child: Padding(
                          padding: const EdgeInsets.symmetric(vertical: 12),
                          child: Row(
                            mainAxisAlignment: MainAxisAlignment.center,
                            children: [
                              Icon(Icons.close, size: 20, color: AppColors.textSecondary),
                              const SizedBox(width: 8),
                              Text(
                                '關閉',
                                style: TextStyle(
                                  color: AppColors.textSecondary,
                                  fontSize: 14,
                                ),
                              ),
                            ],
                          ),
                        ),
                      ),
                    ),
                  ),
                  // Appliance list
                  Flexible(
                    child: ListView(
                      shrinkWrap: true,
                      padding: EdgeInsets.zero,
                      children: ApplianceData.getSortedAppliances().map((appliance) {
                        final isSelected = _selectedAppliance?.id == appliance.id;
                        return Material(
                          color: Colors.transparent,
                          child: InkWell(
                            onTap: () {
                              setState(() {
                                _selectedAppliance = appliance;
                                _isDropdownOpen = false;
                                // Reset duration to default when appliance changes
                                _selectedDuration = const Duration(hours: 1);
                                // Adjust if duration exceeds new max
                                final maxDuration = _getMaxDuration();
                                if (_selectedDuration > maxDuration) {
                                  _selectedDuration = maxDuration;
                                }
                              });
                              _calculateSavings();
                            },
                            child: Container(
                              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                              decoration: BoxDecoration(
                                color: isSelected 
                                    ? AppColors.accent.withValues(alpha: 0.1) 
                                    : Colors.transparent,
                              ),
                              child: Row(
                                children: [
                                  Text(
                                    appliance.icon,
                                    style: const TextStyle(fontSize: 24),
                                  ),
                                  const SizedBox(width: 12),
                                  Expanded(
                                    child: Text(
                                      appliance.name,
                                      style: TextStyle(
                                        color: isSelected 
                                            ? AppColors.accent 
                                            : AppColors.textPrimary,
                                        fontSize: 16,
                                        fontWeight: isSelected 
                                            ? FontWeight.w600 
                                            : FontWeight.w400,
                                      ),
                                    ),
                                  ),
                                  Text(
                                    '${appliance.kw} kW',
                                    style: TextStyle(
                                      color: AppColors.textSecondary,
                                      fontSize: 14,
                                    ),
                                  ),
                                ],
                              ),
                            ),
                          ),
                        );
                      }).toList(),
                    ),
                  ),
                ],
              ),
            ),
          ],
        ],
      ),
    );
  }

  Widget _buildDurationInput() {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: AppColors.surface,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppColors.border),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            '使用時長',
            style: TextStyle(
              fontSize: 18,
              fontWeight: FontWeight.w600,
              color: AppColors.textPrimary,
            ),
          ),
          const SizedBox(height: 16),
          
          // Quick selection buttons
          Wrap(
            spacing: 8,
            children: _getQuickDurations().map((entry) {
              return _buildDurationChip(entry.key, entry.value);
            }).toList(),
          ),
          
          const SizedBox(height: 16),
          
          // Custom duration display
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
            decoration: BoxDecoration(
              color: AppColors.bgSecondary,
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: AppColors.border),
            ),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Icon(Icons.access_time, color: AppColors.textSecondary, size: 20),
                const SizedBox(width: 8),
                Text(
                  '${_selectedDuration.inHours}小時 ${_selectedDuration.inMinutes % 60}分鐘',
                  style: TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.w500,
                    color: AppColors.textPrimary,
                  ),
                ),
              ],
            ),
          ),
          
          const SizedBox(height: 16),
          
          // Duration slider
          SliderTheme(
            data: SliderThemeData(
              activeTrackColor: AppColors.accent,
              inactiveTrackColor: AppColors.border,
              thumbColor: AppColors.accent,
              overlayColor: AppColors.accent.withValues(alpha: 0.2),
            ),
            child: Slider(
              value: _selectedDuration.inMinutes.toDouble(),
              min: 0,
              max: _getMaxDuration().inMinutes.toDouble(),
              divisions: _getMaxDuration().inMinutes,
              onChanged: (double value) {
                setState(() {
                  _selectedDuration = Duration(minutes: value.round());
                });
                _calculateSavings();
              },
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildDurationChip(String label, Duration duration) {
    final isSelected = _selectedDuration == duration;
    return GestureDetector(
      onTap: () {
        setState(() {
          _selectedDuration = duration;
        });
        _calculateSavings();
      },
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
        decoration: BoxDecoration(
          color: isSelected ? AppColors.accent : AppColors.bgSecondary,
          borderRadius: BorderRadius.circular(20),
          border: Border.all(
            color: isSelected ? AppColors.accent : AppColors.border,
          ),
        ),
        child: Text(
          label,
          style: TextStyle(
            color: isSelected ? AppColors.textPrimary : AppColors.textSecondary,
            fontWeight: isSelected ? FontWeight.w600 : FontWeight.w400,
          ),
        ),
      ),
    );
  }

  Widget _buildSavingsPreview() {
    final hours = _selectedDuration.inHours;
    final minutes = _selectedDuration.inMinutes % 60;
    String durationText = '';
    if (hours > 0) {
      durationText += '$hours小時';
    }
    if (minutes > 0) {
      durationText += '$minutes分鐘';
    }
    
    return AnimatedContainer(
      duration: const Duration(milliseconds: 300),
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [
            AppColors.green.withValues(alpha: 0.1),
            AppColors.green.withValues(alpha: 0.05),
          ],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppColors.green.withValues(alpha: 0.3)),
      ),
      child: Column(
        children: [
          Text(
            '現在開始使用${_selectedAppliance!.name}$durationText',
            style: TextStyle(
              fontSize: 16,
              fontWeight: FontWeight.w500,
              color: AppColors.textPrimary,
            ),
            textAlign: TextAlign.center,
          ),
          const SizedBox(height: 12),
          Text(
            '預計少排放',
            style: TextStyle(
              fontSize: 14,
              color: AppColors.textSecondary,
            ),
          ),
          const SizedBox(height: 8),
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Text(
                '${_predictedSavings!.toStringAsFixed(0)} gCO₂',
                style: TextStyle(
                  fontSize: 36,
                  fontWeight: FontWeight.w700,
                  color: AppColors.green,
                ),
              ),
              const SizedBox(width: 8),
              Text(
                '🌱',
                style: const TextStyle(fontSize: 24),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildStartButton() {
    final isEnabled = _selectedAppliance != null && _predictedSavings != null;
    
    return GestureDetector(
      onTap: isEnabled ? _startLogging : null,
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 16),
        decoration: BoxDecoration(
          color: isEnabled ? AppColors.accent : AppColors.surface,
          borderRadius: BorderRadius.circular(12),
          border: Border.all(
            color: isEnabled ? AppColors.accent : AppColors.border,
          ),
          boxShadow: isEnabled ? [
            BoxShadow(
              color: AppColors.accent.withValues(alpha: 0.3),
              blurRadius: 12,
              offset: const Offset(0, 4),
            ),
          ] : [],
        ),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Text(
              '現在開始',
              style: TextStyle(
                fontSize: 18,
                fontWeight: FontWeight.w600,
                color: isEnabled ? AppColors.textPrimary : AppColors.textSecondary,
              ),
            ),
            if (isEnabled) ...[
              const SizedBox(width: 8),
              Icon(
                Icons.bolt,
                color: AppColors.textPrimary,
                size: 24,
              ),
            ],
          ],
        ),
      ),
    );
  }
}