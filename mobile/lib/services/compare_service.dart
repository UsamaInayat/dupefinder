import 'dart:convert';
import 'package:shared_preferences/shared_preferences.dart';
import 'api_service.dart';

/// Local compare list: up to 4 products for side-by-side comparison.
class CompareService {
  static const _key = 'compare_products';
  static const _migratedKey = 'compare_migrated_to_backend';
  static const maxItems = 4;
  static const Duration _cacheTtl = Duration(seconds: 60);
  final _api = ApiService();
  List<Map<String, dynamic>>? _memoryCache;
  DateTime? _cacheAt;

  /// Fast path for UI: memory TTL hit, else local disk only (no network). Pair with [getList] to sync server.
  Future<List<Map<String, dynamic>>> snapshotForUi() async {
    if (_memoryCache != null &&
        _cacheAt != null &&
        DateTime.now().difference(_cacheAt!) < _cacheTtl) {
      return _cloneList(_memoryCache!);
    }
    return _getLocal();
  }

  Future<List<Map<String, dynamic>>> getList() async {
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
        final list = data['compare'] as List<dynamic>? ?? [];
        final parsed =
            list.map((e) => Map<String, dynamic>.from(e as Map)).toList();
        final merged = _mergeById(local, parsed);
        if (merged.length != parsed.length) {
          try {
            await _api.putCompare(merged);
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

  Future<void> _save(List<Map<String, dynamic>> list) async {
    if (await _api.isLoggedIn()) {
      await _api.putCompare(list);
    }
    await _saveLocal(list);
    _setCache(list);
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
      final id = _id(p);
      if (seen.add(id)) out.add(Map<String, dynamic>.from(p));
    }
    return out;
  }
}
