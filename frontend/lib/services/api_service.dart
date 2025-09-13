import 'dart:convert';
import 'dart:io';
import 'dart:async';
import 'package:flutter/foundation.dart';
import 'package:network_info_plus/network_info_plus.dart';
import 'package:shared_preferences/shared_preferences.dart';
import 'package:http/http.dart' as http;
import '../models/food_analysis.dart';

class ApiService {
  // REPLACE THIS IP WITH YOUR LAPTOP'S ACTUAL IP ADDRESS
  // Keep no leading/trailing spaces to avoid URI parsing issues (see FormatException)
  // Default fallback; discovery will attempt to find the correct host.
  static const String _defaultLaptopIP = '192.168.29.185';

  static String? _detectedHost; // cached in-memory

  static String get _trimmedLaptopIP {
    return (_detectedHost ?? _defaultLaptopIP).trim();
  }

  static const _prefsKeyDetectedHost = 'detected_server_host';

  // Increase upload timeout to 60s to allow slower networks/large images.
  static const Duration _timeout = Duration(seconds: 60);

  // Build URIs using Uri constructor to avoid accidental percent-encoding of
  // interpolated literals and to ensure correct URL encoding.
  static Uri _buildApiUri(String path) {
    // `path` should start with a leading slash like '/analyze/'.
    final apiPath = path.startsWith('/') ? 'api/v1$path' : 'api/v1/$path';
    return Uri(scheme: 'http', host: _trimmedLaptopIP, port: 8000, path: apiPath);
  }

  // Discover a reachable host on port 8000 by probing likely candidates.
  // Strategy:
  // 1. Use cached host from SharedPreferences
  // 2. Use device Wi-Fi IP to create candidates on the same subnet
  // 3. Try common local addresses (127.0.0.1, 10.0.2.2, defaultLaptopIP)
  // 4. Cache the first reachable host
  static Future<void> _discoverHost({Duration timeout = const Duration(seconds: 3)}) async {
    if (_detectedHost != null) return;

    final prefs = await SharedPreferences.getInstance();
    final cached = prefs.getString(_prefsKeyDetectedHost);
    if (cached != null) {
      _detectedHost = cached;
      return;
    }

    final info = NetworkInfo();
    String? wifiIp;
    try {
      wifiIp = await info.getWifiIP();
    } catch (_) {
      wifiIp = null;
    }

    // Build a short, deterministic candidate list to avoid slow /24 scans.
    final candidates = <String>{};
    if (wifiIp != null && wifiIp.contains('.')) {
      // Add the device Wi-Fi IP (useful when phone and server run on same device/emulator)
      candidates.add(wifiIp);

      // Try likely laptop addresses on the same subnet: gateway-like (.1) and common .254
      final parts = wifiIp.split('.');
      if (parts.length == 4) {
        final prefix = '${parts[0]}.${parts[1]}.${parts[2]}.';
        candidates.add('${prefix}1');
        candidates.add('${prefix}254');
      }
    }

    // Add small set of common fallbacks
    candidates.addAll(['127.0.0.1', '10.0.2.2', _defaultLaptopIP]);

    // Try candidates with short timeout and stop at first that responds
    for (final host in candidates) {
      try {
        final uri = Uri(scheme: 'http', host: host, port: 8000, path: '/');
        final response = await http.get(uri).timeout(timeout);
        if (response.statusCode < 500) {
          _detectedHost = host;
          await prefs.setString(_prefsKeyDetectedHost, host);
          return;
        }
      } catch (_) {
        // ignore and try next
      }
    }
  }

