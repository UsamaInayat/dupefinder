import 'package:flutter/material.dart';
import 'package:cached_network_image/cached_network_image.dart';
import 'package:google_fonts/google_fonts.dart';
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
    _bootstrap();
  }

  /// Stale-while-revalidate: show local list immediately, then refresh from server when logged in.
  Future<void> _bootstrap() async {
    final snap = await _compareService.snapshotForUi();
    if (mounted) {
      setState(() {
        _items = snap;
        _loading = false;
      });
    }
    await _load(silent: true);
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
    final topInset = MediaQuery.paddingOf(context).top;
    final title = Padding(
      padding: EdgeInsets.fromLTRB(20, topInset + 10, 20, 8),
      child: Text(
        'Compare',
        style: GoogleFonts.playfairDisplay(
          fontSize: 26,
          fontWeight: FontWeight.w700,
          color: DupePalette.textPrimary,
        ),
      ),
    );

    Widget content;
    if (_loading) {
      content = const Center(
        child: CircularProgressIndicator(color: DupePalette.pink),
      );
    } else if (_items.isEmpty) {
      content = Container(
        decoration: BoxDecoration(
          gradient: LinearGradient(
            colors: [
              DupePalette.teal.withValues(alpha: 0.12),
              DupePalette.pink.withValues(alpha: 0.1),
            ],
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
          ),
        ),
        child: Center(
          child: Padding(
            padding: const EdgeInsets.all(32),
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Icon(Icons.compare_arrows_rounded,
                    size: 72, color: DupePalette.pink.withValues(alpha: 0.65)),
                const SizedBox(height: 12),
                Text(
                  'Side-by-side luxury analysis — tap the compare icon on any search result. Add 2–4 items to compare price, brand, and match score.',
                  textAlign: TextAlign.center,
                  style: GoogleFonts.inter(
                      color: DupePalette.greySubtitle, height: 1.45),
                ),
              ],
            ),
          ),
        ),
      );
    } else {
      content = RefreshIndicator(
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
                  final productUrl = _resolveProductUrl(p);
                  final score = (p['final_score'] as num?)?.toDouble() ?? 0;
                  final matchPercent = (score * 100).round();
                  return Card(
                    clipBehavior: Clip.antiAlias,
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(16),
                      side: (index == 1 && _items.length >= 2)
                          ? BorderSide(color: DupePalette.teal.withValues(alpha: 0.65), width: 1.5)
                          : BorderSide.none,
                    ),
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
                                        memCacheWidth: 400,
                                        placeholder: (_, __) => const Center(
                                            child: CircularProgressIndicator(
                                          strokeWidth: 2,
                                          color: DupePalette.pink,
                                        )),
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
                                      horizontal: 8, vertical: 3),
                                  decoration: BoxDecoration(
                                    gradient: DupePalette.ctaGradient,
                                    borderRadius: BorderRadius.circular(8),
                                  ),
                                  child: Text('$matchPercent% match',
                                      style: const TextStyle(
                                          color: Colors.white,
                                          fontSize: 11,
                                          fontWeight: FontWeight.w600)),
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

    return Container(
      color: DupePalette.scaffoldLight,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          title,
          Expanded(child: content),
        ],
      ),
    );
  }

  Widget _buildComparisonSummary() {
    final prices = <double>[];
    final matches = <int>[];
    final brands = <String>{};
    final showFeatureSummary = _items.any(_hasBackendFeatureData);
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
    final savePct = (priceMin != null &&
            priceMax != null &&
            priceMax > priceMin &&
            priceMax > 0)
        ? (((priceMax - priceMin) / priceMax) * 100).round()
        : null;

    return Container(
      margin: const EdgeInsets.only(top: 20),
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        gradient: DupePalette.ctaGradientWide,
        borderRadius: BorderRadius.circular(20),
        boxShadow: [
          BoxShadow(
            color: DupePalette.pink.withValues(alpha: 0.25),
            blurRadius: 16,
            offset: const Offset(0, 8),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          if (savePct != null && savePct > 0) ...[
            Text(
              'You save',
              textAlign: TextAlign.center,
              style: GoogleFonts.inter(
                color: Colors.white.withValues(alpha: 0.9),
                fontSize: 13,
                fontWeight: FontWeight.w500,
              ),
            ),
            const SizedBox(height: 6),
            Text(
              '$savePct%',
              textAlign: TextAlign.center,
              style: GoogleFonts.inter(
                fontSize: 34,
                fontWeight: FontWeight.w800,
                color: Colors.white,
                height: 1.0,
                letterSpacing: -0.5,
              ),
            ),
            if (priceDiff != null) ...[
              const SizedBox(height: 12),
              Padding(
                padding: const EdgeInsets.symmetric(horizontal: 8),
                child: Text(
                  'That’s about PKR ${priceDiff.toString()} less vs. the highest price.',
                  textAlign: TextAlign.center,
                  style: GoogleFonts.inter(
                    color: Colors.white.withValues(alpha: 0.92),
                    fontSize: 13,
                    height: 1.4,
                    fontWeight: FontWeight.w500,
                  ),
                ),
              ),
            ],
            const SizedBox(height: 18),
          ],
          Text(
            'Comparison summary',
            style: GoogleFonts.inter(
              fontSize: 15,
              fontWeight: FontWeight.bold,
              color: Colors.white,
            ),
          ),
          const SizedBox(height: 10),
          if (priceMin != null && priceMax != null) ...[
            _summaryRowLight('Price range',
                'PKR ${priceMin.toStringAsFixed(0)} – PKR ${priceMax.toStringAsFixed(0)}'),
            if (priceDiff != null && priceDiff > 0)
              _summaryRowLight(
                  'Price spread', 'PKR ${priceDiff.toString()} between lowest and highest'),
            const SizedBox(height: 6),
          ],
          if (matchMin != null && matchMax != null) ...[
            _summaryRowLight(
                'Match score',
                matchMin == matchMax
                    ? '$matchMin% (same)'
                    : '$matchMin% – $matchMax%'),
            const SizedBox(height: 6),
          ],
          _summaryRowLight(
              'Brands',
              brands.isEmpty
                  ? '—'
                  : brands.length == 1
                      ? 'Same: ${brands.first}'
                      : '${brands.length} different: ${brands.take(3).join(', ')}${brands.length > 3 ? '...' : ''}'),
          if (showFeatureSummary) ...[
            const SizedBox(height: 6),
            _summaryFeaturesBulleted(_items),
          ],
        ],
      ),
    );
  }

  /// Feature text from enrichment only (not category fallbacks).
  String _featureLabelFromBackend(Map<String, dynamic> product) {
    final keywords = product['feature_keywords'];
    if (keywords is List && keywords.isNotEmpty) {
      final tokens = keywords
          .whereType<String>()
          .map((e) => e.trim())
          .where((e) => e.isNotEmpty)
          .take(3)
          .toList();
      if (tokens.isNotEmpty) return tokens.join(', ');
    }
    final direct = [
      product['fabric'],
      product['material'],
      product['features'],
    ];
    for (final value in direct) {
      if (value is String && value.trim().isNotEmpty) {
        return value.trim();
      }
    }
    return '';
  }

  bool _hasBackendFeatureData(Map<String, dynamic> product) {
    return _featureLabelFromBackend(product).isNotEmpty;
  }

  /// Tokens for summary bullets: prefer `feature_keywords`, else comma-split label.
  Iterable<String> _featureTokensForProduct(Map<String, dynamic> product) sync* {
    final keywords = product['feature_keywords'];
    if (keywords is List && keywords.isNotEmpty) {
      var yielded = false;
      for (final x in keywords) {
        if (x is String) {
          final s = x.trim();
          if (s.isNotEmpty) {
            yielded = true;
            yield s;
          }
        }
      }
      if (yielded) return;
    }
    final label = _featureLabelFromBackend(product);
    if (label.isEmpty) return;
    for (final part in label.split(',')) {
      final s = part.trim();
      if (s.isNotEmpty) yield s;
    }
  }

  /// Dedupe tokens only within one product (same keyword twice, etc.).
  List<String> _featureTokensForProductUnique(Map<String, dynamic> product) {
    final seen = <String>{};
    final out = <String>[];
    for (final t in _featureTokensForProduct(product)) {
      if (seen.add(t.toLowerCase())) out.add(t);
    }
    return out;
  }

  String _compareItemFeatureHeading(Map<String, dynamic> p) {
    final brand = (p['brand'] as String?)?.trim() ?? '';
    final name = (p['name'] as String?)?.trim() ?? 'Product';
    const maxName = 40;
    final short = name.length <= maxName
        ? name
        : '${name.substring(0, maxName - 1)}…';
    if (brand.isNotEmpty) return '$brand — $short';
    return short;
  }

  /// One block per compared item so users can tell which product has which features.
  Widget _summaryFeaturesBulleted(List<Map<String, dynamic>> items) {
    final labelStyle = GoogleFonts.inter(
      fontSize: 12,
      color: Colors.white.withValues(alpha: 0.85),
      fontWeight: FontWeight.w500,
    );
    final bulletStyle = GoogleFonts.inter(
      fontSize: 12,
      color: Colors.white,
      fontWeight: FontWeight.w600,
      height: 1.25,
    );
    final headingStyle = GoogleFonts.inter(
      fontSize: 12,
      color: Colors.white.withValues(alpha: 0.95),
      fontWeight: FontWeight.w700,
      height: 1.2,
    );

    final sections = <Widget>[];
    for (final p in items) {
      if (!_hasBackendFeatureData(p)) continue;
      final tokens = _featureTokensForProductUnique(p);
      if (tokens.isEmpty) continue;
      sections.add(
        Padding(
          padding: const EdgeInsets.only(bottom: 10),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                _compareItemFeatureHeading(p),
                style: headingStyle,
                maxLines: 2,
                overflow: TextOverflow.ellipsis,
              ),
              const SizedBox(height: 4),
              ...tokens.map(
                (t) => Padding(
                  padding: const EdgeInsets.only(bottom: 2),
                  child: Text('• $t', style: bulletStyle),
                ),
              ),
            ],
          ),
        ),
      );
    }

    return Padding(
      padding: const EdgeInsets.only(bottom: 4),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 110,
            child: Text('Features', style: labelStyle),
          ),
          Expanded(
            child: sections.isEmpty
                ? Text('—', style: bulletStyle)
                : Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: sections,
                  ),
          ),
        ],
      ),
    );
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

  Widget _summaryRowLight(String label, String value) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 4),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 110,
            child: Text(
              label,
              style: GoogleFonts.inter(
                fontSize: 12,
                color: Colors.white.withValues(alpha: 0.85),
                fontWeight: FontWeight.w500,
              ),
            ),
          ),
          Expanded(
            child: Text(
              value,
              style: GoogleFonts.inter(
                fontSize: 12,
                color: Colors.white,
                fontWeight: FontWeight.w600,
              ),
            ),
          ),
        ],
      ),
    );
  }
}
