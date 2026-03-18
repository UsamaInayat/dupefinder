import 'dart:convert';
import 'package:shared_preferences/shared_preferences.dart';

/// Local compare list: up to 4 products for side-by-side comparison.
class CompareService {
  static const _key = 'compare_products';
  static const maxItems = 4;

  Future<List<Map<String, dynamic>>> getList() async {
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

  Future<void> _save(List<Map<String, dynamic>> list) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_key, jsonEncode(list));
  }

  Future<bool> addProduct(Map<String, dynamic> product) async {
    final list = await getList();
    if (list.length >= maxItems) return false;
    final id = _id(product);
    if (list.any((p) => _id(p) == id)) return true;
    list.add(product);
    await _save(list);
    return true;
  }

  Future<void> removeAt(int index) async {
    final list = await getList();
    if (index >= 0 && index < list.length) {
      list.removeAt(index);
      await _save(list);
    }
  }

  Future<void> clear() async {
    await _save([]);
  }

  static String _id(Map<String, dynamic> p) {
    final url = p['product_url'] as String?;
    if (url != null && url.isNotEmpty) return url;
    return '${p['name']}_${p['image_url']}';
  }
}
