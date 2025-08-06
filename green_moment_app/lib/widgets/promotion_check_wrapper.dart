import 'package:flutter/material.dart';
import '../services/user_progress_service.dart';
import '../widgets/league_upgrade_animation.dart';

class PromotionCheckWrapper extends StatefulWidget {
  final Widget child;
  final String? previousLeague;

  const PromotionCheckWrapper({
    super.key,
    required this.child,
    this.previousLeague,
  });

  @override
  State<PromotionCheckWrapper> createState() => _PromotionCheckWrapperState();
}

class _PromotionCheckWrapperState extends State<PromotionCheckWrapper> {
  final UserProgressService _progressService = UserProgressService();
  bool _isChecking = true;
  bool _showAnimation = false;
  String? _oldLeague;
  String? _newLeague;

  @override
  void initState() {
    super.initState();
    _checkPromotion();
  }

  Future<void> _checkPromotion() async {
    print('🎯 PromotionCheckWrapper: Starting promotion check');
    print('🎯 Previous league from widget: ${widget.previousLeague}');
    
    try {
      final progress = await _progressService.getUserProgress();
      print('🎯 Progress received:');
      print('  - Current league: ${progress.currentLeague}');
      print('  - Should show upgrade: ${progress.shouldShowLeagueUpgrade}');
      print('  - Previous league: ${widget.previousLeague}');

      if (progress.shouldShowLeagueUpgrade && widget.previousLeague != null) {
        print('🎯 SHOWING PROMOTION ANIMATION!');
        print('  - From: ${widget.previousLeague}');
        print('  - To: ${progress.currentLeague}');
        setState(() {
          _showAnimation = true;
          _oldLeague = widget.previousLeague;
          _newLeague = progress.currentLeague;
          _isChecking = false;
        });
      } else {
        print('🎯 NOT showing promotion animation because:');
        if (!progress.shouldShowLeagueUpgrade) {
          print('  - shouldShowLeagueUpgrade is false');
        }
        if (widget.previousLeague == null) {
          print('  - previousLeague is null');
        }
        setState(() {
          _isChecking = false;
        });
      }
    } catch (e) {
      print('🎯 ERROR checking promotion: $e');
      // If check fails, just continue without animation
      setState(() {
        _isChecking = false;
      });
    }
  }

  void _onAnimationComplete() async {
    // Mark as shown
    await _progressService.markLeagueUpgradeShown();

    setState(() {
      _showAnimation = false;
    });
  }

  @override
  Widget build(BuildContext context) {
    if (_isChecking) {
      return const Scaffold(
        body: Center(
          child: CircularProgressIndicator(),
        ),
      );
    }

    if (_showAnimation && _oldLeague != null && _newLeague != null) {
      return LeagueUpgradeAnimation(
        oldLeague: _oldLeague!,
        newLeague: _newLeague!,
        onComplete: _onAnimationComplete,
      );
    }

    return widget.child;
  }
}