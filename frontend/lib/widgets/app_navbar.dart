import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import '../theme/app_theme.dart';

class AppNavbar extends StatelessWidget {
  const AppNavbar({super.key});

  static const _navItems = [
    _NavItem('Dashboard',   Icons.dashboard_outlined,          '/dashboard'),
    _NavItem('Interview',   Icons.mic_outlined,                '/interview-session'),
    _NavItem('Resume',      Icons.document_scanner_outlined,   '/resume-upload'),
    _NavItem('History',     Icons.history_outlined,            '/interview-history'),
    _NavItem('Reports',     Icons.bar_chart_outlined,          '/performance-report'),
  ];

  @override
  Widget build(BuildContext context) {
    // Use GoRouter's uri to detect the current route for highlighting
    final currentPath = GoRouter.of(context).state.matchedLocation;

    return Container(
      height: 64,
      decoration: BoxDecoration(
        color: Colors.white.withOpacity(0.95),
        boxShadow: [BoxShadow(color: Colors.black.withOpacity(0.06), blurRadius: 12, offset: const Offset(0, 2))],
      ),
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 28),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            // Logo
            ShaderMask(
              shaderCallback: (b) => AppTheme.primaryGradient.createShader(b),
              child: const Text('InterviewMate', style: TextStyle(
                fontSize: 20, fontWeight: FontWeight.w900, color: Colors.white)),
            ),
            // Nav links
            Row(
              children: _navItems.map((item) {
                final active = currentPath == item.route;
                return Padding(
                  padding: const EdgeInsets.symmetric(horizontal: 4),
                  child: TextButton.icon(
                    onPressed: () => context.go(item.route),
                    icon: Icon(item.icon, size: 18,
                      color: active ? AppTheme.primaryCyan : AppTheme.textGray),
                    label: Text(item.label, style: TextStyle(
                      fontSize: 13, fontWeight: FontWeight.w600,
                      color: active ? AppTheme.primaryCyan : AppTheme.textGray)),
                    style: TextButton.styleFrom(
                      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                      backgroundColor: active ? AppTheme.primaryCyan.withOpacity(0.08) : null,
                    ),
                  ),
                );
              }).toList(),
            ),
            // Profile avatar
            GestureDetector(
              onTap: () => context.go('/profile-settings'),
              child: Container(
                width: 36, height: 36,
                decoration: BoxDecoration(
                  gradient: AppTheme.primaryGradient,
                  borderRadius: BorderRadius.circular(18),
                ),
                child: const Icon(Icons.person_outline, color: Colors.white, size: 18),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _NavItem {
  final String label;
  final IconData icon;
  final String route;
  const _NavItem(this.label, this.icon, this.route);
}
