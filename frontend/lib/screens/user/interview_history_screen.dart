import 'package:flutter/material.dart';
import '../../theme/app_theme.dart';
import '../../services/auth_service.dart';
import '../../services/api_service.dart';

extension _LMI<T> on List<T> {
  List<R> mapIndexed<R>(R Function(int i, T item) f) =>
      List.generate(length, (i) => f(i, this[i]));
}

class InterviewHistoryScreen extends StatefulWidget {
  const InterviewHistoryScreen({super.key});
  @override
  State<InterviewHistoryScreen> createState() => _IHState();
}

class _IHState extends State<InterviewHistoryScreen> {
  int _selectedFilter = 0;
  final _filters = ['All', 'Software Eng.', 'Data Science', 'Product Mgmt', 'UI/UX'];

  List<Map<String, dynamic>> _history = [];
  bool _loading = true;

  static const _staticHistory = [
    ['Software Engineer – Behavioral', '82%', 'Jan 30, 2026', '18 min', Icons.check_circle_outlined, AppTheme.successGreen, 'Strong use of STAR method. Improve on quantifying results.'],
    ['Data Scientist – Technical', '74%', 'Jan 28, 2026', '22 min', Icons.warning_outlined, Color(0xFFF59E0B), 'Good statistical knowledge. Practice ML algorithm explanations.'],
    ['Product Manager – Case Study', '88%', 'Jan 26, 2026', '25 min', Icons.check_circle_outlined, AppTheme.successGreen, 'Excellent product thinking. Very structured approach.'],
    ['DevOps Engineer – System Design', '61%', 'Jan 24, 2026', '20 min', Icons.error_outlined, AppTheme.errorRed, 'Review containerization and CI/CD pipeline concepts.'],
    ['UI/UX Designer – Portfolio', '79%', 'Jan 22, 2026', '15 min', Icons.warning_outlined, Color(0xFFF59E0B), 'Creative solutions but need more user-centric reasoning.'],
  ];

  @override
  void initState() {
    super.initState();
    _loadHistory();
  }

  Future<void> _loadHistory() async {
    final uid = AuthService().uid;
    if (uid == null) { setState(() => _loading = false); return; }
    try {
      final res = await ApiService().getInterviewHistory(uid);
      final sessions = (res['sessions'] as List? ?? []).cast<Map<String, dynamic>>();
      if (mounted) setState(() { _history = sessions; _loading = false; });
    } catch (e) {
      if (mounted) setState(() => _loading = false);
    }
  }

  List<dynamic> _sessionToRow(Map<String, dynamic> s) {
    final skills = s['skills'] is List ? (s['skills'] as List).take(2).join(' & ') : 'Interview';
    final score = s['score'] ?? s['overallScore'] ?? 0;
    final scoreStr = '$score%';
    final date = s['startTime']?.toString().split('T').first ?? '—';
    final scoreNum = score is int ? score : (score as num).toInt();
    final statusIcon = scoreNum >= 80 ? Icons.check_circle_outlined : scoreNum >= 65 ? Icons.warning_outlined : Icons.error_outlined;
    final statusColor = scoreNum >= 80 ? AppTheme.successGreen : scoreNum >= 65 ? const Color(0xFFF59E0B) : AppTheme.errorRed;
    final feedback = s['summary'] ?? 'Tap to view full performance report.';
    return [skills, scoreStr, date, '~20 min', statusIcon, statusColor, feedback];
  }

  List<dynamic> get _displayHistory {
    if (_history.isNotEmpty) return _history.map(_sessionToRow).toList();
    return _staticHistory;
  }

