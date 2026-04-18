import 'package:cached_network_image/cached_network_image.dart';
import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:url_launcher/url_launcher.dart';

import '../services/api_service.dart';
import '../services/dupe_history_service.dart';
import '../theme/app_theme.dart';
import 'category_browse_screen.dart';

/// Home: Discover header, hero, shop-by-category, and DB-backed trending dupes strip.
class HomeTab extends StatefulWidget {
  final VoidCallback onOpenSearch;

  const HomeTab({
    super.key,
    required this.onOpenSearch,
  });

  @override
  State<HomeTab> createState() => _HomeTabState();
}

class _HomeTabState extends State<HomeTab> {
  final _apiService = ApiService();
  final _history = DupeHistoryService();
  String? _userName;
  String? _userEmail;
  bool _guest = false;
  List<Map<String, dynamic>> _trending = [];
  bool _trendingLoading = true;
  String? _trendingError;

  @override
  void initState() {
    super.initState();
    _load();
    _loadTrendingDupes();
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
            padding: const EdgeInsets.fromLTRB(16, 4, 16, 28),
            sliver: SliverToBoxAdapter(
              child: _trendingStrip(),
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

  Future<void> _loadTrendingDupes() async {
    if (!mounted) return;
    setState(() {
      _trendingLoading = true;
      _trendingError = null;
    });
    const slots = ['dresses', 'bags', 'accessories', 'jewelry'];
    final seen = <String>{};
    final merged = <Map<String, dynamic>>[];
    try {
      for (final slot in slots) {
        final body = await _apiService.shopBrowse(slot: slot, limit: 4);
        final raw = body['items'] as List<dynamic>? ?? [];
        for (final e in raw) {
          final m = Map<String, dynamic>.from(e as Map);
          final id = (m['id'] ?? m['_id'] ?? '').toString();
          if (id.isEmpty) continue;
          if (seen.add(id)) merged.add(m);
          if (merged.length >= 12) break;
        }
        if (merged.length >= 12) break;
      }
      if (!mounted) return;
      setState(() {
        _trending = merged;
        _trendingLoading = false;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _trendingError = e.toString().replaceFirst('Exception: ', '');
        _trendingLoading = false;
      });
    }
  }

  String _apiOrigin() {
    final base = ApiService.baseUrl;
    return base.endsWith('/api') ? base.substring(0, base.length - 4) : base;
  }

  String? _resolveImageUrl(Map<String, dynamic> product) {
    final origin = _apiOrigin();
    final imageUrl = (product['image_url'] as String?)?.trim();
    final imagePath = (product['image_path'] as String?)?.trim();

    if (imagePath != null && imagePath.isNotEmpty) {
      final path = imagePath.replaceAll('\\', '/');
      if (!path.startsWith('http://') && !path.startsWith('https://')) {
        return '$origin/data/$path';
      }
    }
    if (imageUrl != null && imageUrl.isNotEmpty) {
      if (imageUrl.startsWith('http://') || imageUrl.startsWith('https://')) {
        return '$origin/api/products/image-proxy?url=${Uri.encodeComponent(imageUrl)}';
      }
      return imageUrl;
    }
    if (imagePath != null && imagePath.isNotEmpty) {
      return imagePath;
    }
    return null;
  }

  String? _resolveProductUrl(Map<String, dynamic> product) {
    final raw = ((product['product_url'] ??
            product['product_link'] ??
            product['url'] ??
            '') as String?)
        ?.trim();
    if (raw == null || raw.isEmpty) return null;
    if (raw.startsWith('http://') || raw.startsWith('https://')) return raw;
    return 'https://$raw';
  }

  Future<void> _openTrendingProduct(Map<String, dynamic> product) async {
    final messenger = ScaffoldMessenger.maybeOf(context);
    await _history.recordClick(product);
    final raw = _resolveProductUrl(product);
    if (raw == null || raw.isEmpty) {
      messenger?.showSnackBar(
        const SnackBar(
          content: Text('No store link for this item.'),
          behavior: SnackBarBehavior.floating,
        ),
      );
      return;
    }
    final normalized = raw.startsWith('http://') || raw.startsWith('https://')
        ? raw
        : (raw.startsWith('//') ? 'https:$raw' : 'https://$raw');
    final uri = Uri.tryParse(normalized);
    if (uri == null) {
      messenger?.showSnackBar(
        const SnackBar(
          content: Text('Invalid product link.'),
          behavior: SnackBarBehavior.floating,
        ),
      );
      return;
    }
    try {
      var opened = await launchUrl(uri, mode: LaunchMode.externalApplication);
      if (!opened) {
        opened = await launchUrl(uri, mode: LaunchMode.platformDefault);
      }
      if (!opened && mounted) {
        messenger?.showSnackBar(
          SnackBar(
            content: Text('Could not open link: ${uri.toString()}'),
            behavior: SnackBarBehavior.floating,
          ),
        );
      }
    } catch (e) {
      if (mounted) {
        messenger?.showSnackBar(
          SnackBar(
            content: Text('Could not open link: $e'),
            behavior: SnackBarBehavior.floating,
          ),
        );
      }
    }
  }

  Widget _trendingStrip() {
    if (_trendingLoading) {
      return const Padding(
        padding: EdgeInsets.symmetric(vertical: 28),
        child: Center(
          child: CircularProgressIndicator(color: DupePalette.pink),
        ),
      );
    }
    if (_trendingError != null) {
      return Padding(
        padding: const EdgeInsets.symmetric(vertical: 12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              _trendingError!,
              style: GoogleFonts.inter(
                fontSize: 13,
                color: DupePalette.greySubtitle,
              ),
            ),
            TextButton(
              onPressed: () => _loadTrendingDupes(),
              child: Text(
                'Retry',
                style: GoogleFonts.inter(
                  fontWeight: FontWeight.w600,
                  color: DupePalette.blue,
                ),
              ),
            ),
          ],
        ),
      );
    }
    if (_trending.isEmpty) {
      return Padding(
        padding: const EdgeInsets.symmetric(vertical: 12),
        child: Text(
          'No dupes to show yet.',
          style: GoogleFonts.inter(
            fontSize: 13,
            color: DupePalette.greySubtitle,
          ),
        ),
      );
    }
    return SizedBox(
      height: 220,
      child: ListView.separated(
        scrollDirection: Axis.horizontal,
        padding: const EdgeInsets.fromLTRB(4, 8, 4, 4),
        itemCount: _trending.length,
        separatorBuilder: (_, __) => const SizedBox(width: 12),
        itemBuilder: (_, i) => _trendingCard(_trending[i]),
      ),
    );
  }

