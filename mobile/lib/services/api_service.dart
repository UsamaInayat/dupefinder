import 'dart:async';
import 'dart:convert';
import 'dart:io';
import 'dart:math';

import 'package:device_info_plus/device_info_plus.dart';
import 'package:http/http.dart' as http;
import 'package:network_info_plus/network_info_plus.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:flutter/foundation.dart'
    show kIsWeb, defaultTargetPlatform, TargetPlatform;
import 'package:image_picker/image_picker.dart';
import 'package:http_parser/http_parser.dart';
import 'package:permission_handler/permission_handler.dart';

class ApiService {
  /// Cleared once so old manual `backend_ip` values (e.g. hotspot IPs) are not reused.
  static const String _kLanDiscoveryPrefsMigration = 'dupefinder_lan_discovery_v2';

  static bool _hasUsableBackendBase() {
    final u = _resolvedUrl;
    return u != null &&
        u.isNotEmpty &&
        !u.contains('unresolvable.invalid');
  }

  /// Slightly longer probe when explicitly checking a saved or scanned host.
  static const Duration _healthProbeTimeout = Duration(seconds: 3);
  static const Duration _authRequestTimeout = Duration(seconds: 25);

  /// Per-host probes while scanning /24 (parallel). Too short misses slow PCs / Wi‑Fi.
  static const Duration _lanScanProbeTimeout = Duration(milliseconds: 2000);
  static const int _lanScanBatchSize = 40;
  // Cloud API (works from any Wi-Fi/internet). Can be overridden at build time:
  // flutter run --dart-define=DUPFINDER_API_BASE=https://dupefinder-api.up.railway.app/api
  static const String _defaultCloudApiBase = String.fromEnvironment(
    'DUPFINDER_API_BASE',
    defaultValue: 'https://dupefinder-api.up.railway.app/api',
  );

  // Cached after resolveBaseUrl(); cleared on force re-probe or connection failure retry.
  static String? _resolvedUrl;
  static String _normalizedApiBase(String raw) {
    var s = raw.trim();
    if (s.isEmpty) return '';
    if (!s.startsWith('http://') && !s.startsWith('https://')) {
      s = 'https://$s';
    }
    s = s.replaceAll(RegExp(r'\/+$'), '');
    if (!s.endsWith('/api')) s = '$s/api';
    return s;
  }

  static String get _cloudApiBase => _normalizedApiBase(_defaultCloudApiBase);

  static Map<String, dynamic>? _userDataCache;
  static DateTime? _userDataCacheAt;
  static const Duration _userDataCacheTtl = Duration(seconds: 20);

  /// One-time v2 migration: old builds could save a wrong hotspot IP. We only drop [backend_ip]
  /// if it is invalid or does not answer DupeFinder on :8000 — a still-working saved IP is kept.
  static Future<void> _migrateClearLegacyBackendIp(SharedPreferences prefs) async {
    if (prefs.getBool(_kLanDiscoveryPrefsMigration) == true) return;

    final savedRaw = (prefs.getString('backend_ip') ?? '').trim();
    final saved = _normalizeLanIpv4(savedRaw);

    if (saved != null && await _probeDupeFinderRoot(saved)) {
      await prefs.setBool(_kLanDiscoveryPrefsMigration, true);
      print('[ApiService] LAN v2 migration: kept reachable backend_ip $saved');
      return;
    }

    if (savedRaw.isNotEmpty) {
      await prefs.remove('backend_ip');
      if (saved == null) {
        print('[ApiService] LAN v2 migration: removed invalid backend_ip: $savedRaw');
      } else {
        print('[ApiService] LAN v2 migration: removed unreachable backend_ip: $saved');
      }
    }
    await prefs.setBool(_kLanDiscoveryPrefsMigration, true);
  }

  static String? _normalizeLanIpv4(String? raw) {
    if (raw == null) return null;
    var s = raw.trim().split('%').first.trim();
    if (s.isEmpty || s == '0.0.0.0') return null;
    if (s.contains(':') && s.contains('.')) {
      final idx = s.lastIndexOf(':');
      s = s.substring(idx + 1);
    }
    if (s.contains(':')) return null;
    final parts = s.split('.');
    if (parts.length != 4) return null;
    for (final p in parts) {
      if (int.tryParse(p) == null) return null;
      final n = int.parse(p);
      if (n < 0 || n > 255) return null;
    }
    return parts.join('.');
  }

