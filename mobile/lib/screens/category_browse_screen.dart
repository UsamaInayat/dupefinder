import 'package:flutter/material.dart';
import 'package:cached_network_image/cached_network_image.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:url_launcher/url_launcher.dart';

import '../services/api_service.dart';
import '../services/dupe_history_service.dart';
import '../theme/app_theme.dart';

/// Home → Shop by category: shows up to 10 DB products for one slot (dresses, bags, …).
class CategoryBrowseScreen extends StatefulWidget {
  final String slot;
  final String title;

  const CategoryBrowseScreen({
    super.key,
    required this.slot,
    required this.title,
  });

  @override
  State<CategoryBrowseScreen> createState() => _CategoryBrowseScreenState();
}

class _CategoryBrowseScreenState extends State<CategoryBrowseScreen> {
  final _api = ApiService();
  final _history = DupeHistoryService();
  final Set<String> _prefetchedImageUrls = <String>{};
  List<Map<String, dynamic>> _items = [];
  String? _error;
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final body = await _api.shopBrowse(slot: widget.slot, limit: 10);
      final raw = body['items'] as List<dynamic>? ?? [];
      if (!mounted) return;
      setState(() {
        _items = raw.map((e) => Map<String, dynamic>.from(e as Map)).toList();
        _loading = false;
      });
      _prefetchCategoryImages(_items);
    } catch (e) {
      if (!mounted) return;
      setState(() {
        _error = e.toString();
        _loading = false;
      });
    }
  }

  String _apiOrigin() {
    final base = ApiService.baseUrl;
    return base.endsWith('/api') ? base.substring(0, base.length - 4) : base;
  }

  bool _isLocalBackendHost(String host) {
    final h = host.toLowerCase();
    return h == 'localhost' || h == '127.0.0.1' || h == '10.0.2.2';
  }

  String _retargetToResolvedOrigin(String rawUrl, String origin) {
    final raw = Uri.tryParse(rawUrl);
    final o = Uri.tryParse(origin);
    if (raw == null || o == null) return rawUrl;
    if (!raw.hasScheme || raw.host.isEmpty) return rawUrl;
    if (!_isLocalBackendHost(raw.host)) return rawUrl;
    return raw
        .replace(
          scheme: o.scheme,
          host: o.host,
          port: o.hasPort ? o.port : null,
        )
        .toString();
  }

  String? _resolveImageUrl(Map<String, dynamic> product) {
    final origin = _apiOrigin();
    final imageSrc = (product['image_src'] as String?)?.trim();
    final imageUrl = (product['image_url'] as String?)?.trim();
    final imagePath = (product['image_path'] as String?)?.trim();

    if (imageSrc != null && imageSrc.isNotEmpty) {
      if (imageSrc.startsWith('http://') || imageSrc.startsWith('https://')) {
        return _retargetToResolvedOrigin(imageSrc, origin);
      }
      if (imageSrc.startsWith('/')) return '$origin$imageSrc';
      return imageSrc;
    }

    if (imagePath != null && imagePath.isNotEmpty) {
      final path = imagePath.replaceAll('\\', '/');
      if (path.startsWith('http://') || path.startsWith('https://')) {
        return _retargetToResolvedOrigin(path, origin);
      }
      if (path.startsWith('/')) return '$origin$path';
      if (!path.startsWith('http://') && !path.startsWith('https://')) {
        return '$origin/data/$path';
      }
    }
    if (imageUrl != null && imageUrl.isNotEmpty) {
      if (imageUrl.startsWith('http://') || imageUrl.startsWith('https://')) {
        final parsed = Uri.tryParse(imageUrl);
        if (parsed != null && _isLocalBackendHost(parsed.host)) {
          return _retargetToResolvedOrigin(imageUrl, origin);
        }
        return '$origin/api/products/image-proxy?url=${Uri.encodeComponent(imageUrl)}';
      }
      if (imageUrl.startsWith('/')) return '$origin$imageUrl';
      return imageUrl;
    }
    if (imagePath != null && imagePath.isNotEmpty) {
      return imagePath;
    }
    return null;
  }

  void _prefetchCategoryImages(List<Map<String, dynamic>> products) {
    if (!mounted) return;
    final urls = <String>{};
    for (final p in products) {
      final u = _resolveImageUrl(p);
      if (u != null && u.isNotEmpty) urls.add(u);
    }
    urls.removeAll(_prefetchedImageUrls);
    if (urls.isEmpty) return;
    _prefetchedImageUrls.addAll(urls);
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!mounted) return;
      for (final url in urls.take(16)) {
        precacheImage(CachedNetworkImageProvider(url), context).catchError((_) {});
      }
    });
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

  Future<void> _openProduct(Map<String, dynamic> product) async {
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
      final openedExternally = await launchUrl(
        uri,
        mode: LaunchMode.externalApplication,
      );
      if (openedExternally) return;
      final openedInApp = await launchUrl(
        uri,
        mode: LaunchMode.platformDefault,
      );
      if (!openedInApp && mounted) {
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
            content: Text('Failed to open: $e'),
            behavior: SnackBarBehavior.floating,
          ),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: DupePalette.scaffoldLight,
      appBar: AppBar(
        title: Text(widget.title),
        backgroundColor: Colors.white,
        foregroundColor: DupePalette.textPrimary,
        elevation: 0,
        surfaceTintColor: Colors.transparent,
      ),
      body: _loading
          ? const Center(child: CircularProgressIndicator(color: DupePalette.pink))
          : _error != null
              ? Center(
                  child: Padding(
                    padding: const EdgeInsets.all(24),
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Text(
                          'Could not load items',
                          style: GoogleFonts.inter(
                            fontWeight: FontWeight.w700,
                            fontSize: 16,
                            color: DupePalette.textPrimary,
                          ),
                        ),
                        const SizedBox(height: 8),
                        Text(
                          _error!,
                          textAlign: TextAlign.center,
                          style: GoogleFonts.inter(
                            fontSize: 13,
                            color: DupePalette.greySubtitle,
                          ),
                        ),
                        const SizedBox(height: 16),
                        FilledButton(
                          onPressed: _load,
                          child: const Text('Retry'),
                        ),
                      ],
                    ),
                  ),
                )
              : _items.isEmpty
                  ? Center(
                      child: Text(
                        'No products in this category yet.',
                        style: GoogleFonts.inter(
                          color: DupePalette.greySubtitle,
                          fontSize: 15,
                        ),
                      ),
                    )
                  : RefreshIndicator(
                      color: DupePalette.pink,
                      onRefresh: _load,
                      child: ListView.separated(
                        padding: const EdgeInsets.fromLTRB(16, 8, 16, 24),
                        itemCount: _items.length,
                        separatorBuilder: (_, __) => const SizedBox(height: 12),
                        itemBuilder: (_, i) {
                          final p = _items[i];
                          final name = (p['name'] as String?) ?? 'Product';
                          final brand = (p['brand'] as String?) ?? '';
                          final price = (p['price'] as num?)?.toDouble() ?? 0;
                          final desc =
                              (p['description'] as String?)?.trim() ?? '';
                          final cat =
                              (p['display_category'] as String?)?.trim() ?? '';
                          final imgUrl = _resolveImageUrl(p);
                          return Material(
                            color: Colors.white,
                            borderRadius: BorderRadius.circular(18),
                            child: InkWell(
                              onTap: () => _openProduct(p),
                              borderRadius: BorderRadius.circular(18),
                              splashColor:
                                  DupePalette.pink.withValues(alpha: 0.12),
                              highlightColor:
                                  DupePalette.pink.withValues(alpha: 0.06),
                              child: Padding(
                                padding: const EdgeInsets.all(12),
                                child: Row(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    ClipRRect(
                                      borderRadius: BorderRadius.circular(12),
                                      child: SizedBox(
                                        width: 88,
                                        height: 88,
                                        child: imgUrl != null
                                            ? CachedNetworkImage(
                                                imageUrl: imgUrl,
                                                fit: BoxFit.cover,
                                                placeholder: (_, __) => const Center(
                                                  child: SizedBox(
                                                    width: 18,
                                                    height: 18,
                                                    child: CircularProgressIndicator(
                                                      strokeWidth: 2,
                                                      color: DupePalette.pink,
                                                    ),
                                                  ),
                                                ),
                                                errorWidget: (_, __, ___) =>
                                                    ColoredBox(
                                                  color: DupePalette.pink
                                                      .withValues(alpha: 0.08),
                                                  child: Icon(
                                                    Icons
                                                        .hide_image_outlined,
                                                    color: DupePalette
                                                        .greySubtitle,
                                                  ),
                                                ),
                                              )
                                            : ColoredBox(
                                                color: DupePalette.pink
                                                    .withValues(alpha: 0.08),
                                                child: Icon(
                                                  Icons.image_not_supported_outlined,
                                                  color: DupePalette.greySubtitle,
                                                ),
                                              ),
                                      ),
                                    ),
                                    const SizedBox(width: 12),
                                    Expanded(
                                      child: Column(
                                        crossAxisAlignment:
                                            CrossAxisAlignment.start,
                                        children: [
                                          if (brand.isNotEmpty)
                                            Text(
                                              brand,
                                              maxLines: 1,
                                              overflow: TextOverflow.ellipsis,
                                              style: GoogleFonts.inter(
                                                fontSize: 12,
                                                fontWeight: FontWeight.w600,
                                                color: DupePalette.blue,
                                              ),
                                            ),
                                          Text(
                                            name,
                                            maxLines: 2,
                                            overflow: TextOverflow.ellipsis,
                                            style: GoogleFonts.inter(
                                              fontSize: 15,
                                              fontWeight: FontWeight.w700,
                                              color: DupePalette.textPrimary,
                                              height: 1.25,
                                            ),
                                          ),
                                          if (cat.isNotEmpty) ...[
                                            const SizedBox(height: 4),
                                            Text(
                                              cat,
                                              maxLines: 1,
                                              overflow: TextOverflow.ellipsis,
                                              style: GoogleFonts.inter(
                                                fontSize: 11,
                                                color: DupePalette.greySubtitle,
                                              ),
                                            ),
                                          ],
                                          const SizedBox(height: 6),
                                          Text(
                                            price > 0
                                                ? 'Rs ${price.toStringAsFixed(0)}'
                                                : 'Price on store',
                                            style: GoogleFonts.inter(
                                              fontSize: 14,
                                              fontWeight: FontWeight.w600,
                                              color: DupePalette.pinkDeep,
                                            ),
                                          ),
                                          if (desc.isNotEmpty) ...[
                                            const SizedBox(height: 6),
                                            Text(
                                              desc,
                                              maxLines: 3,
                                              overflow: TextOverflow.ellipsis,
                                              style: GoogleFonts.inter(
                                                fontSize: 12,
                                                color: DupePalette.greySubtitle,
                                                height: 1.35,
                                              ),
                                            ),
                                          ],
                                          const SizedBox(height: 6),
                                          Row(
                                            children: [
                                              Text(
                                                'Open on website',
                                                style: GoogleFonts.inter(
                                                  fontSize: 12,
                                                  color: DupePalette.teal,
                                                  fontWeight: FontWeight.w700,
                                                ),
                                              ),
                                              const SizedBox(width: 4),
                                              Icon(
                                                Icons.open_in_new_rounded,
                                                size: 16,
                                                color: DupePalette.teal,
                                              ),
                                            ],
                                          ),
                                        ],
                                      ),
                                    ),
                                    Icon(
                                      Icons.chevron_right_rounded,
                                      color: DupePalette.greySubtitle,
                                    ),
                                  ],
                                ),
                              ),
                            ),
                          );
                        },
                      ),
                    ),
    );
  }
}
