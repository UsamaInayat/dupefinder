import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../theme/app_theme.dart';

/// FYP Home: quick access to modules (no admin messaging).
class HomeTab extends StatefulWidget {
  final VoidCallback onOpenSearch;

  const HomeTab({super.key, required this.onOpenSearch});

  @override
  State<HomeTab> createState() => _HomeTabState();
}

class _HomeTabState extends State<HomeTab> {
  String? _userEmail;
  bool _guest = false;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    final p = await SharedPreferences.getInstance();
    setState(() {
      _userEmail = p.getString('user_email');
      _guest = p.getBool('guest_mode') == true;
    });
  }

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Container(
            decoration: AppDecor.welcomeBanner,
            child: Padding(
              padding: const EdgeInsets.all(20),
              child: Column(
                children: [
                  Icon(Icons.waving_hand_rounded, size: 48, color: AppColors.bluePrimary),
                  const SizedBox(height: 12),
                  Text(
                    _guest ? 'Hi, Guest' : 'Welcome back',
                    style: const TextStyle(
                      fontSize: 22,
                      fontWeight: FontWeight.bold,
                      color: AppColors.purpleDark,
                    ),
                  ),
                  const SizedBox(height: 6),
                  Text(
                    _guest
                        ? 'Search by image to find affordable dupes.'
                        : (_userEmail ?? ''),
                    style: TextStyle(color: AppColors.greySubtitle, fontSize: 14),
                    textAlign: TextAlign.center,
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 24),
          Row(
            children: [
              Container(
                width: 4,
                height: 22,
                decoration: BoxDecoration(
                  color: AppColors.bluePrimary,
                  borderRadius: BorderRadius.circular(2),
                ),
              ),
              const SizedBox(width: 10),
              const Text(
                'Explore',
                style: TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.bold,
                  color: AppColors.purpleDark,
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          GridView.count(
            shrinkWrap: true,
            physics: const NeverScrollableScrollPhysics(),
            crossAxisCount: 2,
            crossAxisSpacing: 14,
            mainAxisSpacing: 14,
            childAspectRatio: 1.05,
            children: [
              _tile(Icons.photo_camera_front_rounded, 'Find similar', 'Image search', AppColors.bluePrimary, widget.onOpenSearch),
              _tile(Icons.compare_arrows_rounded, 'Compare', 'Side‑by‑side picks', AppColors.purpleDark, () => _snack(context, 'Open Compare tab')),
              _tile(Icons.favorite_rounded, 'Wishlist', 'Saved items', const Color(0xFFE91E8C), () => _snack(context, 'Open Wishlist tab')),
              _tile(Icons.insights_rounded, 'Insights', 'Trends & savings', const Color(0xFF7C3AED), () => _snack(context, 'Open Me → Insights')),
            ],
          ),
          const SizedBox(height: 20),
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: AppColors.cardSurface,
              borderRadius: BorderRadius.circular(AppDecor.cardRadius),
              border: Border.all(color: AppColors.borderLightBlue.withValues(alpha: 0.5)),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Icon(Icons.lightbulb_outline, color: AppColors.bluePrimary, size: 22),
                    const SizedBox(width: 8),
                    const Text(
                      'Tip',
                      style: TextStyle(
                        fontWeight: FontWeight.bold,
                        color: AppColors.purpleDark,
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 8),
                Text(
                  'Use a clear photo of the outfit or item. '
                  'Filter by category for faster, more accurate matches.',
                  style: TextStyle(fontSize: 13, color: AppColors.greySubtitle, height: 1.35),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  void _snack(BuildContext context, String msg) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(content: Text(msg), behavior: SnackBarBehavior.floating),
    );
  }

  Widget _tile(IconData icon, String title, String subtitle, Color accent, VoidCallback onTap) {
    return Material(
      color: AppColors.cardSurface,
      borderRadius: BorderRadius.circular(AppDecor.tileRadius),
      elevation: 0,
      shadowColor: AppColors.bluePrimary.withValues(alpha: 0.08),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(AppDecor.tileRadius),
        child: Padding(
          padding: const EdgeInsets.all(14),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(icon, size: 36, color: accent),
              const SizedBox(height: 10),
              Text(title, style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 15, color: AppColors.purpleDark)),
              const SizedBox(height: 4),
              Text(subtitle, style: TextStyle(fontSize: 12, color: AppColors.greySubtitle)),
            ],
          ),
        ),
      ),
    );
  }
}
