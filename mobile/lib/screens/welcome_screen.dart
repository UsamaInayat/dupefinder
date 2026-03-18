import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../theme/app_theme.dart';

/// Full-screen welcome image; Log In / Sign Up only on lower area (no card, no guest).
class WelcomeScreen extends StatelessWidget {
  const WelcomeScreen({super.key});

  static Future<void> setGuestMode(bool value) async {
    final p = await SharedPreferences.getInstance();
    if (value) {
      await p.setBool('guest_mode', true);
    } else {
      await p.remove('guest_mode');
    }
  }

  static Future<bool> isGuest() async {
    final p = await SharedPreferences.getInstance();
    return p.getBool('guest_mode') == true;
  }

  @override
  Widget build(BuildContext context) {
    final bottomInset = MediaQuery.of(context).padding.bottom;
    return Scaffold(
      body: Stack(
        fit: StackFit.expand,
        children: [
          // Full background — image already has logo + art + white strip below
          Positioned.fill(
            child: Image.asset(
              'assets/login_welcome.png',
              fit: BoxFit.cover,
              alignment: Alignment.topCenter,
              errorBuilder: (_, __, ___) => Container(
                color: const Color(0xFFF8FAFC),
                child: Icon(
                  Icons.image_not_supported_rounded,
                  size: 80,
                  color: AppColors.bluePrimary.withValues(alpha: 0.4),
                ),
              ),
            ),
          ),
          // Buttons sit on lower white area — no box, no card, just the two pills
          SafeArea(
            child: Align(
              alignment: Alignment.bottomCenter,
              child: Padding(
                padding: EdgeInsets.fromLTRB(28, 0, 28, 20 + bottomInset),
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    SizedBox(
                      height: 52,
                      child: DecoratedBox(
                        decoration: AppTheme.loginGradientButton,
                        child: Material(
                          color: Colors.transparent,
                          child: InkWell(
                            onTap: () => Navigator.of(context).pushNamed('/login'),
                            borderRadius: BorderRadius.circular(32),
                            child: const Center(
                              child: Text(
                                'Log In',
                                style: TextStyle(
                                  color: Colors.white,
                                  fontSize: 16,
                                  fontWeight: FontWeight.bold,
                                ),
                              ),
                            ),
                          ),
                        ),
                      ),
                    ),
                    const SizedBox(height: 14),
                    SizedBox(
                      height: 52,
                      child: OutlinedButton(
                        onPressed: () => Navigator.of(context).pushNamed('/register'),
                        style: OutlinedButton.styleFrom(
                          backgroundColor: Colors.white,
                          side: const BorderSide(color: AppColors.bluePrimary, width: 2),
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(32),
                          ),
                          elevation: 0,
                        ),
                        child: const Text(
                          'Sign Up',
                          style: TextStyle(
                            color: AppColors.bluePrimary,
                            fontSize: 16,
                            fontWeight: FontWeight.bold,
                          ),
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}
