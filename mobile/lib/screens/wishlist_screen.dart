import 'package:flutter/material.dart';
import 'package:cached_network_image/cached_network_image.dart';
import 'package:url_launcher/url_launcher.dart';
import '../theme/app_theme.dart';
import '../services/wishlist_service.dart';
import '../services/compare_service.dart';

/// Wishlist: saved products from search. Local persistence via WishlistService.
class WishlistScreen extends StatefulWidget {
  final int? refreshKey;

  const WishlistScreen({super.key, this.refreshKey});

  @override
  State<WishlistScreen> createState() => _WishlistScreenState();
}

class _WishlistScreenState extends State<WishlistScreen> {
  final _wishlistService = WishlistService();
  final _compareService = CompareService();
  List<Map<String, dynamic>> _items = [];
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _load(silent: false);
  }

  @override
  void didUpdateWidget(covariant WishlistScreen oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.refreshKey != widget.refreshKey) _load(silent: true);
  }

  Future<void> _load({bool silent = false}) async {
    if (!silent || _items.isEmpty) {
      setState(() => _loading = true);
    }
    final list = await _wishlistService.getSavedProducts();
    if (mounted)
      setState(() {
        _items = list;
        _loading = false;
      });
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

  Future<void> _remove(Map<String, dynamic> product) async {
    await _wishlistService.removeProduct(WishlistService.productId(product));
    if (mounted) await _load(silent: true);
  }

  Future<void> _addToCompare(Map<String, dynamic> product) async {
    final added = await _compareService.addProduct(product);
    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content:
              Text(added ? 'Added to Compare' : 'Compare list full (max 4)'),
          behavior: SnackBarBehavior.floating,
        ),
      );
    }
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
              Icon(Icons.favorite_border_rounded,
                  size: 72,
                  color: AppColors.bluePrimary.withValues(alpha: 0.5)),
              const SizedBox(height: 20),
              const Text(
                'Wishlist',
                style: TextStyle(
                    fontSize: 22,
                    fontWeight: FontWeight.bold,
                    color: AppColors.purpleDark),
              ),
              const SizedBox(height: 12),
              Text(
                'Save products from search results by tapping the heart on any result.',
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
      child: GridView.builder(
        padding: const EdgeInsets.all(16),
        gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
          crossAxisCount: 2,
          childAspectRatio: 0.72,
          crossAxisSpacing: 12,
          mainAxisSpacing: 12,
        ),
        itemCount: _items.length,
        itemBuilder: (context, index) {
          final p = _items[index];
          final name = p['name'] as String? ?? '';
          final brand = p['brand'] as String? ?? '';
          final price =
              p['price'] != null ? (p['price'] as num).toDouble() : null;
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
                                errorWidget: (_, __, ___) =>
                                    const Icon(Icons.broken_image, size: 48),
                              )
                            : const Center(
                                child:
                                    Icon(Icons.image_not_supported, size: 48)),
                        Padding(
                          padding: const EdgeInsets.all(6),
                          child: Row(
                            mainAxisSize: MainAxisSize.min,
                            mainAxisAlignment: MainAxisAlignment.end,
                            children: [
                              Material(
                                color: Colors.white.withValues(alpha: 0.9),
                                shape: const CircleBorder(),
                                child: IconButton(
                                  icon: Icon(Icons.compare_arrows_rounded,
                                      size: 20, color: Colors.grey[700]),
                                  onPressed: () => _addToCompare(p),
                                  padding: const EdgeInsets.all(6),
                                  constraints: const BoxConstraints(
                                      minWidth: 34, minHeight: 34),
                                ),
                              ),
                              const SizedBox(width: 4),
                              Material(
                                color: Colors.white.withValues(alpha: 0.9),
                                shape: const CircleBorder(),
                                child: IconButton(
                                  icon: const Icon(Icons.favorite_rounded,
                                      color: Colors.red, size: 22),
                                  onPressed: () => _remove(p),
                                  padding: const EdgeInsets.all(6),
                                  constraints: const BoxConstraints(
                                      minWidth: 36, minHeight: 36),
                                ),
                              ),
                            ],
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
                              fontWeight: FontWeight.w600, fontSize: 12),
                        ),
                        if (brand.isNotEmpty)
                          Text(
                            brand,
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                            style: TextStyle(
                                fontSize: 11, color: Colors.grey[600]),
                          ),
                        if (price != null)
                          Text(
                            'PKR ${price.toStringAsFixed(0)}',
                            style: const TextStyle(
                                fontWeight: FontWeight.bold, fontSize: 12),
                          ),
                        const SizedBox(height: 4),
                        Container(
                          padding: const EdgeInsets.symmetric(
                              horizontal: 6, vertical: 2),
                          decoration: BoxDecoration(
                            color: AppColors.bluePrimary,
                            borderRadius: BorderRadius.circular(4),
                          ),
                          child: Text(
                            '$matchPercent% match',
                            style: const TextStyle(
                                color: Colors.white,
                                fontSize: 11,
                                fontWeight: FontWeight.w500),
                          ),
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
    );
  }
}
