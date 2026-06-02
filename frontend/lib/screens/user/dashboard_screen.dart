import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import '../../theme/app_theme.dart';
import '../../services/auth_service.dart';
import '../../services/api_service.dart';

class UserDashboardScreen extends StatefulWidget {
  const UserDashboardScreen({super.key});
  @override
  State<UserDashboardScreen> createState() => _UserDashboardScreenState();
}

class _UserDashboardScreenState extends State<UserDashboardScreen> {
  String _userName = 'User';
  List<dynamic> _history = [];
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _loadData();
  }

  Future<void> _loadData() async {
    // 1. Load user name from AuthService (no Firebase needed)
    setState(() => _userName = AuthService().fullName ?? 'User');

    // 2. Load interview history from FastAPI backend
    final uid = AuthService().uid;
    if (uid != null) {
      try {
        final res = await ApiService().getInterviewHistory(uid);
        if (mounted) setState(() => _history = res['sessions'] ?? []);
      } catch (e) {
        debugPrint('Backend not available, using empty history: $e');
      }
    }

    if (mounted) setState(() => _loading = false);
  }

  String get _firstName => _userName.split(' ').first;

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(24),
      child: _loading
          ? const Center(
        child: Padding(
          padding: EdgeInsets.only(top: 80),
          child: CircularProgressIndicator(color: AppTheme.primaryCyan),
        ),
      )
          : _DashboardContent(userName: _firstName, history: _history),
    );
  }
}

// ═══════════════════════════════════════════════════════════════════════════
class _DashboardContent extends StatelessWidget {
  final String userName;
  final List<dynamic> history;
  const _DashboardContent({required this.userName, required this.history});

  @override
  Widget build(BuildContext context) {
    final totalSessions = history.length;
    final avgScore = history.isEmpty
        ? 0
        : (history
        .map((s) => (s['score'] ?? 0) as num)
        .reduce((a, b) => a + b) /
        history.length)
        .round();

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // ── Greeting ──────────────────────────────────────────
        _glassCard(
          padding: 22,
          child: LayoutBuilder(
            builder: (ctx, constraints) {
              final isNarrow = constraints.maxWidth < 480;
              final greeting = _buildGreeting(userName);
              final button = _buildStartButton(context);
              return isNarrow
                  ? Column(crossAxisAlignment: CrossAxisAlignment.start, children: [greeting, const SizedBox(height: 16), button])
                  : Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [Expanded(child: greeting), const SizedBox(width: 16), button]);
            },
          ),
        ),
        const SizedBox(height: 20),

        // ── KPI Cards ─────────────────────────────────────────
        LayoutBuilder(
          builder: (ctx, constraints) {
            final w = constraints.maxWidth;
            final cols = w >= 600 ? 4 : w >= 380 ? 2 : 1;
            const gap = 12.0;
            final cardW = (w - (gap * (cols - 1))) / cols;
            return Wrap(
              spacing: gap,
              runSpacing: gap,
              children: [
                _statCard('$totalSessions', 'Interviews', Icons.people_outlined, '+${totalSessions > 0 ? 1 : 0} this week', cardW),
                _statCard('$avgScore%', 'Avg Score', Icons.trending_up_outlined, 'Based on sessions', cardW),
                _statCard('8.5h', 'Practiced', Icons.access_time_outlined, 'This month', cardW),
                _statCard('5', 'Day Streak', Icons.local_fire_department_outlined, 'Keep it up!', cardW),
              ],
            );
          },
        ),
        const SizedBox(height: 20),