  static Future<bool> _probeDupeFinderRoot(String hostIp,
      {Duration? timeout}) async {
    try {
      final r = await http
          .get(Uri.parse('http://$hostIp:8000/'))
          .timeout(timeout ?? _healthProbeTimeout);
      return r.statusCode == 200 &&
          r.body.toLowerCase().contains('dupefinder');
    } catch (_) {
      return false;
    }
  }

  /// First host in this /24 batch that responds with DupeFinder root JSON.
  static Future<String?> _scanBatchForDupeFinder(
      String prefix, List<int> lastOctets) async {
    if (lastOctets.isEmpty) return null;
    final completer = Completer<String?>();
    var remaining = lastOctets.length;
    for (final o in lastOctets) {
      final ip = '$prefix.$o';
      _probeDupeFinderRoot(ip, timeout: _lanScanProbeTimeout)
          .then((ok) {
        if (ok && !completer.isCompleted) {
          completer.complete(ip);
        }
      })
          .catchError((_) {})
          .whenComplete(() {
        remaining--;
        if (remaining == 0 && !completer.isCompleted) {
          completer.complete(null);
        }
      });
    }
    return completer.future;
  }

  /// Scans 1–254 on [prefix].0/24 (e.g. prefix `192.168.1`), optionally skipping [excludeLastOctet].
  static Future<String?> _scanSubnetPrefix(
      String prefix, int? excludeLastOctet) async {
    final octets = <int>[];
    for (var o = 1; o <= 254; o++) {
      if (excludeLastOctet != null && o == excludeLastOctet) continue;
      octets.add(o);
    }
    int bucket(int o) {
      if (o >= 100 && o <= 220) return 0;
      if (o >= 2 && o <= 99) return 1;
      return 2;
    }
    octets.sort((a, b) {
      final c = bucket(a).compareTo(bucket(b));
      return c != 0 ? c : a.compareTo(b);
    });

    for (var i = 0; i < octets.length; i += _lanScanBatchSize) {
      final end = min(i + _lanScanBatchSize, octets.length);
      final batch = octets.sublist(i, end);
      final hit = await _scanBatchForDupeFinder(prefix, batch);
      if (hit != null) return hit;
    }
    return null;
  }

  /// Same /24 as this device’s IPv4; skips the phone’s own address.
  static Future<String?> _scanSubnetForBackend(String myIpv4) async {
    final parts = myIpv4.split('.');
    if (parts.length != 4) return null;
    final self = int.tryParse(parts[3]);
    if (self == null) return null;
    final prefix = '${parts[0]}.${parts[1]}.${parts[2]}';
    return _scanSubnetPrefix(prefix, self);
  }

  /// Probe common last-octets on the same /24 in parallel (faster than serial for login cold start).
  static Future<String?> _slowProbeLikelyHostsOnSubnet(String myIpv4) async {
    final parts = myIpv4.split('.');
    if (parts.length != 4) return null;
    final self = int.tryParse(parts[3]);
    if (self == null) return null;
    final prefix = '${parts[0]}.${parts[1]}.${parts[2]}';
    final targets = <String>[];
    for (final last in [8, 100, 108, 1, 254, 2, 50, 3, 20]) {
      if (last == self) continue;
      targets.add('$prefix.$last');
    }
    if (targets.isEmpty) return null;
    final completer = Completer<String?>();
    var pending = targets.length;
    for (final ip in targets) {
      _probeDupeFinderRoot(ip, timeout: _healthProbeTimeout)
          .then((ok) {
        if (ok && !completer.isCompleted) {
          completer.complete(ip);
        }
      })
          .catchError((_) {})
          .whenComplete(() {
        pending--;
        if (pending == 0 && !completer.isCompleted) {
          completer.complete(null);
        }
      });
    }
    return completer.future;
  }

  static Future<bool> _isAndroidEmulator() async {
    if (defaultTargetPlatform != TargetPlatform.android) return false;
    try {
      final a = await DeviceInfoPlugin().androidInfo;
      return !a.isPhysicalDevice;
    } catch (_) {
      return false;
    }
  }

  static Future<bool> _isIosSimulator() async {
    if (defaultTargetPlatform != TargetPlatform.iOS) return false;
    try {
      final ios = await DeviceInfoPlugin().iosInfo;
      return !ios.isPhysicalDevice;
    } catch (_) {
      return false;
    }
  }

