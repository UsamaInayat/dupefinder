import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../theme/app_theme.dart';
import '../services/wishlist_service.dart';
import '../services/dupe_history_service.dart';
import 'dupe_history_screen.dart';

/// Insights: old 3 options, all live from local data.
class InsightsScreen extends StatefulWidget {
  const InsightsScreen({super.key});

  @override
  State<InsightsScreen> createState() => _InsightsScreenState();
}

class _InsightsScreenState extends State<InsightsScreen> {
  final _wishlistService = WishlistService();
  final _historyService = DupeHistoryService();
  List<Map<String, dynamic>> _wishlist = [];
  int _historyCount = 0;
  int _reviewedCount = 0;
  List<String> _searchCategories = [];
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    final wishlist = await _wishlistService.getSavedProducts();
    final history = await _historyService.getHistory();
    final prefs = await SharedPreferences.getInstance();
    final categories = prefs.getStringList('insights_search_categories') ?? [];
    if (mounted) setState(() {
      _wishlist = wishlist;
      _historyCount = history.length;
      _reviewedCount = history.where((e) => e.review != null).length;
      _searchCategories = categories;
      _loading = false;
    });
  }

  /// Total price of saved items (estimate of what you're comparing to luxury).
  double get _totalSavedValue {
    double sum = 0;
    for (final p in _wishlist) {
      final price = p['price'];
      if (price != null) sum += (price as num).toDouble();
    }
    return sum;
  }

  /// Top categories by search frequency (most searched first).
  List<MapEntry<String, int>> get _topCategories {
    final counts = <String, int>{};
    for (final c in _searchCategories) {
      if (c.isNotEmpty) counts[c] = (counts[c] ?? 0) + 1;
    }
    final list = counts.entries.toList();
    list.sort((a, b) => b.value.compareTo(a.value));
    return list.take(5).toList();
  }

  /// Top brands in wishlist (trending for you).
  List<MapEntry<String, int>> get _trendingBrands {
    final counts = <String, int>{};
    for (final p in _wishlist) {
      final brand = p['brand'] as String? ?? 'Unknown';
      if (brand.isNotEmpty) counts[brand] = (counts[brand] ?? 0) + 1;
    }
    final list = counts.entries.toList();
    list.sort((a, b) => b.value.compareTo(a.value));
    return list.take(5).toList();
  }

  @override
  Widget build(BuildContext context) {
    if (_loading) {
      return const Center(child: CircularProgressIndicator());
    }
    return Scaffold(
      appBar: AppBar(
        title: const Text('Insights'),
        backgroundColor: AppColors.cardSurface,
        foregroundColor: AppColors.purpleDark,
      ),
      body: RefreshIndicator(
        onRefresh: _load,
        child: ListView(
          padding: const EdgeInsets.all(20),
          children: [
            _card(
              Icons.savings_outlined,
              'Average savings',
              _wishlist.isEmpty
                  ? 'See how much you save vs luxury retail once you start searching and saving items.'
                  : 'You have ${_wishlist.length} saved item${_wishlist.length == 1 ? '' : 's'}. '
                      'Total value PKR ${_totalSavedValue.toStringAsFixed(0)} — compare with luxury retail to see your savings.',
            ),
            _card(
              Icons.trending_up_rounded,
              'Top categories',
              _topCategories.isEmpty
                  ? 'Your most searched styles will appear here. Run a search with a category selected.'
                  : _topCategories.map((e) => '${e.key} (${e.value})').join(' • '),
            ),
            _card(
              Icons.local_fire_department_outlined,
              'Trending alternatives',
              _trendingBrands.isEmpty
                  ? 'Popular dupes in your list will appear here once you save items from search.'
                  : 'Top in your list: ${_trendingBrands.map((e) => '${e.key} (${e.value})').join(', ')}.',
            ),
            _card(
              Icons.history_rounded,
              'Dupe history & reviews',
              'Clicked dupes: $_historyCount | Reviewed: $_reviewedCount. Tap to open and rate with stars.',
              onTap: () {
                Navigator.push(
                  context,
                  MaterialPageRoute(builder: (_) => const DupeHistoryScreen()),
                );
              },
            ),
          ],
        ),
      ),
    );
  }

  Widget _card(IconData icon, String title, String body, {VoidCallback? onTap}) {
    return Card(
      margin: const EdgeInsets.only(bottom: 14),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      child: InkWell(
        borderRadius: BorderRadius.circular(16),
        onTap: onTap,
        child: Padding(
          padding: const EdgeInsets.all(18),
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Container(
                padding: const EdgeInsets.all(10),
                decoration: BoxDecoration(
                  color: AppColors.bluePrimary.withValues(alpha: 0.12),
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Icon(icon, color: AppColors.bluePrimary, size: 32),
              ),
              const SizedBox(width: 16),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      title,
                      style: const TextStyle(
                        fontWeight: FontWeight.bold,
                        fontSize: 16,
                        color: AppColors.purpleDark,
                      ),
                    ),
                    const SizedBox(height: 6),
                    Text(
                      body,
                      style: TextStyle(
                        color: AppColors.greySubtitle,
                        height: 1.35,
                        fontSize: 13,
                      ),
                    ),
                  ],
                ),
              ),
              if (onTap != null) const Icon(Icons.chevron_right_rounded),
            ],
          ),
        ),
      ),
    );
  }
}
