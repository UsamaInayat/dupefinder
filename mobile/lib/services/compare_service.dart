import 'dart:convert';
import 'package:shared_preferences/shared_preferences.dart';
import 'api_service.dart';

/// Local compare list: up to 4 products for side-by-side comparison.
class CompareService {
  static const _key = 'compare_products';
  static const _migratedKey = 'compare_migrated_to_backend';
  static const maxItems = 4;
  final _api = ApiService();

  Future<List<Map<String, dynamic>>> getList() async {
    if (await _api.isLoggedIn()) {
      await _migrateLocalIfNeeded();
      final data = await _api.getUserData();
      final list = data['compare'] as List<dynamic>? ?? [];
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

  Future<void> _save(List<Map<String, dynamic>> list) async {
    if (await _api.isLoggedIn()) {
      await _api.putCompare(list);
    } else {
      await _saveLocal(list);
    }
  }

  Future<void> _migrateLocalIfNeeded() async {
    final prefs = await SharedPreferences.getInstance();
    if (prefs.getBool(_migratedKey) == true) return;
    final local = await _getLocal();
    if (local.isNotEmpty) {
      await _api.putCompare(local);
    }
    await prefs.setBool(_migratedKey, true);
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
