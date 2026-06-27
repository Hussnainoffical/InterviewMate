import 'dart:convert';
import 'package:http/http.dart' as http;
import 'auth_service.dart';

// ── Change this URL based on your setup ──────────────────────────────────────
// Web / Desktop  →  http://localhost:8000
// Android Emu    →  http://10.0.2.2:8000
// Physical phone →  http://YOUR_PC_LAN_IP:8000
// ─────────────────────────────────────────────────────────────────────────────
const String kBaseUrl = 'http://localhost:8000';

class ApiService {
  static final ApiService _i = ApiService._();
  factory ApiService() => _i;
  ApiService._();

  Map<String, String> get _h {
    final headers = {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
    };
    final token = AuthService().token;
    if (token != null && token.isNotEmpty) {
      headers['Authorization'] = 'Bearer $token';
    }
    return headers;
  }

  // ── Core ─────────────────────────────────────────────────────────────────

  Future<Map<String, dynamic>> _get(String path) async {
    final res = await http.get(Uri.parse('$kBaseUrl$path'), headers: _h)
        .timeout(const Duration(seconds: 10));
    return _handle(res);
  }

  Future<Map<String, dynamic>> _post(String path, Map<String, dynamic> body,
      {Duration timeout = const Duration(seconds: 10)}) async {
    final res = await http.post(Uri.parse('$kBaseUrl$path'),
        headers: _h, body: jsonEncode(body))
        .timeout(timeout);
    return _handle(res);
  }

  Future<Map<String, dynamic>> _put(String path, Map<String, dynamic> body) async {
    final res = await http.put(Uri.parse('$kBaseUrl$path'),
        headers: _h, body: jsonEncode(body))
        .timeout(const Duration(seconds: 10));
    return _handle(res);
  }

  Future<Map<String, dynamic>> _delete(String path) async {
    final res = await http.delete(Uri.parse('$kBaseUrl$path'), headers: _h)
        .timeout(const Duration(seconds: 10));
    return _handle(res);
  }

  Map<String, dynamic> _handle(http.Response res) {
    Map<String, dynamic> data;
    try {
      final decoded = jsonDecode(res.body);
      data = decoded is Map<String, dynamic>
          ? decoded
          : {'detail': res.body};
    } catch (_) {
      data = {'detail': res.body.isEmpty ? res.reasonPhrase ?? 'Empty response' : res.body};
    }
    if (res.statusCode >= 200 && res.statusCode < 300) return data;
    throw ApiException(data['detail']?.toString() ?? 'Unknown error', res.statusCode);
  }

  // ── Auth ─────────────────────────────────────────────────────────────────

  Future<Map<String, dynamic>> register({
    required String fullName, required String email,
    required String password, String? phoneNumber,
  }) => _post('/api/v1/auth/register', {
    'fullName': fullName, 'email': email, 'password': password,
    if (phoneNumber != null) 'phoneNumber': phoneNumber,
  });

  Future<Map<String, dynamic>> login({
    required String email, required String password,
  }) => _post('/api/v1/auth/login', {'email': email, 'password': password});

  Future<Map<String, dynamic>> forgotPassword(String email) =>
      _post('/api/v1/auth/forgot-password', {'email': email});

  // ── Profile ───────────────────────────────────────────────────────────────

  Future<Map<String, dynamic>> getProfile(String uid) =>
      _get('/api/v1/profile/$uid');

  Future<Map<String, dynamic>> updateProfile(String uid, Map<String, dynamic> data) =>
      _put('/api/v1/profile/$uid', data);

  // ── Resume ────────────────────────────────────────────────────────────────

  Future<Map<String, dynamic>> uploadResume(
      List<int> fileBytes, String fileName, String uid) async {
    final uri = Uri.parse('$kBaseUrl/api/v1/resume/upload?uid=$uid');
    final req = http.MultipartRequest('POST', uri)
      ..headers.addAll(_h..remove('Content-Type'))
      ..files.add(http.MultipartFile.fromBytes('file', fileBytes, filename: fileName));
    final streamed = await req.send().timeout(const Duration(seconds: 180));
    final res = await http.Response.fromStream(streamed);
    return _handle(res);
  }

  Future<Map<String, dynamic>> getSkills(String uid) =>
      _get('/api/v1/resume/skills/$uid');

  Future<Map<String, dynamic>> updateSkills(String uid, List<String> skills) =>
      _put('/api/v1/resume/skills/$uid', {'skills': skills});

  // ── GitHub ────────────────────────────────────────────────────────────────

  Future<Map<String, dynamic>> extractGithubSkills(
      String username, String uid) async {
    final uri = Uri.parse('$kBaseUrl/api/v1/github/extract-skills?uid=$uid');
    final res = await http.post(uri, headers: _h,
        body: jsonEncode({'githubUsername': username}))
        .timeout(const Duration(seconds: 15));
    return _handle(res);
  }

  // ── Interview ─────────────────────────────────────────────────────────────