  // Public API: allow manual override of the server host (persisted).
  static Future<void> setDetectedHost(String host) async {
    _detectedHost = host.trim();
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_prefsKeyDetectedHost, _detectedHost!);
  }

  static Future<void> clearDetectedHost() async {
    _detectedHost = null;
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove(_prefsKeyDetectedHost);
  }

  // Alternative: Auto-detect configuration
  static String get baseUrl {
    // Backwards-compatible string for debug displays only.
  return 'http://$_trimmedLaptopIP:8000/api/v1';
  }

  Future<FoodAnalysis> analyzeFoodImage(File imageFile) async {
    try {
  await _discoverHost();
  final uri = _buildApiUri('/analyze/');

  // Quick pre-check: ensure the server is reachable before attempting upload.
  final canReach = await testConnection();
    if (!canReach) {
    throw ApiException(
      '❌ Cannot reach server at $_trimmedLaptopIP:8000.\nPlease verify your network and that the Django server is running.',
      0,
    );
  }

  debugPrint('🚀 Sending request to: $uri');
  debugPrint('📱 Device IP trying to reach: $_trimmedLaptopIP:8000');
      
      final request = http.MultipartRequest('POST', uri);
      request.files.add(
        await http.MultipartFile.fromPath('image', imageFile.path),
      );
      
      // Set headers
      // Do NOT manually set 'Content-Type' for multipart requests.
      // MultipartRequest will set the correct Content-Type with boundary.
      request.headers.addAll({
        'Accept': 'application/json',
      });

  debugPrint('📤 Uploading image: ${imageFile.path}');

      // Send request with timeout and a single retry on timeout.
      // Note: a MultipartRequest cannot be sent twice — on retry we must
      // create a fresh MultipartRequest instance.
      http.StreamedResponse streamedResponse;
      try {
        streamedResponse = await request.send().timeout(_timeout);
      } on TimeoutException {
        // Retry once by building a new request (cannot reuse the old one).
        final retryRequest = http.MultipartRequest('POST', uri);
        retryRequest.files.add(
          await http.MultipartFile.fromPath('image', imageFile.path),
        );
        retryRequest.headers.addAll({
          'Accept': 'application/json',
        });
        streamedResponse = await retryRequest.send().timeout(_timeout);
      }

      final response = await http.Response.fromStream(streamedResponse);

  debugPrint('📥 Response status: ${response.statusCode}');
  debugPrint('📥 Response body: ${response.body}');

    if (response.statusCode == 200) {
        final jsonData = json.decode(response.body);
        return FoodAnalysis.fromJson(jsonData);
      } else {
        final errorData = json.decode(response.body);
        throw ApiException(
      'Failed to analyze image: ${errorData['error'] ?? 'Unknown error'}',
          response.statusCode,
        );
      }
    } on SocketException {
      throw ApiException(
  '❌ Cannot reach server at $_trimmedLaptopIP:8000\n'
        'Make sure:\n'
        '• Your laptop and phone are on the same WiFi\n'
        '• Django server is running with: python manage.py runserver 0.0.0.0:8000\n'
        '• Laptop firewall allows port 8000',
        0,
      );
    } on TimeoutException {
      throw ApiException('❌ Request timed out after ${_timeout.inSeconds}s. Try again or check your network.', 0);
    } on http.ClientException catch (e) {
      throw ApiException('❌ Failed to connect: $e', 0);
    } catch (e) {
      if (e is ApiException) rethrow;
      throw ApiException('❌ Unexpected error: $e', 0);
    }
  }

  // Test connection to your laptop
  Future<bool> testConnection() async {
    try {
  await _discoverHost();
  debugPrint('🔍 Testing connection to $_trimmedLaptopIP:8000...');

  // Probe the server and treat any non-server-error HTTP response as reachable.
  final uri = Uri(scheme: 'http', host: _trimmedLaptopIP, port: 8000, path: 'admin/');
  final response = await http.get(uri).timeout(const Duration(seconds: 10));

  debugPrint('✅ Connection test result: ${response.statusCode}');
  // Consider the server reachable if it responds with anything below 500.
  return response.statusCode < 500;
    } catch (e) {
  debugPrint('❌ Connection test failed: $e');
      return false;
    }
  }

  // Get network info for debugging
  static String getNetworkDebugInfo() {
  return '''
🔧 Network Configuration:
• Laptop IP: $_trimmedLaptopIP
• Server URL: $baseUrl
• Make sure both devices are on same WiFi network
• Django command: python manage.py runserver 0.0.0.0:8000
  ''';
  }
}

class ApiException implements Exception {
  final String message;
  final int statusCode;

  ApiException(this.message, this.statusCode);

  @override
  String toString() => message;
}