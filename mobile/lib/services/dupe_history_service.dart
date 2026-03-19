import 'dart:convert';
import 'package:shared_preferences/shared_preferences.dart';
import 'api_service.dart';

class DupeReview {
  final int stars;
  final DateTime reviewedAt;

  DupeReview({required this.stars, required this.reviewedAt});

  Map<String, dynamic> toJson() => {
        'stars': stars,
        'reviewedAt': reviewedAt.toIso8601String(),
      };

  static DupeReview fromJson(Map<String, dynamic> json) => DupeReview(
        stars: (json['stars'] as num?)?.toInt() ?? 0,
        reviewedAt:
            DateTime.tryParse(json['reviewedAt'] as String? ?? '') ?? DateTime.now(),
      );
}

class DupeHistoryEntry {
  final String id;
  final Map<String, dynamic> product;
  final DateTime clickedAt;
  final DupeReview? review;
  final bool promptShown;

  DupeHistoryEntry({
    required this.id,
    required this.product,
    required this.clickedAt,
    this.review,
    this.promptShown = false,
  });

  Map<String, dynamic> toJson() => {
        'id': id,
        'product': product,
        'clickedAt': clickedAt.toIso8601String(),
        'promptShown': promptShown,
        if (review != null) 'review': review!.toJson(),
      };

  static DupeHistoryEntry fromJson(Map<String, dynamic> json) => DupeHistoryEntry(
        id: json['id'] as String? ?? '',
        product: Map<String, dynamic>.from((json['product'] as Map?) ?? {}),
        clickedAt:
            DateTime.tryParse(json['clickedAt'] as String? ?? '') ?? DateTime.now(),
        review: json['review'] is Map<String, dynamic>
            ? DupeReview.fromJson(json['review'] as Map<String, dynamic>)
            : (json['review'] is Map
                ? DupeReview.fromJson(
                    Map<String, dynamic>.from(json['review'] as Map))
                : null),
        promptShown: json['promptShown'] == true,
      );
}

class DupeHistoryService {
  static const _historyKey = 'dupe_history_entries';
  static const _historyCacheKey = 'dupe_history_backend_cache';
  static const _reviewDbKey = 'review_category_db';
  static const _migratedKey = 'dupe_history_migrated_to_backend';
  final _api = ApiService();

  String entryIdForProduct(Map<String, dynamic> p) {
    final url = (p['product_url'] as String?)?.trim();
    if (url != null && url.isNotEmpty) return url;
    return '${p['name']}_${p['image_url']}';
  }

  Future<List<DupeHistoryEntry>> getHistory() async {
    if (await _api.isLoggedIn()) {
      try {
        await _migrateLocalIfNeeded();
        final data = await _api.getUserData();
        final list = data['dupe_history'] as List<dynamic>? ?? [];
        final parsed = list
            .map((e) => DupeHistoryEntry.fromJson(Map<String, dynamic>.from(e as Map)))
            .toList();
        await _saveBackendCache(parsed);
        return parsed;
      } catch (_) {
        return _getBackendCache();
      }
    }
    return _getLocal();
  }

  Future<List<DupeHistoryEntry>> _getLocal() async {
    final prefs = await SharedPreferences.getInstance();
    final raw = prefs.getString(_historyKey);
    if (raw == null || raw.isEmpty) return [];
    try {
      final list = jsonDecode(raw) as List<dynamic>;
      return list
          .map((e) => DupeHistoryEntry.fromJson(Map<String, dynamic>.from(e as Map)))
          .toList();
    } catch (_) {
      return [];
    }
  }

  Future<void> _saveHistoryLocal(List<DupeHistoryEntry> list) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_historyKey, jsonEncode(list.map((e) => e.toJson()).toList()));
  }

  Future<void> _saveHistory(List<DupeHistoryEntry> list) async {
    if (await _api.isLoggedIn()) {
      await _api.putDupeHistory(list.map((e) => e.toJson()).toList());
      await _saveBackendCache(list);
    } else {
      await _saveHistoryLocal(list);
    }
  }

  Future<void> _migrateLocalIfNeeded() async {
    final prefs = await SharedPreferences.getInstance();
    if (prefs.getBool(_migratedKey) == true) return;
    final local = await _getLocal();
    if (local.isNotEmpty) {
      await _api.putDupeHistory(local.map((e) => e.toJson()).toList());
    }
    await prefs.setBool(_migratedKey, true);
  }

  Future<void> _saveBackendCache(List<DupeHistoryEntry> list) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(
      _historyCacheKey,
      jsonEncode(list.map((e) => e.toJson()).toList()),
    );
  }

  Future<List<DupeHistoryEntry>> _getBackendCache() async {
    final prefs = await SharedPreferences.getInstance();
    final raw = prefs.getString(_historyCacheKey);
    if (raw == null || raw.isEmpty) return [];
    try {
      final list = jsonDecode(raw) as List<dynamic>;
      return list
          .map((e) => DupeHistoryEntry.fromJson(Map<String, dynamic>.from(e as Map)))
          .toList();
    } catch (_) {
      return [];
    }
  }

  Future<void> recordClick(Map<String, dynamic> product) async {
    final list = await getHistory();
    final id = entryIdForProduct(product);
    final idx = list.indexWhere((e) => e.id == id);
    final now = DateTime.now();
    final next = DupeHistoryEntry(
      id: id,
      product: product,
      clickedAt: now,
      review: idx >= 0 ? list[idx].review : null,
      promptShown: false,
    );
    if (idx >= 0) {
      list[idx] = next;
    } else {
      list.insert(0, next);
    }
    await _saveHistory(list);
  }

  Future<void> addReview(String entryId, int stars) async {
    final list = await getHistory();
    final idx = list.indexWhere((e) => e.id == entryId);
    if (idx < 0) return;
    final updated = DupeHistoryEntry(
      id: list[idx].id,
      product: list[idx].product,
      clickedAt: list[idx].clickedAt,
      review: DupeReview(stars: stars, reviewedAt: DateTime.now()),
      promptShown: true,
    );
    list[idx] = updated;
    await _saveHistory(list);
    await _saveReviewDb(list);
  }

  Future<void> _saveReviewDb(List<DupeHistoryEntry> list) async {
    final prefs = await SharedPreferences.getInstance();
    final reviewDocs = list
        .where((e) => e.review != null)
        .map((e) => {
              'entry_id': e.id,
              'product': e.product,
              'stars': e.review!.stars,
              'reviewed_at': e.review!.reviewedAt.toIso8601String(),
              'category': 'review',
            })
        .toList();
    await prefs.setString(_reviewDbKey, jsonEncode(reviewDocs));
  }

  Future<DupeHistoryEntry?> nextPendingPrompt() async {
    final list = await getHistory();
    for (final e in list) {
      if (e.review == null && !e.promptShown) return e;
    }
    return null;
  }

  Future<void> markPromptShown(String entryId) async {
    final list = await getHistory();
    final idx = list.indexWhere((e) => e.id == entryId);
    if (idx < 0) return;
    final curr = list[idx];
    list[idx] = DupeHistoryEntry(
      id: curr.id,
      product: curr.product,
      clickedAt: curr.clickedAt,
      review: curr.review,
      promptShown: true,
    );
    await _saveHistory(list);
  }
}
