import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import 'package:interviewmate/widgets/app_logo.dart';
import '../../theme/app_theme.dart';

class WelcomeScreen extends StatelessWidget {
  const WelcomeScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Container(
        decoration: BoxDecoration(gradient: AppTheme.backgroundGradient),
        child: SingleChildScrollView(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              _Navbar(ctx: context),
              _Hero(ctx: context),
              _Features(),
              _HowItWorks(),
              _StatsBar(),
              _CTA(ctx: context),
              _Footer(),
            ],
          ),
        ),
      ),
    );
  }
}

// ─── Navbar ───────────────────────────────────────────
class _Navbar extends StatelessWidget {
  final BuildContext ctx;
  const _Navbar({super.key, required this.ctx});
  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 48, vertical: 18),
      decoration: BoxDecoration(
        color: Colors.white.withOpacity(0.9),
        border: Border(bottom: BorderSide(color: Colors.grey.shade100)),
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          ShaderMask(
            shaderCallback: (b) => AppTheme.primaryGradient.createShader(b),
            child: const AppLogo(height: 32),
          ),
          Row(children: [
            _navBtn('Features'),
            _navBtn('How It Works'),
            _navBtn('About'),
            const SizedBox(width: 20),
            TextButton(
              onPressed: () => ctx.go('/login'),
              child: const Text('Sign In',
                  style: TextStyle(
                      fontWeight: FontWeight.w600, color: AppTheme.textDark)),
            ),
            const SizedBox(width: 8),
            ElevatedButton(
              onPressed: () => ctx.go('/signup'),
              style: ElevatedButton.styleFrom(
                backgroundColor: AppTheme.primaryCyan,
                foregroundColor: Colors.white,
                shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(10)),
                padding:
                    const EdgeInsets.symmetric(horizontal: 24, vertical: 10),
              ),
              child: const Text('Get Started',
                  style: TextStyle(fontWeight: FontWeight.w600)),
            ),
          ]),
        ],
      ),
    );
  }

  Widget _navBtn(String t) => TextButton(
        onPressed: () {},
        child: Text(t,
            style: const TextStyle(
                color: AppTheme.textGray, fontWeight: FontWeight.w500)),
      );
}

