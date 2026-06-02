import 'package:flutter/material.dart';
import '../../theme/app_theme.dart';
import '../../services/auth_service.dart';
import '../../services/api_service.dart';

extension _LMI<T> on List<T> {
  List<R> mapIndexed<R>(R Function(int i, T item) f) =>
      List.generate(length, (i) => f(i, this[i]));
}

class PerformanceReportScreen extends StatefulWidget {
  const PerformanceReportScreen({super.key});
  @override
  State<PerformanceReportScreen> createState() => _PRState();
}

class _PRState extends State<PerformanceReportScreen> {
  List<dynamic> _reports = [];
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _loadReports();
  }

  Future<void> _loadReports() async {
    final uid = AuthService().uid;
    if (uid == null) { setState(() => _loading = false); return; }
    try {
      final res = await ApiService().listReports(uid);
      final reports = res['reports'] as List? ?? [];
      if (mounted) setState(() { _reports = reports; _loading = false; });
    } catch (e) {
      if (mounted) setState(() => _loading = false);
    }
  }

  String get _overallScore {
    if (_reports.isEmpty) return '0%';
    final scores = _reports.map((r) => (r['overallScore'] ?? 0) as num).toList();
    return '${(scores.reduce((a, b) => a + b) / scores.length).round()}%';
  }

  int get _totalSessions => _reports.length;

  String get _latestStrength {
    if (_reports.isEmpty || _reports.first is! Map) return 'No data';
    final strengths = (_reports.first as Map)['strengths'];
    if (strengths is List && strengths.isNotEmpty) return strengths.first.toString();
    return 'No data';
  }

  List<int> get _scoreTrend {
    if (_reports.isEmpty) return [];
    return _reports.take(12).map((r) => ((r['overallScore'] ?? 0) as num).round()).toList();
  }

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(24),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        _glassCard(padding: 22, child: LayoutBuilder(builder: (ctx, constraints) {
          final isNarrow = constraints.maxWidth < 420;
          final title = Column(crossAxisAlignment: CrossAxisAlignment.start, children: const [
            Text('Performance Reports', style: TextStyle(fontSize: 22, fontWeight: FontWeight.w800, color: AppTheme.textDark)),
            SizedBox(height: 4),
            Text('Track your interview performance over time', style: TextStyle(fontSize: 14, color: AppTheme.textGray)),
          ]);
          final exportBtn = ElevatedButton.icon(
            onPressed: () {},
            icon: const Icon(Icons.download_outlined),
            label: const Text('Export PDF'),
            style: ElevatedButton.styleFrom(backgroundColor: Colors.white, foregroundColor: AppTheme.textDark, side: BorderSide(color: Colors.grey.shade200), shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10))),
          );
          return isNarrow
              ? Column(crossAxisAlignment: CrossAxisAlignment.start, children: [title, const SizedBox(height: 14), exportBtn])
              : Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [Expanded(child: title), const SizedBox(width: 12), exportBtn]);
        })),
        const SizedBox(height: 20),

        if (_loading)
          const Center(child: Padding(padding: EdgeInsets.all(40), child: CircularProgressIndicator(color: AppTheme.primaryCyan)))
        else ...[
          LayoutBuilder(builder: (ctx, constraints) {
            final w = constraints.maxWidth;
            final cols = w >= 700 ? 3 : w >= 450 ? 2 : 1;
            const gap = 12.0;
            final cardW = (w - (gap * (cols - 1))) / cols;
            return Wrap(spacing: gap, runSpacing: gap, children: [
              _overviewCard('Overall Score', _overallScore, '', Icons.trending_up, AppTheme.primaryCyan, cardW),
              _overviewCard('Latest Strength', _latestStrength, '', Icons.chat_bubble_outline, AppTheme.primaryPurple, cardW),
              _overviewCard('Total Sessions', '$_totalSessions', '', Icons.people_outlined, AppTheme.successGreen, cardW),
            ]);
          }),
          const SizedBox(height: 20),

          _glassCard(padding: 22, child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [
              const Text('Score Trend', style: TextStyle(fontSize: 17, fontWeight: FontWeight.w700, color: AppTheme.textDark)),
              Row(children: [_legendDot('Score', AppTheme.primaryCyan), const SizedBox(width: 14), _legendDot('Target', AppTheme.primaryPurple)]),
            ]),
            const SizedBox(height: 18),
            _simulatedChart(_scoreTrend),
          ])),
          const SizedBox(height: 20),

          LayoutBuilder(builder: (ctx, constraints) {
            if (constraints.maxWidth < 600) {
              return Column(crossAxisAlignment: CrossAxisAlignment.start, children: [_skillBreakdownCard(), const SizedBox(height: 20), _recentSessionsCard()]);
            }
            return Row(crossAxisAlignment: CrossAxisAlignment.start, children: [Expanded(child: _skillBreakdownCard()), const SizedBox(width: 18), Expanded(child: _recentSessionsCard())]);
          }),
          const SizedBox(height: 20),
          _questionScoresCard(),
        ],
      ]),
    );
  }

  Widget _questionScoresCard() {
    final latest = _reports.isNotEmpty ? _reports.first : null;
    final scores = latest is Map ? latest['questionScores'] as List? ?? [] : [];
    final strengths = latest is Map ? latest['strengths'] as List? ?? [] : [];
    final improvements = latest is Map ? latest['improvements'] as List? ?? [] : [];

    if (scores.isEmpty && strengths.isEmpty && improvements.isEmpty) {
      return const SizedBox.shrink();
    }

    return _glassCard(padding: 22, child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      const Text('Latest Evaluation', style: TextStyle(fontSize: 17, fontWeight: FontWeight.w700, color: AppTheme.textDark)),
      const SizedBox(height: 14),
      if (strengths.isNotEmpty)
        Text('Strengths: ${strengths.join(', ')}', style: const TextStyle(fontSize: 13, color: AppTheme.textDark)),
      if (improvements.isNotEmpty) ...[
        const SizedBox(height: 8),
        Text('Improve: ${improvements.join(', ')}', style: const TextStyle(fontSize: 13, color: AppTheme.textGray)),
      ],
      if (scores.isNotEmpty) ...[
        const SizedBox(height: 14),
        ...scores.take(5).map((item) {
          final score = item is Map ? item['overallScore'] ?? item['relevanceScore'] ?? '-' : '-';
          final feedback = item is Map ? item['feedback']?.toString() ?? '' : '';
          final question = item is Map ? item['questionText']?.toString() ?? 'Question' : 'Question';
          return Padding(
            padding: const EdgeInsets.only(bottom: 10),
            child: Container(
              width: double.infinity,
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(color: Colors.white.withOpacity(0.6), borderRadius: BorderRadius.circular(10)),
              child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                Text(question, maxLines: 2, overflow: TextOverflow.ellipsis, style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w600, color: AppTheme.textDark)),
                const SizedBox(height: 6),
                Text('Score: $score%  $feedback', style: const TextStyle(fontSize: 12, color: AppTheme.textGray)),
              ]),
            ),
          );
        }),
      ],
    ]));
  }

  Widget _skillBreakdownCard() {
    final latest = _reports.isNotEmpty && _reports.first is Map ? _reports.first as Map : null;
    final scores = latest?['questionScores'] as List? ?? [];
    final metrics = scores.isEmpty
        ? <List<dynamic>>[]
        : [
            ['Relevance', _averageMetric(scores, 'relevanceScore') / 100, AppTheme.primaryCyan],
            ['Clarity', _averageMetric(scores, 'clarityScore') / 100, AppTheme.primaryPurple],
            ['Completeness', _averageMetric(scores, 'completenessScore') / 100, AppTheme.successGreen],
          ];

    return _glassCard(padding: 22, child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      const Text('Skill Breakdown', style: TextStyle(fontSize: 17, fontWeight: FontWeight.w700, color: AppTheme.textDark)),
      const SizedBox(height: 18),
      if (metrics.isEmpty)
        const Text('No evaluated answers yet.', style: TextStyle(fontSize: 13, color: AppTheme.textGray))
      else
        ...metrics.map((s) => Padding(padding: const EdgeInsets.only(bottom: 14), child: Column(children: [
          Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [
            Text(s[0] as String, style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w600, color: AppTheme.textDark)),
            Text('${((s[1] as double) * 100).round()}%', style: TextStyle(fontSize: 14, fontWeight: FontWeight.w700, color: s[2] as Color)),
          ]),
          const SizedBox(height: 6),
          ClipRRect(borderRadius: BorderRadius.circular(4), child: LinearProgressIndicator(value: s[1] as double, minHeight: 8, backgroundColor: Colors.grey.shade100, valueColor: AlwaysStoppedAnimation(s[2] as Color))),
        ]))),
    ]));
  }

  Widget _recentSessionsCard() {
    final sessions = _reports.isNotEmpty
        ? _reports.take(5).map((r) {
      final score = (r['overallScore'] ?? 0) as num;
      final color = score >= 80 ? AppTheme.successGreen : score >= 65 ? const Color(0xFFF59E0B) : AppTheme.errorRed;
      final date = r['createdAt']?.toString().split('T').first ?? '—';
      return [r['sessionId'] ?? 'Session', '${score.round()}%', date, color];
    }).toList()
        : [];

    return _glassCard(padding: 22, child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      const Text('Recent Sessions', style: TextStyle(fontSize: 17, fontWeight: FontWeight.w700, color: AppTheme.textDark)),
      const SizedBox(height: 14),
      if (sessions.isEmpty)
        const Text('No completed sessions yet.', style: TextStyle(fontSize: 13, color: AppTheme.textGray))
      else
        ...sessions.map((s) => Padding(padding: const EdgeInsets.only(bottom: 8), child: Container(
        decoration: BoxDecoration(color: Colors.white.withOpacity(0.6), borderRadius: BorderRadius.circular(10)),
        padding: const EdgeInsets.all(12),
        child: Row(children: [
          Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Text(s[0] as String, style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w600, color: AppTheme.textDark)),
            Text(s[2] as String, style: const TextStyle(fontSize: 11, color: AppTheme.textGray)),
          ])),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
            decoration: BoxDecoration(color: (s[3] as Color).withOpacity(0.1), borderRadius: BorderRadius.circular(14)),
            child: Text(s[1] as String, style: TextStyle(fontSize: 13, fontWeight: FontWeight.w700, color: s[3] as Color)),
          ),
        ]),
      ))),
    ]));
  }

  Widget _overviewCard(String title, String value, String sub, IconData icon, Color color, double width) =>
      SizedBox(width: width, child: _glassCard(padding: 18, child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [
          Container(width: 40, height: 40, decoration: BoxDecoration(color: color.withOpacity(0.1), borderRadius: BorderRadius.circular(10)), child: Icon(icon, color: color, size: 21)),
          if (sub.isNotEmpty)
            Container(padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3), decoration: BoxDecoration(color: AppTheme.successGreen.withOpacity(0.1), borderRadius: BorderRadius.circular(12)),
                child: Text(sub, style: const TextStyle(fontSize: 11, fontWeight: FontWeight.w600, color: AppTheme.successGreen))),
        ]),
        const SizedBox(height: 8),
        Text(value, style: const TextStyle(fontSize: 22, fontWeight: FontWeight.w800, color: AppTheme.textDark)),
        const SizedBox(height: 2),
        Text(title, style: const TextStyle(fontSize: 12, color: AppTheme.textGray)),
      ])));

  Widget _legendDot(String label, Color color) => Row(children: [
    Container(width: 10, height: 10, decoration: BoxDecoration(color: color, borderRadius: BorderRadius.circular(5))),
    const SizedBox(width: 5),
    Text(label, style: const TextStyle(fontSize: 12, color: AppTheme.textGray)),
  ]);

  Widget _simulatedChart(List<int> scores) {
    const max = 100.0;
    const target = 80.0;
    if (scores.isEmpty) {
      return const SizedBox(
        height: 170,
        child: Center(child: Text('No score trend yet.', style: TextStyle(fontSize: 13, color: AppTheme.textGray))),
      );
    }
    return SizedBox(height: 170, child: Row(crossAxisAlignment: CrossAxisAlignment.end, children: [
      const Column(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [
        Text('100', style: TextStyle(fontSize: 10, color: AppTheme.textGray)),
        Text('75',  style: TextStyle(fontSize: 10, color: AppTheme.textGray)),
        Text('50',  style: TextStyle(fontSize: 10, color: AppTheme.textGray)),
        Text('25',  style: TextStyle(fontSize: 10, color: AppTheme.textGray)),
        Text('0',   style: TextStyle(fontSize: 10, color: AppTheme.textGray)),
      ]),
      const SizedBox(width: 10),
      Expanded(child: Stack(children: [
        Positioned(top: (1 - target / max) * 170, left: 0, right: 0, child: Container(height: 1, color: AppTheme.primaryPurple.withOpacity(0.4))),
        Row(mainAxisAlignment: MainAxisAlignment.spaceAround, crossAxisAlignment: CrossAxisAlignment.end, children: scores.map((s) => Column(mainAxisAlignment: MainAxisAlignment.end, children: [
          Text('$s', style: const TextStyle(fontSize: 9, color: AppTheme.textGray)),
          const SizedBox(height: 2),
          Container(width: 26, height: (s / max) * 145, decoration: BoxDecoration(
            gradient: const LinearGradient(colors: [AppTheme.primaryCyan, AppTheme.primaryPurple], begin: Alignment.bottomCenter, end: Alignment.topCenter),
            borderRadius: const BorderRadius.only(topLeft: Radius.circular(4), topRight: Radius.circular(4)),
          )),
        ])).toList()),
      ])),
    ]));
  }

  double _averageMetric(List<dynamic> scores, String key) {
    final values = scores
        .whereType<Map>()
        .map((s) => s[key])
        .whereType<num>()
        .toList();
    if (values.isEmpty) return 0;
    return (values.reduce((a, b) => a + b) / values.length).toDouble();
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
