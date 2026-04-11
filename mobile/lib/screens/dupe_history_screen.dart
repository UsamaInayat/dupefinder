import 'package:flutter/material.dart';
import 'package:cached_network_image/cached_network_image.dart';
import 'package:url_launcher/url_launcher.dart';
import '../services/dupe_history_service.dart';
import '../theme/app_theme.dart';

class DupeHistoryScreen extends StatefulWidget {
  const DupeHistoryScreen({super.key});

  @override
  State<DupeHistoryScreen> createState() => _DupeHistoryScreenState();
}

class _DupeHistoryScreenState extends State<DupeHistoryScreen> {
  final _service = DupeHistoryService();
  List<DupeHistoryEntry> _entries = [];
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    final list = await _service.getHistory();
    if (mounted) {
      setState(() {
        _entries = list;
        _loading = false;
      });
    }
  }

  Future<void> _openProduct(Map<String, dynamic> p) async {
    final url = p['product_url'] as String?;
    if (url == null || url.isEmpty) return;
    final uri = Uri.tryParse(url);
    if (uri != null && await canLaunchUrl(uri)) {
      await launchUrl(uri, mode: LaunchMode.externalApplication);
    }
  }

  Future<void> _rate(DupeHistoryEntry e, int stars) async {
    await _service.addReview(e.id, stars);
    await _load();
    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Saved $stars-star review'),
          behavior: SnackBarBehavior.floating,
        ),
      );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Dupe History')),
      body: _loading
          ? const Center(child: CircularProgressIndicator())
          : _entries.isEmpty
              ? const Center(
                  child: Text(
                    'No clicked dupes yet.',
                    style: TextStyle(color: AppColors.greySubtitle),
                  ),
                )
              : ListView.builder(
                  padding: const EdgeInsets.all(16),
                  itemCount: _entries.length,
                  itemBuilder: (_, i) {
                    final e = _entries[i];
                    final p = e.product;
                    final imageUrl = p['image_url'] as String?;
                    final name = p['name'] as String? ?? 'Unknown';
                    final brand = p['brand'] as String? ?? '';
                    final stars = e.review?.stars ?? 0;
                    return Card(
                      margin: const EdgeInsets.only(bottom: 12),
                      child: InkWell(
                        onTap: () => _openProduct(p),
                        child: Padding(
                          padding: const EdgeInsets.all(12),
                          child: Row(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              ClipRRect(
                                borderRadius: BorderRadius.circular(10),
                                child: SizedBox(
                                  width: 78,
                                  height: 78,
                                  child: imageUrl != null && imageUrl.isNotEmpty
                                      ? CachedNetworkImage(
                                          imageUrl: imageUrl,
                                          fit: BoxFit.cover,
                                          errorWidget: (_, __, ___) => const Icon(Icons.broken_image),
                                        )
                                      : const Icon(Icons.image_not_supported),
                                ),
                              ),
                              const SizedBox(width: 12),
                              Expanded(
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Text(
                                      name,
                                      style: const TextStyle(
                                        fontWeight: FontWeight.w600,
                                        color: AppColors.purpleDark,
                                      ),
                                      maxLines: 2,
                                      overflow: TextOverflow.ellipsis,
                                    ),
                                    if (brand.isNotEmpty)
                                      Text(
                                        brand,
                                        style: const TextStyle(color: AppColors.greySubtitle),
                                      ),
                                    const SizedBox(height: 4),
                                    Text(
                                      'Clicked: ${e.clickedAt.toLocal().toString().substring(0, 16)}',
                                      style: TextStyle(fontSize: 12, color: Colors.grey[600]),
                                    ),
                                    const SizedBox(height: 8),
                                    Wrap(
                                      spacing: 2,
                                      children: List.generate(5, (idx) {
                                        final s = idx + 1;
                                        final filled = s <= stars;
                                        return InkWell(
                                          onTap: () => _rate(e, s),
                                          child: Icon(
                                            filled ? Icons.star_rounded : Icons.star_border_rounded,
                                            color: filled ? Colors.amber[700] : Colors.grey[500],
                                            size: 22,
                                          ),
                                        );
                                      }),
                                    ),
                                    Text(
                                      stars > 0 ? '$stars star review saved' : 'Tap stars to review',
                                      style: TextStyle(
                                        fontSize: 12,
                                        color: stars > 0 ? AppColors.bluePrimary : AppColors.greySubtitle,
                                      ),
                                    ),
                                  ],
                                ),
                              ),
                            ],
                          ),
                        ),
                      ),
                    );
                  },
                ),
    );
  }
}
