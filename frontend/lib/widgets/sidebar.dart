import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import '../theme/app_theme.dart';
import '../services/auth_service.dart';
import 'app_logo.dart';

// ═══════════════════════════════════════════════════════════════════════════
// AppShell
// ═══════════════════════════════════════════════════════════════════════════
class AppShell extends StatefulWidget {
  final Widget body;
  const AppShell({super.key, required this.body});
  @override
  State<AppShell> createState() => _AppShellState();
}

class _AppShellState extends State<AppShell>
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

  // ─── Layout strategy ────────────────────────────────────────────────────
  // Stack-based: the nav panel is Positioned absolutely and slides via
  // Transform.translate — it NEVER participates in layout, so it can never
  // cause a RenderFlex overflow.
  // The main content sits in a Column with an AnimatedContainer on top whose
  // height animates 0 → _sideW, acting as a left-margin spacer via a Row.
  // ───────────────────────────────────────────────────────────────────────
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Stack(
        children: [
          // ── 1. Main content area ──────────────────────────────────
          // A Row with an animated-width spacer on the left pushes content
          // right without overflowing.
          AnimatedBuilder(
            animation: _anim,
            builder: (ctx, child) => Row(
              children: [
                // Spacer that grows 0 → 250 as sidebar opens
                AnimatedContainer(
                  duration: Duration.zero, // driven by _anim already
                  width: _sideW * _anim.value,
                ),
                // Main content fills the rest
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

          // ── 2. Nav panel — absolutely positioned, slides via Transform ─
          // Positioned at left: 0, full height. Transform slides it from
          // -250 (hidden) to 0 (visible). Because it is Positioned it does
          // NOT affect the layout of siblings — zero overflow possible.
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
            child: _GlassNavPanel(onClose: _close),
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
    '/dashboard': 'Dashboard',
    '/interview-session': 'Interview',
    '/resume-upload': 'Resume Upload',
    '/interview-history': 'History',
    '/performance-report': 'Reports',
    '/profile-settings': 'Settings',
    '/admin-dashboard': 'Admin Dashboard',
    '/user-management': 'User Management',
    '/system-statistics': 'System Statistics',
  };

  @override
  Widget build(BuildContext context) {
    final currentPath = GoRouter.of(context).state.matchedLocation;
    final title = _titles[currentPath] ?? 'Dashboard';

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
                // ── Left: hamburger + title ──
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
                // ── Right: logo (conditional) + avatar ──
                Row(children: [
                  if (showLogo) ...[
                    const AppLogo(height: 32),
                    const SizedBox(width: 14),
                  ],
                  Container(
                    width: 38,
                    height: 38,
                    decoration: BoxDecoration(
                      gradient: AppTheme.primaryGradient,
                      borderRadius: BorderRadius.circular(10),
                      boxShadow: [
                        BoxShadow(
                          color: AppTheme.primaryCyan.withOpacity(0.3),
                          blurRadius: 8,
                        )
                      ],
                    ),
                    child: const Center(
                      child: Text('MS',
                          style: TextStyle(
                            fontSize: 14,
                            fontWeight: FontWeight.w800,
                            color: Colors.white,
                          )),
                    ),
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

// ─── Glass Nav Panel ──────────────────────────────────────────────────────
class _GlassNavPanel extends StatelessWidget {
  final VoidCallback onClose;
  const _GlassNavPanel({super.key, required this.onClose});

  static const _items = [
    _SideNavItem('Dashboard', Icons.dashboard_outlined, '/dashboard'),
    _SideNavItem('Interview', Icons.mic_outlined, '/interview-session'),
    _SideNavItem('Resume', Icons.document_scanner_outlined, '/resume-upload'),
    _SideNavItem('History', Icons.history_outlined, '/interview-history'),
    _SideNavItem('Reports', Icons.bar_chart_outlined, '/performance-report'),
    _SideNavItem('Settings', Icons.settings_outlined, '/profile-settings'),
  ];

  @override
  Widget build(BuildContext context) {
    final currentPath = GoRouter.of(context).state.matchedLocation;

    return Container(
      // This panel is always rendered at exactly 250px wide.
      // It lives inside a Positioned + Transform so it never touches layout.
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
          // ── Header ──
          Container(
            height: 64,
            padding: const EdgeInsets.symmetric(horizontal: 20),
            child: const Align(
              alignment: Alignment.centerLeft,
              child: AppLogo(height: 36),
            ),
          ),

          // ── Divider ──
          Container(
            height: 1,
            margin: const EdgeInsets.symmetric(horizontal: 16),
            color: Colors.grey.shade200,
          ),
          const SizedBox(height: 10),

          // ── Nav items ──
          Expanded(
            child: ListView(
              padding: EdgeInsets.zero,
              children: _items.map((item) {
                final active = currentPath == item.route;
                return Padding(
                  padding:
                      const EdgeInsets.symmetric(horizontal: 10, vertical: 2),
                  child: GestureDetector(
                    onTap: () => context.go(item.route),
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

          // ── User card ──
          Padding(
            padding: const EdgeInsets.all(10),
            child: Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: Colors.white.withOpacity(0.7),
                borderRadius: BorderRadius.circular(14),
                border: Border.all(color: Colors.grey.shade200),
              ),
              child: GestureDetector(
                onTap: () => context.go('/profile-settings'),
                child: Row(children: [
                  Container(
                    width: 40,
                    height: 40,
                    decoration: BoxDecoration(
                      gradient: AppTheme.primaryGradient,
                      borderRadius: BorderRadius.circular(20),
                    ),
                    child: const Icon(Icons.person_outline,
                        color: Colors.white, size: 20),
                  ),
                  const SizedBox(width: 10),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text('Muhammad',
                            style: TextStyle(
                              fontSize: 13,
                              fontWeight: FontWeight.w700,
                              color: AppTheme.textDark,
                            )),
                        const Text('Free Plan',
                            style: TextStyle(
                              fontSize: 11,
                              color: AppTheme.textGray,
                            )),
                      ],
                    ),
                  ),
                  const Icon(Icons.chevron_right,
                      color: AppTheme.textGray, size: 16),
                ]),
              ),
            ),
          ),
          const SizedBox(height: 10),

          // ── Logout button ──
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
                  children: [
                    Icon(Icons.logout_outlined,
                        color: AppTheme.errorRed, size: 19),
                    const SizedBox(width: 10),
                    const Text('Log Out',
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

// ═══════════════════════════════════════════════════════════════════════════
// CutLogo
// ═══════════════════════════════════════════════════════════════════════════
class CutLogo extends StatelessWidget {
  final bool dark;
  const CutLogo({super.key, this.dark = false});

  static const double _bracketGap = 10;

  @override
  Widget build(BuildContext context) {
    final interviewColor = dark ? Colors.white : AppTheme.textDark;

    return Stack(
      clipBehavior: Clip.none,
      children: [
        Padding(
          padding: const EdgeInsets.only(left: _bracketGap),
          child: Row(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.center,
            children: [
              Text('Interview',
                  style: TextStyle(
                    fontSize: 20,
                    fontWeight: FontWeight.w900,
                    color: interviewColor,
                  )),
              ShaderMask(
                shaderCallback: (b) => AppTheme.primaryGradient.createShader(b),
                child: const Text('Mate',
                    style: TextStyle(
                      fontSize: 20,
                      fontWeight: FontWeight.w900,
                      color: Colors.white,
                    )),
              ),
            ],
          ),
        ),
        Positioned.fill(
          child: IgnorePointer(
            child: CustomPaint(
              painter: _CutLogoPainter(
                color: AppTheme.primaryCyan,
                bracketGap: _bracketGap,
              ),
            ),
          ),
        ),
      ],
    );
  }
}

class _CutLogoPainter extends CustomPainter {
  final Color color;
  final double bracketGap;
  _CutLogoPainter({required this.color, required this.bracketGap});

  @override
  void paint(Canvas canvas, Size size) {
    final bracketPaint = Paint()
      ..color = color
      ..style = PaintingStyle.stroke
      ..strokeWidth = 2.5
      ..strokeCap = StrokeCap.round;

    canvas.drawLine(
      const Offset(0, 0),
      Offset(0, size.height * 0.55),
      bracketPaint,
    );
    canvas.drawLine(
      const Offset(0, 0),
      Offset(bracketGap, 0),
      bracketPaint,
    );

    final bandH = size.height * 0.40;
    final bandTop = (size.height - bandH) / 2.0;

    final bandPaint = Paint()
      ..color = color.withOpacity(0.35)
      ..style = PaintingStyle.fill;

    canvas.drawRect(
      Rect.fromLTWH(
        bracketGap,
        bandTop,
        size.width - bracketGap,
        bandH,
      ),
      bandPaint,
    );
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}

class _SideNavItem {
  final String label;
  final IconData icon;
  final String route;
  const _SideNavItem(this.label, this.icon, this.route);
}
