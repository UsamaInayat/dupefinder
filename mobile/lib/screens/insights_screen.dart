import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:url_launcher/url_launcher.dart';
import '../theme/app_theme.dart';
import '../services/wishlist_service.dart';
import '../services/dupe_history_service.dart';

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
  List<DupeHistoryEntry> _history = [];
  List<String> _searchCategories = [];
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    final results = await Future.wait([
      _wishlistService.getSavedProducts(),
      _historyService.getHistory(),
      SharedPreferences.getInstance(),
    ]);
    final wishlist = results[0] as List<Map<String, dynamic>>;
    final history = results[1] as List<DupeHistoryEntry>;
    final prefs = results[2] as SharedPreferences;
    final categories = prefs.getStringList('insights_search_categories') ?? [];
    if (mounted) {
      setState(() {
      _wishlist = wishlist;
      _history = history;
      _searchCategories = categories;
      _loading = false;
    });
    }
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

  List<DupeHistoryEntry> get _topClickedDupes {
    final list = [..._history];
    list.sort((a, b) {
      final byCount = b.clickCount.compareTo(a.clickCount);
      if (byCount != 0) return byCount;
      return b.clickedAt.compareTo(a.clickedAt);
    });
    return list.take(10).toList();
  }

  Future<void> _openProduct(Map<String, dynamic> product) async {
    final raw = ((product['product_url'] ?? product['product_link'] ?? product['url'] ?? '') as String).trim();
    if (raw.isEmpty) return;
    final normalized = raw.startsWith('http://') || raw.startsWith('https://') ? raw : 'https://$raw';
    final uri = Uri.tryParse(normalized);
    if (uri == null) return;
    await launchUrl(uri, mode: LaunchMode.externalApplication);
  }

  void _showTrendingDupes() {
    final items = _topClickedDupes;
    showModalBottomSheet<void>(
      context: context,
      showDragHandle: true,
      builder: (ctx) => SafeArea(
        child: items.isEmpty
            ? const Padding(
                padding: EdgeInsets.all(20),
                child: Text('No clicked dupes yet. Open products from Find Similar first.'),
              )
            : ListView.separated(
                itemCount: items.length,
                separatorBuilder: (_, __) => const Divider(height: 1),
                itemBuilder: (_, i) {
                  final e = items[i];
                  final name = (e.product['name'] ?? 'Unknown product').toString();
                  final brand = (e.product['brand'] ?? '').toString();
                  return ListTile(
                    title: Text(name, maxLines: 2, overflow: TextOverflow.ellipsis),
                    subtitle: Text(
                      '${brand.isNotEmpty ? '$brand • ' : ''}${e.clickCount} click${e.clickCount == 1 ? '' : 's'}',
                    ),
                    trailing: const Icon(Icons.open_in_new_rounded),
                    onTap: () => _openProduct(e.product),
                  );
                },
              ),
      ),
    );
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
              _topClickedDupes.isEmpty
                  ? 'Most-clicked dupes will appear here. Tap to open items once available.'
                  : _topClickedDupes
                      .take(3)
                      .map((e) => '${(e.product['name'] ?? 'Item').toString()} (${e.clickCount})')
                      .join(' • '),
              onTap: _showTrendingDupes,
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
                      style: const TextStyle(
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