  static String _apiUrlFromIp(String ip) => 'http://$ip:8000/api';

  static String? _ipFromApiUrl(String apiUrl) {
    final uri = Uri.tryParse(apiUrl);
    return uri?.host;
  }

  /// Ordered API roots for community / login failover (resolved URL + saved IPv4).
  static Future<List<String>> _orderedApiUrls() async {
    final prefs = await SharedPreferences.getInstance();
    final savedRaw = (prefs.getString('backend_ip') ?? '').trim();
    final saved = _normalizeLanIpv4(savedRaw);
    final urls = <String>[];
    final seen = <String>{};
    void addApi(String apiUrl) {
      if (seen.add(apiUrl)) urls.add(apiUrl);
    }
    if (_resolvedUrl != null && _resolvedUrl!.isNotEmpty) {
      if (!_resolvedUrl!.contains('unresolvable.invalid')) {
        addApi(_resolvedUrl!);
      }
    }
    // Prefer deployed API first so mobile works on any Wi-Fi/internet.
    if (_cloudApiBase.isNotEmpty) {
      addApi(_cloudApiBase);
    }
    if (saved != null) {
      addApi(_apiUrlFromIp(saved));
    }
    // Extra roots for login/community retry when discovery cached a bad URL.
    try {
      final wifiRaw = await NetworkInfo().getWifiIP();
      final wifi = _normalizeLanIpv4(wifiRaw);
      if (wifi != null) {
        final parts = wifi.split('.');
        if (parts.length == 4) {
          final self = int.tryParse(parts[3]);
          final prefix = '${parts[0]}.${parts[1]}.${parts[2]}';
          for (final last in [8, 100, 108, 1, 254]) {
            if (self != null && last == self) continue;
            addApi(_apiUrlFromIp('$prefix.$last'));
          }
        }
      }
    } catch (_) {}
    return urls;
  }

