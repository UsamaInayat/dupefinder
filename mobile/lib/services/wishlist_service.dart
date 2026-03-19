import 'dart:convert';
import 'package:shared_preferences/shared_preferences.dart';
import 'api_service.dart';

/// Local wishlist: add/remove products, persist as JSON in SharedPreferences.
class WishlistService {
  static const _key = 'wishlist_products';
  static const _migratedKey = 'wishlist_migrated_to_backend';
  final _api = ApiService();

  Future<List<Map<String, dynamic>>> getSavedProducts() async {
    if (await _api.isLoggedIn()) {
      await _migrateLocalIfNeeded();
      final data = await _api.getUserData();
      final list = data['wishlist'] as List<dynamic>? ?? [];
      return list.map((e) => Map<String, dynamic>.from(e as Map)).toList();
    }
    return _getLocal();
  }

  Future<List<Map<String, dynamic>>> _getLocal() async {
    final prefs = await SharedPreferences.getInstance();
    final raw = prefs.getString(_key);
    if (raw == null || raw.isEmpty) return [];
    try {
      final list = jsonDecode(raw) as List<dynamic>?;
      return list?.map((e) => Map<String, dynamic>.from(e as Map)).toList() ?? [];
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
    } else {
      await _saveLocal(list);
    }
  }

  Future<void> removeProduct(String id) async {
    final list = await getSavedProducts();
    list.removeWhere((p) => productId(p) == id);
    if (await _api.isLoggedIn()) {
      await _api.putWishlist(list);
    } else {
      await _saveLocal(list);
    }
  }

  Future<void> toggleProduct(Map<String, dynamic> product) async {
    final id = productId(product);
    if (await isSaved(id)) {
      await removeProduct(id);
    } else {
      await addProduct(product);
    }
  }
}