// ─── Hero ─────────────────────────────────────────────
class _Hero extends StatelessWidget {
  final BuildContext ctx;
  const _Hero({super.key, required this.ctx});
  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 48, vertical: 64),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.center,
        children: [
          // Left – text
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text('Master Your Next Interview',
                    style: TextStyle(
                        fontSize: 42,
                        fontWeight: FontWeight.w800,
                        color: AppTheme.textDark,
                        height: 1.2)),
                const SizedBox(height: 8),
                ShaderMask(
                  shaderCallback: (b) =>
                      AppTheme.primaryGradient.createShader(b),
                  child: const Text('with AI Power',
                      style: TextStyle(
                          fontSize: 42,
                          fontWeight: FontWeight.w800,
                          color: Colors.white,
                          height: 1.2)),
                ),
                const SizedBox(height: 20),
                const Text(
                    'AI-powered mock interviews designed for Pakistani professionals. '
                    'Practice with realistic scenarios, get instant feedback, and '
                    'boost your confidence before the big day.',
                    style: TextStyle(
                        fontSize: 16, color: AppTheme.textGray, height: 1.6)),
                const SizedBox(height: 32),
                Row(children: [
                  ElevatedButton(
                    onPressed: () => ctx.go('/signup'),
                    style: ElevatedButton.styleFrom(
                      backgroundColor: AppTheme.primaryCyan,
                      foregroundColor: Colors.white,
                      shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(12)),
                      padding: const EdgeInsets.symmetric(
                          horizontal: 32, vertical: 14),
                    ),
                    child: const Text('Get Started Free',
                        style: TextStyle(
                            fontSize: 16, fontWeight: FontWeight.w600)),
                  ),
                  const SizedBox(width: 16),
                  OutlinedButton(
                    onPressed: () {},
                    style: OutlinedButton.styleFrom(
                      shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(12)),
                      side: BorderSide(color: Colors.grey.shade300),
                      padding: const EdgeInsets.symmetric(
                          horizontal: 28, vertical: 14),
                    ),
                    child: const Text('Watch Demo',
                        style: TextStyle(
                            fontSize: 16,
                            fontWeight: FontWeight.w600,
                            color: AppTheme.textDark)),
                  ),
                ]),
                const SizedBox(height: 40),
                // Quick stats
                Row(children: [
                  _quickStat('500+', 'Active Users'),
                  const SizedBox(width: 32),
                  _quickStat('10K+', 'Practice Sessions'),
                  const SizedBox(width: 32),
                  _quickStat('4.9/5', 'Rating'),
                ]),
              ],
            ),
          ),
          const SizedBox(width: 48),
          // Right – glass card preview
          Expanded(
            child: Container(
              decoration: AppTheme.glassCard,
              padding: const EdgeInsets.all(40),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.center,
                children: [
                  Container(
                    width: 100,
                    height: 100,
                    decoration: BoxDecoration(
                      gradient: AppTheme.primaryGradient,
                      borderRadius: BorderRadius.circular(50),
                    ),
                    child: const Icon(Icons.smart_toy_outlined,
                        color: Colors.white, size: 48),
                  ),
                  const SizedBox(height: 20),
                  const Text('AI Interview Coach',
                      style: TextStyle(
                          fontSize: 18,
                          fontWeight: FontWeight.w700,
                          color: AppTheme.textDark)),
                  const SizedBox(height: 16),
                  // Sample question bubble
                  Container(
                    decoration: BoxDecoration(
                      color: AppTheme.primaryCyan.withOpacity(0.08),
                      borderRadius: const BorderRadius.only(
                          topLeft: Radius.circular(16),
                          topRight: Radius.circular(16),
                          bottomRight: Radius.circular(16)),
                    ),
                    padding: const EdgeInsets.all(16),
                    child: const Text(
                        '"Tell me about yourself and your experience with software development."',
                        style: TextStyle(
                            fontSize: 14,
                            color: AppTheme.textDark,
                            height: 1.5)),
                  ),
                  const SizedBox(height: 20),
                  Row(children: [
                    _actionChip(Icons.mic, 'Answer'),
                    const SizedBox(width: 8),
                    _actionChip(Icons.skip_next, 'Skip'),
                    const SizedBox(width: 8),
                    _actionChip(Icons.lightbulb_outline, 'Hint'),
                  ]),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _quickStat(String val, String label) => Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(val,
              style: const TextStyle(
                  fontSize: 22,
                  fontWeight: FontWeight.w800,
                  color: AppTheme.textDark)),
          Text(label,
              style: const TextStyle(fontSize: 13, color: AppTheme.textGray)),
        ],
      );

  Widget _actionChip(IconData icon, String label) => Container(
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(20),
          border: Border.all(color: Colors.grey.shade200),
          boxShadow: [
            BoxShadow(color: Colors.black.withOpacity(0.04), blurRadius: 4)
          ],
        ),
        child: Row(children: [
          Icon(icon, size: 16, color: AppTheme.primaryCyan),
          const SizedBox(width: 6),
          Text(label,
              style: const TextStyle(
                  fontSize: 13,
                  fontWeight: FontWeight.w600,
                  color: AppTheme.textDark)),
        ]),
      );
}