  /// Finds the DupeFinder API base on the LAN. No hardcoded router or hotspot IPs.
  /// [force] clears cache and re-runs discovery (e.g. after a connection error).
  /// [fullLanScan] when false, skips scanning the whole /24 (saves many seconds on login).
  static Future<void> resolveBaseUrl(
      {bool force = false, bool fullLanScan = true}) async {
    if (kIsWeb && _cloudApiBase.isNotEmpty) {
      _resolvedUrl = _cloudApiBase;
      print('[ApiService] Web platform — using cloud API: $_resolvedUrl');
      return;
    }
    // Do not treat unresolvable.invalid as "done" — otherwise login keeps using 10.0.2.2 on real phones.
    if (!force && _hasUsableBackendBase()) {
      return;
    }
    if (force ||
        (_resolvedUrl != null &&
            _resolvedUrl!.contains('unresolvable.invalid'))) {
      _resolvedUrl = null;
    }

    final prefs = await SharedPreferences.getInstance();
    await _migrateClearLegacyBackendIp(prefs);

    // Cloud-first path: stable deployment endpoint works on any network.
    if (_cloudApiBase.isNotEmpty) {
      _resolvedUrl = _cloudApiBase;
      return;
    }

    final savedRaw = prefs.getString('backend_ip')?.trim();
    final saved = _normalizeLanIpv4(savedRaw);
    if (saved != null && await _probeDupeFinderRoot(saved)) {
      _resolvedUrl = 'http://$saved:8000/api';
      print('[ApiService] Using saved backend_ip -> $_resolvedUrl');
      return;
    }
    if (savedRaw != null && savedRaw.isNotEmpty && saved == null) {
      print('[ApiService] Ignoring invalid saved backend_ip: $savedRaw');
    }

    String? wifiRaw = await NetworkInfo().getWifiIP();
    String? wifiIp = _normalizeLanIpv4(wifiRaw);
    if (wifiIp == null &&
        !kIsWeb &&
        defaultTargetPlatform == TargetPlatform.android &&
        !await _isAndroidEmulator()) {
      try {
        final loc = await Permission.locationWhenInUse.request();
        if (loc.isGranted || loc.isLimited) {
          wifiRaw = await NetworkInfo().getWifiIP();
          wifiIp = _normalizeLanIpv4(wifiRaw);
          if (wifiIp != null) {
            print('[ApiService] Wi‑Fi IPv4 after location permission: $wifiIp');
          }
        } else {
          print(
            '[ApiService] Location not granted — Wi‑Fi IP may stay hidden on Android 10+. '
            'Grant location for this app or set your PC IP manually (backend_ip).',
          );
        }
      } catch (e) {
        print('[ApiService] Location permission request failed: $e');
      }
    }
    if (wifiIp != null) {
      print(
          '[ApiService] Wi‑Fi IPv4 $wifiIp — probing likely PC addresses on :8000 ...');
      final slow = await _slowProbeLikelyHostsOnSubnet(wifiIp);
      if (slow != null) {
        _resolvedUrl = 'http://$slow:8000/api';
        await prefs.setString('backend_ip', slow);
        print('[ApiService] Likely-host probe found backend -> $_resolvedUrl');
        return;
      }
      if (fullLanScan) {
        print('[ApiService] Likely-host probe missed — scanning /24 for DupeFinder ...');
        final found = await _scanSubnetForBackend(wifiIp);
        if (found != null) {
          _resolvedUrl = 'http://$found:8000/api';
          await prefs.setString('backend_ip', found);
          print('[ApiService] LAN scan found backend -> $_resolvedUrl');
          return;
        }
        print('[ApiService] LAN scan found no DupeFinder on this subnet');
      } else {
        print(
            '[ApiService] Skipping full /24 scan (fast path); login will retry on failure.',
        );
      }
    } else {
      print(
          '[ApiService] No Wi‑Fi device IP (common on Android 10+ without location) — trying gateway /24');
      if (fullLanScan) {
        final gwRaw = await NetworkInfo().getWifiGatewayIP();
        final gw = _normalizeLanIpv4(gwRaw);
        if (gw != null) {
          final gp = gw.split('.');
          if (gp.length == 4) {
            final prefix = '${gp[0]}.${gp[1]}.${gp[2]}';
            final found = await _scanSubnetPrefix(prefix, null);
            if (found != null) {
              _resolvedUrl = 'http://$found:8000/api';
              await prefs.setString('backend_ip', found);
              print(
                  '[ApiService] Gateway-prefix scan found backend -> $_resolvedUrl');
              return;
            }
          }
        }
        print('[ApiService] Gateway-based scan did not find DupeFinder');
      }
    }

    if (await _isAndroidEmulator()) {
      if (await _probeDupeFinderRoot('10.0.2.2')) {
        _resolvedUrl = 'http://10.0.2.2:8000/api';
        print('[ApiService] Android emulator -> $_resolvedUrl');
        return;
      }
    }

    if (await _isIosSimulator()) {
      if (await _probeDupeFinderRoot('127.0.0.1')) {
        _resolvedUrl = 'http://127.0.0.1:8000/api';
        print('[ApiService] iOS Simulator -> $_resolvedUrl');
        return;
      }
    }

    _resolvedUrl = 'http://unresolvable.invalid:8000/api';
    print('[ApiService] Could not find DupeFinder on your network.');
    print('[ApiService] Fix checklist:');
    print('  1) PC: backend/start_lan.ps1 (uvicorn --host 0.0.0.0 --port 8000)');
    print('  2) Windows Firewall: inbound TCP 8000');
    print('  3) Phone + PC on same Wi‑Fi; open http://<PC-ip>:8000/ in phone browser');
    print('  4) Optional: ApiService.setBackendIP("<ipv4>") if discovery is blocked');
  }

  static bool _isConnectionFailure(Object e) {
    if (e is TimeoutException) return true;
    final s = e.toString().toLowerCase();
    return s.contains('socketexception') ||
        s.contains('connection timed out') ||
        s.contains('connection refused') ||
        s.contains('failed host lookup') ||
        s.contains('network is unreachable') ||
        s.contains('timeoutexception') ||
        s.contains('future not completed') ||
        s.contains('clientexception');
  }

  static String get baseUrl {
    final u = _resolvedUrl;
    if (u != null &&
        u.isNotEmpty &&
        !u.contains('unresolvable.invalid')) {
      return u;
    }
    if (kIsWeb) return 'http://localhost:8000/api';
    if (_cloudApiBase.isNotEmpty) return _cloudApiBase;
    // Before resolveBaseUrl() (e.g. tests): prefer emulator loopback.
    if (defaultTargetPlatform == TargetPlatform.android) {
      return 'http://10.0.2.2:8000/api';
    }
    return 'http://127.0.0.1:8000/api';
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
    await prefs.remove('user_name');
    await prefs.remove('user_id');
    await prefs.remove('user_profile_image');
    _userDataCache = null;
    _userDataCacheAt = null;
  }

