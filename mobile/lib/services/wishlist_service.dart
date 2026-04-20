import 'dart:convert';
import 'package:shared_preferences/shared_preferences.dart';
import 'api_service.dart';

/// Local wishlist: add/remove products, persist as JSON in SharedPreferences.
class WishlistService {
  static const _key = 'wishlist_products';
  static const _migratedKey = 'wishlist_migrated_to_backend';
  static const Duration _cacheTtl = Duration(seconds: 60);
  final _api = ApiService();
  List<Map<String, dynamic>>? _memoryCache;
  DateTime? _cacheAt;

  /// Clears in-memory cache on **all** service instances.
  ///
  /// Multiple widgets each construct their own `WishlistService()`. Without this,
  /// one screen can persist to disk while another still serves a stale 60s TTL
  /// cache until app restart.
  static void invalidateAllMemoryCaches() {
    _globalWishlistCaches.removeWhere((ref) {
      final svc = ref.target;
      if (svc == null) return true;
      svc._memoryCache = null;
      svc._cacheAt = null;
      return false;
    });
  }

  static final List<WeakReference<WishlistService>> _globalWishlistCaches = [];

  WishlistService() {
    _globalWishlistCaches.add(WeakReference(this));
  }

  /// Fast path for UI: memory TTL hit, else local disk only (no network). Pair with [getSavedProducts] to sync server.
  Future<List<Map<String, dynamic>>> snapshotForUi() async {
    if (_memoryCache != null &&
        _cacheAt != null &&
        DateTime.now().difference(_cacheAt!) < _cacheTtl) {
      return _cloneList(_memoryCache!);
    }
    return _getLocal();
  }

  Future<List<Map<String, dynamic>>> getSavedProducts() async {
    if (_memoryCache != null &&
        _cacheAt != null &&
        DateTime.now().difference(_cacheAt!) < _cacheTtl) {
      return _cloneList(_memoryCache!);
    }
    if (await _api.isLoggedIn()) {
      final local = await _getLocal();
      try {
        await _migrateLocalIfNeeded();
        final data = await _api.getUserData();
        final list = data['wishlist'] as List<dynamic>? ?? [];
        final parsed =
            list.map((e) => Map<String, dynamic>.from(e as Map)).toList();
        final merged = _mergeById(local, parsed);
        if (merged.length != parsed.length) {
          try {
            await _api.putWishlist(merged);
          } catch (_) {}
        }
        await _saveLocal(merged);
        _setCache(merged);
        return _cloneList(merged);
      } catch (_) {
        _setCache(local);
        return _cloneList(local);
      }
    }
    final local = await _getLocal();
    _setCache(local);
    return _cloneList(local);
  }

  Future<List<Map<String, dynamic>>> _getLocal() async {
    final prefs = await SharedPreferences.getInstance();
    final raw = prefs.getString(_key);
    if (raw == null || raw.isEmpty) return [];
    try {
      final list = jsonDecode(raw) as List<dynamic>?;
      return list?.map((e) => Map<String, dynamic>.from(e as Map)).toList() ??
          [];
    } catch (_) {
      return [];
    }
  }

  Future<void> _saveLocal(List<Map<String, dynamic>> list) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_key, jsonEncode(list));
  }

  Future<void> _migrateLocalIfNeeded() async {
    final prefs = await SharedPreferences.getInstance();
    if (prefs.getBool(_migratedKey) == true) return;
    final local = await _getLocal();
    if (local.isNotEmpty) {
      await _api.putWishlist(local);
    }
    await prefs.setBool(_migratedKey, true);
  }

  /// Id is product_url; if missing, use name+image_url hash.
  static String productId(Map<String, dynamic> p) {
    final url = p['product_url'] as String?;
    if (url != null && url.isNotEmpty) return url;
    return '${p['name']}_${p['image_url']}';
  }

  Future<bool> isSaved(String id) async {
    final list = await getSavedProducts();
    return list.any((p) => productId(p) == id);
  }

  Future<void> addProduct(Map<String, dynamic> product) async {
    final list = await getSavedProducts();
    final id = productId(product);
    if (list.any((p) => productId(p) == id)) return;
    list.add(product);
    if (await _api.isLoggedIn()) {
      await _api.putWishlist(list);
    }
    await _saveLocal(list);
    invalidateAllMemoryCaches();
    _setCache(list);
  }

  Future<void> removeProduct(String id) async {
    final list = await getSavedProducts();
    list.removeWhere((p) => productId(p) == id);
    if (await _api.isLoggedIn()) {
      await _api.putWishlist(list);
    }
    await _saveLocal(list);
    invalidateAllMemoryCaches();
    _setCache(list);
  }

  Future<void> toggleProduct(Map<String, dynamic> product) async {
    final id = productId(product);
    if (await isSaved(id)) {
      await removeProduct(id);
    } else {
      await addProduct(product);
    }
  }

  void _setCache(List<Map<String, dynamic>> list) {
    _memoryCache = _cloneList(list);
    _cacheAt = DateTime.now();
  }

  List<Map<String, dynamic>> _cloneList(List<Map<String, dynamic>> list) {
    return list.map((e) => Map<String, dynamic>.from(e)).toList();
  }

  List<Map<String, dynamic>> _mergeById(
    List<Map<String, dynamic>> local,
    List<Map<String, dynamic>> remote,
  ) {
    final out = <Map<String, dynamic>>[];
    final seen = <String>{};
    for (final p in [...remote, ...local]) {
      final id = productId(p);
      if (seen.add(id)) out.add(Map<String, dynamic>.from(p));
    }
    return out;
  }
}
