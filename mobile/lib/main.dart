import 'package:flutter/material.dart';
import 'screens/welcome_screen.dart';
import 'screens/login_screen.dart';
import 'screens/register_screen.dart';
import 'screens/main_shell.dart';
import 'screens/search/image_search_screen.dart';
import 'services/api_service.dart';
import 'theme/app_theme.dart';

void main() {
  runApp(const DupeFinderApp());
}

class DupeFinderApp extends StatelessWidget {
  const DupeFinderApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'DupeFinder',
      theme: AppTheme.dupeFinderTheme(),
      initialRoute: '/',
      routes: {
        '/': (context) => const AuthCheckScreen(),
        '/welcome': (context) => const WelcomeScreen(),
        '/login': (context) => const LoginScreen(),
        '/register': (context) => const RegisterScreen(),
        '/home': (context) => const MainShell(),
        '/search': (context) => const ImageSearchScreen(),
      },
    );
  }
}

class AuthCheckScreen extends StatefulWidget {
  const AuthCheckScreen({super.key});

  @override
  State<AuthCheckScreen> createState() => _AuthCheckScreenState();
}

class _AuthCheckScreenState extends State<AuthCheckScreen> {
  final _apiService = ApiService();

  @override
  void initState() {
    super.initState();
    _checkAuth();
  }

  Future<void> _checkAuth() async {
    final loggedIn = await _apiService.isLoggedIn();
    final guest = await WelcomeScreen.isGuest();
    if (!mounted) return;
    if (loggedIn || guest) {
      Navigator.of(context).pushReplacementNamed('/home');
    } else {
      Navigator.of(context).pushReplacementNamed('/welcome');
    }
  }

  @override
  Widget build(BuildContext context) {
    return const Scaffold(
      body: Center(
        child: CircularProgressIndicator(color: AppColors.bluePrimary),
      ),
    );
  }
}