  // Get headers with auth token
  Future<Map<String, String>> getHeaders() async {
    final token = await getAccessToken();
    return {
      'Content-Type': 'application/json',
      if (token != null) 'Authorization': 'Bearer $token',
    };
  }

  static const _communityLikeDeviceIdKey = 'community_like_device_id';

  /// Stable id for community likes when not logged in (sent as X-Community-Like-Id).
  Future<Map<String, String>> getCommunityHeaders() async {
    final base = await getHeaders();
    final prefs = await SharedPreferences.getInstance();
    var id = prefs.getString(_communityLikeDeviceIdKey);
    if (id == null || id.length < 8) {
      const chars = '0123456789abcdef';
      final r = Random.secure();
      id = List.generate(24, (_) => chars[r.nextInt(chars.length)]).join();
      await prefs.setString(_communityLikeDeviceIdKey, id);
    }
    return {
      ...base,
      'X-Community-Like-Id': id,
    };
  }

  /// POST to /api/{path} with JSON body; re-probes LAN IPs once on connection failure.
  Future<http.Response> _postAuthWithRetry(
      String path, Map<String, dynamic> body) async {
    // Fast path first; if still no backend (e.g. app started before PC API was up), run full LAN once.
    await resolveBaseUrl(fullLanScan: false);
    if (!_hasUsableBackendBase()) {
      await resolveBaseUrl(force: true, fullLanScan: true);
    }
    Future<http.Response> postOnce() => http
        .post(
          Uri.parse('$baseUrl/$path'),
          headers: {'Content-Type': 'application/json'},
          body: jsonEncode(body),
        )
        .timeout(_authRequestTimeout);
    try {
      return await postOnce();
    } catch (e) {
      if (_isConnectionFailure(e)) {
        print('[ApiService] $path failed ($e); re-probing backend (full LAN)...');
        await resolveBaseUrl(force: true, fullLanScan: true);
        return await postOnce();
      }
      rethrow;
    }
  }