        // ── Quick Actions ─────────────────────────────────────
        const Text('Quick Actions', style: TextStyle(fontSize: 17, fontWeight: FontWeight.w700, color: AppTheme.textDark)),
        const SizedBox(height: 12),
        LayoutBuilder(
          builder: (ctx, constraints) {
            final w = constraints.maxWidth;
            final cols = w >= 600 ? 4 : w >= 380 ? 2 : 1;
            const gap = 12.0;
            final cardW = (w - (gap * (cols - 1))) / cols;
            return Wrap(
              spacing: gap,
              runSpacing: gap,
              children: [
                _actionCard(context, Icons.upload_outlined, 'Upload Resume', '/resume-upload', AppTheme.primaryCyan, cardW),
                _actionCard(context, Icons.mic_outlined, 'Mock Interview', '/interview-session', AppTheme.primaryPurple, cardW),
                _actionCard(context, Icons.bar_chart_outlined, 'View Reports', '/performance-report', const Color(0xFF06B6D4), cardW),
                _actionCard(context, Icons.history_outlined, 'Past Interviews', '/interview-history', const Color(0xFF8B5CF6), cardW),
              ],
            );
          },
        ),
        const SizedBox(height: 20),

        // ── Activity + Skills ─────────────────────────────────
        LayoutBuilder(
          builder: (ctx, constraints) {
            if (constraints.maxWidth < 600) {
              return Column(crossAxisAlignment: CrossAxisAlignment.start, children: [_activityColumn(context), const SizedBox(height: 20), _skillsColumn()]);
            }
            return Row(crossAxisAlignment: CrossAxisAlignment.start, children: [Expanded(child: _activityColumn(context)), const SizedBox(width: 20), Expanded(child: _skillsColumn())]);
          },
        ),
      ],
    );
  }

  Widget _buildGreeting(String name) => Column(
    crossAxisAlignment: CrossAxisAlignment.start,
    children: [
      Text('Good Morning, $name 👋', style: const TextStyle(fontSize: 20, fontWeight: FontWeight.w700, color: AppTheme.textDark)),
      const SizedBox(height: 4),
      const Text("Here's your interview journey overview", style: TextStyle(fontSize: 14, color: AppTheme.textGray)),
    ],
  );

  Widget _buildStartButton(BuildContext context) => ElevatedButton.icon(
    onPressed: () => context.go('/interview-session'),
    icon: const Icon(Icons.play_circle_outlined),
    label: const Text('Start Interview'),
    style: ElevatedButton.styleFrom(
      backgroundColor: AppTheme.primaryCyan, foregroundColor: Colors.white,
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      padding: const EdgeInsets.symmetric(horizontal: 22, vertical: 12),
    ),
  );

  Widget _activityColumn(BuildContext context) {
    final items = history.isNotEmpty
        ? history.take(5).map((s) {
      final role = s['skills'] is List ? (s['skills'] as List).take(2).join(' & ') : 'Interview';
      final score = s['score'] ?? s['overallScore'] ?? '—';
      return ['Completed $role Interview — Score: $score%', s['startTime'] ?? 'Recently', Icons.check_circle_outlined, AppTheme.successGreen];
    }).toList()
        : [
      ['Completed Software Engineer Interview', '2 hours ago', Icons.check_circle_outlined, AppTheme.successGreen],
      ['Uploaded new resume', 'Yesterday', Icons.document_scanner_outlined, AppTheme.primaryCyan],
      ['Practiced Data Structures Q&A', 'Yesterday', Icons.lightbulb_outlined, AppTheme.primaryPurple],
      ['Achieved 5-day streak!', '2 days ago', Icons.local_fire_department_outlined, const Color(0xFFF59E0B)],
      ['Reviewed performance report', '3 days ago', Icons.bar_chart_outlined, const Color(0xFF06B6D4)],
    ];

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text('Recent Activity', style: TextStyle(fontSize: 17, fontWeight: FontWeight.w700, color: AppTheme.textDark)),
        const SizedBox(height: 12),
        ...items.map((a) => _activityItem(a)).toList(),
      ],
    );
  }

  Widget _skillsColumn() => Column(
    crossAxisAlignment: CrossAxisAlignment.start,
    children: [
      const Text('Skills Progress', style: TextStyle(fontSize: 17, fontWeight: FontWeight.w700, color: AppTheme.textDark)),
      const SizedBox(height: 12),
      _glassCard(padding: 20, child: Column(children: [
        _skillBar('Communication', 0.78, AppTheme.primaryCyan),
        const SizedBox(height: 16),
        _skillBar('Technical', 0.65, AppTheme.primaryPurple),
        const SizedBox(height: 16),
        _skillBar('Problem Solving', 0.82, AppTheme.successGreen),
        const SizedBox(height: 16),
        _skillBar('Leadership', 0.55, const Color(0xFFF59E0B)),
      ])),
    ],
  );

  Widget _statCard(String value, String label, IconData icon, String sub, double width) =>
      SizedBox(width: width, child: _glassCard(padding: 18, child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [
          Text(value, style: const TextStyle(fontSize: 26, fontWeight: FontWeight.w800, color: AppTheme.textDark)),
          Container(width: 40, height: 40,
              decoration: BoxDecoration(color: AppTheme.primaryCyan.withOpacity(0.1), borderRadius: BorderRadius.circular(10)),
              child: Icon(icon, color: AppTheme.primaryCyan, size: 21)),
        ]),
        const SizedBox(height: 6),
        Text(label, style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w600, color: AppTheme.textDark)),
        const SizedBox(height: 2),
        Text(sub, style: const TextStyle(fontSize: 11, color: AppTheme.textGray)),
      ])));

  Widget _actionCard(BuildContext ctx, IconData icon, String label, String route, Color color, double width) =>
      SizedBox(width: width, child: GestureDetector(
        onTap: () => ctx.go(route),
        child: _glassCard(padding: 18, child: Column(children: [
          Container(width: 46, height: 46,
              decoration: BoxDecoration(color: color.withOpacity(0.1), borderRadius: BorderRadius.circular(12)),
              child: Icon(icon, color: color, size: 23)),
          const SizedBox(height: 10),
          Text(label, style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w600, color: AppTheme.textDark), textAlign: TextAlign.center),
        ])),
      ));

  Widget _activityItem(List<dynamic> a) => Padding(
    padding: const EdgeInsets.only(bottom: 10),
    child: _glassCard(padding: 14, child: Row(children: [
      Container(width: 38, height: 38,
          decoration: BoxDecoration(color: (a[3] as Color).withOpacity(0.1), borderRadius: BorderRadius.circular(10)),
          child: Icon(a[2] as IconData, color: a[3] as Color, size: 20)),
      const SizedBox(width: 12),
      Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Text(a[0] as String, style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w600, color: AppTheme.textDark)),
        Text(a[1] as String, style: const TextStyle(fontSize: 11, color: AppTheme.textGray)),
      ])),
    ])),
  );

  Widget _skillBar(String name, double pct, Color color) => Column(children: [
    Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [
      Text(name, style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w600, color: AppTheme.textDark)),
      Text('${(pct * 100).toInt()}%', style: TextStyle(fontSize: 13, fontWeight: FontWeight.w700, color: color)),
    ]),
    const SizedBox(height: 6),
    ClipRRect(borderRadius: BorderRadius.circular(4), child: LinearProgressIndicator(
      value: pct, minHeight: 8, backgroundColor: Colors.grey.shade100,
      valueColor: AlwaysStoppedAnimation(color),
    )),
  ]);
}

Widget _glassCard({required Widget child, double padding = 20}) {
  return Container(
    decoration: BoxDecoration(
      color: Colors.white.withOpacity(0.75),
      borderRadius: BorderRadius.circular(18),
      border: Border.all(color: Colors.white.withOpacity(0.8), width: 1.5),
      boxShadow: [
        BoxShadow(color: Colors.black.withOpacity(0.08), blurRadius: 24, offset: const Offset(0, 6)),
        BoxShadow(color: Colors.white.withOpacity(0.6), blurRadius: 1, offset: const Offset(-1, -1)),
      ],
    ),
    padding: EdgeInsets.all(padding),
    child: child,
  );
}