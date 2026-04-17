import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../theme/app_theme.dart';

/// Welcome: full-screen teal (matches photo backdrop), hero image scaled to show
/// both subjects (`BoxFit.contain`), letterboxing filled by scaffold color — no framed band.
class WelcomeScreen extends StatefulWidget {
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
  State<WelcomeScreen> createState() => _WelcomeScreenState();
}

class _WelcomeScreenState extends State<WelcomeScreen>
    with SingleTickerProviderStateMixin {
  late final AnimationController _bgController;
  late final Animation<double> _bgDriftX;
  late final Animation<double> _bgDriftY;

  @override
  void initState() {
    super.initState();
    _bgController = AnimationController(
      vsync: this,
      duration: const Duration(seconds: 18),
    )..repeat(reverse: true);
    _bgDriftX = Tween<double>(begin: -0.008, end: 0.008).animate(
      CurvedAnimation(parent: _bgController, curve: Curves.easeInOut),
    );
    _bgDriftY = Tween<double>(begin: -0.006, end: 0.006).animate(
      CurvedAnimation(parent: _bgController, curve: Curves.easeInOutSine),
    );
  }

  @override
  void dispose() {
    _bgController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final bottomInset = MediaQuery.of(context).padding.bottom;
    return Scaffold(
      backgroundColor: DupePalette.welcomeHeroWall,
      body: Stack(
        fit: StackFit.expand,
        children: [
          const ColoredBox(color: DupePalette.welcomeHeroWall),
          Positioned.fill(
            child: AnimatedBuilder(
              animation: _bgController,
              builder: (context, _) {
                final size = MediaQuery.of(context).size;
                return Transform.translate(
                  offset: Offset(
                    _bgDriftX.value * size.width,
                    _bgDriftY.value * size.height,
                  ),
                  child: Center(
                    child: Stack(
                      alignment: Alignment.center,
                      clipBehavior: Clip.none,
                      children: [
                        Image.asset(
                          'assets/splash_hero.png',
                          fit: BoxFit.contain,
                          alignment: Alignment.center,
                          width: size.width,
                          height: size.height,
                          filterQuality: FilterQuality.medium,
                          errorBuilder: (_, __, ___) => Icon(
                            Icons.image_not_supported_rounded,
                            size: 80,
                            color: Colors.white.withValues(alpha: 0.5),
                          ),
                        ),
                        // Opaque wall-colored disc (no fade-to-transparent) hides baked-in sparkle
                        // in the PNG; sits mostly off-screen so only a soft arc meets the photo.
                        Positioned(
                          right: -56,
                          bottom: size.height * 0.06,
                          child: IgnorePointer(
                            child: Container(
                              width: 280,
                              height: 280,
                              decoration: const BoxDecoration(
                                shape: BoxShape.circle,
                                color: DupePalette.welcomeHeroWall,
                              ),
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                );
              },
            ),
          ),
          SafeArea(
            child: Align(
              alignment: Alignment.bottomCenter,
              child: Padding(
                padding: EdgeInsets.fromLTRB(24, 0, 24, 16 + bottomInset),
                child: Center(
                  child: ConstrainedBox(
                    constraints: const BoxConstraints(maxWidth: 300),
                    child: DecoratedBox(
                      decoration: BoxDecoration(
                        color: DupePalette.cardSurface,
                        borderRadius: BorderRadius.circular(22),
                        boxShadow: [
                          BoxShadow(
                            color: Colors.black.withValues(alpha: 0.07),
                            blurRadius: 10,
                            offset: const Offset(0, 4),
                          ),
                        ],
                      ),
                      child: Padding(
                        padding: const EdgeInsets.fromLTRB(14, 14, 14, 12),
                        child: Column(
                          mainAxisSize: MainAxisSize.min,
                          crossAxisAlignment: CrossAxisAlignment.stretch,
                          children: [
                            SizedBox(
                              height: 52,
                              child: DecoratedBox(
                                decoration: BoxDecoration(
                                  borderRadius: BorderRadius.circular(32),
                                  gradient: LinearGradient(
                                    colors: [
                                      DupePalette.pink,
                                      DupePalette.welcomeHeroWall,
                                    ],
                                    begin: Alignment.centerLeft,
                                    end: Alignment.centerRight,
                                  ),
                                  boxShadow: [
                                    BoxShadow(
                                      color: DupePalette.pink
                                          .withValues(alpha: 0.18),
                                      blurRadius: 8,
                                      offset: const Offset(0, 3),
                                    ),
                                  ],
                                ),
                                child: Material(
                                  color: Colors.transparent,
                                  child: InkWell(
                                    onTap: () => Navigator.of(context)
                                        .pushNamed('/register'),
                                    borderRadius: BorderRadius.circular(32),
                                    child: Center(
                                      child: Text(
                                        'Register here',
                                        style: DupePalette.serifHeading(
                                          17,
                                          color: Colors.white,
                                          w: FontWeight.w700,
                                        ),
                                      ),
                                    ),
                                  ),
                                ),
                              ),
                            ),
                            const SizedBox(height: 12),
                            SizedBox(
                              height: 50,
                              child: OutlinedButton(
                                onPressed: () =>
                                    Navigator.of(context).pushNamed('/login'),
                                style: OutlinedButton.styleFrom(
                                  backgroundColor: DupePalette.scaffoldLight,
                                  side: BorderSide(
                                    color: DupePalette.greyGuest
                                        .withValues(alpha: 0.55),
                                  ),
                                  shape: RoundedRectangleBorder(
                                    borderRadius: BorderRadius.circular(32),
                                  ),
                                  elevation: 0,
                                ),
                                child: Text(
                                  'Log In',
                                  style: TextStyle(
                                    color: DupePalette.textPrimary,
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
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}
