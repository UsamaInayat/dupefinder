import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import 'package:flutter/foundation.dart' show kIsWeb;
import 'package:image_picker/image_picker.dart';
import 'package:http_parser/http_parser.dart';

class ApiService {
  // Candidate IPs tried in order at startup — first reachable one wins.
  // 192.168.1.108  = same WiFi router as phone
  // 192.168.137.1  = PC mobile hotspot
  static const List<String> _candidateIPs = [
    '192.168.1.108',
    '192.168.137.1',
  ];

  // Cached after resolveBaseUrl() runs once at app startup.
  static String? _resolvedUrl;

  /// Call once in main() before runApp().
  /// Probes each candidate IP with a 3-second timeout and caches the first
  /// one that responds. Falls back to the first candidate if none respond.
  static Future<void> resolveBaseUrl() async {
    if (kIsWeb) {
      _resolvedUrl = 'http://localhost:8000/api';
      print('[ApiService] Web platform — using localhost');
      return;
    }
    for (final ip in _candidateIPs) {
      try {
        final uri = Uri.parse('http://$ip:8000/health');
        final resp = await http.get(uri).timeout(const Duration(seconds: 3));
        if (resp.statusCode < 500) {
          _resolvedUrl = 'http://$ip:8000/api';
          print('[ApiService] Resolved backend -> $_resolvedUrl');
          return;
        }
      } catch (_) {
        print('[ApiService] $ip unreachable, trying next...');
      }
    }
    // No candidate responded — fall back to first entry so the app still starts.
    _resolvedUrl = 'http://${_candidateIPs.first}:8000/api';
    print('[ApiService] No backend reachable — defaulting to $_resolvedUrl');
  }

  static String get baseUrl {
    if (_resolvedUrl != null) return _resolvedUrl!;
    // resolveBaseUrl() not yet called (e.g. unit tests) — use safe default.
    if (kIsWeb) return 'http://localhost:8000/api';
    return 'http://${_candidateIPs.first}:8000/api';
  }