  int get _totalSessions => _history.isNotEmpty ? _history.length : 12;
  String get _avgScore {
    if (_history.isEmpty) return '78%';
    final scores = _history.map((s) => (s['score'] ?? s['overallScore'] ?? 0) as num).toList();
    return '${(scores.reduce((a, b) => a + b) / scores.length).round()}%';
  }
  String get _bestScore {
    if (_history.isEmpty) return '88%';
    final scores = _history.map((s) => (s['score'] ?? s['overallScore'] ?? 0) as num).toList();
    return '${scores.reduce((a, b) => a > b ? a : b).round()}%';
  }

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(24),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        _glassCard(padding: 22, child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: const [
          Text('Interview History', style: TextStyle(fontSize: 22, fontWeight: FontWeight.w800, color: AppTheme.textDark)),
          SizedBox(height: 4),
          Text('Review your past interview sessions and feedback', style: TextStyle(fontSize: 14, color: AppTheme.textGray)),
        ])),
        const SizedBox(height: 18),

        LayoutBuilder(builder: (ctx, constraints) {
          final w = constraints.maxWidth;
          final cols = w >= 700 ? 4 : w >= 450 ? 2 : 1;
          const gap = 12.0;
          final cardW = (w - (gap * (cols - 1))) / cols;
          return Wrap(spacing: gap, runSpacing: gap, children: [
            _summaryCard('Total Sessions', '$_totalSessions', Icons.people_outlined, AppTheme.primaryCyan, cardW),
            _summaryCard('Average Score', _avgScore, Icons.trending_up_outlined, AppTheme.primaryPurple, cardW),
            _summaryCard('Best Score', _bestScore, Icons.star_outlined, AppTheme.successGreen, cardW),
            _summaryCard('Hours Practiced', '8.5h', Icons.access_time_outlined, const Color(0xFFF59E0B), cardW),
          ]);
        }),
        const SizedBox(height: 18),

        Wrap(spacing: 8, runSpacing: 8, children: _filters.mapIndexed((i, f) => GestureDetector(
          onTap: () => setState(() => _selectedFilter = i),
          child: Container(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
            decoration: BoxDecoration(
              color: i == _selectedFilter ? AppTheme.primaryCyan.withOpacity(0.1) : Colors.white.withOpacity(0.7),
              border: Border.all(color: i == _selectedFilter ? AppTheme.primaryCyan : Colors.grey.shade200),
              borderRadius: BorderRadius.circular(20),
            ),
            child: Text(f, style: TextStyle(fontSize: 13, fontWeight: FontWeight.w600, color: i == _selectedFilter ? AppTheme.primaryCyan : AppTheme.textGray)),
          ),
        )).toList()),
        const SizedBox(height: 16),

        if (_loading)
          const Center(child: Padding(padding: EdgeInsets.all(40), child: CircularProgressIndicator(color: AppTheme.primaryCyan)))
        else
          ..._displayHistory.map((h) => _historyCard(h as List<dynamic>)).toList(),
      ]),
    );
  }

  Widget _summaryCard(String label, String value, IconData icon, Color color, double width) =>
      SizedBox(width: width, child: _glassCard(padding: 16, child: Row(children: [
        Container(width: 42, height: 42, decoration: BoxDecoration(color: color.withOpacity(0.1), borderRadius: BorderRadius.circular(10)), child: Icon(icon, color: color, size: 21)),
        const SizedBox(width: 12),
        Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Text(value, style: const TextStyle(fontSize: 20, fontWeight: FontWeight.w800, color: AppTheme.textDark)),
          Text(label, style: const TextStyle(fontSize: 12, color: AppTheme.textGray)),
        ])),
      ])));

  Widget _historyCard(List<dynamic> h) {
    final scoreColor = h[5] is Color ? h[5] as Color : Color(h[5] as int);
    return Padding(
      padding: const EdgeInsets.only(bottom: 10),
      child: _glassCard(padding: 16, child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Row(children: [
          Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text(h[0] as String, style: const TextStyle(fontSize: 15, fontWeight: FontWeight.w700, color: AppTheme.textDark)),
            const SizedBox(height: 4),
            Wrap(spacing: 10, children: [
              Row(mainAxisSize: MainAxisSize.min, children: [const Icon(Icons.calendar_today_outlined, size: 13, color: AppTheme.textGray), const SizedBox(width: 4), Text(h[2] as String, style: const TextStyle(fontSize: 12, color: AppTheme.textGray))]),
              Row(mainAxisSize: MainAxisSize.min, children: [const Icon(Icons.access_time_outlined, size: 13, color: AppTheme.textGray), const SizedBox(width: 4), Text(h[3] as String, style: const TextStyle(fontSize: 12, color: AppTheme.textGray))]),
            ]),
          ])),
          Row(children: [
            Icon(h[4] as IconData, color: scoreColor, size: 20),
            const SizedBox(width: 8),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 5),
              decoration: BoxDecoration(color: scoreColor.withOpacity(0.1), borderRadius: BorderRadius.circular(16)),
              child: Text(h[1] as String, style: TextStyle(fontSize: 14, fontWeight: FontWeight.w700, color: scoreColor)),
            ),
          ]),
        ]),
        const SizedBox(height: 10),
        Container(
          padding: const EdgeInsets.all(10),
          decoration: BoxDecoration(color: Colors.white.withOpacity(0.5), borderRadius: BorderRadius.circular(8)),
          child: Row(children: [
            const Icon(Icons.feedback_outlined, size: 15, color: AppTheme.textGray),
            const SizedBox(width: 8),
            Expanded(child: Text(h[6] as String, style: const TextStyle(fontSize: 13, color: AppTheme.textGray))),
          ]),
        ),
      ])),
    );
  }
}

Widget _glassCard({required Widget child, double padding = 20}) {
  return Container(
    decoration: BoxDecoration(
      color: Colors.white.withOpacity(0.75),
      borderRadius: BorderRadius.circular(18),
      border: Border.all(color: Colors.white.withOpacity(0.8), width: 1.5),
      boxShadow: [BoxShadow(color: Colors.black.withOpacity(0.08), blurRadius: 24, offset: const Offset(0, 6))],
    ),
    padding: EdgeInsets.all(padding),
    child: child,
  );
}