  // Register new user
  Future<Map<String, dynamic>> register(String email, String password,
      {String? fullName}) async {
    try {
      final response = await _postAuthWithRetry('auth/signup', {
        'email': email,
        'password': password,
        if (fullName != null && fullName.trim().isNotEmpty)
          'full_name': fullName.trim(),
      });

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
      final response = await _postAuthWithRetry('auth/verify-otp', {
        'email': email,
        'otp_code': otp, // Backend expects 'otp_code' not 'otp'
      });

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
    final loginUrl = '$baseUrl/auth/login';
    try {
      final response = await _postAuthWithRetry('auth/login', {
        'email': email,
        'password': password,
      });

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

          // Profile sync can wait — do not block returning from login().
          unawaited(syncUserProfileFromBackend());
        }

        return data;
      } else {
        final error = jsonDecode(response.body);
        throw Exception(error['detail'] ?? 'Login failed');
      }
    } on TimeoutException catch (e) {
      return await _loginFailoverOrThrow(
        email: email,
        password: password,
        loginUrl: loginUrl,
        probeError: e,
      );
    } on SocketException catch (e) {
      return await _loginFailoverOrThrow(
        email: email,
        password: password,
        loginUrl: loginUrl,
        probeError: e,
      );
    } catch (e) {
      if (_isConnectionFailure(e)) {
        return await _loginFailoverOrThrow(
          email: email,
          password: password,
          loginUrl: loginUrl,
          probeError: e,
        );
      }
      throw Exception('Login failed: ${e.toString()}');
    }
  }

  Future<Map<String, dynamic>> _loginFailoverOrThrow({
    required String email,
    required String password,
    required String loginUrl,
    required Object probeError,
  }) async {
    try {
      return await _tryLoginAcrossKnownBackends(
          email: email, password: password);
    } catch (_) {
      final detail = probeError is SocketException
          ? probeError.message
          : probeError.toString();
      if (probeError is TimeoutException) {
        throw Exception(
          'Login timed out. Check backend/network and try again. Endpoint: $loginUrl',
        );
      }
      throw Exception(
        'Cannot reach backend. Use the same Wi‑Fi as the PC (not guest Wi‑Fi), run the API on '
        '0.0.0.0:8000, and allow TCP 8000 in Windows Firewall. On Android, allow Location for '
        'this app so it can read your Wi‑Fi IP for discovery. In the phone browser open '
        'http://YOUR_PC_IP:8000/ — you should see JSON mentioning DupeFinder. '
        'Endpoint: $loginUrl. Error: $detail',
      );
    }
  }

  Future<Map<String, dynamic>> _tryLoginAcrossKnownBackends({
    required String email,
    required String password,
  }) async {
    final apiUrls = await _orderedApiUrls();
    final attempted = <String>[];
    for (final api in apiUrls) {
      final endpoint = '$api/auth/login';
      attempted.add(endpoint);
      try {
        final response = await http
            .post(
              Uri.parse(endpoint),
              headers: {'Content-Type': 'application/json'},
              body: jsonEncode({
                'email': email,
                'password': password,
              }),
            )
            .timeout(const Duration(seconds: 5));

        if (response.statusCode == 200) {
          _resolvedUrl = api;
          final ip = _ipFromApiUrl(api);
          if (ip != null && ip.isNotEmpty) {
            final prefs = await SharedPreferences.getInstance();
            await prefs.setString('backend_ip', ip);
          }

          final data = jsonDecode(response.body);
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
            unawaited(syncUserProfileFromBackend());
          }
          return Map<String, dynamic>.from(data as Map);
        }

        // Reachable backend with auth response (wrong creds/verify/etc) => stop fallback and show server message.
        final error = jsonDecode(response.body);
        throw Exception(error['detail'] ?? 'Login failed');
      } on SocketException {
        continue;
      } on TimeoutException {
        continue;
      } catch (e) {
        if (_isConnectionFailure(e)) {
          continue;
        }
        throw Exception(e.toString().replaceFirst('Exception: ', ''));
      }
    }

    throw Exception(
      'Cannot reach backend on known addresses. Tried: ${attempted.join(', ')}',
    );
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
      final body = await getMe().timeout(
        const Duration(seconds: 15),
        onTimeout: () => throw TimeoutException('getMe'),
      );
      final user = Map<String, dynamic>.from((body['user'] as Map?) ?? {});
      Map<String, dynamic> profile = {};
      try {
        profile = await getUserProfileData().timeout(
          const Duration(seconds: 12),
          onTimeout: () => throw TimeoutException('getUserProfileData'),
        );
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
      } else {
        await prefs.remove('user_profile_image');
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
        : (name.toLowerCase().endsWith('.webp') ? 'image/webp' : 'image/jpeg');

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

  /// Home category chips: `dresses` | `bags` | `accessories` | `jewelry` | `watches` → up to [limit] products.
  Future<Map<String, dynamic>> shopBrowse({
    required String slot,
    int limit = 10,
  }) async {
    Future<http.Response> getSlot(String s) async {
      final uri = Uri.parse('$baseUrl/products/shop-browse').replace(
        queryParameters: {
          'slot': s,
          'limit': limit.toString(),
        },
      );
      return http.get(uri, headers: await getHeaders());
    }

    var response = await getSlot(slot);
    // Older APIs reject `watches` (422). Fall back until production is redeployed.
    if (response.statusCode == 422 && slot == 'watches') {
      response = await getSlot('accessories');
    }
    if (response.statusCode != 200) {
      throw Exception(
        'Shop browse failed (${response.statusCode}): ${response.body}',
      );
    }
    return Map<String, dynamic>.from(jsonDecode(response.body) as Map);
  }

  Future<List<Map<String, dynamic>>> getCommunityPosts() async {
    const communityTimeout = Duration(seconds: 35);

    Future<List<Map<String, dynamic>>> run(String apiRoot) async {
      final endpoint = '$apiRoot/community/posts';
      final response = await http
          .get(
            Uri.parse(endpoint),
            headers: await getCommunityHeaders(),
          )
          .timeout(communityTimeout);
      if (response.statusCode != 200) {
        throw Exception(
            'Failed to load community posts (${response.statusCode}) via $endpoint');
      }
      final body = jsonDecode(response.body) as Map<String, dynamic>;
      return (body['posts'] as List<dynamic>? ?? [])
          .map((e) => Map<String, dynamic>.from(e as Map))
          .toList();
    }

    final tried = <String>[];

    Future<List<Map<String, dynamic>>?> walk(List<String> urls) async {
      for (final api in urls) {
        final endpoint = '$api/community/posts';
        tried.add(endpoint);
        try {
          final posts = await run(api);
          _resolvedUrl = api;
          final ip = _ipFromApiUrl(api);
          if (ip != null && ip.isNotEmpty) {
            final prefs = await SharedPreferences.getInstance();
            await prefs.setString('backend_ip', ip);
          }
          return posts;
        } catch (_) {
          continue;
        }
      }
      return null;
    }

    var urls = await _orderedApiUrls();
    var posts = await walk(urls);
    if (posts != null) return posts;

    await Future<void>.delayed(const Duration(milliseconds: 500));
    posts = await walk(urls);
    if (posts != null) return posts;

    await ApiService.resolveBaseUrl(force: true);
    urls = await _orderedApiUrls();
    posts = await walk(urls);
    if (posts != null) return posts;

    await Future<void>.delayed(const Duration(milliseconds: 500));
    posts = await walk(urls);
    if (posts != null) return posts;

    throw Exception(
      'Community feed unreachable. Tried: ${tried.join(', ')}',
    );
  }

  /// Full single post (includes image bytes). Same URL failover as feed.
  Future<Map<String, dynamic>> getCommunityPost(String postId) async {
    Future<Map<String, dynamic>> run(String apiRoot) async {
      final endpoint = '$apiRoot/community/posts/$postId';
      final response = await http
          .get(
            Uri.parse(endpoint),
            headers: await getCommunityHeaders(),
          )
          .timeout(const Duration(seconds: 45));
      if (response.statusCode != 200) {
        throw Exception(
            'Failed to load post (${response.statusCode}) via $endpoint');
      }
      final body = jsonDecode(response.body) as Map<String, dynamic>;
      return Map<String, dynamic>.from(body['post'] as Map);
    }

    final tried = <String>[];
    final urls = await _orderedApiUrls();

    for (final api in urls) {
      tried.add('$api/community/posts/$postId');
      try {
        final post = await run(api);
        _resolvedUrl = api;
        final ip = _ipFromApiUrl(api);
        if (ip != null && ip.isNotEmpty) {
          final prefs = await SharedPreferences.getInstance();
          await prefs.setString('backend_ip', ip);
        }
        return post;
      } catch (_) {
        continue;
      }
    }

    await ApiService.resolveBaseUrl(force: true);
    final urls2 = await _orderedApiUrls();
    for (final api in urls2) {
      tried.add('$api/community/posts/$postId');
      try {
        final post = await run(api);
        _resolvedUrl = api;
        final ip = _ipFromApiUrl(api);
        if (ip != null && ip.isNotEmpty) {
          final prefs = await SharedPreferences.getInstance();
          await prefs.setString('backend_ip', ip);
        }
        return post;
      } catch (_) {
        continue;
      }
    }

    throw Exception(
      'Community post unreachable. Tried: ${tried.join(', ')}',
    );
  }

  Future<Map<String, dynamic>> addCommunityPost({
    required String description,
    required String author,
    String? authorPfp,
    String? imageBase64,
  }) async {
    final response = await http.post(
      Uri.parse('$baseUrl/community/posts'),
      headers: await getCommunityHeaders(),
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
    String? parentReplyId,
  }) async {
    final response = await http.post(
      Uri.parse('$baseUrl/community/posts/$postId/replies'),
      headers: await getCommunityHeaders(),
      body: jsonEncode({
        'body': body,
        'author': author,
        'author_pfp': authorPfp,
        'parent_reply_id': parentReplyId,
      }),
    );
    if (response.statusCode != 200) {
      throw Exception('Failed to add reply');
    }
    return Map<String, dynamic>.from(
      (jsonDecode(response.body) as Map<String, dynamic>)['post'] as Map,
    );
  }

  Future<Map<String, dynamic>> getCommunityNotifications({
    int limit = 20,
    bool unreadOnly = false,
  }) async {
    final uri = Uri.parse('$baseUrl/community/notifications').replace(
      queryParameters: {
        'limit': '$limit',
        'unread_only': unreadOnly ? 'true' : 'false',
      },
    );
    final response = await http.get(uri, headers: await getCommunityHeaders());
    if (response.statusCode != 200) {
      throw Exception('Failed to load notifications');
    }
    return Map<String, dynamic>.from(jsonDecode(response.body) as Map);
  }

  Future<int> markCommunityNotificationRead(String notificationId) async {
    final response = await http.post(
      Uri.parse('$baseUrl/community/notifications/$notificationId/read'),
      headers: await getCommunityHeaders(),
    );
    if (response.statusCode != 200) {
      throw Exception('Failed to mark notification read');
    }
    final decoded = Map<String, dynamic>.from(jsonDecode(response.body) as Map);
    return (decoded['unreadCount'] as num?)?.toInt() ?? 0;
  }

  Future<void> deleteCommunityReply({
    required String postId,
    required String replyId,
  }) async {
    final response = await http.delete(
      Uri.parse('$baseUrl/community/posts/$postId/replies/$replyId'),
      headers: await getCommunityHeaders(),
    );
    if (response.statusCode != 200) {
      throw Exception('Failed to delete reply');
    }
  }

  Future<void> deleteCommunityPost(String postId) async {
    final response = await http.delete(
      Uri.parse('$baseUrl/community/posts/$postId'),
      headers: await getCommunityHeaders(),
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
      headers: await getCommunityHeaders(),
      body: jsonEncode({'reason': reason}),
    );
    if (response.statusCode != 200) {
      throw Exception('Failed to report post');
    }
  }

  Future<void> reportCommunityReply({
    required String postId,
    required String replyId,
    required String reason,
  }) async {
    final response = await http.post(
      Uri.parse('$baseUrl/community/posts/$postId/replies/$replyId/report'),
      headers: await getCommunityHeaders(),
      body: jsonEncode({'reason': reason}),
    );
    if (response.statusCode != 200) {
      throw Exception('Failed to report reply');
    }
  }

  Future<void> blockCommunityUser(String targetUserId) async {
    final response = await http.post(
      Uri.parse('$baseUrl/community/users/$targetUserId/block'),
      headers: await getCommunityHeaders(),
    );
    if (response.statusCode != 200) {
      throw Exception('Failed to block user');
    }
  }

  Future<void> editCommunityPost({
    required String postId,
    required String description,
  }) async {
    final response = await http.put(
      Uri.parse('$baseUrl/community/posts/$postId'),
      headers: await getCommunityHeaders(),
      body: jsonEncode({'description': description}),
    );
    if (response.statusCode != 200) {
      throw Exception('Failed to edit post');
    }
  }

  Future<Map<String, dynamic>> toggleCommunityPostLike(String postId) async {
    const timeout = Duration(seconds: 28);
    final uri = Uri.parse('$baseUrl/community/posts/$postId/like');
    for (var attempt = 0; attempt < 3; attempt++) {
      try {
        final response = await http
            .post(uri, headers: await getCommunityHeaders())
            .timeout(timeout);
        if (response.statusCode != 200) {
          throw Exception(
            'Failed to toggle like (${response.statusCode}): ${response.body}',
          );
        }
        return Map<String, dynamic>.from(
          (jsonDecode(response.body) as Map<String, dynamic>)['post'] as Map,
        );
      } catch (e, st) {
        if (attempt >= 2) {
          Error.throwWithStackTrace(e, st);
        }
        await Future<void>.delayed(Duration(milliseconds: 280 * (attempt + 1)));
      }
    }
    throw StateError('toggleCommunityPostLike: exhausted retries');
  }

  Future<Map<String, dynamic>> getUserData() async {
    if (_userDataCache != null &&
        _userDataCacheAt != null &&
        DateTime.now().difference(_userDataCacheAt!) < _userDataCacheTtl) {
      return Map<String, dynamic>.from(_userDataCache!);
    }
    final response = await http.get(
      Uri.parse('$baseUrl/user-data'),
      headers: await getHeaders(),
    );
    if (response.statusCode != 200) {
      throw Exception('Failed to load user data');
    }
    final decoded = Map<String, dynamic>.from(jsonDecode(response.body) as Map);
    _userDataCache = decoded;
    _userDataCacheAt = DateTime.now();
    return Map<String, dynamic>.from(decoded);
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
    if (_userDataCache != null) {
      _userDataCache = {
        ..._userDataCache!,
        'wishlist': items,
      };
      _userDataCacheAt = DateTime.now();
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
    if (_userDataCache != null) {
      _userDataCache = {
        ..._userDataCache!,
        'compare': items,
      };
      _userDataCacheAt = DateTime.now();
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
    if (_userDataCache != null) {
      _userDataCache = {
        ..._userDataCache!,
        'dupe_history': items,
      };
      _userDataCacheAt = DateTime.now();
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
    _userDataCacheAt = null;
  }
}
