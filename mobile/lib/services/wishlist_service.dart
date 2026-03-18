import 'dart:convert';
import 'package:shared_preferences/shared_preferences.dart';

/// Local wishlist: add/remove products, persist as JSON in SharedPreferences.
class WishlistService {
  static const _key = 'wishlist_products';

  Future<List<Map<String, dynamic>>> getSavedProducts() async {
    final prefs = await SharedPreferences.getInstance();
    final json = prefs.getString(_key);
    if (json == null || json.isEmpty) return [];
    try {
      final list = jsonDecode(json) as List<dynamic>?;
      return list?.map((e) => Map<String, dynamic>.from(e as Map)).toList() ?? [];
    } catch (_) {
      return [];
    }
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
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_key, jsonEncode(list));
  }

  Future<void> removeProduct(String id) async {
    final list = await getSavedProducts();
    list.removeWhere((p) => productId(p) == id);
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_key, jsonEncode(list));
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
