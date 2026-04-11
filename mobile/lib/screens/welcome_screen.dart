import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../theme/app_theme.dart';

/// Splash: full-bleed hero image (models preserved via left-weighted cover), themed CTAs.
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
      backgroundColor: DupePalette.tealWall,
      body: Stack(
        fit: StackFit.expand,
        children: [
          Positioned.fill(
            child: Image.asset(
              'assets/splash_hero.png',
              fit: BoxFit.cover,
              alignment: Alignment.centerLeft,
              errorBuilder: (_, __, ___) => Container(
                decoration: BoxDecoration(gradient: DupePalette.heroGradient),
                child: Icon(
                  Icons.image_not_supported_rounded,
                  size: 80,
                  color: Colors.white.withValues(alpha: 0.5),
                ),
              ),
            ),
          ),
          // Soft bottom fade so buttons stay readable on any crop
          Positioned(
            left: 0,
            right: 0,
            bottom: 0,
            height: 200,
            child: DecoratedBox(
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  begin: Alignment.topCenter,
                  end: Alignment.bottomCenter,
                  colors: [
                    Colors.transparent,
                    DupePalette.tealWall.withValues(alpha: 0.35),
                    DupePalette.tealWall.withValues(alpha: 0.85),
                  ],
                ),
              ),
            ),
          ),
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
                      height: 54,
                      child: DecoratedBox(
                        decoration: BoxDecoration(
                          borderRadius: BorderRadius.circular(32),
                          gradient: DupePalette.ctaGradient,
                          boxShadow: [
                            BoxShadow(
                              color: DupePalette.pink.withValues(alpha: 0.35),
                              blurRadius: 16,
                              offset: const Offset(0, 8),
                            ),
                          ],
                        ),
                        child: Material(
                          color: Colors.transparent,
                          child: InkWell(
                            onTap: () => Navigator.of(context).pushNamed('/register'),
                            borderRadius: BorderRadius.circular(32),
                            child: Center(
                              child: Text(
                                'Register here',
                                style: DupePalette.serifHeading(18,
                                    color: Colors.white, w: FontWeight.w700),
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
                        onPressed: () => Navigator.of(context).pushNamed('/login'),
                        style: OutlinedButton.styleFrom(
                          backgroundColor: Colors.white.withValues(alpha: 0.9),
                          side: BorderSide(color: Colors.white.withValues(alpha: 0.95), width: 2),
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(32),
                          ),
                          elevation: 0,
                        ),
                        child: Text(
                          'Log In',
                          style: TextStyle(
                            color: DupePalette.tealWall,
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
