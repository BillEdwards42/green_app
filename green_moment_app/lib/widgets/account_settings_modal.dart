import 'package:flutter/material.dart';
import '../constants/app_colors.dart';
import '../services/auth_service.dart';
import '../screens/auth/welcome_screen.dart';
import 'package:intl/intl.dart';

class AccountSettingsModal extends StatefulWidget {
  const AccountSettingsModal({super.key});

  @override
  State<AccountSettingsModal> createState() => _AccountSettingsModalState();
}

class _AccountSettingsModalState extends State<AccountSettingsModal> {
  final AuthService _authService = AuthService();
  bool _isDeleting = false;

  Future<void> _handleLogout() async {
    // Show confirmation dialog
    final confirm = await showDialog<bool>(
      context: context,
      builder: (context) => Dialog(
        backgroundColor: AppColors.bgPrimary,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(20),
        ),
        child: Container(
          constraints: const BoxConstraints(maxWidth: 400),
          padding: const EdgeInsets.all(24),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              // Header
              Row(
                children: [
                  Container(
                    padding: const EdgeInsets.all(8),
                    decoration: BoxDecoration(
                      color: AppColors.accent.withOpacity(0.1),
                      shape: BoxShape.circle,
                    ),
                    child: Icon(
                      Icons.logout_rounded,
                      color: AppColors.accent,
                      size: 24,
                    ),
                  ),
                  const SizedBox(width: 12),
                  Text(
                    '確認登出',
                    style: TextStyle(
                      fontSize: 24,
                      fontWeight: FontWeight.bold,
                      color: AppColors.textPrimary,
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 20),
              // Content
              Text(
                '確定要登出嗎？',
                style: TextStyle(
                  fontSize: 16,
                  color: AppColors.textSecondary,
                  height: 1.5,
                ),
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 24),
              // Actions
              Row(
                mainAxisAlignment: MainAxisAlignment.end,
                children: [
                  TextButton(
                    onPressed: () => Navigator.pop(context, false),
                    style: TextButton.styleFrom(
                      padding: const EdgeInsets.symmetric(
                        horizontal: 24,
                        vertical: 12,
                      ),
                    ),
                    child: Text(
                      '取消',
                      style: TextStyle(
                        color: AppColors.textSecondary,
                        fontSize: 16,
                        fontWeight: FontWeight.w500,
                      ),
                    ),
                  ),
                  const SizedBox(width: 8),
                  TextButton(
                    onPressed: () => Navigator.pop(context, true),
                    style: TextButton.styleFrom(
                      backgroundColor: AppColors.accent.withOpacity(0.1),
                      foregroundColor: AppColors.accent,
                      padding: const EdgeInsets.symmetric(
                        horizontal: 24,
                        vertical: 12,
                      ),
                    ),
                    child: Text(
                      '登出',
                      style: TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );

    if (confirm == true && mounted) {
      await _authService.signOut();
      
      if (mounted) {
        Navigator.of(context).pushAndRemoveUntil(
          MaterialPageRoute(builder: (context) => const WelcomeScreen()),
          (route) => false,
        );
      }
    }
  }

  Future<void> _handleDeleteAccount() async {
    // First confirmation dialog
    final firstConfirm = await showDialog<bool>(
      context: context,
      barrierDismissible: false,
      builder: (context) => Dialog(
        backgroundColor: AppColors.bgPrimary,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(20),
        ),
        child: Container(
          constraints: const BoxConstraints(maxWidth: 400),
          padding: const EdgeInsets.all(24),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              // Header
              Row(
                children: [
                  Container(
                    padding: const EdgeInsets.all(8),
                    decoration: BoxDecoration(
                      color: AppColors.error.withOpacity(0.1),
                      shape: BoxShape.circle,
                    ),
                    child: Icon(
                      Icons.warning_amber_rounded,
                      color: AppColors.error,
                      size: 24,
                    ),
                  ),
                  const SizedBox(width: 12),
                  Text(
                    '刪除帳號',
                    style: TextStyle(
                      fontSize: 24,
                      fontWeight: FontWeight.bold,
                      color: AppColors.textPrimary,
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 20),
              // Content
              Container(
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: AppColors.error.withOpacity(0.08),
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(
                    color: AppColors.error.withOpacity(0.2),
                  ),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      '這將永久刪除：',
                      style: TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.w600,
                        color: AppColors.textPrimary,
                      ),
                    ),
                    const SizedBox(height: 8),
                    _buildDeleteItem('所有家電使用記錄'),
                    _buildDeleteItem('碳減量成就與積分'),
                    _buildDeleteItem('聯盟等級進度'),
                    _buildDeleteItem('個人資料'),
                    const SizedBox(height: 12),
                    Container(
                      padding: const EdgeInsets.all(12),
                      decoration: BoxDecoration(
                        color: AppColors.bgSecondary,
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: Row(
                        children: [
                          Icon(
                            Icons.info_outline,
                            color: AppColors.textSecondary,
                            size: 16,
                          ),
                          const SizedBox(width: 8),
                          Expanded(
                            child: Text(
                              '刪除後可使用相同 Google 帳號重新註冊，但所有資料將無法復原',
                              style: TextStyle(
                                fontSize: 12,
                                color: AppColors.textSecondary,
                                height: 1.4,
                              ),
                            ),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 24),
              // Actions
              Row(
                mainAxisAlignment: MainAxisAlignment.end,
                children: [
                  TextButton(
                    onPressed: () => Navigator.pop(context, false),
                    style: TextButton.styleFrom(
                      padding: const EdgeInsets.symmetric(
                        horizontal: 24,
                        vertical: 12,
                      ),
                    ),
                    child: Text(
                      '取消',
                      style: TextStyle(
                        color: AppColors.textSecondary,
                        fontSize: 16,
                        fontWeight: FontWeight.w500,
                      ),
                    ),
                  ),
                  const SizedBox(width: 8),
                  TextButton(
                    onPressed: () => Navigator.pop(context, true),
                    style: TextButton.styleFrom(
                      backgroundColor: AppColors.error.withOpacity(0.1),
                      foregroundColor: AppColors.error,
                      padding: const EdgeInsets.symmetric(
                        horizontal: 24,
                        vertical: 12,
                      ),
                    ),
                    child: const Text(
                      '我了解，繼續',
                      style: TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );

    if (firstConfirm != true) return;

    // Second confirmation dialog - require typing "DELETE"
    final TextEditingController confirmController = TextEditingController();
    final secondConfirm = await showDialog<bool>(
      context: context,
      barrierDismissible: false,
      builder: (context) {
        String confirmText = '';
        return StatefulBuilder(
          builder: (context, setDialogState) {
            final isConfirmed = confirmText == 'DELETE';
            return Dialog(
              backgroundColor: AppColors.bgPrimary,
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(20),
              ),
              child: Container(
                constraints: const BoxConstraints(maxWidth: 400),
                padding: const EdgeInsets.all(24),
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    // Header
                    Row(
                      children: [
                        Container(
                          padding: const EdgeInsets.all(8),
                          decoration: BoxDecoration(
                            color: AppColors.error.withOpacity(0.1),
                            shape: BoxShape.circle,
                          ),
                          child: Icon(
                            Icons.delete_forever,
                            color: AppColors.error,
                            size: 24,
                          ),
                        ),
                        const SizedBox(width: 12),
                        Text(
                          '最終確認',
                          style: TextStyle(
                            fontSize: 24,
                            fontWeight: FontWeight.bold,
                            color: AppColors.textPrimary,
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 20),
                    // Content
                    Text(
                      '請輸入 "DELETE" 以確認永久刪除您的帳號：',
                      style: TextStyle(
                        fontSize: 16,
                        color: AppColors.textSecondary,
                        height: 1.5,
                      ),
                    ),
                    const SizedBox(height: 16),
                    TextField(
                      controller: confirmController,
                      onChanged: (value) {
                        confirmText = value;
                        setDialogState(() {});
                      },
                      autofocus: true,
                      style: TextStyle(
                        color: AppColors.textPrimary,
                        fontSize: 18,
                        fontWeight: FontWeight.w600,
                      ),
                      textAlign: TextAlign.center,
                      decoration: InputDecoration(
                        hintText: '輸入 DELETE',
                        hintStyle: TextStyle(
                          color: AppColors.textSecondary.withOpacity(0.3),
                          fontSize: 16,
                          fontWeight: FontWeight.w400,
                        ),
                        filled: true,
                        fillColor: AppColors.bgSecondary,
                        border: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(12),
                          borderSide: BorderSide(
                            color: isConfirmed 
                                ? AppColors.error.withOpacity(0.5)
                                : AppColors.border,
                          ),
                        ),
                        enabledBorder: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(12),
                          borderSide: BorderSide(
                            color: isConfirmed 
                                ? AppColors.error.withOpacity(0.5)
                                : AppColors.border,
                          ),
                        ),
                        focusedBorder: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(12),
                          borderSide: BorderSide(
                            color: isConfirmed ? AppColors.error : AppColors.accent,
                            width: 2,
                          ),
                        ),
                      ),
                    ),
                    const SizedBox(height: 24),
                    // Actions
                    Row(
                      mainAxisAlignment: MainAxisAlignment.end,
                      children: [
                        TextButton(
                          onPressed: () => Navigator.pop(context, false),
                          style: TextButton.styleFrom(
                            padding: const EdgeInsets.symmetric(
                              horizontal: 24,
                              vertical: 12,
                            ),
                          ),
                          child: Text(
                            '取消',
                            style: TextStyle(
                              color: AppColors.textSecondary,
                              fontSize: 16,
                              fontWeight: FontWeight.w500,
                            ),
                          ),
                        ),
                        const SizedBox(width: 8),
                        AnimatedContainer(
                          duration: const Duration(milliseconds: 200),
                          child: TextButton(
                            onPressed: isConfirmed
                                ? () => Navigator.pop(context, true)
                                : null,
                            style: TextButton.styleFrom(
                              backgroundColor: isConfirmed 
                                  ? AppColors.error
                                  : AppColors.error.withValues(alpha: 0.1),
                              foregroundColor: isConfirmed
                                  ? AppColors.bgPrimary
                                  : AppColors.error.withOpacity(0.3),
                              padding: const EdgeInsets.symmetric(
                                horizontal: 24,
                                vertical: 12,
                              ),
                            ),
                            child: Text(
                              '永久刪除',
                              style: TextStyle(
                                fontSize: 16,
                                fontWeight: FontWeight.w600,
                              ),
                            ),
                          ),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
            );
          },
        );
      },
    );

    confirmController.dispose();

    if (secondConfirm == true && mounted) {
      setState(() => _isDeleting = true);
      
      try {
        final success = await _authService.deleteAccount();
        
        if (success && mounted) {
          Navigator.of(context).pushAndRemoveUntil(
            MaterialPageRoute(builder: (context) => const WelcomeScreen()),
            (route) => false,
          );
        } else if (mounted) {
          _showError('刪除帳號失敗，請稍後再試');
        }
      } catch (e) {
        if (mounted) {
          _showError('發生錯誤：${e.toString()}');
        }
      } finally {
        if (mounted) {
          setState(() => _isDeleting = false);
        }
      }
    }
  }

  Widget _buildDeleteItem(String text) {
    return Padding(
      padding: const EdgeInsets.only(left: 8, bottom: 4),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            margin: const EdgeInsets.only(top: 6),
            width: 4,
            height: 4,
            decoration: BoxDecoration(
              color: AppColors.error.withOpacity(0.6),
              shape: BoxShape.circle,
            ),
          ),
          const SizedBox(width: 8),
          Expanded(
            child: Text(
              text,
              style: TextStyle(
                fontSize: 14,
                color: AppColors.textSecondary,
                height: 1.4,
              ),
            ),
          ),
        ],
      ),
    );
  }

  void _showError(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        backgroundColor: AppColors.error,
      ),
    );
  }

  String _formatDate(DateTime date) {
    return DateFormat('yyyy年MM月dd日').format(date);
  }

  @override
  Widget build(BuildContext context) {
    final user = _authService.currentUser;
    final createdAt = user?['created_at'] != null
        ? DateTime.parse(user!['created_at'])
        : DateTime.now();

    return Dialog(
      backgroundColor: AppColors.bgPrimary,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(20),
      ),
      insetPadding: const EdgeInsets.symmetric(horizontal: 20, vertical: 40),
      child: Container(
        constraints: const BoxConstraints(
          maxWidth: 400,
          minWidth: 320,
        ),
        child: SingleChildScrollView(
          child: Padding(
            padding: const EdgeInsets.all(24.0),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
          // Header
          Row(
            children: [
              Icon(
                Icons.account_circle,
                color: AppColors.accent,
                size: 28,
              ),
              const SizedBox(width: 12),
              Text(
                '帳號資訊',
                style: TextStyle(
                  fontSize: 24,
                  fontWeight: FontWeight.bold,
                  color: AppColors.textPrimary,
                ),
              ),
            ],
          ),
          const SizedBox(height: 24),

          // User Info
          _buildInfoRow(Icons.person, '用戶名稱', user?['username'] ?? '未知'),
          const SizedBox(height: 16),
          
          if (user?['email'] != null) ...[
            _buildInfoRow(Icons.email, '電子郵件', user!['email']),
            const SizedBox(height: 16),
          ],
          
          _buildInfoRow(
            Icons.calendar_today,
            '加入日期',
            _formatDate(createdAt),
          ),
          const SizedBox(height: 16),
          
          _buildInfoRow(
            Icons.emoji_events,
            '目前聯盟',
            _getLeagueName(user?['current_league'] ?? 'bronze'),
          ),

          const SizedBox(height: 32),
          const Divider(color: AppColors.border, height: 1),
          const SizedBox(height: 24),

          // Action Buttons
          Row(
            children: [
              Expanded(
                child: OutlinedButton(
                  onPressed: _isDeleting ? null : _handleLogout,
                  style: OutlinedButton.styleFrom(
                    padding: const EdgeInsets.symmetric(vertical: 12),
                    side: const BorderSide(color: AppColors.border),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(8),
                    ),
                  ),
                  child: const Text(
                    '登出',
                    style: TextStyle(color: AppColors.textPrimary),
                  ),
                ),
              ),
              const SizedBox(width: 16),
              Expanded(
                child: ElevatedButton(
                  onPressed: _isDeleting ? null : _handleDeleteAccount,
                  style: ElevatedButton.styleFrom(
                    backgroundColor: AppColors.error.withOpacity(0.1),
                    foregroundColor: AppColors.error,
                    padding: const EdgeInsets.symmetric(vertical: 12),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(8),
                    ),
                  ),
                  child: _isDeleting
                      ? const SizedBox(
                          height: 20,
                          width: 20,
                          child: CircularProgressIndicator(
                            strokeWidth: 2,
                            valueColor: AlwaysStoppedAnimation<Color>(
                              AppColors.error,
                            ),
                          ),
                        )
                      : const Text('刪除帳號'),
                ),
              ),
            ],
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
                '關閉',
                style: TextStyle(
                  color: AppColors.accent,
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
    );
  }

  Widget _buildInfoRow(IconData icon, String label, String value) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Container(
          padding: const EdgeInsets.all(8),
          decoration: BoxDecoration(
            color: AppColors.bgSecondary,
            borderRadius: BorderRadius.circular(8),
            border: Border.all(
              color: AppColors.border.withOpacity(0.5),
              width: 1,
            ),
          ),
          child: Icon(
            icon,
            size: 16,
            color: AppColors.textSecondary,
          ),
        ),
        const SizedBox(width: 12),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                label,
                style: const TextStyle(
                  color: AppColors.textSecondary,
                  fontSize: 12,
                ),
              ),
              const SizedBox(height: 2),
              Text(
                value,
                style: const TextStyle(
                  color: AppColors.textPrimary,
                  fontSize: 14,
                  fontWeight: FontWeight.w500,
                ),
                overflow: TextOverflow.ellipsis,
                maxLines: 1,
              ),
            ],
          ),
        ),
      ],
    );
  }

  String _getLeagueName(String league) {
    switch (league) {
      case 'bronze':
        return '青銅聯盟';
      case 'silver':
        return '白銀聯盟';
      case 'gold':
        return '黃金聯盟';
      case 'emerald':
        return '翡翠聯盟';
      case 'diamond':
        return '鑽石聯盟';
      default:
        return '青銅聯盟';
    }
  }
}