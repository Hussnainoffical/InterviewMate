import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import '../../theme/app_theme.dart';

class AdminDashboardScreen extends StatelessWidget {
  const AdminDashboardScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(32),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text('Admin Dashboard',
              style: TextStyle(
                  fontSize: 26,
                  fontWeight: FontWeight.w800,
                  color: AppTheme.textDark)),
          const SizedBox(height: 6),
          const Text('Platform overview and management',
              style: TextStyle(fontSize: 14, color: AppTheme.textGray)),
          const SizedBox(height: 24),

          // KPI Cards
          LayoutBuilder(
            builder: (ctx, constraints) {
              final w = constraints.maxWidth;
              final cols = w >= 900
                  ? 4
                  : w >= 600
                      ? 2
                      : 1;
              final gap = 14.0;
              final cardW = (w - (gap * (cols - 1))) / cols;

              return Wrap(
                spacing: gap,
                runSpacing: gap,
                children: [
                  _kpiCard('Total Users', '1,248', '+12%',
                      Icons.people_outlined, AppTheme.primaryCyan, cardW),
                  _kpiCard(
                      'Active Sessions',
                      '84',
                      '+5',
                      Icons.play_circle_outlined,
                      AppTheme.primaryPurple,
                      cardW),
                  _kpiCard('Revenue', '10,320', '+18%', Icons.attach_money,
                      AppTheme.successGreen, cardW),
                  _kpiCard('Avg Rating', '4.8/5', '+0.2', Icons.star_outlined,
                      const Color(0xFFF59E0B), cardW),
                ],
              );
            },
          ),
          const SizedBox(height: 28),

          LayoutBuilder(
            builder: (ctx, constraints) {
              if (constraints.maxWidth < 800) {
                return Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    _recentSignupsCard(context),
                    const SizedBox(height: 20),
                    _quickActionsCard(context),
                  ],
                );
              }
              return Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Expanded(child: _recentSignupsCard(context)),
                  const SizedBox(width: 20),
                  SizedBox(width: 280, child: _quickActionsCard(context)),
                ],
              );
            },
          ),
        ],
      ),
    );
  }

  Widget _kpiCard(String title, String value, String change, IconData icon,
      Color color, double width) {
    return SizedBox(
      width: width,
      child: Container(
        decoration: AppTheme.glassCard,
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Container(
                  width: 42,
                  height: 42,
                  decoration: BoxDecoration(
                      color: color.withOpacity(0.1),
                      borderRadius: BorderRadius.circular(10)),
                  child: Icon(icon, color: color, size: 22),
                ),
                Container(
                  padding:
                      const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                  decoration: BoxDecoration(
                      color: AppTheme.successGreen.withOpacity(0.1),
                      borderRadius: BorderRadius.circular(12)),
                  child: Text(change,
                      style: const TextStyle(
                          fontSize: 11,
                          fontWeight: FontWeight.w600,
                          color: AppTheme.successGreen)),
                ),
              ],
            ),
            const SizedBox(height: 10),
            Text(value,
                style: const TextStyle(
                    fontSize: 26,
                    fontWeight: FontWeight.w800,
                    color: AppTheme.textDark)),
            const SizedBox(height: 2),
            Text(title,
                style: const TextStyle(fontSize: 13, color: AppTheme.textGray)),
          ],
        ),
      ),
    );
  }

  Widget _recentSignupsCard(BuildContext context) {
    return Container(
      decoration: AppTheme.glassCard,
      padding: const EdgeInsets.all(24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              const Text('Recent Signups',
                  style: TextStyle(
                      fontSize: 18,
                      fontWeight: FontWeight.w700,
                      color: AppTheme.textDark)),
              GestureDetector(
                onTap: () => context.go('/admin/user-management'),
                child: const Text('View All →',
                    style: TextStyle(
                        fontSize: 13,
                        color: AppTheme.primaryCyan,
                        fontWeight: FontWeight.w600)),
              ),
            ],
          ),
          const SizedBox(height: 16),
          ...[
            ['Ahmed Khan', 'ahmed@email.com', 'Software Engineer', '2 min ago'],
            ['Sara Malik', 'sara@email.com', 'Data Scientist', '15 min ago'],
            ['Omar Hassan', 'omar@email.com', 'Product Manager', '1 hour ago'],
            [
              'Fatima Noor',
              'fatima@email.com',
              'UI/UX Designer',
              '2 hours ago'
            ],
            ['Raza Ahmed', 'raza@email.com', 'DevOps Engineer', '3 hours ago'],
          ].map((u) => Padding(
                padding: const EdgeInsets.only(bottom: 10),
                child: Row(
                  children: [
                    Container(
                      width: 38,
                      height: 38,
                      decoration: BoxDecoration(
                          gradient: AppTheme.primaryGradient,
                          borderRadius: BorderRadius.circular(19)),
                      child: Center(
                          child: Text((u[0] as String)[0],
                              style: const TextStyle(
                                  fontSize: 16,
                                  fontWeight: FontWeight.w700,
                                  color: Colors.white))),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                        child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(u[0] as String,
                            style: const TextStyle(
                                fontSize: 14,
                                fontWeight: FontWeight.w600,
                                color: AppTheme.textDark)),
                        Text('${u[1]} • ${u[2]}',
                            style: const TextStyle(
                                fontSize: 12, color: AppTheme.textGray)),
                      ],
                    )),
                    Text(u[3] as String,
                        style: const TextStyle(
                            fontSize: 11, color: AppTheme.textGray)),
                  ],
                ),
              ))
        ],
      ),
    );
  }

  Widget _quickActionsCard(BuildContext context) {
    return Container(
      decoration: AppTheme.glassCard,
      padding: const EdgeInsets.all(24),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text('Quick Actions',
              style: TextStyle(
                  fontSize: 18,
                  fontWeight: FontWeight.w700,
                  color: AppTheme.textDark)),
          const SizedBox(height: 16),
          ...[
            [
              'Manage Users',
              Icons.people_outlined,
              '/admin/user-management',
              AppTheme.primaryCyan
            ],
            [
              'System Statistics',
              Icons.analytics_outlined,
              '/admin/system-statistics',
              AppTheme.primaryPurple
            ],
            [
              'Export Reports',
              Icons.download_outlined,
              '/admin/dashboard',
              AppTheme.successGreen
            ],
            [
              'System Settings',
              Icons.settings_outlined,
              '/admin/dashboard',
              const Color(0xFFF59E0B)
            ],
          ].map((a) => Padding(
                padding: const EdgeInsets.only(bottom: 8),
                child: GestureDetector(
                  onTap: () => context.go(a[2] as String),
                  child: Container(
                    padding: const EdgeInsets.all(14),
                    decoration: BoxDecoration(
                        color: Colors.white.withOpacity(0.7),
                        borderRadius: BorderRadius.circular(10)),
                    child: Row(
                      children: [
                        Container(
                          width: 36,
                          height: 36,
                          decoration: BoxDecoration(
                              color: (a[3] as Color).withOpacity(0.1),
                              borderRadius: BorderRadius.circular(8)),
                          child: Icon(a[1] as IconData,
                              color: a[3] as Color, size: 20),
                        ),
                        const SizedBox(width: 12),
                        Expanded(
                          child: Text(a[0] as String,
                              style: const TextStyle(
                                  fontSize: 14,
                                  fontWeight: FontWeight.w600,
                                  color: AppTheme.textDark)),
                        ),
                        const Icon(Icons.chevron_right,
                            color: AppTheme.textGray, size: 18),
                      ],
                    ),
                  ),
                ),
              ))
        ],
      ),
    );
  }
}