// ─── Features ─────────────────────────────────────────
class _Features extends StatelessWidget {
  static const _items = [
    [
      'AI Avatar Interviews',
      'Practice with a realistic AI interviewer powered by D-ID avatars.',
      Icons.smart_toy_outlined
    ],
    [
      'Resume Analysis',
      'Upload your resume and get instant AI-driven feedback and suggestions.',
      Icons.document_scanner_outlined
    ],
    [
      'Pakistani English',
      'Tailored for Pakistani professionals with context-aware language support.',
      Icons.language
    ],
    [
      'Question Generation',
      'Smart question generation based on role, industry, and experience level.',
      Icons.lightbulb_outline
    ],
    [
      'Performance Reports',
      'Detailed analytics on communication, technical skills, and confidence.',
      Icons.bar_chart_outlined
    ],
    [
      'Cross-Platform',
      'Works seamlessly on Web, Android, and iOS with a single codebase.',
      Icons.devices_outlined
    ],
  ];

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 48, vertical: 48),
      child: Column(
        children: [
          const Text('Why InterviewMate?',
              style: TextStyle(
                  fontSize: 32,
                  fontWeight: FontWeight.w800,
                  color: AppTheme.textDark)),
          const SizedBox(height: 8),
          const Text('Everything you need to ace your next interview',
              style: TextStyle(fontSize: 16, color: AppTheme.textGray)),
          const SizedBox(height: 40),
          Wrap(
            spacing: 20,
            runSpacing: 20,
            children: _items
                .map((item) => SizedBox(
                      width: 340,
                      child: Container(
                        decoration: AppTheme.glassCard,
                        padding: const EdgeInsets.all(28),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Container(
                              width: 48,
                              height: 48,
                              decoration: BoxDecoration(
                                color: AppTheme.primaryCyan.withOpacity(0.1),
                                borderRadius: BorderRadius.circular(12),
                              ),
                              child: Icon(item[2] as IconData,
                                  color: AppTheme.primaryCyan, size: 24),
                            ),
                            const SizedBox(height: 16),
                            Text(item[0] as String,
                                style: const TextStyle(
                                    fontSize: 17,
                                    fontWeight: FontWeight.w700,
                                    color: AppTheme.textDark)),
                            const SizedBox(height: 8),
                            Text(item[1] as String,
                                style: const TextStyle(
                                    fontSize: 14,
                                    color: AppTheme.textGray,
                                    height: 1.5)),
                          ],
                        ),
                      ),
                    ))
                .toList(),
          ),
        ],
      ),
    );
  }
}

// ─── How It Works ─────────────────────────────────────
class _HowItWorks extends StatelessWidget {
  static const _steps = [
    [
      'Create Account',
      'Sign up and set up your profile with your target role and experience.',
      Icons.person_add_outlined
    ],
    [
      'Upload Resume',
      'Upload your resume for AI analysis and tailored question generation.',
      Icons.upload_outlined
    ],
    [
      'Start Interview',
      'Begin a mock interview with our AI avatar in a realistic setting.',
      Icons.play_circle_outlined
    ],
    [
      'Get Feedback',
      'Receive detailed performance feedback and tips to improve.',
      Icons.feedback_outlined
    ],
  ];

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 48),
      padding: const EdgeInsets.all(48),
      decoration: BoxDecoration(
        color: Colors.white.withOpacity(0.7),
        borderRadius: BorderRadius.circular(24),
      ),
      child: Column(
        children: [
          const Text('How It Works',
              style: TextStyle(
                  fontSize: 32,
                  fontWeight: FontWeight.w800,
                  color: AppTheme.textDark)),
          const SizedBox(height: 8),
          const Text('Four simple steps to interview mastery',
              style: TextStyle(fontSize: 16, color: AppTheme.textGray)),
          const SizedBox(height: 40),
          // Each step is a fixed-height column so all 4 tops align perfectly
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            crossAxisAlignment: CrossAxisAlignment.start, // ← top-aligned
            children: List.generate(_steps.length, (i) {
              final s = _steps[i];
              return Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  SizedBox(
                    width: 170,
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        // Number badge + icon on the same baseline
                        Row(
                          crossAxisAlignment: CrossAxisAlignment.center,
                          children: [
                            Container(
                              width: 44,
                              height: 44,
                              decoration: BoxDecoration(
                                gradient: AppTheme.primaryGradient,
                                borderRadius: BorderRadius.circular(22),
                              ),
                              child: Center(
                                  child: Text('${i + 1}',
                                      style: const TextStyle(
                                          fontSize: 18,
                                          fontWeight: FontWeight.w800,
                                          color: Colors.white))),
                            ),
                            const SizedBox(width: 12),
                            Icon(s[2] as IconData,
                                color: AppTheme.primaryCyan, size: 28),
                          ],
                        ),
                        const SizedBox(height: 14),
                        Text(s[0] as String,
                            style: const TextStyle(
                                fontSize: 16,
                                fontWeight: FontWeight.w700,
                                color: AppTheme.textDark)),
                        const SizedBox(height: 6),
                        Text(s[1] as String,
                            style: const TextStyle(
                                fontSize: 13,
                                color: AppTheme.textGray,
                                height: 1.5)),
                      ],
                    ),
                  ),
                  // Chevron arrow between steps – vertically centred with the badge row
                  if (i < _steps.length - 1)
                    Padding(
                      padding: const EdgeInsets.only(
                          top: 10), // nudge to mid-badge height
                      child: const Icon(Icons.chevron_right,
                          color: AppTheme.primaryCyan, size: 28),
                    ),
                ],
              );
            }),
          ),
        ],
      ),
    );
  }
}

