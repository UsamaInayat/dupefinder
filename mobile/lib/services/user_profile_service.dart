import 'dart:convert';
import 'package:shared_preferences/shared_preferences.dart';
import 'api_service.dart';

class UserProfileService {
  static const _usernameKey = 'user_name';
  static const _joinedAtKey = 'user_joined_at';
  static const _profileImageKey = 'user_profile_image';
  final _api = ApiService();

  Future<void> initializeAfterSignup({
    required String username,
    String? profileImage,
  }) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_usernameKey, username.trim());
    if (!prefs.containsKey(_joinedAtKey)) {
      await prefs.setString(_joinedAtKey, DateTime.now().toIso8601String());
    }
    if (profileImage != null && profileImage.trim().isNotEmpty) {
      await prefs.setString(_profileImageKey, profileImage.trim());
    }
  }

  Future<void> ensureDefaultsForLogin(String email) async {
    final prefs = await SharedPreferences.getInstance();
    if (!prefs.containsKey(_usernameKey) || (prefs.getString(_usernameKey) ?? '').isEmpty) {
      final fallback = email.split('@').first.trim();
      if (fallback.isNotEmpty) {
        await prefs.setString(_usernameKey, fallback);
      }
    }
    if (!prefs.containsKey(_joinedAtKey)) {
      await prefs.setString(_joinedAtKey, DateTime.now().toIso8601String());
    }
  }

  Future<Map<String, dynamic>> getProfile() async {
    await syncFromBackend();
    final prefs = await SharedPreferences.getInstance();
    final joined = prefs.getString(_joinedAtKey);
    return {
      'username': prefs.getString(_usernameKey) ?? '',
      'joinedAt': joined,
      'profileImage': prefs.getString(_profileImageKey),
    };
  }

  Future<void> setProfileImageFromBytes(List<int> bytes) async {
    final prefs = await SharedPreferences.getInstance();
    final base64 = base64Encode(bytes);
    await prefs.setString(_profileImageKey, base64);
    if (await _api.isLoggedIn()) {
      try {
        await _api.putUserProfileData(profileImageBase64: base64);
      } catch (_) {}
    }
  }

  Future<void> setDisplayName(String name) async {
    final trimmed = name.trim();
    if (trimmed.isEmpty) return;
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_usernameKey, trimmed);
    if (await _api.isLoggedIn()) {
      try {
        await _api.putUserProfileData(displayName: trimmed);
      } catch (_) {}
    }
  }

  Future<void> syncFromBackend() async {
    if (!await _api.isLoggedIn()) return;
    try {
      final me = await _api.getMe();
      final profile = await _api.getUserProfileData();
      final prefs = await SharedPreferences.getInstance();

      final meUser = Map<String, dynamic>.from((me['user'] as Map?) ?? {});
      final profileName = (profile['display_name'] ?? '').toString().trim();
      final meName = ((meUser['full_name'] ?? meUser['name'] ?? meUser['username'] ?? '')).toString().trim();
      final resolvedName = profileName.isNotEmpty ? profileName : meName;
      if (resolvedName.isNotEmpty) {
        await prefs.setString(_usernameKey, resolvedName);
      }

      final profileImage = (profile['profile_image'] ?? '').toString().trim();
      if (profileImage.isNotEmpty) {
        await prefs.setString(_profileImageKey, profileImage);
      }
    } catch (_) {
      // Best effort sync.
    }
  }
}