  Widget _trendingCard(Map<String, dynamic> product) {
    final name = (product['name'] as String?)?.trim() ?? 'Product';
    final brand = (product['brand'] as String?)?.trim() ?? '';
    final price = (product['price'] as num?)?.toDouble() ?? 0;
    final imgUrl = _resolveImageUrl(product);
    return SizedBox(
      width: 138,
      height: 220,
      child: Material(
        color: Colors.white,
        borderRadius: BorderRadius.circular(18),
        clipBehavior: Clip.antiAlias,
        elevation: 0,
        shadowColor: DupePalette.pink.withValues(alpha: 0.12),
        child: InkWell(
          onTap: () => _openTrendingProduct(product),
          borderRadius: BorderRadius.circular(18),
          splashColor: DupePalette.pink.withValues(alpha: 0.12),
          child: Padding(
            padding: const EdgeInsets.all(8),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                Expanded(
                  child: ClipRRect(
                    borderRadius: BorderRadius.circular(12),
                    child: imgUrl == null
                        ? ColoredBox(
                            color: DupePalette.pink.withValues(alpha: 0.06),
                            child: Icon(
                              Icons.image_not_supported_outlined,
                              color: DupePalette.greySubtitle,
                            ),
                          )
                        : CachedNetworkImage(
                            imageUrl: imgUrl,
                            fit: BoxFit.cover,
                            width: double.infinity,
                            placeholder: (_, __) => const Center(
                              child: SizedBox(
                                width: 22,
                                height: 22,
                                child: CircularProgressIndicator(
                                  strokeWidth: 2,
                                  color: DupePalette.pink,
                                ),
                              ),
                            ),
                            errorWidget: (_, __, ___) => ColoredBox(
                              color: DupePalette.pink.withValues(alpha: 0.06),
                              child: Icon(
                                Icons.hide_image_outlined,
                                color: DupePalette.greySubtitle,
                              ),
                            ),
                          ),
                  ),
                ),
                const SizedBox(height: 8),
                if (brand.isNotEmpty)
                  Text(
                    brand,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: GoogleFonts.inter(
                      fontSize: 11,
                      fontWeight: FontWeight.w600,
                      color: DupePalette.blue,
                    ),
                  ),
                Text(
                  name,
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                  style: GoogleFonts.inter(
                    fontSize: 13,
                    fontWeight: FontWeight.w700,
                    color: DupePalette.textPrimary,
                    height: 1.2,
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  price > 0
                      ? 'Rs ${price.toStringAsFixed(0)}'
                      : 'Price on store',
                  style: GoogleFonts.inter(
                    fontSize: 12,
                    fontWeight: FontWeight.w600,
                    color: DupePalette.pinkDeep,
                  ),
                ),
              ],
            ),
          ),
        ),
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
}
