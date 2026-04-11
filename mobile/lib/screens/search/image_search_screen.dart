import 'dart:typed_data';
import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:image_picker/image_picker.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:url_launcher/url_launcher.dart';
import 'package:cached_network_image/cached_network_image.dart';
import '../../services/api_service.dart';
import '../../services/wishlist_service.dart';
import '../../services/compare_service.dart';
import '../../services/dupe_history_service.dart';
import '../../theme/app_theme.dart';

/// FYP: User Experience + Image Matching — upload/capture image, get similar products.
class ImageSearchScreen extends StatefulWidget {
  final bool embedded;
  const ImageSearchScreen({super.key, this.embedded = false});

  @override
  State<ImageSearchScreen> createState() => _ImageSearchScreenState();
}

class _ImageSearchScreenState extends State<ImageSearchScreen> {
  final _apiService = ApiService();
  final _wishlistService = WishlistService();
  final _compareService = CompareService();
  final _historyService = DupeHistoryService();
  final _picker = ImagePicker();

  XFile? _pickedImage;
  bool _loading = false;
  String? _error;
  Map<String, dynamic>? _searchResult;
  String _selectedCategory = '';
  int _selectedPriceRangeIndex = 0; // 0 = Any
  Set<String> _savedIds = {};
  Map<String, int> _reviewStarsById = {};

  /// [minPrice, maxPrice] in PKR; null = no limit.
  static const List<(double?, double?)> _priceRanges = [
    (null, null), // Any
    (null, 2000), // Under 2,000
    (2000, 5000), // 2,000 – 5,000
    (5000, 10000), // 5,000 – 10,000
    (10000, 20000), // 10,000 – 20,000
    (20000, null), // 20,000+
  ];
  static const List<String> _priceRangeLabels = [
    'Any',
    'Under PKR 2,000',
    'PKR 2,000 – 5,000',
    'PKR 5,000 – 10,000',
    'PKR 10,000 – 20,000',
    'PKR 20,000+',
  ];

  static const _categories = [
    '',
    'Women Kurta',
    'Women Lawn',
    'Women Luxe',
    'Women Short Kurti',
    'Women Anarkali Frock',
    'Women Bottoms',
    'Women Bags',
    'Women Jewelry',
    'Women Tops',
    'Women Unstitched',
    'Women Western',
    'Women Winter Pants',
    'Women Accessories',
    'Men Standard Suit',
    'Men Traditional Suit',
    'Men Casual Wear',
    'Men Footwear',
    'Men Shoes',
    'Men Sweater',
    'Men Wrist Watches',
  ];

