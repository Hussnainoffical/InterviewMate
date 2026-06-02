import 'package:flutter/material.dart';
import '../../theme/app_theme.dart';
import '../../services/api_service.dart';

extension _ListMapIndexed<T> on List<T> {
  List<R> mapIndexed<R>(R Function(int index, T item) f) =>
      List.generate(length, (i) => f(i, this[i]));
}

class SystemStatisticsScreen extends StatefulWidget {
  const SystemStatisticsScreen({super.key});
  @override
  State<SystemStatisticsScreen> createState() => _SSState();
}

class _SSState extends State<SystemStatisticsScreen> {
  Map<String, dynamic> _stats = {};
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _loadStats();
  }

  Future<void> _loadStats() async {
    try {
      final res = await ApiService().getSystemStats();
      if (mounted) setState(() { _stats = res; _loading = false; });
    } catch (e) {
      if (mounted) setState(() => _loading = false);
    }
  }

  String _stat(String key, String fallback) =>
      _stats[key]?.toString() ?? fallback;

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(32),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        const Text('System Statistics', style: TextStyle(fontSize: 26, fontWeight: FontWeight.w800, color: AppTheme.textDark)),
        const SizedBox(height: 6),
        const Text('Platform-wide metrics and analytics', style: TextStyle(fontSize: 14, color: AppTheme.textGray)),
        const SizedBox(height: 24),

        // Date filter chips
        Row(children: [
          _dateChip('7D', true),
          const SizedBox(width: 6),
          _dateChip('30D', false),
          const SizedBox(width: 6),
          _dateChip('90D', false),
        ]),
        const SizedBox(height: 24),

        if (_loading)
          const Center(child: Padding(padding: EdgeInsets.all(60), child: CircularProgressIndicator(color: AppTheme.primaryCyan)))
        else ...[
          // ── KPI Row ───────────────────────────────────────────
          LayoutBuilder(builder: (context, constraints) {
            if (constraints.maxWidth < 900) {
              return Column(children: [
                _kpi('Total Users', _stat('totalUsers', '1,248'), Icons.people_outlined, AppTheme.primaryCyan, '+47 this week'),
                const SizedBox(height: 14),
                _kpi('Sessions Today', _stat('activeSessionsToday', '84'), Icons.play_circle_outlined, AppTheme.primaryPurple, '+12 vs yesterday'),
                const SizedBox(height: 14),
                _kpi('Avg Score', _stat('avgScore', '78%'), Icons.trending_up_outlined, AppTheme.successGreen, '+2% this week'),
                const SizedBox(height: 14),
                _kpi('Server Uptime', _stat('serverUptime', '99.9%'), Icons.cloud_outlined, const Color(0xFF06B6D4), 'Last 30 days'),
              ]);
            }
            return Row(children: [
              Expanded(child: _kpi('Total Users', _stat('totalUsers', '1,248'), Icons.people_outlined, AppTheme.primaryCyan, '+47 this week')),
              const SizedBox(width: 14),
              Expanded(child: _kpi('Sessions Today', _stat('activeSessionsToday', '84'), Icons.play_circle_outlined, AppTheme.primaryPurple, '+12 vs yesterday')),
              const SizedBox(width: 14),
              Expanded(child: _kpi('Avg Score', _stat('avgScore', '78%'), Icons.trending_up_outlined, AppTheme.successGreen, '+2% this week')),
              const SizedBox(width: 14),
              Expanded(child: _kpi('Server Uptime', _stat('serverUptime', '99.9%'), Icons.cloud_outlined, const Color(0xFF06B6D4), 'Last 30 days')),
            ]);
          }),
          const SizedBox(height: 28),

          // ── Charts Row ────────────────────────────────────────
          LayoutBuilder(builder: (context, constraints) {
            if (constraints.maxWidth < 900) {
              return Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                _sessionsChart(), const SizedBox(height: 20), _roleDistributionChart(),
              ]);
            }
            return Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Expanded(child: _sessionsChart()),
              const SizedBox(width: 20),
              SizedBox(width: 320, child: _roleDistributionChart()),
            ]);
          }),
          const SizedBox(height: 24),

          // ── Score Trend ───────────────────────────────────────
          Container(
            decoration: AppTheme.glassCard,
            padding: const EdgeInsets.all(24),
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [
                const Flexible(child: Text('Platform Average Score Trend', style: TextStyle(fontSize: 17, fontWeight: FontWeight.w700, color: AppTheme.textDark))),
                const SizedBox(width: 12),
                Wrap(spacing: 16, children: [_legendDot('Score', AppTheme.primaryCyan), _legendDot('Target (80%)', AppTheme.primaryPurple)]),
              ]),
              const SizedBox(height: 18),
              _lineChart(labels: ['Week 1', 'Week 2', 'Week 3', 'Week 4', 'Week 5', 'Week 6', 'Week 7', 'Week 8'], values: [62, 65, 68, 71, 74, 76, 78, 78], target: 80),
            ]),
          ),
          const SizedBox(height: 24),

          // ── Bottom Row ────────────────────────────────────────
          LayoutBuilder(builder: (context, constraints) {
            if (constraints.maxWidth < 900) {
              return Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                _topPerformersCard(), const SizedBox(height: 20), _systemHealthCard(),
              ]);
            }
            return Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Expanded(child: _topPerformersCard()),
              const SizedBox(width: 20),
              SizedBox(width: 300, child: _systemHealthCard()),
            ]);
          }),
        ],
      ]),
    );
  }

  Widget _sessionsChart() => Container(
    decoration: AppTheme.glassCard,
    padding: const EdgeInsets.all(24),
    child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [
        const Text('Daily Sessions', style: TextStyle(fontSize: 17, fontWeight: FontWeight.w700, color: AppTheme.textDark)),
        Wrap(spacing: 16, children: [_legendDot('Completed', AppTheme.primaryCyan), _legendDot('Target', AppTheme.primaryPurple.withOpacity(0.4))]),
      ]),
      const SizedBox(height: 20),
      _barChart(labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'], values: [42, 58, 51, 67, 74, 38, 29], max: 100),
    ]),
  );

  Widget _roleDistributionChart() => Container(
    decoration: AppTheme.glassCard,
    padding: const EdgeInsets.all(24),
    child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      const Text('Role Distribution', style: TextStyle(fontSize: 17, fontWeight: FontWeight.w700, color: AppTheme.textDark)),
      const SizedBox(height: 20),
      _donutChart(),
    ]),
  );

  Widget _topPerformersCard() => Container(
    decoration: AppTheme.glassCard,
    padding: const EdgeInsets.all(24),
    child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      const Text('Top Performers', style: TextStyle(fontSize: 17, fontWeight: FontWeight.w700, color: AppTheme.textDark)),
      const SizedBox(height: 16),
      _performerRow('Ahmed Khan', 94, 1), const SizedBox(height: 10),
      _performerRow('Fatima Ali', 92, 2), const SizedBox(height: 10),
      _performerRow('Hassan Malik', 89, 3), const SizedBox(height: 10),
      _performerRow('Ayesha Noor', 87, 4), const SizedBox(height: 10),
      _performerRow('Usman Sheikh', 85, 5),
    ]),
  );

  Widget _performerRow(String name, int score, int rank) {
    final colors = [const Color(0xFFFFD700), const Color(0xFFC0C0C0), const Color(0xFFCD7F32), AppTheme.textGray, AppTheme.textGray];
    return Row(children: [
      Container(width: 32, height: 32, decoration: BoxDecoration(color: colors[rank - 1].withOpacity(0.15), borderRadius: BorderRadius.circular(16)),
          child: Center(child: Text('$rank', style: TextStyle(fontSize: 13, fontWeight: FontWeight.w700, color: colors[rank - 1])))),
      const SizedBox(width: 12),
      Expanded(child: Text(name, style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w600, color: AppTheme.textDark))),
      Container(padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
          decoration: BoxDecoration(gradient: AppTheme.primaryGradient, borderRadius: BorderRadius.circular(8)),
          child: Text('$score%', style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w700, color: Colors.white))),
    ]);
  }

  Widget _systemHealthCard() => Container(
    decoration: AppTheme.glassCard,
    padding: const EdgeInsets.all(24),
    child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      const Text('System Health', style: TextStyle(fontSize: 17, fontWeight: FontWeight.w700, color: AppTheme.textDark)),
      const SizedBox(height: 18),
      _healthMetric('CPU Usage', 34, AppTheme.successGreen), const SizedBox(height: 14),
      _healthMetric('Memory', 58, AppTheme.primaryCyan), const SizedBox(height: 14),
      _healthMetric('Disk I/O', 72, const Color(0xFFF59E0B)), const SizedBox(height: 14),
      _healthMetric('Network', 23, AppTheme.successGreen),
    ]),
  );

  Widget _kpi(String label, String value, IconData icon, Color color, String sub) => Container(
    padding: const EdgeInsets.all(20),
    decoration: AppTheme.glassCard,
    child: Row(children: [
      Container(width: 52, height: 52,
          decoration: BoxDecoration(gradient: LinearGradient(colors: [color, color.withOpacity(0.6)], begin: Alignment.topLeft, end: Alignment.bottomRight), borderRadius: BorderRadius.circular(14),
              boxShadow: [BoxShadow(color: color.withOpacity(0.25), blurRadius: 8)]),
          child: Icon(icon, color: Colors.white, size: 26)),
      const SizedBox(width: 16),
      Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Text(label, style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: AppTheme.textGray)),
        const SizedBox(height: 4),
        Text(value, style: const TextStyle(fontSize: 24, fontWeight: FontWeight.w800, color: AppTheme.textDark)),
        const SizedBox(height: 2),
        Text(sub, style: TextStyle(fontSize: 11, color: AppTheme.textGray.withOpacity(0.8))),
      ])),
    ]),
  );

  Widget _dateChip(String label, bool active) => Container(
    padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
    decoration: BoxDecoration(gradient: active ? AppTheme.primaryGradient : null, color: active ? null : Colors.grey.shade200, borderRadius: BorderRadius.circular(8)),
    child: Text(label, style: TextStyle(fontSize: 11, fontWeight: FontWeight.w700, color: active ? Colors.white : AppTheme.textGray)),
  );

  Widget _legendDot(String label, Color color) => Row(mainAxisSize: MainAxisSize.min, children: [
    Container(width: 10, height: 10, decoration: BoxDecoration(color: color, borderRadius: BorderRadius.circular(5))),
    const SizedBox(width: 6),
    Text(label, style: const TextStyle(fontSize: 11, color: AppTheme.textGray)),
  ]);

  Widget _healthMetric(String label, int percent, Color color) => Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
    Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [
      Text(label, style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w600, color: AppTheme.textDark)),
      Text('$percent%', style: TextStyle(fontSize: 13, fontWeight: FontWeight.w700, color: color)),
    ]),
    const SizedBox(height: 6),
    ClipRRect(borderRadius: BorderRadius.circular(8), child: LinearProgressIndicator(value: percent / 100, backgroundColor: Colors.grey.shade200, valueColor: AlwaysStoppedAnimation(color), minHeight: 6)),
  ]);

  Widget _barChart({required List<String> labels, required List<int> values, required int max}) {
    const chartH = 140.0;
    return SizedBox(height: chartH + 40, child: Row(mainAxisAlignment: MainAxisAlignment.spaceAround, crossAxisAlignment: CrossAxisAlignment.end, children: labels.mapIndexed((i, label) {
      final barH = (values[i] / max) * chartH;
      return Expanded(child: Column(mainAxisAlignment: MainAxisAlignment.end, children: [
        Text('${values[i]}', style: const TextStyle(fontSize: 9, color: AppTheme.textGray)),
        const SizedBox(height: 3),
        Container(width: 32, height: barH, decoration: BoxDecoration(gradient: const LinearGradient(colors: [AppTheme.primaryCyan, AppTheme.primaryPurple], begin: Alignment.bottomCenter, end: Alignment.topCenter), borderRadius: const BorderRadius.only(topLeft: Radius.circular(5), topRight: Radius.circular(5)))),
        const SizedBox(height: 6),
        Text(label, style: const TextStyle(fontSize: 10, color: AppTheme.textGray)),
      ]));
    }).toList()));
  }

  Widget _donutChart() {
    final roles = [
      ['Software Eng.', 38, AppTheme.primaryCyan],
      ['Data Science', 22, AppTheme.primaryPurple],
      ['Product Mgmt', 18, AppTheme.successGreen],
      ['UI/UX Design', 12, const Color(0xFFF59E0B)],
      ['DevOps', 10, const Color(0xFF8B5CF6)],
    ];
    return Row(children: [
      SizedBox(width: 120, height: 120, child: CustomPaint(painter: _DonutPainter(roles),
          child: Center(child: Column(mainAxisAlignment: MainAxisAlignment.center, children: [
            Text(_stat('totalUsers', '1,248'), style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w800, color: AppTheme.textDark)),
            const Text('users', style: TextStyle(fontSize: 10, color: AppTheme.textGray)),
          ])))),
      const SizedBox(width: 20),
      Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: roles.map((r) => Padding(padding: const EdgeInsets.only(bottom: 8), child: Row(children: [
        Container(width: 10, height: 10, decoration: BoxDecoration(color: r[2] as Color, borderRadius: BorderRadius.circular(5))),
        const SizedBox(width: 8),
        Expanded(child: Text(r[0] as String, style: const TextStyle(fontSize: 12, color: AppTheme.textDark))),
        Text('${r[1]}%', style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: AppTheme.textGray)),
      ]))).toList())),
    ]);
  }

  Widget _lineChart({required List<String> labels, required List<int> values, required int target}) {
    const max = 100;
    const chartH = 160.0;
    return SizedBox(height: chartH + 30, child: LayoutBuilder(builder: (context, constraints) {
      return Row(crossAxisAlignment: CrossAxisAlignment.end, children: [
        SizedBox(width: 30, child: Column(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: const [
          Text('100', style: TextStyle(fontSize: 10, color: AppTheme.textGray)),
          Text('75',  style: TextStyle(fontSize: 10, color: AppTheme.textGray)),
          Text('50',  style: TextStyle(fontSize: 10, color: AppTheme.textGray)),
          Text('25',  style: TextStyle(fontSize: 10, color: AppTheme.textGray)),
          Text('0',   style: TextStyle(fontSize: 10, color: AppTheme.textGray)),
        ])),
        const SizedBox(width: 10),
        Expanded(child: SizedBox(height: chartH, child: Stack(children: [
          Positioned(top: (1 - target / max) * chartH, left: 0, right: 0, child: Container(height: 1.5, color: AppTheme.primaryPurple.withOpacity(0.4))),
          Row(mainAxisAlignment: MainAxisAlignment.spaceAround, crossAxisAlignment: CrossAxisAlignment.end, children: labels.mapIndexed((i, label) {
            final dotY = (1 - values[i] / max) * chartH;
            return Expanded(child: Column(mainAxisAlignment: MainAxisAlignment.end, children: [
              Expanded(child: Stack(clipBehavior: Clip.none, children: [
                Positioned(top: dotY - 6, left: 0, right: 0, child: Column(mainAxisSize: MainAxisSize.min, children: [
                  Text('${values[i]}', style: const TextStyle(fontSize: 9, color: AppTheme.textGray)),
                  const SizedBox(height: 2),
                  Container(width: 12, height: 12, decoration: BoxDecoration(color: AppTheme.primaryCyan, shape: BoxShape.circle, border: Border.all(color: Colors.white, width: 2), boxShadow: [BoxShadow(color: AppTheme.primaryCyan.withOpacity(0.3), blurRadius: 4)])),
                ])),
              ])),
              const SizedBox(height: 6),
              Text(label, style: const TextStyle(fontSize: 9, color: AppTheme.textGray), overflow: TextOverflow.ellipsis, maxLines: 1),
            ]));
          }).toList()),
        ]))),
      ]);
    }));
  }
}

class _DonutPainter extends CustomPainter {
  final List<List<dynamic>> segments;
  _DonutPainter(this.segments);
  @override
  void paint(Canvas canvas, Size size) {
    final center = Offset(size.width / 2, size.height / 2);
    final radius = size.width / 2 - 4;
    double angle = -90.0;
    for (final seg in segments) {
      final sweep = (seg[1] as int) / 100.0 * 360.0;
      final paint = Paint()..color = seg[2] as Color..style = PaintingStyle.stroke..strokeWidth = 22..strokeCap = StrokeCap.round;
      canvas.drawArc(Rect.fromCircle(center: center, radius: radius), _toRad(angle), _toRad(sweep - 2), false, paint);
      angle += sweep;
    }
  }
  double _toRad(double deg) => deg * 3.14159265 / 180.0;
  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}