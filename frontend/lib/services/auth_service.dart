import 'dart:convert';
import 'package:shared_preferences/shared_preferences.dart';
import 'api_service.dart';

/// AuthService — replaces Firebase Auth.
/// Stores the logged-in user in SharedPreferences.
/// Phase 4: swap token storage for a proper JWT refresh mechanism.
class AuthService {
  static final AuthService _i = AuthService._();
  factory AuthService() => _i;
  AuthService._();

  // ── In-memory session (loaded from prefs on startup) ──────────────────
  Map<String, dynamic>? _session;   // { uid, fullName, email, role, token }

  // ── Public getters ────────────────────────────────────────────────────
  bool   get isLoggedIn => _session != null;
  String? get uid       => _session?['uid'];
  String? get role      => _session?['role'];
  String? get fullName  => _session?['fullName'];
  String? get email     => _session?['email'];

  // ── Load session from disk (call once at app start) ───────────────────
  Future<void> loadSession() async {
    final prefs = await SharedPreferences.getInstance();
    final raw   = prefs.getString('session');
    if (raw != null) _session = jsonDecode(raw);
  }

  // ── Register ──────────────────────────────────────────────────────────
  Future<void> register({
    required String fullName,
    required String email,
    required String password,
    String? phoneNumber,
  }) async {
    final res = await ApiService().register(
      fullName: fullName, email: email,
      password: password, phoneNumber: phoneNumber,
    );
    await _saveSession(res);
  }

  // ── Login ─────────────────────────────────────────────────────────────
  Future<void> login({
    required String email,
    required String password,
  }) async {
    final res = await ApiService().login(email: email, password: password);
    await _saveSession(res);
  }

  // ── Logout ────────────────────────────────────────────────────────────
  Future<void> signOut() async {
    _session = null;
    final prefs = await SharedPreferences.getInstance();
    await prefs.remove('session');
  }

  // ── Internal ──────────────────────────────────────────────────────────
  Future<void> _saveSession(Map<String, dynamic> res) async {
    _session = {
      'uid':       res['uid'],
      'fullName':  res['fullName'],
      'email':     res['email'],
      'role':      res['role'],
      'token':     res['access_token'],
    };
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString('session', jsonEncode(_session));
  }
}