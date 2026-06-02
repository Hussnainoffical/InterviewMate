import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

class AppTheme {
  // ─── Colors ───────────────────────────────────────────
  static const Color primaryCyan   = Color(0xFF00D9FF);
  static const Color primaryPurple = Color(0xFF6366F1);
  static const Color textDark      = Color(0xFF0F172A);
  static const Color textGray      = Color(0xFF64748B);
  static const Color bgLight       = Color(0xFFF0F9FF);
  static const Color errorRed      = Color(0xFFEF4444);
  static const Color successGreen  = Color(0xFF10B981);

  // ─── Gradients ────────────────────────────────────────
  static const LinearGradient primaryGradient = LinearGradient(
    colors: [primaryCyan, primaryPurple],
    begin: Alignment.centerLeft,
    end: Alignment.centerRight,
  );

  static const LinearGradient backgroundGradient = LinearGradient(
    colors: [Color(0xFFD0E8FF), Color(0xFFE0D4FF), Color(0xFFCCEDFF)],
    begin: Alignment.topLeft,
    end: Alignment.bottomRight,
  );

  // ─── Glass Card ───────────────────────────────────────
  static BoxDecoration glassCard = BoxDecoration(
    color: Colors.white.withOpacity(0.92),
    borderRadius: BorderRadius.circular(20),
    border: Border.all(color: Colors.white.withOpacity(0.6), width: 1),
    boxShadow: [
      BoxShadow(
        color: Colors.black.withOpacity(0.06),
        blurRadius: 24,
        offset: const Offset(0, 8),
      ),
    ],
  );

  // ─── Input Decoration ─────────────────────────────────
  static InputDecoration inputDecoration(String label, {IconData? icon}) {
    return InputDecoration(
      labelText: label,
      prefixIcon: icon != null ? Icon(icon, color: primaryCyan) : null,
      filled: true,
      fillColor: Colors.white,
      border: OutlineInputBorder(
        borderRadius: BorderRadius.circular(12),
        borderSide: BorderSide(color: Colors.grey.shade200),
      ),
      enabledBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(12),
        borderSide: BorderSide(color: Colors.grey.shade200),
      ),
      focusedBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(12),
        borderSide: const BorderSide(color: primaryCyan, width: 2),
      ),
      errorBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(12),
        borderSide: const BorderSide(color: errorRed),
      ),
      contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
    );
  }

  // ─── Theme ────────────────────────────────────────────
  static ThemeData get lightTheme {
    final base = GoogleFonts.interTextTheme();
    return ThemeData(
      textTheme: base,
      colorScheme: ColorScheme.fromSeed(
        seedColor: primaryCyan,
        brightness: Brightness.light,
      ),
      useMaterial3: true,
      scaffoldBackgroundColor: Colors.white,
    );
  }
}
