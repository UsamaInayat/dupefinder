import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../theme/app_theme.dart';

/// Welcome: full-bleed hero with horizontal motion.
/// We use `BoxFit.cover` so the image fills the full phone viewport.
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
  late final AnimationController _heroPanController;
  late final Animation<double> _heroPanX;

  @override
  void initState() {
    super.initState();
    _heroPanController = AnimationController(
      vsync: this,
      duration: const Duration(seconds: 10),
    )..repeat(reverse: true);
    _heroPanX = Tween<double>(
      begin: 0.42, // Start further right so the face stays fully visible.
      end: -0.3, // Pan to left.
    ).animate(
      CurvedAnimation(
        parent: _heroPanController,
        curve: Curves.easeInOut,
      ),
    );
  }

  @override
  void dispose() {
    _heroPanController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: DupePalette.welcomeHeroWall,
      body: Stack(
        fit: StackFit.expand,
        children: [
          Positioned.fill(
            child: DecoratedBox(
              decoration: const BoxDecoration(
                color: DupePalette.welcomeHeroWall,
              ),
              child: AnimatedBuilder(
                animation: _heroPanX,
                builder: (context, _) => Image.asset(
                  'assets/splash_hero.png',
                  fit: BoxFit.cover,
                  alignment: Alignment(_heroPanX.value, 0.06),
                  width: double.infinity,
                  height: double.infinity,
                  filterQuality: FilterQuality.high,
                  errorBuilder: (_, __, ___) => Icon(
                    Icons.image_not_supported_rounded,
                    size: 80,
                    color: Colors.white.withValues(alpha: 0.5),
                  ),
                ),
              ),
            ),
          ),
          Positioned.fill(
            child: SafeArea(
              child: Column(
                children: [
                  const Spacer(),
                  Padding(
                    padding: const EdgeInsets.fromLTRB(24, 0, 24, 20),
                    child: Center(
                      child: ConstrainedBox(
                        constraints: const BoxConstraints(maxWidth: 320),
                        child: DecoratedBox(
                          decoration: BoxDecoration(
                            color: DupePalette.cardSurface,
                            borderRadius: BorderRadius.circular(22),
                            boxShadow: [
                              BoxShadow(
                                color: Colors.black.withValues(alpha: 0.14),
                                blurRadius: 28,
                                offset: const Offset(0, 14),
                                spreadRadius: -6,
                              ),
                              BoxShadow(
                                color: Colors.black.withValues(alpha: 0.08),
                                blurRadius: 12,
                                offset: const Offset(0, 6),
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
                                      gradient: const LinearGradient(
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
                                              .withValues(alpha: 0.22),
                                          blurRadius: 12,
                                          offset: const Offset(0, 4),
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
                                      backgroundColor: DupePalette.textPrimary
                                          .withValues(alpha: 0.42),
                                      side: BorderSide(
                                        color: Colors.white
                                            .withValues(alpha: 0.7),
                                      ),
                                      shape: RoundedRectangleBorder(
                                        borderRadius: BorderRadius.circular(32),
                                      ),
                                      elevation: 0,
                                    ),
                                    child: const Text(
                                      'Log In',
                                      style: TextStyle(
                                        color: Colors.white,
                                        fontSize: 16,
                                        fontWeight: FontWeight.w700,
                                        height: 1.2, // Prevent descender clipping (e.g., "g").
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
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}
