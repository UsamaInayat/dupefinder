import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../theme/app_theme.dart';
import 'category_browse_screen.dart';

/// Home: Discover header, hero, shop-by-category (classic icons), explore tiles.
class HomeTab extends StatefulWidget {
  final VoidCallback onOpenSearch;
  final VoidCallback onOpenCompare;
  final VoidCallback onOpenWishlist;
  final VoidCallback onOpenInsights;

  const HomeTab({
    super.key,
    required this.onOpenSearch,
    required this.onOpenCompare,
    required this.onOpenWishlist,
    required this.onOpenInsights,
  });

  @override
  State<HomeTab> createState() => _HomeTabState();
}

class _HomeTabState extends State<HomeTab> {
  String? _userName;
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
      _userName = p.getString('user_name');
      _userEmail = p.getString('user_email');
      _guest = p.getBool('guest_mode') == true;
    });
  }

  @override
  Widget build(BuildContext context) {
    final topPad = MediaQuery.of(context).padding.top;
    return ColoredBox(
      color: DupePalette.scaffoldLight,
      child: CustomScrollView(
        slivers: [
          SliverToBoxAdapter(
            child: Container(
              padding: EdgeInsets.fromLTRB(20, topPad + 12, 20, 24),
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  colors: [
                    DupePalette.pink.withValues(alpha: 0.85),
                    DupePalette.blue.withValues(alpha: 0.65),
                    DupePalette.teal.withValues(alpha: 0.75),
                  ],
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                ),
                borderRadius: const BorderRadius.vertical(bottom: Radius.circular(28)),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              'Discover',
                              style: DupePalette.serifHeading(28, w: FontWeight.w700, color: Colors.white),
                            ),
                            const SizedBox(height: 6),
                            Text(
                              'Find your perfect luxury dupe',
                              style: GoogleFonts.inter(
                                fontSize: 14,
                                color: Colors.white.withValues(alpha: 0.92),
                                height: 1.3,
                              ),
                            ),
                          ],
                        ),
                      ),
                      Material(
                        color: Colors.white.withValues(alpha: 0.25),
                        shape: const CircleBorder(),
                        child: IconButton(
                          icon: Icon(Icons.tune_rounded, color: Colors.white.withValues(alpha: 0.95)),
                          onPressed: widget.onOpenSearch,
                          tooltip: 'Search & filters',
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 18),
                  Material(
                    color: Colors.transparent,
                    child: InkWell(
                      onTap: widget.onOpenSearch,
                      borderRadius: BorderRadius.circular(22),
                      child: Container(
                        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
                        decoration: BoxDecoration(
                          color: Colors.white.withValues(alpha: 0.22),
                          borderRadius: BorderRadius.circular(22),
                          border: Border.all(color: Colors.white.withValues(alpha: 0.45)),
                        ),
                        child: Row(
                          children: [
                            Icon(Icons.search_rounded, color: Colors.white.withValues(alpha: 0.9)),
                            const SizedBox(width: 12),
                            Expanded(
                              child: Text(
                                'Search luxury items…',
                                style: GoogleFonts.inter(
                                  fontSize: 15,
                                  color: Colors.white.withValues(alpha: 0.88),
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
            ),
          ),
          SliverPadding(
            padding: const EdgeInsets.fromLTRB(20, 20, 20, 8),
            sliver: SliverToBoxAdapter(
              child: _heroCard(context),
            ),
          ),
          SliverPadding(
            padding: const EdgeInsets.symmetric(horizontal: 20),
            sliver: SliverToBoxAdapter(
              child: Text(
                'Shop by Category',
                style: GoogleFonts.inter(
                  fontSize: 17,
                  fontWeight: FontWeight.bold,
                  color: DupePalette.textPrimary,
                ),
              ),
            ),
          ),
          SliverToBoxAdapter(
            child: SizedBox(
              height: 118,
              child: ListView(
                scrollDirection: Axis.horizontal,
                padding: const EdgeInsets.fromLTRB(16, 12, 16, 8),
                children: [
                  _categoryChip(
                    label: 'Dresses',
                    slot: 'dresses',
                    icon: Icons.checkroom_outlined,
                    gradient: [DupePalette.pink, DupePalette.pinkDeep],
                  ),
                  _categoryChip(
                    label: 'Bags',
                    slot: 'bags',
                    icon: Icons.shopping_bag_outlined,
                    gradient: [DupePalette.pinkDeep, DupePalette.blue],
                  ),
                  _categoryChip(
                    label: 'Accessories',
                    slot: 'accessories',
                    icon: Icons.style_rounded,
                    gradient: [DupePalette.blue, DupePalette.teal],
                  ),
                  _categoryChip(
                    label: 'Jewellery',
                    slot: 'jewelry',
                    icon: Icons.diamond_outlined,
                    gradient: [DupePalette.teal, DupePalette.tealWall],
                  ),
                ],
              ),
            ),
          ),
          SliverPadding(
            padding: const EdgeInsets.fromLTRB(20, 8, 20, 8),
            sliver: SliverToBoxAdapter(
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text(
                    'Trending Dupes',
                    style: GoogleFonts.inter(
                      fontSize: 17,
                      fontWeight: FontWeight.bold,
                      color: DupePalette.textPrimary,
                    ),
                  ),
                  TextButton(
                    onPressed: widget.onOpenSearch,
                    child: Text(
                      'View All',
                      style: GoogleFonts.inter(
                        fontWeight: FontWeight.w600,
                        color: DupePalette.blue,
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),
          SliverPadding(
            padding: const EdgeInsets.symmetric(horizontal: 20),
            sliver: SliverToBoxAdapter(
              child: Text(
                _guest
                    ? 'Upload a photo in Search to see matches and savings.'
                    : 'Hi ${_displayName()} — open Search to find looks like yours.',
                style: GoogleFonts.inter(fontSize: 13, color: DupePalette.greySubtitle, height: 1.35),
              ),
            ),
          ),
          SliverPadding(
            padding: const EdgeInsets.fromLTRB(20, 20, 20, 8),
            sliver: SliverToBoxAdapter(
              child: Text(
                'Explore',
                style: GoogleFonts.inter(
                  fontSize: 17,
                  fontWeight: FontWeight.bold,
                  color: DupePalette.textPrimary,
                ),
              ),
            ),
          ),
          SliverPadding(
            padding: const EdgeInsets.fromLTRB(20, 0, 20, 28),
            sliver: SliverGrid(
              gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                crossAxisCount: 2,
                crossAxisSpacing: 14,
                mainAxisSpacing: 14,
                childAspectRatio: 1.05,
              ),
              delegate: SliverChildListDelegate([
                _tile(Icons.photo_camera_front_rounded, 'Find similar', 'Image search', DupePalette.pink, widget.onOpenSearch),
                _tile(Icons.compare_arrows_rounded, 'Compare', 'Side‑by‑side picks', DupePalette.blue, widget.onOpenCompare),
                _tile(Icons.favorite_rounded, 'Wishlist', 'Saved items', DupePalette.pinkDeep, widget.onOpenWishlist),
                _tile(Icons.insights_rounded, 'Insights', 'Trends & savings', DupePalette.teal, widget.onOpenInsights),
              ]),
            ),
          ),
        ],
      ),
    );
  }

  String _displayName() {
    if (_guest) return 'Guest';
    if (_userName != null && _userName!.trim().isNotEmpty) return _userName!.trim();
    if (_userEmail != null && _userEmail!.contains('@')) {
      return _userEmail!.split('@').first.trim();
    }
    return 'there';
  }

  void _openCategoryBrowse(String slot, String title) {
    Navigator.of(context).push<void>(
      MaterialPageRoute<void>(
        builder: (_) => CategoryBrowseScreen(slot: slot, title: title),
      ),
    );
  }

  Widget _heroCard(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(24),
        gradient: LinearGradient(
          colors: [
            DupePalette.textPrimary.withValues(alpha: 0.88),
            DupePalette.blue.withValues(alpha: 0.55),
          ],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        boxShadow: [
          BoxShadow(
            color: DupePalette.pink.withValues(alpha: 0.2),
            blurRadius: 20,
            offset: const Offset(0, 10),
          ),
        ],
      ),
      child: ClipRRect(
        borderRadius: BorderRadius.circular(24),
        child: Stack(
          children: [
            Positioned.fill(
              child: DecoratedBox(
                decoration: BoxDecoration(
                  gradient: LinearGradient(
                    colors: [
                      Colors.black.withValues(alpha: 0.55),
                      Colors.black.withValues(alpha: 0.35),
                    ],
                  ),
                ),
              ),
            ),
            Padding(
              padding: const EdgeInsets.all(22),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Discover Luxury For Less',
                    style: DupePalette.serifHeading(22, color: Colors.white),
                  ),
                  const SizedBox(height: 8),
                  Text(
                    'Find affordable alternatives to high-end fashion',
                    style: GoogleFonts.inter(
                      fontSize: 14,
                      color: Colors.white.withValues(alpha: 0.9),
                      height: 1.35,
                    ),
                  ),
                  const SizedBox(height: 18),
                  SizedBox(
                    height: 44,
                    child: DecoratedBox(
                      decoration: BoxDecoration(
                        borderRadius: BorderRadius.circular(22),
                        gradient: DupePalette.ctaGradient,
                      ),
                      child: Material(
                        color: Colors.transparent,
                        child: InkWell(
                          onTap: widget.onOpenSearch,
                          borderRadius: BorderRadius.circular(22),
                          child: Center(
                            child: Text(
                              'Explore Now',
                              style: GoogleFonts.inter(
                                color: Colors.white,
                                fontWeight: FontWeight.bold,
                                fontSize: 15,
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

  Widget _categoryChip({
    required String label,
    required String slot,
    required IconData icon,
    required List<Color> gradient,
  }) {
    return Padding(
      padding: const EdgeInsets.only(right: 12),
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          onTap: () => _openCategoryBrowse(slot, label),
          borderRadius: BorderRadius.circular(20),
          child: Ink(
            width: 96,
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(20),
              gradient: LinearGradient(colors: gradient, begin: Alignment.topLeft, end: Alignment.bottomRight),
              boxShadow: [
                BoxShadow(
                  color: gradient.first.withValues(alpha: 0.35),
                  blurRadius: 10,
                  offset: const Offset(0, 4),
                ),
              ],
            ),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Icon(icon, color: Colors.white, size: 32),
                const SizedBox(height: 8),
                Text(
                  label,
                  style: GoogleFonts.inter(
                    color: Colors.white,
                    fontWeight: FontWeight.w700,
                    fontSize: 12,
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _tile(IconData icon, String title, String subtitle, Color accent, VoidCallback onTap) {
    return Material(
      color: AppColors.cardSurface,
      borderRadius: BorderRadius.circular(AppDecor.tileRadius),
      elevation: 0,
      shadowColor: DupePalette.pink.withValues(alpha: 0.12),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(AppDecor.tileRadius),
        child: Container(
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(AppDecor.tileRadius),
            border: Border.all(color: DupePalette.pink.withValues(alpha: 0.08)),
            boxShadow: [
              BoxShadow(
                color: Colors.black.withValues(alpha: 0.04),
                blurRadius: 12,
                offset: const Offset(0, 4),
              ),
            ],
          ),
          padding: const EdgeInsets.all(14),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(icon, size: 36, color: accent),
              const SizedBox(height: 10),
              Text(title, style: GoogleFonts.inter(fontWeight: FontWeight.bold, fontSize: 15, color: DupePalette.textPrimary)),
              const SizedBox(height: 4),
              Text(subtitle, style: GoogleFonts.inter(fontSize: 12, color: DupePalette.greySubtitle)),
            ],
          ),
        ),
      ),
    );
  }
}
