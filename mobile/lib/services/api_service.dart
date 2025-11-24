import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import 'package:flutter/foundation.dart' show kIsWeb;

class ApiService {
  // Platform-aware base URL
  // For web (Chrome): use localhost
  // For Android emulator: use 10.0.2.2
  // For iOS simulator: use localhost
  // For physical device: use your computer's IP (e.g., 192.168.1.100)
  
  static String get baseUrl {
    String url;
    if (kIsWeb) {
      // Web platform (Chrome) - use localhost
      url = 'http://localhost:8000/api';
    } else {
      // For mobile platforms, check if Android
      try {
        // Try to import Platform only when not on web
        // For now, default to Android emulator address for mobile
        // Change this to localhost if testing on iOS simulator
        url = 'http://10.0.2.2:8000/api'; // Android emulator
        // return 'http://localhost:8000/api'; // iOS simulator or physical device
      } catch (e) {
        // Fallback to localhost
        url = 'http://localhost:8000/api';
      }
    }
    // Debug: print the URL being used (remove in production)
    print('[ApiService] Using baseUrl: $url (kIsWeb: $kIsWeb)');
    return url;
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
  Future<Map<String, dynamic>> register(String email, String password) async {
    try {
      final response = await http.post(
        Uri.parse('$baseUrl/auth/signup'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'email': email,
          'password': password,
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
          if (data['refresh_token'] != null) {
            await prefs.setString('refresh_token', data['refresh_token']);
          }
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
}
