import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import '../theme/app_theme.dart';
import '../services/auth_service.dart';
import 'app_logo.dart';

// ═══════════════════════════════════════════════════════════════════════════
// AdminShell - Sidebar for admin screens
// ═══════════════════════════════════════════════════════════════════════════
class AdminShell extends StatefulWidget {
  final Widget body;
  const AdminShell({super.key, required this.body});
  @override
  State<AdminShell> createState() => _AdminShellState();
}

class _AdminShellState extends State<AdminShell>
    with SingleTickerProviderStateMixin {
  static const double _sideW = 250;

  bool _open = false;
  late final AnimationController _ctrl;
  late final Animation<double> _anim;

  @override
  void initState() {
    super.initState();
    _ctrl = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 300),
    );
    _anim = CurvedAnimation(parent: _ctrl, curve: Curves.easeOutCubic);
  }

  @override
  void dispose() {
    _ctrl.dispose();
    super.dispose();
  }

  void _toggle() {
    setState(() => _open = !_open);
    _open ? _ctrl.forward() : _ctrl.reverse();
  }

  void _close() {
    if (!_open) return;
    setState(() => _open = false);
    _ctrl.reverse();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Stack(
        children: [
          // Main content
          AnimatedBuilder(
            animation: _anim,
            builder: (ctx, child) => Row(
              children: [
                AnimatedContainer(
                  duration: Duration.zero,
                  width: _sideW * _anim.value,
                ),
                Expanded(child: child!),
              ],
            ),
            child: Container(
              decoration: BoxDecoration(gradient: AppTheme.backgroundGradient),
              child: Column(
                children: [
                  _TopBar(onHamburger: _toggle, navOpen: _open),
                  Expanded(child: widget.body),
                ],
              ),
            ),
          ),

          // Nav panel
          AnimatedBuilder(
            animation: _anim,
            builder: (ctx, child) => Positioned(
              top: 0,
              bottom: 0,
              left: 0,
              width: _sideW,
              child: Transform.translate(
                offset: Offset(-_sideW + (_sideW * _anim.value), 0),
                child: child!,
              ),
            ),
            child: _AdminNavPanel(onClose: _close),
          ),
        ],
      ),
    );
  }
}

// ─── Top Bar ──────────────────────────────────────────────────────────────
class _TopBar extends StatelessWidget {
  final VoidCallback onHamburger;
  final bool navOpen;
  const _TopBar({super.key, required this.onHamburger, required this.navOpen});

  static const Map<String, String> _titles = {
    '/admin/dashboard': 'Admin Dashboard',
    '/admin/user-management': 'User Management',
    '/admin/system-statistics': 'System Statistics',
    '/admin/settings': 'Settings',
    '/admin/plan-settings': 'Plan Settings',
  };

  @override
  Widget build(BuildContext context) {
    final currentPath = GoRouter.of(context).state?.matchedLocation ?? '';
    final title = _titles[currentPath] ?? 'Admin Panel';

    return Container(
      height: 64,
      decoration: BoxDecoration(
        color: Colors.white.withOpacity(0.85),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.06),
            blurRadius: 14,
            offset: const Offset(0, 2),
          )
        ],
      ),
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 20),
        child: LayoutBuilder(
          builder: (ctx, constraints) {
            final showLogo = constraints.maxWidth > 320;

            return Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                // Left: hamburger + title
                Expanded(
                  child: Row(
                    children: [
                      GestureDetector(
                        onTap: onHamburger,
                        child: Container(
                          width: 40,
                          height: 40,
                          decoration: BoxDecoration(
                            color: Colors.white.withOpacity(0.9),
                            borderRadius: BorderRadius.circular(10),
                            border: Border.all(color: Colors.grey.shade200),
                            boxShadow: [
                              BoxShadow(
                                color: Colors.black.withOpacity(0.04),
                                blurRadius: 6,
                              )
                            ],
                          ),
                          child: const Icon(
                            Icons.menu,
                            color: AppTheme.textDark,
                            size: 22,
                          ),
                        ),
                      ),
                      const SizedBox(width: 16),
                      Expanded(
                        child: Text(title,
                            overflow: TextOverflow.ellipsis,
                            style: const TextStyle(
                              fontSize: 18,
                              fontWeight: FontWeight.w700,
                              color: AppTheme.textDark,
                            )),
                      ),
                    ],
                  ),
                ),
                const SizedBox(width: 12),
                // Right: logo + ADMIN badge
                Row(children: [
                  if (showLogo) ...[
                    const AppLogo(height: 32),
                    const SizedBox(width: 10),
                  ],
                  Container(
                    padding:
                        const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                    decoration: BoxDecoration(
                      color: AppTheme.errorRed.withOpacity(0.1),
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: const Text('ADMIN',
                        style: TextStyle(
                          fontSize: 10,
                          fontWeight: FontWeight.w800,
                          color: AppTheme.errorRed,
                          letterSpacing: 1,
                        )),
                  ),
                ]),
              ],
            );
          },
        ),
      ),
    );
  }
}

// ─── Admin Nav Panel ──────────────────────────────────────────────────────
class _AdminNavPanel extends StatelessWidget {
  final VoidCallback onClose;
  const _AdminNavPanel({super.key, required this.onClose});