  // Method to set custom backend IP (for switching between emulator and physical device)
  static Future<void> setBackendIP(String ip) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('backend_ip', ip);
  }

  // Get saved backend IP
  static Future<String?> getBackendIP() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString('backend_ip');
  }

  // Get stored access token
  Future<String?> getAccessToken() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString('access_token');
  }

  // Store access token
  Future<void> setAccessToken(String token) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('access_token', token);
  }

  // Remove access token (logout)
  Future<void> removeAccessToken() async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove('access_token');
    await prefs.remove('refresh_token');
    await prefs.remove('user_email');
  }

  // Get headers with auth token
  Future<Map<String, String>> getHeaders() async {
    final token = await getAccessToken();
    return {
      'Content-Type': 'application/json',
      if (token != null) 'Authorization': 'Bearer $token',
    };
  }

  // Register new user
  Future<Map<String, dynamic>> register(String email, String password, {String? fullName}) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/auth/signup'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'email': email,
          'password': password,
          if (fullName != null && fullName.trim().isNotEmpty) 'full_name': fullName.trim(),
        }),
      );

      if (response.statusCode == 201) {
        return jsonDecode(response.body);
      } else {
        final error = jsonDecode(response.body);
        throw Exception(error['detail'] ?? 'Registration failed');
      }
    } catch (e) {
      throw Exception('Registration failed: ${e.toString()}');
    }
  }

  // Verify OTP
  Future<Map<String, dynamic>> verifyOTP(String email, String otp) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/auth/verify-otp'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'email': email,
          'otp_code': otp,  // Backend expects 'otp_code' not 'otp'
        }),
      );

      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      } else {
        final error = jsonDecode(response.body);
        throw Exception(error['detail'] ?? 'OTP verification failed');
      }
    } catch (e) {
      throw Exception('OTP verification failed: ${e.toString()}');
    }
  }

  // Login
  Future<Map<String, dynamic>> login(String email, String password) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/auth/login'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'email': email,
          'password': password,
        }),
      );

      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        
        // Store tokens
        if (data['access_token'] != null) {
          await setAccessToken(data['access_token']);
          final prefs = await SharedPreferences.getInstance();
          await prefs.setString('user_email', email);
          final user = data['user'] as Map<String, dynamic>?;
          final fullName = _extractDisplayName(user);
          final userId = (user?['_id'] ?? user?['id'] ?? '').toString().trim();
          if (fullName.isNotEmpty) {
            await prefs.setString('user_name', fullName);
          }
          if (userId.isNotEmpty) {
            await prefs.setString('user_id', userId);
          }
          if (data['refresh_token'] != null) {
            await prefs.setString('refresh_token', data['refresh_token']);
          }

          // Strong sync for older accounts so existing users also get their real backend name.
          await syncUserProfileFromBackend();
        }
        
        return data;
      } else {
        final error = jsonDecode(response.body);
        throw Exception(error['detail'] ?? 'Login failed');
      }
    } catch (e) {
      throw Exception('Login failed: ${e.toString()}');
    }
  }

  // Logout
  Future<void> logout() async {
    await removeAccessToken();
  }

  // Check if user is logged in
  Future<bool> isLoggedIn() async {
    final token = await getAccessToken();
    return token != null && token.isNotEmpty;
  }

  String _extractDisplayName(Map<String, dynamic>? user) {
    if (user == null) return '';
    final candidates = [
      user['full_name'],
      user['name'],
      user['username'],
    ];
    for (final c in candidates) {
      final v = (c ?? '').toString().trim();
      if (v.isNotEmpty) return v;
    }
    return '';
  }

  Future<void> syncUserProfileFromBackend() async {
    final token = await getAccessToken();
    if (token == null || token.isEmpty) return;
    try {
      final body = await getMe();
      final user = Map<String, dynamic>.from((body['user'] as Map?) ?? {});
      Map<String, dynamic> profile = {};
      try {
        profile = await getUserProfileData();
      } catch (_) {}
      final name = _extractDisplayName(user);
      final profileName = (profile['display_name'] ?? '').toString().trim();
      final resolvedName = profileName.isNotEmpty ? profileName : name;
      final email = (user['email'] ?? '').toString().trim();
      final userId = (user['_id'] ?? user['id'] ?? '').toString().trim();
      final profileImage = (profile['profile_image'] ?? '').toString().trim();
      final prefs = await SharedPreferences.getInstance();
      if (resolvedName.isNotEmpty) {
        await prefs.setString('user_name', resolvedName);
      } else if (email.isNotEmpty) {
        await prefs.setString('user_name', email.split('@').first);
      }
      if (email.isNotEmpty) {
        await prefs.setString('user_email', email);
      }
      if (userId.isNotEmpty) {
        await prefs.setString('user_id', userId);
      }
      if (profileImage.isNotEmpty) {
        await prefs.setString('user_profile_image', profileImage);
      }
    } catch (_) {
      // best effort sync only
    }
  }

  Future<Map<String, dynamic>> getMe() async {
    final response = await http.get(
      Uri.parse('$baseUrl/auth/me'),
      headers: await getHeaders(),
    );
    if (response.statusCode != 200) {
      throw Exception('Failed to load current user');
    }
    return Map<String, dynamic>.from(jsonDecode(response.body) as Map);
  }

  /// Image-based similarity search (FYP: Image Matching & Recommendation).
  /// Sends image to POST /api/search/similar and returns results with match %, price, link.
  Future<Map<String, dynamic>> searchSimilarImages({
    required XFile imageFile,
    int topK = 10,
    String? category,
    double? minPrice,
    double? maxPrice,
    double wSim = 0.7,
    double wPrice = 0.2,
    double wAttr = 0.1,
  }) async {
    final uri = Uri.parse('$baseUrl/search/similar').replace(
      queryParameters: <String, String>{
        'top_k': topK.toString(),
        if (category != null && category.isNotEmpty) 'category': category,
        if (minPrice != null) 'min_price': minPrice.toString(),
        if (maxPrice != null) 'max_price': maxPrice.toString(),
        'w_sim': wSim.toString(),
        'w_price': wPrice.toString(),
        'w_attr': wAttr.toString(),
      },
    );

    final bytes = await imageFile.readAsBytes();
    final name = imageFile.name;
    final mime = name.toLowerCase().endsWith('.png')
        ? 'image/png'
        : (name.toLowerCase().endsWith('.webp')
            ? 'image/webp'
            : 'image/jpeg');

    final request = http.MultipartRequest('POST', uri);
    request.files.add(http.MultipartFile.fromBytes(
      'file',
      bytes,
      filename: name.isNotEmpty ? name : 'image.jpg',
      contentType: MediaType.parse(mime),
    ));
    final token = await getAccessToken();
    if (token != null && token.isNotEmpty) {
      request.headers['Authorization'] = 'Bearer $token';
    }

    final streamed = await request.send();
    final response = await http.Response.fromStream(streamed);

    if (response.statusCode != 200) {
      final body = response.body;
      String msg = 'Search failed';
      try {
        final decoded = jsonDecode(body);
        if (decoded is Map && decoded['detail'] != null) {
          msg = decoded['detail'].toString();
        }
      } catch (_) {}
      throw Exception(msg);
    }

    return jsonDecode(response.body) as Map<String, dynamic>;
  }

  Future<List<Map<String, dynamic>>> getCommunityPosts() async {
    final response = await http.get(
      Uri.parse('$baseUrl/community/posts'),
      headers: await getHeaders(),
    );
    if (response.statusCode != 200) {
      throw Exception('Failed to load community posts');
    }
    final body = jsonDecode(response.body) as Map<String, dynamic>;
    final posts = (body['posts'] as List<dynamic>? ?? [])
        .map((e) => Map<String, dynamic>.from(e as Map))
        .toList();
    return posts;
  }

  Future<Map<String, dynamic>> addCommunityPost({
    required String description,
    required String author,
    String? authorPfp,
    String? imageBase64,
  }) async {
    final response = await http.post(
      Uri.parse('$baseUrl/community/posts'),
      headers: await getHeaders(),
      body: jsonEncode({
        'description': description,
        'author': author,
        'author_pfp': authorPfp,
        'image_base64': imageBase64,
      }),
    );
    if (response.statusCode != 200) {
      throw Exception('Failed to add post');
    }
    return Map<String, dynamic>.from(
      (jsonDecode(response.body) as Map<String, dynamic>)['post'] as Map,
    );
  }

  Future<Map<String, dynamic>> addCommunityReply({
    required String postId,
    required String body,
    required String author,
    String? authorPfp,
  }) async {
    final response = await http.post(
      Uri.parse('$baseUrl/community/posts/$postId/replies'),
      headers: await getHeaders(),
      body: jsonEncode({
        'body': body,
        'author': author,
        'author_pfp': authorPfp,
      }),
    );
    if (response.statusCode != 200) {
      throw Exception('Failed to add reply');
    }
    return Map<String, dynamic>.from(
      (jsonDecode(response.body) as Map<String, dynamic>)['post'] as Map,
    );
  }

  Future<void> deleteCommunityReply({
    required String postId,
    required String replyId,
  }) async {
    final response = await http.delete(
      Uri.parse('$baseUrl/community/posts/$postId/replies/$replyId'),
      headers: await getHeaders(),
    );
    if (response.statusCode != 200) {
      throw Exception('Failed to delete reply');
    }
  }

  Future<void> deleteCommunityPost(String postId) async {
    final response = await http.delete(
      Uri.parse('$baseUrl/community/posts/$postId'),
      headers: await getHeaders(),
    );
    if (response.statusCode != 200) {
      throw Exception('Failed to delete post');
    }
  }

  Future<void> reportCommunityPost({
    required String postId,
    required String reason,
  }) async {
    final response = await http.post(
      Uri.parse('$baseUrl/community/posts/$postId/report'),
      headers: await getHeaders(),
      body: jsonEncode({'reason': reason}),
    );
    if (response.statusCode != 200) {
      throw Exception('Failed to report post');
    }
  }

  Future<void> editCommunityPost({
    required String postId,
    required String description,
  }) async {
    final response = await http.put(
      Uri.parse('$baseUrl/community/posts/$postId'),
      headers: await getHeaders(),
      body: jsonEncode({'description': description}),
    );
    if (response.statusCode != 200) {
      throw Exception('Failed to edit post');
    }
  }

  Future<Map<String, dynamic>> getUserData() async {
    final response = await http.get(
      Uri.parse('$baseUrl/user-data'),
      headers: await getHeaders(),
    );
    if (response.statusCode != 200) {
      throw Exception('Failed to load user data');
    }
    return Map<String, dynamic>.from(jsonDecode(response.body) as Map);
  }

  Future<void> putWishlist(List<Map<String, dynamic>> items) async {
    final response = await http.put(
      Uri.parse('$baseUrl/user-data/wishlist'),
      headers: await getHeaders(),
      body: jsonEncode({'items': items}),
    );
    if (response.statusCode != 200) {
      throw Exception('Failed to save wishlist');
    }
  }

  Future<void> putCompare(List<Map<String, dynamic>> items) async {
    final response = await http.put(
      Uri.parse('$baseUrl/user-data/compare'),
      headers: await getHeaders(),
      body: jsonEncode({'items': items}),
    );
    if (response.statusCode != 200) {
      throw Exception('Failed to save compare list');
    }
  }

  Future<void> putDupeHistory(List<Map<String, dynamic>> items) async {
    final response = await http.put(
      Uri.parse('$baseUrl/user-data/dupe-history'),
      headers: await getHeaders(),
      body: jsonEncode({'items': items}),
    );
    if (response.statusCode != 200) {
      throw Exception('Failed to save dupe history');
    }
  }

  Future<Map<String, dynamic>> getUserProfileData() async {
    final response = await http.get(
      Uri.parse('$baseUrl/user-data/profile'),
      headers: await getHeaders(),
    );
    if (response.statusCode != 200) {
      throw Exception('Failed to load profile');
    }
    return Map<String, dynamic>.from(jsonDecode(response.body) as Map);
  }

  Future<void> putUserProfileData({
    String? displayName,
    String? profileImageBase64,
  }) async {
    final response = await http.put(
      Uri.parse('$baseUrl/user-data/profile'),
      headers: await getHeaders(),
      body: jsonEncode({
        if (displayName != null) 'display_name': displayName,
        if (profileImageBase64 != null) 'profile_image': profileImageBase64,
      }),
    );
    if (response.statusCode != 200) {
      throw Exception('Failed to save profile');
    }
  }
}
