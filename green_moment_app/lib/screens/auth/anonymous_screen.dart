import 'package:flutter/material.dart';
import '../../constants/app_colors.dart';
import '../../services/auth_service.dart';
import '../../services/user_progress_service.dart';
import '../main_screen.dart';

class AnonymousScreen extends StatefulWidget {
  const AnonymousScreen({super.key});

  @override
  State<AnonymousScreen> createState() => _AnonymousScreenState();
}

class _AnonymousScreenState extends State<AnonymousScreen> {
  final _usernameController = TextEditingController();
  bool _isLoading = false;
  String? _errorMessage;

  Future<void> _signInAnonymously() async {
    final username = _usernameController.text.trim();
    
    if (username.isEmpty) {
      setState(() {
        _errorMessage = '請輸入用戶名稱';
      });
      return;
    }

    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    final authService = AuthService();
    final success = await authService.signInAnonymously(username);

    setState(() {
      _isLoading = false;
    });

    if (success) {
      // Initialize progress for new user (this handles bronze task initialization)
      final progressService = UserProgressService();
      await progressService.initializeNewUserProgress();
      
      if (mounted) {
        Navigator.pushReplacement(
          context,
          MaterialPageRoute(builder: (context) => const MainScreen()),
        );
      }
    } else {
      setState(() {
        // Use the specific error message from the backend
        _errorMessage = authService.lastErrorMessage ?? '建立帳戶失敗，請重新嘗試。';
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.bgPrimary,
      resizeToAvoidBottomInset: false,
      body: SafeArea(
        child: Stack(
          children: [
            // Background gradient overlay
            Container(
              decoration: const BoxDecoration(
                gradient: RadialGradient(
                  center: Alignment(0.3, -0.8),
                  radius: 1.5,
                  colors: [
                    Color(0x1A6366F1), // Purple glow for anonymous
                    Color(0x086366F1),
                    Colors.transparent,
                  ],
                ),
              ),
            ),
            
            // Back button
            Positioned(
              top: 16,
              left: 16,
              child: IconButton(
                onPressed: () => Navigator.pop(context),
                icon: Container(
                  padding: const EdgeInsets.all(8),
                  decoration: BoxDecoration(
                    color: AppColors.surface,
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(
                      color: AppColors.border,
                      width: 1,
                    ),
                  ),
                  child: const Icon(
                    Icons.arrow_back_ios_new,
                    color: AppColors.textPrimary,
                    size: 20,
                  ),
                ),
              ),
            ),
            
            // Main content
            Padding(
              padding: const EdgeInsets.all(24.0),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  const SizedBox(height: 80),
                  
                  // Header section
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                        decoration: BoxDecoration(
                          color: AppColors.accent.withValues(alpha: 0.15),
                          borderRadius: BorderRadius.circular(20),
                          border: Border.all(
                            color: AppColors.accent.withValues(alpha: 0.3),
                            width: 1,
                          ),
                        ),
                        child: const Text(
                          '🔒 Anonymous',
                          style: TextStyle(
                            fontSize: 14,
                            color: AppColors.accent,
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                      ),
                      const SizedBox(height: 24),
                      
                      const Text(
                        '建立用戶名稱',
                        style: TextStyle(
                          fontSize: 32,
                          fontWeight: FontWeight.bold,
                          color: AppColors.textPrimary,
                          height: 1.2,
                        ),
                      ),
                      const SizedBox(height: 12),
                      
                      const Text(
                        '您的資料僅會儲存在此裝置上，\n不會同步至雲端或其他裝置',
                        style: TextStyle(
                          fontSize: 16,
                          color: AppColors.textSecondary,
                          height: 1.5,
                        ),
                      ),
                    ],
                  ),
                  
                  const SizedBox(height: 32),
                  
                  // Warning card
                  Container(
                    padding: const EdgeInsets.all(16),
                    decoration: BoxDecoration(
                      color: AppColors.yellow.withValues(alpha: 0.1),
                      borderRadius: BorderRadius.circular(12),
                      border: Border.all(
                        color: AppColors.yellow.withValues(alpha: 0.3),
                        width: 1,
                      ),
                    ),
                    child: Row(
                      children: [
                        Icon(
                          Icons.warning_amber_rounded,
                          color: AppColors.yellow,
                          size: 22,
                        ),
                        const SizedBox(width: 12),
                        const Expanded(
                          child: Text(
                            '如果您刪除應用程式，所有資料將永久遺失。',
                            style: TextStyle(
                              fontSize: 14,
                              color: AppColors.textPrimary,
                              fontWeight: FontWeight.w500,
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                  
                  const SizedBox(height: 48),
                  
                  // Username input section
                  Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text(
                        '用戶名稱',
                        style: TextStyle(
                          fontSize: 16,
                          fontWeight: FontWeight.w600,
                          color: AppColors.textPrimary,
                        ),
                      ),
                      const SizedBox(height: 12),
                      
                      Container(
                        decoration: BoxDecoration(
                          borderRadius: BorderRadius.circular(16),
                          border: Border.all(
                            color: AppColors.border,
                            width: 1,
                          ),
                          color: AppColors.surface,
                        ),
                        child: TextField(
                          controller: _usernameController,
                          style: const TextStyle(
                            color: AppColors.textPrimary,
                            fontSize: 16,
                          ),
                          decoration: InputDecoration(
                            hintText: '輸入用戶名稱',
                            hintStyle: TextStyle(
                              color: AppColors.textSecondary.withValues(alpha: 0.7),
                              fontSize: 16,
                            ),
                            border: InputBorder.none,
                            contentPadding: const EdgeInsets.all(20),
                            prefixIcon: Icon(
                              Icons.person_outline,
                              color: AppColors.textSecondary.withValues(alpha: 0.7),
                              size: 22,
                            ),
                          ),
                          onSubmitted: (_) => _signInAnonymously(),
                        ),
                      ),
                      const SizedBox(height: 8),
                      
                      Text(
                        '可使用繁體中文或英文字符',
                        style: TextStyle(
                          fontSize: 14,
                          color: AppColors.textSecondary.withValues(alpha: 0.8),
                        ),
                      ),
                    ],
                  ),
                  
                  const SizedBox(height: 32),
                  
                  // Error message
                  if (_errorMessage != null)
                    Container(
                      padding: const EdgeInsets.all(16),
                      margin: const EdgeInsets.only(bottom: 24),
                      decoration: BoxDecoration(
                        color: AppColors.red.withValues(alpha: 0.1),
                        borderRadius: BorderRadius.circular(12),
                        border: Border.all(
                          color: AppColors.red.withValues(alpha: 0.3),
                          width: 1,
                        ),
                      ),
                      child: Row(
                        children: [
                          Icon(
                            Icons.error_outline,
                            color: AppColors.red,
                            size: 20,
                          ),
                          const SizedBox(width: 12),
                          Expanded(
                            child: Text(
                              _errorMessage!,
                              style: const TextStyle(
                                color: AppColors.red,
                                fontSize: 14,
                                fontWeight: FontWeight.w500,
                              ),
                            ),
                          ),
                        ],
                      ),
                    ),
                  
                  const Spacer(),
                  
                  // Continue button
                  Container(
                    height: 56,
                    decoration: BoxDecoration(
                      gradient: const LinearGradient(
                        colors: [AppColors.accent, AppColors.accentLight],
                        begin: Alignment.centerLeft,
                        end: Alignment.centerRight,
                      ),
                      borderRadius: BorderRadius.circular(16),
                      boxShadow: [
                        BoxShadow(
                          color: AppColors.accent.withValues(alpha: 0.3),
                          blurRadius: 20,
                          offset: const Offset(0, 8),
                        ),
                      ],
                    ),
                    child: Material(
                      color: Colors.transparent,
                      child: InkWell(
                        onTap: _isLoading ? null : _signInAnonymously,
                        borderRadius: BorderRadius.circular(16),
                        child: Container(
                          padding: const EdgeInsets.symmetric(horizontal: 24),
                          child: _isLoading
                              ? const Center(
                                  child: SizedBox(
                                    width: 24,
                                    height: 24,
                                    child: CircularProgressIndicator(
                                      strokeWidth: 2.5,
                                      valueColor: AlwaysStoppedAnimation<Color>(Colors.white),
                                    ),
                                  ),
                                )
                              : const Center(
                                  child: Text(
                                    '開始使用匿名模式',
                                    style: TextStyle(
                                      color: Colors.white,
                                      fontSize: 16,
                                      fontWeight: FontWeight.w600,
                                    ),
                                  ),
                                ),
                        ),
                      ),
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

  @override
  void dispose() {
    _usernameController.dispose();
    super.dispose();
  }
}