  static const _items = [
    _SideNavItem('Dashboard', Icons.dashboard_outlined, '/admin/dashboard'),
    _SideNavItem('Users', Icons.people_outlined, '/admin/user-management'),
    _SideNavItem(
        'Statistics', Icons.analytics_outlined, '/admin/system-statistics'),
    _SideNavItem('Settings', Icons.settings_outlined, '/admin/settings'),
    _SideNavItem('Plan Settings', Icons.card_membership_outlined,
        '/admin/plan-settings'),
  ];

  @override
  Widget build(BuildContext context) {
    final currentPath = GoRouter.of(context).state?.matchedLocation ?? '';

    return Container(
      width: _sideW,
      decoration: BoxDecoration(
        color: Colors.white.withOpacity(0.92),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.12),
            blurRadius: 28,
            offset: const Offset(6, 0),
          )
        ],
        border: Border(
          right: BorderSide(color: Colors.white.withOpacity(0.5)),
        ),
      ),
      child: Column(
        children: [
          // Header with logo only (NO ADMIN BADGE HERE)
          Container(
            height: 64,
            padding: const EdgeInsets.symmetric(horizontal: 20),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: const [
                AppLogo(height: 36),
              ],
            ),
          ),

          // Divider
          Container(
            height: 1,
            margin: const EdgeInsets.symmetric(horizontal: 16),
            color: Colors.grey.shade200,
          ),
          const SizedBox(height: 10),

          // Nav items
          Expanded(
            child: ListView(
              padding: EdgeInsets.zero,
              children: _items.map((item) {
                final active = currentPath == item.route;
                return Padding(
                  padding:
                      const EdgeInsets.symmetric(horizontal: 10, vertical: 2),
                  child: GestureDetector(
                    onTap: () {
                      context.go(item.route);
                      onClose();
                    },
                    child: Container(
                      padding: const EdgeInsets.symmetric(
                          horizontal: 14, vertical: 12),
                      decoration: BoxDecoration(
                        color: active
                            ? AppTheme.primaryCyan.withOpacity(0.08)
                            : null,
                        borderRadius: BorderRadius.circular(12),
                        border: active
                            ? Border.all(
                                color: AppTheme.primaryCyan.withOpacity(0.22))
                            : null,
                      ),
                      child: Row(children: [
                        Container(
                          width: 36,
                          height: 36,
                          decoration: BoxDecoration(
                            color: active
                                ? AppTheme.primaryCyan.withOpacity(0.13)
                                : Colors.grey.shade100,
                            borderRadius: BorderRadius.circular(9),
                          ),
                          child: Icon(item.icon,
                              size: 19,
                              color: active
                                  ? AppTheme.primaryCyan
                                  : AppTheme.textGray),
                        ),
                        const SizedBox(width: 12),
                        Text(item.label,
                            style: TextStyle(
                              fontSize: 14,
                              fontWeight: FontWeight.w600,
                              color: active
                                  ? AppTheme.primaryCyan
                                  : AppTheme.textDark,
                            )),
                      ]),
                    ),
                  ),
                );
              }).toList(),
            ),
          ),

          // Admin info card
          Padding(
            padding: const EdgeInsets.all(10),
            child: Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: Colors.white.withOpacity(0.7),
                borderRadius: BorderRadius.circular(14),
                border: Border.all(color: Colors.grey.shade200),
              ),
              child: Row(children: [
                Container(
                  width: 40,
                  height: 40,
                  decoration: BoxDecoration(
                    gradient: AppTheme.primaryGradient,
                    borderRadius: BorderRadius.circular(20),
                  ),
                  child: const Icon(Icons.admin_panel_settings,
                      color: Colors.white, size: 20),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: const [
                      Text('Administrator',
                          style: TextStyle(
                            fontSize: 13,
                            fontWeight: FontWeight.w700,
                            color: AppTheme.textDark,
                          )),
                      Text('Full Access',
                          style: TextStyle(
                            fontSize: 11,
                            color: AppTheme.textGray,
                          )),
                    ],
                  ),
                ),
              ]),
            ),
          ),
          const SizedBox(height: 10),

          // Logout button
          Padding(
            padding: const EdgeInsets.symmetric(horizontal: 10),
            child: GestureDetector(
              onTap: () async {
                await AuthService().signOut();
                if (context.mounted) context.go('/login');
              },
              child: Container(
                width: double.infinity,
                padding: const EdgeInsets.symmetric(vertical: 13),
                decoration: BoxDecoration(
                  color: AppTheme.errorRed.withOpacity(0.06),
                  borderRadius: BorderRadius.circular(12),
                  border:
                      Border.all(color: AppTheme.errorRed.withOpacity(0.18)),
                ),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.center,
                  children: const [
                    Icon(Icons.logout_outlined,
                        color: AppTheme.errorRed, size: 19),
                    SizedBox(width: 10),
                    Text('Log Out',
                        style: TextStyle(
                          fontSize: 14,
                          fontWeight: FontWeight.w600,
                          color: AppTheme.errorRed,
                        )),
                  ],
                ),
              ),
            ),
          ),
          const SizedBox(height: 6),
        ],
      ),
    );
  }

  static const double _sideW = 250;
}

class _SideNavItem {
  final String label;
  final IconData icon;
  final String route;
  const _SideNavItem(this.label, this.icon, this.route);
}