// ─── Stats Bar ────────────────────────────────────────
class _StatsBar extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 48, vertical: 48),
      child: Container(
        decoration: BoxDecoration(
          gradient: AppTheme.primaryGradient,
          borderRadius: BorderRadius.circular(20),
        ),
        padding: const EdgeInsets.all(40),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.spaceAround,
          children: [
            _stat('98%', 'Accuracy Rate'),
            _stat('100%', 'Pakistani English'),
            _stat('24/7', 'Availability'),
          ],
        ),
      ),
    );
  }

  Widget _stat(String val, String label) => Column(
        children: [
          Text(val,
              style: const TextStyle(
                  fontSize: 36,
                  fontWeight: FontWeight.w800,
                  color: Colors.white)),
          const SizedBox(height: 4),
          Text(label,
              style: const TextStyle(fontSize: 14, color: Colors.white70)),
        ],
      );
}

// ─── CTA ──────────────────────────────────────────────
class _CTA extends StatelessWidget {
  final BuildContext ctx;
  const _CTA({super.key, required this.ctx});
  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 48, vertical: 32),
      child: Container(
        decoration: AppTheme.glassCard,
        padding: const EdgeInsets.symmetric(vertical: 56, horizontal: 40),
        child: Column(
          children: [
            const Text('Ready to Ace Your Next Interview?',
                style: TextStyle(
                    fontSize: 30,
                    fontWeight: FontWeight.w800,
                    color: AppTheme.textDark)),
            const SizedBox(height: 12),
            const Text(
                'Join thousands of Pakistani professionals who already use InterviewMate.',
                style: TextStyle(fontSize: 16, color: AppTheme.textGray)),
            const SizedBox(height: 28),
            ElevatedButton(
              onPressed: () => ctx.go('/signup'),
              style: ElevatedButton.styleFrom(
                backgroundColor: AppTheme.primaryCyan,
                foregroundColor: Colors.white,
                shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(12)),
                padding:
                    const EdgeInsets.symmetric(horizontal: 40, vertical: 16),
              ),
              child: const Text('Get Started – It\'s Free',
                  style: TextStyle(fontSize: 17, fontWeight: FontWeight.w600)),
            ),
          ],
        ),
      ),
    );
  }
}

// ─── Footer ───────────────────────────────────────────
class _Footer extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Container(
      color: Colors.white.withOpacity(0.6),
      padding: const EdgeInsets.symmetric(horizontal: 48, vertical: 36),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            ShaderMask(
              shaderCallback: (b) => AppTheme.primaryGradient.createShader(b),
              child: const Text('InterviewMate',
                  style: TextStyle(
                      fontSize: 20,
                      fontWeight: FontWeight.w900,
                      color: Colors.white)),
            ),
            const SizedBox(height: 8),
            const Text(
                'AI-powered interview prep for\nPakistani professionals.',
                style: TextStyle(
                    fontSize: 13, color: AppTheme.textGray, height: 1.5)),
          ]),
          _col('Product', ['Features', 'Pricing', 'Demo', 'FAQ']),
          _col('Resources', ['Documentation', 'Blog', 'Support', 'Community']),
          _col('Company', ['About Us', 'Team', 'Careers', 'Contact']),
        ],
      ),
    );
  }

  Widget _col(String title, List<String> items) => Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(title,
              style: const TextStyle(
                  fontSize: 14,
                  fontWeight: FontWeight.w700,
                  color: AppTheme.textDark)),
          const SizedBox(height: 12),
          ...items.map((i) => Padding(
                padding: const EdgeInsets.only(bottom: 8),
                child: Text(i,
                    style: const TextStyle(
                        fontSize: 13, color: AppTheme.textGray)),
              )),
        ],
      );
}
