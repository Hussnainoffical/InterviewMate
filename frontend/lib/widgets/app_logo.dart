import 'package:flutter/material.dart';

// ═══════════════════════════════════════════════════════════════════════════
// AppLogo — reusable InterviewMate logo widget
// ═══════════════════════════════════════════════════════════════════════════
class AppLogo extends StatelessWidget {
  final double height;
  final BoxFit fit;

  const AppLogo({
    super.key,
    this.height = 40,
    this.fit = BoxFit.contain,
  });

  @override
  Widget build(BuildContext context) {
    return Image.asset(
      'assets/images/app_logo.png',
      height: height,
      fit: fit,
      errorBuilder: (context, error, stackTrace) {
        // Fallback to text if image fails
        return Text(
          'InterviewMate',
          style: TextStyle(
            fontSize: height * 0.4,
            fontWeight: FontWeight.w900,
            color: const Color(0xFF0ea5e9),
          ),
        );
      },
    );
  }
}