  Future<void> _pickImage(bool fromCamera) async {
    try {
      final source = fromCamera ? ImageSource.camera : ImageSource.gallery;
      final xFile = await _picker.pickImage(source: source, imageQuality: 85);
      if (xFile != null && mounted) {
        setState(() {
          _pickedImage = xFile;
          _error = null;
          _searchResult = null;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() => _error = 'Failed to pick image: $e');
      }
    }
  }

  Future<void> _findSimilar() async {
    if (_pickedImage == null) {
      setState(() => _error = 'Please pick an image first.');
      return;
    }
    setState(() {
      _loading = true;
      _error = null;
      _searchResult = null;
    });
    try {
      final range = _priceRanges[_selectedPriceRangeIndex];
      final result = await _apiService.searchSimilarImages(
        imageFile: _pickedImage!,
        topK: 10,
        category: _selectedCategory.isEmpty ? null : _selectedCategory,
        minPrice: range.$1,
        maxPrice: range.$2,
      );
      if (mounted) {
        final results = result['results'] as List<dynamic>? ?? [];
        final ids = <String>{};
        for (final r in results) {
          final map = Map<String, dynamic>.from(r as Map);
          if (await _wishlistService.isSaved(WishlistService.productId(map))) {
            ids.add(WishlistService.productId(map));
          }
        }
        final prefs = await SharedPreferences.getInstance();
        await prefs.setInt('insights_search_count',
            (prefs.getInt('insights_search_count') ?? 0) + 1);
        if (_selectedCategory.isNotEmpty) {
          final list = prefs.getStringList('insights_search_categories') ?? [];
          list.add(_selectedCategory);
          await prefs.setStringList('insights_search_categories', list);
        }
        setState(() {
          _loading = false;
          _searchResult = result;
          _savedIds = ids;
        });
        await _refreshReviewMap();
      }
    } catch (e) {
      if (mounted) {
        String msg = e.toString().replaceFirst('Exception: ', '');
        if (msg.contains('FashionCLIP indices not loaded') ||
            msg.contains('Run embedding generation')) {
          msg = 'Search is not ready yet. The server needs to run '
              'embedding generation once (see backend docs).';
        }
        setState(() {
          _loading = false;
          _error = msg;
        });
      }
    }
  }

  Future<void> _openProductUrl(String? url) async {
    if (url == null || url.isEmpty) return;
    final normalized = url.startsWith('http://') || url.startsWith('https://')
        ? url
        : 'https://$url';
    final uri = Uri.tryParse(normalized);
    if (uri != null && await canLaunchUrl(uri)) {
      await launchUrl(uri, mode: LaunchMode.platformDefault);
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

  Future<void> _openAndRecordProduct(Map<String, dynamic> product) async {
    await _historyService.recordClick(product);
    await _refreshReviewMap();
    await _openProductUrl(_resolveProductUrl(product));
  }

  Future<void> _refreshReviewMap() async {
    final history = await _historyService.getHistory();
    final map = <String, int>{};
    for (final e in history) {
      if (e.review != null) {
        map[e.id] = e.review!.stars;
      }
    }
    if (mounted) {
      setState(() => _reviewStarsById = map);
    }
  }

  void _clearImage() {
    setState(() {
      _pickedImage = null;
      _searchResult = null;
      _error = null;
    });
  }

  Widget _scrollBody() {
    return SingleChildScrollView(
      padding: const EdgeInsets.fromLTRB(16, 8, 16, 24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          if (widget.embedded) ...[
            Text(
              'Find Similar',
              style: GoogleFonts.playfairDisplay(
                fontSize: 26,
                fontWeight: FontWeight.bold,
                color: DupePalette.textPrimary,
              ),
            ),
            const SizedBox(height: 6),
            Text(
              'Upload or take a photo to discover dupes',
              style: GoogleFonts.inter(
                fontSize: 14,
                color: DupePalette.greySubtitle,
                height: 1.35,
              ),
            ),
            const SizedBox(height: 18),
          ],
          Container(
            padding: const EdgeInsets.all(20),
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(22),
              gradient: LinearGradient(
                colors: [
                  const Color(0xFF2D3A5A),
                  DupePalette.pinkDeep.withValues(alpha: 0.85),
                ],
                begin: Alignment.topLeft,
                end: Alignment.bottomRight,
              ),
            ),
            child: Column(
              children: [
                Icon(Icons.add_photo_alternate_outlined, color: Colors.white.withValues(alpha: 0.95), size: 36),
                const SizedBox(height: 10),
                Text(
                  'Upload your item',
                  style: GoogleFonts.inter(
                    color: Colors.white,
                    fontWeight: FontWeight.bold,
                    fontSize: 17,
                  ),
                ),
                const SizedBox(height: 6),
                Text(
                  'Take a photo or choose from gallery',
                  textAlign: TextAlign.center,
                  style: GoogleFonts.inter(
                    color: Colors.white.withValues(alpha: 0.85),
                    fontSize: 13,
                  ),
                ),
                const SizedBox(height: 16),
                Row(
                  children: [
                    Expanded(
                      child: OutlinedButton.icon(
                        onPressed: _loading ? null : () => _pickImage(true),
                        icon: const Icon(Icons.camera_alt, color: Colors.white, size: 20),
                        label: Text('Camera', style: GoogleFonts.inter(color: Colors.white, fontWeight: FontWeight.w600)),
                        style: OutlinedButton.styleFrom(
                          side: BorderSide(color: Colors.white.withValues(alpha: 0.85)),
                          padding: const EdgeInsets.symmetric(vertical: 12),
                        ),
                      ),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: OutlinedButton.icon(
                        onPressed: _loading ? null : () => _pickImage(false),
                        icon: const Icon(Icons.photo_library, color: Colors.white, size: 20),
                        label: Text('Gallery', style: GoogleFonts.inter(color: Colors.white, fontWeight: FontWeight.w600)),
                        style: OutlinedButton.styleFrom(
                          side: BorderSide(color: Colors.white.withValues(alpha: 0.85)),
                          padding: const EdgeInsets.symmetric(vertical: 12),
                        ),
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),
          const SizedBox(height: 16),

          // Preview
          if (_pickedImage != null) ...[
            FutureBuilder<Uint8List>(
              future: _pickedImage!.readAsBytes(),
              builder: (context, snap) {
                if (!snap.hasData) {
                  return const SizedBox(
                    height: 200,
                    child: Center(child: CircularProgressIndicator()),
                  );
                }
                return ClipRRect(
                  borderRadius: BorderRadius.circular(12),
                  child: Image.memory(
                    snap.data!,
                    width: double.infinity,
                    height: 200,
                    fit: BoxFit.cover,
                  ),
                );
              },
            ),
            const SizedBox(height: 12),
            // Category + Price range in one row
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(
                  'Filters',
                  style: GoogleFonts.inter(
                    fontWeight: FontWeight.w700,
                    fontSize: 15,
                    color: DupePalette.textPrimary,
                  ),
                ),
                Text(
                  'Advanced',
                  style: GoogleFonts.inter(
                    fontWeight: FontWeight.w600,
                    fontSize: 13,
                    color: DupePalette.blue,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 10),
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Expanded(
                  child: DropdownButtonFormField<String>(
                    key: ValueKey<String?>(
                        _selectedCategory.isEmpty ? null : _selectedCategory),
                    initialValue:
                        _selectedCategory.isEmpty ? null : _selectedCategory,
                    menuMaxHeight: 420,
                    decoration: InputDecoration(
                      labelText: 'Category',
                      filled: true,
                      fillColor: Colors.white,
                      border: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(16),
                        borderSide: BorderSide(color: DupePalette.pink.withValues(alpha: 0.25)),
                      ),
                      contentPadding:
                          const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                    ),
                    isExpanded: true,
                    items: _categories
                        .map((c) => DropdownMenuItem(
                              value: c.isEmpty ? null : c,
                              child: Text(c.isEmpty ? 'All' : c,
                                  overflow: TextOverflow.ellipsis),
                            ))
                        .toList(),
                    onChanged: (v) =>
                        setState(() => _selectedCategory = v ?? ''),
                  ),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: DropdownButtonFormField<int>(
                    key: ValueKey<int>(_selectedPriceRangeIndex),
                    initialValue: _selectedPriceRangeIndex,
                    menuMaxHeight: 320,
                    decoration: InputDecoration(
                      labelText: 'Price range',
                      filled: true,
                      fillColor: Colors.white,
                      border: OutlineInputBorder(
                        borderRadius: BorderRadius.circular(16),
                        borderSide: BorderSide(color: DupePalette.teal.withValues(alpha: 0.35)),
                      ),
                      contentPadding:
                          const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                    ),
                    isExpanded: true,
                    items: List.generate(
                        _priceRangeLabels.length,
                        (i) => DropdownMenuItem(
                            value: i,
                            child: Text(_priceRangeLabels[i],
                                overflow: TextOverflow.ellipsis))),
                    onChanged: (v) =>
                        setState(() => _selectedPriceRangeIndex = v ?? 0),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            DecoratedBox(
              decoration: BoxDecoration(
                borderRadius: BorderRadius.circular(28),
                gradient: DupePalette.ctaGradient,
              ),
              child: FilledButton.icon(
                onPressed: _loading ? null : _findSimilar,
                style: FilledButton.styleFrom(
                  backgroundColor: Colors.transparent,
                  shadowColor: Colors.transparent,
                  foregroundColor: Colors.white,
                  padding: const EdgeInsets.symmetric(vertical: 16),
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(28)),
                ),
                icon: _loading
                    ? const SizedBox(
                        width: 20,
                        height: 20,
                        child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white),
                      )
                    : const Icon(Icons.search, color: Colors.white),
                label: Text(
                  _loading ? 'Searching...' : 'Find Similar',
                  style: GoogleFonts.inter(fontWeight: FontWeight.bold),
                ),
              ),
            ),
            const SizedBox(height: 16),
          ],

          if (_error != null) ...[
            Card(
              color: Theme.of(context).colorScheme.errorContainer,
              child: Padding(
                padding: const EdgeInsets.all(12),
                child:
                    Text(_error!, style: const TextStyle(color: Colors.white)),
              ),
            ),
            const SizedBox(height: 16),
          ],

          if (_searchResult != null) _buildResults(),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    if (widget.embedded) {
      return Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          if (_pickedImage != null)
            Padding(
              padding: const EdgeInsets.fromLTRB(8, 0, 8, 0),
              child: Align(
                alignment: Alignment.centerRight,
                child: TextButton.icon(
                  onPressed: _clearImage,
                  icon: const Icon(Icons.clear_rounded, size: 20),
                  label: const Text('Clear image'),
                ),
              ),
            ),
          Expanded(child: _scrollBody()),
        ],
      );
    }
    return Scaffold(
      appBar: AppBar(
        title: const Text('Find Similar'),
        actions: [
          if (_pickedImage != null)
            IconButton(
              icon: const Icon(Icons.clear),
              onPressed: _clearImage,
              tooltip: 'Clear image',
            ),
        ],
      ),
      body: SafeArea(child: _scrollBody()),
    );
  }

  Widget _buildResults() {
    final results = _searchResult!['results'] as List<dynamic>? ?? [];
    final total = _searchResult!['total_results'] as int? ?? 0;
    final timeMs = _searchResult!['search_time_ms'] as num? ?? 0;
    final category = _searchResult!['category_searched'] as String? ?? '';

    if (results.isEmpty) {
      return Card(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            children: [
              Icon(Icons.search_off, size: 48, color: Colors.grey[600]),
              const SizedBox(height: 12),
              const Text(
                  'No similar products found. Try another image or category.'),
            ],
          ),
        ),
      );
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          '$total result${total == 1 ? '' : 's'}'
          '${category.isNotEmpty ? ' in $category' : ''}'
          ' (${timeMs.toStringAsFixed(0)} ms)',
          style: Theme.of(context).textTheme.titleSmall?.copyWith(
                color: Colors.grey[600],
              ),
        ),
        const SizedBox(height: 12),
        GridView.builder(
          shrinkWrap: true,
          physics: const NeverScrollableScrollPhysics(),
          gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
            crossAxisCount: 2,
            childAspectRatio: 0.72,
            crossAxisSpacing: 12,
            mainAxisSpacing: 12,
          ),
          itemCount: results.length,
          itemBuilder: (context, index) {
            final r = Map<String, dynamic>.from(results[index] as Map);
            final id = WishlistService.productId(r);
            return _ProductCard(
              name: r['name'] as String? ?? '',
              brand: r['brand'] as String? ?? '',
              price: r['price'] != null ? (r['price'] as num).toDouble() : null,
              imageUrl: _resolveImageUrl(r),
              productUrl: _resolveProductUrl(r),
              finalScore: (r['final_score'] as num?)?.toDouble() ?? 0,
              onTap: () => _openAndRecordProduct(r),
              isSaved: _savedIds.contains(id),
              reviewStars: _reviewStarsById[id] ?? 0,
              onSaveToggle: () async {
                await _wishlistService.toggleProduct(r);
                if (mounted) {
                  setState(() {
                    if (_savedIds.contains(id)) {
                      _savedIds.remove(id);
                    } else {
                      _savedIds.add(id);
                    }
                  });
                }
              },
              onAddToCompare: () async {
                final added = await _compareService.addProduct(r);
                if (mounted) {
                  ScaffoldMessenger.of(context).showSnackBar(
                    SnackBar(
                      content: Text(added
                          ? 'Added to Compare'
                          : 'Compare list full (max 4)'),
                      behavior: SnackBarBehavior.floating,
                    ),
                  );
                }
              },
            );
          },
        ),
      ],
    );
  }
}

class _ProductCard extends StatelessWidget {
  final String name;
  final String brand;
  final double? price;
  final String? imageUrl;
  final String? productUrl;
  final double finalScore;
  final VoidCallback onTap;
  final bool isSaved;
  final int reviewStars;
  final VoidCallback? onSaveToggle;
  final VoidCallback? onAddToCompare;

  const _ProductCard({
    required this.name,
    required this.brand,
    this.price,
    this.imageUrl,
    this.productUrl,
    required this.finalScore,
    required this.onTap,
    this.isSaved = false,
    this.reviewStars = 0,
    this.onSaveToggle,
    this.onAddToCompare,
  });

  @override
  Widget build(BuildContext context) {
    final matchPercent = (finalScore * 100).round();

    return Card(
      clipBehavior: Clip.antiAlias,
      child: InkWell(
        onTap: onTap,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            Expanded(
              flex: 3,
              child: Stack(
                alignment: Alignment.topRight,
                children: [
                  imageUrl != null && imageUrl!.isNotEmpty
                      ? CachedNetworkImage(
                          imageUrl: imageUrl!,
                          fit: BoxFit.cover,
                          width: double.infinity,
                          height: double.infinity,
                          placeholder: (_, __) =>
                              const Center(child: CircularProgressIndicator()),
                          errorWidget: (_, __, ___) =>
                              const Icon(Icons.image_not_supported, size: 48),
                        )
                      : const Center(
                          child: Icon(Icons.image_not_supported, size: 48),
                        ),
                  if (onSaveToggle != null || onAddToCompare != null)
                    Padding(
                      padding: const EdgeInsets.all(6),
                      child: Row(
                        mainAxisSize: MainAxisSize.min,
                        mainAxisAlignment: MainAxisAlignment.end,
                        children: [
                          if (onAddToCompare != null)
                            Material(
                              color: Colors.white.withValues(alpha: 0.9),
                              shape: const CircleBorder(),
                              child: IconButton(
                                icon: Icon(Icons.compare_arrows_rounded,
                                    color: Colors.grey[700], size: 20),
                                onPressed: onAddToCompare,
                                padding: const EdgeInsets.all(6),
                                constraints: const BoxConstraints(
                                    minWidth: 34, minHeight: 34),
                              ),
                            ),
                          if (onSaveToggle != null) ...[
                            const SizedBox(width: 4),
                            Material(
                              color: Colors.white.withValues(alpha: 0.9),
                              shape: const CircleBorder(),
                              child: IconButton(
                                icon: Icon(
                                  isSaved
                                      ? Icons.favorite_rounded
                                      : Icons.favorite_border_rounded,
                                  color:
                                      isSaved ? Colors.red : Colors.grey[700],
                                  size: 22,
                                ),
                                onPressed: onSaveToggle,
                                padding: const EdgeInsets.all(6),
                                constraints: const BoxConstraints(
                                    minWidth: 36, minHeight: 36),
                              ),
                            ),
                          ],
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
                      fontWeight: FontWeight.w600,
                      fontSize: 12,
                    ),
                  ),
                  if (brand.isNotEmpty)
                    Text(
                      brand,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: TextStyle(
                        fontSize: 11,
                        color: Colors.grey[600],
                      ),
                    ),
                  if (price != null)
                    Text(
                      'PKR ${price!.toStringAsFixed(0)}',
                      style: const TextStyle(
                        fontWeight: FontWeight.bold,
                        fontSize: 12,
                      ),
                    ),
                  const SizedBox(height: 4),
                  Container(
                    padding:
                        const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                    decoration: BoxDecoration(
                      gradient: DupePalette.ctaGradient,
                      borderRadius: BorderRadius.circular(10),
                    ),
                    child: Text(
                      '$matchPercent% match',
                      style: const TextStyle(
                        color: Colors.white,
                        fontSize: 11,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ),
                  if (reviewStars > 0) ...[
                    const SizedBox(height: 4),
                    Row(
                      children: [
                        ...List.generate(
                          5,
                          (i) => Icon(
                            i < reviewStars
                                ? Icons.star_rounded
                                : Icons.star_border_rounded,
                            size: 14,
                            color: i < reviewStars
                                ? Colors.amber[700]
                                : Colors.grey[500],
                          ),
                        ),
                        const SizedBox(width: 4),
                        Text(
                          '($reviewStars)',
                          style:
                              TextStyle(fontSize: 11, color: Colors.grey[600]),
                        ),
                      ],
                    ),
                  ],
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}
