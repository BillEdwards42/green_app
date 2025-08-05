import 'package:flutter/material.dart';
import 'package:firebase_core/firebase_core.dart';
import 'screens/main_screen.dart';
import 'screens/auth/welcome_screen.dart';
import 'services/user_progress_service.dart';
import 'services/auth_service.dart';
import 'services/notification_service.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  
  // Initialize Firebase first
  await Firebase.initializeApp();
  
  // Initialize services
  await AuthService().initialize();
  
  // Initialize notification service
  await NotificationService().initialize();
  
  // Track app open
  final progressService = UserProgressService();
  await progressService.trackAppOpen();
  
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: '減碳時刻',
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.deepPurple),
        useMaterial3: true,
        fontFamily: 'Noto Sans TC',
      ),
      home: const AuthWrapper(),
      debugShowCheckedModeBanner: false,
    );
  }
}

class AuthWrapper extends StatelessWidget {
  const AuthWrapper({super.key});

  @override
  Widget build(BuildContext context) {
    // Check if user is authenticated
    final authService = AuthService();
    
    if (authService.isAuthenticated) {
      return const MainScreen();
    } else {
      return const WelcomeScreen();
    }
  }
}