  Future<Map<String, dynamic>> startInterview(
      List<String> skills, String uid, {Map<String, dynamic>? candidateProfile, int questionCount = 5}) async {
    final uri = Uri.parse('$kBaseUrl/api/v1/interview/start?uid=$uid');
    final res = await http.post(uri, headers: _h,
        body: jsonEncode({
          'skills': skills,
          'questionCount': questionCount,
          if (candidateProfile != null) 'candidateProfile': candidateProfile,
        }))
        .timeout(const Duration(seconds: 240));  // Qwen generation can take minutes on CPU
    return _handle(res);
  }

  Future<Map<String, dynamic>> submitAnswer({
    required String sessionId, required String questionId,
    required List<int> audioBytes, required String uid,
    String audioFileName = 'answer.wav',
  }) async {
    final uri = Uri.parse('$kBaseUrl/api/v1/interview/submit-answer');
    final req = http.MultipartRequest('POST', uri)
      ..headers.addAll(_h..remove('Content-Type'))
      ..fields['sessionId']  = sessionId
      ..fields['questionId'] = questionId
      ..fields['uid']        = uid
      ..files.add(http.MultipartFile.fromBytes('audio', audioBytes, filename: audioFileName));
    final streamed = await req.send().timeout(const Duration(seconds: 180));
    final res = await http.Response.fromStream(streamed);
    return _handle(res);
  }

  Future<Map<String, dynamic>> submitTranscriptAnswer({
    required String sessionId,
    required String questionId,
    required String transcript,
    required String uid,
    String source = 'realtime',
  }) =>
      _post('/api/v1/interview/submit-transcript', {
        'sessionId': sessionId,
        'questionId': questionId,
        'uid': uid,
        'transcript': transcript,
        'source': source,
      }, timeout: const Duration(seconds: 90));

  Future<Map<String, dynamic>> completeInterview(
      String sessionId, String uid) =>
      _post('/api/v1/interview/complete', {'sessionId': sessionId, 'uid': uid},
          timeout: const Duration(seconds: 180));

  Future<Map<String, dynamic>> getInterviewHistory(String uid) =>
      _get('/api/v1/interview/history?uid=$uid');

  Future<Map<String, dynamic>> createRealtimeSession({
    required String sessionId,
    required String uid,
    required int questionIndex,
    required String offerSdp,
    Map<String, dynamic>? candidateProfile,
  }) =>
      _post('/api/v1/interview/realtime/session', {
        'sessionId': sessionId,
        'uid': uid,
        'questionIndex': questionIndex,
        'offerSdp': offerSdp,
        if (candidateProfile != null) 'candidateProfile': candidateProfile,
      });

  Future<Map<String, dynamic>> createAvatarTalk(String text, {String? presenterId}) =>
      _post('/api/v1/avatar/talk', {
        'text': text,
        if (presenterId != null) 'presenterId': presenterId,
      });

  Future<Map<String, dynamic>> getAvatarTalkStatus(String talkId) =>
      _get('/api/v1/avatar/talk/$talkId');

  Future<List<int>> synthesizeQuestionSpeech(String text) async {
    final res = await http.post(
      Uri.parse('$kBaseUrl/api/v1/avatar/speech'),
      headers: _h,
      body: jsonEncode({'text': text}),
    ).timeout(const Duration(seconds: 15));
    if (res.statusCode >= 200 && res.statusCode < 300) {
      return res.bodyBytes;
    }
    throw ApiException(res.body, res.statusCode);
  }

  String questionSpeechUrl(String text) {
    final uri = Uri.parse('$kBaseUrl/api/v1/avatar/speech')
        .replace(queryParameters: {'text': text});
    return uri.toString();
  }

  // ── Reports ───────────────────────────────────────────────────────────────

  Future<Map<String, dynamic>> listReports(String uid) =>
      _get('/api/v1/report/list?uid=$uid');

  Future<Map<String, dynamic>> getReport(String reportId) =>
      _get('/api/v1/report/$reportId');

  // ── Admin ─────────────────────────────────────────────────────────────────

  Future<Map<String, dynamic>> getSystemStats() => _get('/api/v1/admin/stats');

  Future<Map<String, dynamic>> getAdminUsers() => _get('/api/v1/admin/users');

  Future<Map<String, dynamic>> updateUserRole(String uid, String role) =>
      _put('/api/v1/admin/users/$uid/role', {'role': role});

  Future<Map<String, dynamic>> deleteUser(String uid) =>
      _delete('/api/v1/admin/users/$uid');

  // ── Health ────────────────────────────────────────────────────────────────

  Future<bool> isBackendRunning() async {
    try {
      final res = await http.get(Uri.parse('$kBaseUrl/health'))
          .timeout(const Duration(seconds: 3));
      return res.statusCode == 200;
    } catch (_) {
      return false;
    }
  }
}

class ApiException implements Exception {
  final String message;
  final int statusCode;
  ApiException(this.message, this.statusCode);
  @override
  String toString() => 'ApiException($statusCode): $message';
}
