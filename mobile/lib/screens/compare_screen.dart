import 'package:flutter/material.dart';
import 'package:cached_network_image/cached_network_image.dart';
import 'package:url_launcher/url_launcher.dart';
import '../theme/app_theme.dart';
import '../services/compare_service.dart';

/// Compare up to 4 products side-by-side. Add from search via compare icon.
class CompareScreen extends StatefulWidget {
  final int? refreshKey;

  const CompareScreen({super.key, this.refreshKey});

  @override
  State<CompareScreen> createState() => _CompareScreenState();
}

class _CompareScreenState extends State<CompareScreen> {
  final _compareService = CompareService();
  List<Map<String, dynamic>> _items = [];
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _load(silent: false);
  }

  @override
  void didUpdateWidget(covariant CompareScreen oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.refreshKey != widget.refreshKey) _load(silent: true);
  }

  Future<void> _load({bool silent = false}) async {
    if (!silent || _items.isEmpty) {
      setState(() => _loading = true);
    }
    final list = await _compareService.getList();
    if (mounted) {
      setState(() {
        _items = list;
        _loading = false;
      });
    }
  }

  Future<void> _openUrl(String? url) async {
    if (url == null || url.isEmpty) return;
    final normalized = url.startsWith('http://') || url.startsWith('https://')
        ? url
        : 'https://$url';
    final uri = Uri.tryParse(normalized);
    if (uri != null && await canLaunchUrl(uri)) {
      await launchUrl(uri, mode: LaunchMode.platformDefault);
    }
  }

  Future<void> _removeAt(int index) async {
    await _compareService.removeAt(index);
    if (mounted) await _load(silent: true);
  }

  @override
  Widget build(BuildContext context) {
    if (_loading) {
      return const Center(child: CircularProgressIndicator());
    }
    if (_items.isEmpty) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(32),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(Icons.compare_arrows_rounded,
                  size: 72,
                  color: AppColors.bluePrimary.withValues(alpha: 0.5)),
              const SizedBox(height: 20),
              const Text(
                'Compare',
                style: TextStyle(
                    fontSize: 22,
                    fontWeight: FontWeight.bold,
                    color: AppColors.purpleDark),
              ),
              const SizedBox(height: 12),
              const Text(
                'Tap the compare icon on any search result to add it here. Pick 2–4 items to compare price, brand, and match score.',
                textAlign: TextAlign.center,
                style: TextStyle(color: AppColors.greySubtitle, height: 1.4),
              ),
            ],
          ),
        ),
      );
    }

    return RefreshIndicator(
      onRefresh: () => _load(silent: false),
      child: ListView(
        physics: const AlwaysScrollableScrollPhysics(),
        padding: const EdgeInsets.all(16),
        children: [
          Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Text(
                    '${_items.length} item${_items.length == 1 ? '' : 's'} to compare',
                    style: TextStyle(fontSize: 14, color: Colors.grey[600]),
                  ),
                  if (_items.isNotEmpty)
                    TextButton.icon(
                      onPressed: () async {
                        await _compareService.clear();
                        if (mounted) await _load(silent: true);
                      },
                      icon: const Icon(Icons.delete_outline, size: 18),
                      label: const Text('Clear all'),
                    ),
                ],
              ),
              const SizedBox(height: 12),
              GridView.builder(
                shrinkWrap: true,
                physics: const NeverScrollableScrollPhysics(),
                gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
                  crossAxisCount: 2,
                  childAspectRatio: 0.68,
                  crossAxisSpacing: 12,
                  mainAxisSpacing: 12,
                ),
                itemCount: _items.length,
                itemBuilder: (context, index) {
                  final p = _items[index];
                  final name = p['name'] as String? ?? '';
                  final brand = p['brand'] as String? ?? '';
                  final price = p['price'] != null
                      ? (p['price'] as num).toDouble()
                      : null;
                  final imageUrl = p['image_url'] as String?;
                  final productUrl = p['product_url'] as String?;
                  final score = (p['final_score'] as num?)?.toDouble() ?? 0;
                  final matchPercent = (score * 100).round();
                  return Card(
                    clipBehavior: Clip.antiAlias,
                    child: InkWell(
                      onTap: () => _openUrl(productUrl),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.stretch,
                        children: [
                          Expanded(
                            flex: 3,
                            child: Stack(
                              alignment: Alignment.topRight,
                              children: [
                                imageUrl != null && imageUrl.isNotEmpty
                                    ? CachedNetworkImage(
                                        imageUrl: imageUrl,
                                        fit: BoxFit.cover,
                                        width: double.infinity,
                                        height: double.infinity,
                                        placeholder: (_, __) => const Center(
                                            child: CircularProgressIndicator()),
                                        errorWidget: (_, __, ___) => const Icon(
                                            Icons.broken_image,
                                            size: 40),
                                      )
                                    : const Center(
                                        child: Icon(Icons.image_not_supported,
                                            size: 40)),
                                IconButton(
                                  icon:
                                      const Icon(Icons.close_rounded, size: 20),
                                  onPressed: () => _removeAt(index),
                                  style: IconButton.styleFrom(
                                    backgroundColor: Colors.black54,
                                    foregroundColor: Colors.white,
                                    padding: const EdgeInsets.all(4),
                                    minimumSize: const Size(32, 32),
                                  ),
                                ),
                              ],
                            ),
                          ),
                          Padding(
                            padding: const EdgeInsets.all(8),
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(
                                  name,
                                  maxLines: 2,
                                  overflow: TextOverflow.ellipsis,
                                  style: const TextStyle(
                                      fontWeight: FontWeight.w600,
                                      fontSize: 12),
                                ),
                                if (brand.isNotEmpty)
                                  Text(brand,
                                      maxLines: 1,
                                      overflow: TextOverflow.ellipsis,
                                      style: TextStyle(
                                          fontSize: 11,
                                          color: Colors.grey[600])),
                                if (price != null)
                                  Text('PKR ${price.toStringAsFixed(0)}',
                                      style: const TextStyle(
                                          fontWeight: FontWeight.bold,
                                          fontSize: 12)),
                                const SizedBox(height: 4),
                                Container(
                                  padding: const EdgeInsets.symmetric(
                                      horizontal: 6, vertical: 2),
                                  decoration: BoxDecoration(
                                    color: AppColors.bluePrimary,
                                    borderRadius: BorderRadius.circular(4),
                                  ),
                                  child: Text('$matchPercent% match',
                                      style: const TextStyle(
                                          color: Colors.white,
                                          fontSize: 11,
                                          fontWeight: FontWeight.w500)),
                                ),
                              ],
                            ),
                          ),
                        ],
                      ),
                    ),
                  );
                },
              ),
              if (_items.length >= 2) _buildComparisonSummary(),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildComparisonSummary() {
    final prices = <double>[];
    final matches = <int>[];
    final brands = <String>{};
    for (final p in _items) {
      final price = p['price'];
      if (price != null) prices.add((price as num).toDouble());
      final score = (p['final_score'] as num?)?.toDouble();
      if (score != null) matches.add((score * 100).round());
      final brand = p['brand'] as String?;
      if (brand != null && brand.isNotEmpty) brands.add(brand);
    }
    final priceMin =
        prices.isEmpty ? null : prices.reduce((a, b) => a < b ? a : b);
    final priceMax =
        prices.isEmpty ? null : prices.reduce((a, b) => a > b ? a : b);
    final priceDiff =
        (priceMin != null && priceMax != null && priceMax > priceMin)
            ? (priceMax - priceMin).round()
            : null;
    final matchMin =
        matches.isEmpty ? null : matches.reduce((a, b) => a < b ? a : b);
    final matchMax =
        matches.isEmpty ? null : matches.reduce((a, b) => a > b ? a : b);

    return Container(
      margin: const EdgeInsets.only(top: 20),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppColors.bluePrimary.withValues(alpha: 0.06),
        borderRadius: BorderRadius.circular(12),
        border:
            Border.all(color: AppColors.borderLightBlue.withValues(alpha: 0.8)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Row(
            children: [
              Icon(Icons.analytics_outlined,
                  size: 20, color: AppColors.bluePrimary),
              SizedBox(width: 8),
              Text(
                'Comparison summary',
                style: TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.bold,
                    color: AppColors.purpleDark),
              ),
            ],
          ),
          const SizedBox(height: 12),
          if (priceMin != null && priceMax != null) ...[
            _summaryRow('Price range',
                'PKR ${priceMin.toStringAsFixed(0)} – PKR ${priceMax.toStringAsFixed(0)}'),
            if (priceDiff != null && priceDiff > 0)
              _summaryRow('Price difference',
                  'PKR ${priceDiff.toString()} between lowest and highest'),
            const SizedBox(height: 8),
          ],
          if (matchMin != null && matchMax != null) ...[
            _summaryRow(
                'Match score',
                matchMin == matchMax
                    ? '$matchMin% (same)'
                    : '$matchMin% – $matchMax%'),
            const SizedBox(height: 8),
          ],
          _summaryRow(
              'Brands',
              brands.isEmpty
                  ? '—'
                  : brands.length == 1
                      ? 'Same: ${brands.first}'
                      : '${brands.length} different: ${brands.take(3).join(', ')}${brands.length > 3 ? '...' : ''}'),
        ],
      ),
    );
  }

  Widget _summaryRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 4),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 120,
            child: Text(label,
                style: TextStyle(
                    fontSize: 13,
                    color: Colors.grey[700],
                    fontWeight: FontWeight.w500)),
          ),
          Expanded(
              child: Text(value,
                  style: const TextStyle(
                      fontSize: 13, color: AppColors.purpleDark))),
        ],
      ),
    );
  }
}
