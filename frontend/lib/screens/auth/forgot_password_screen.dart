import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import '../../theme/app_theme.dart';
import '../../widgets/auth_widgets.dart';
import '../../services/api_service.dart';

class ForgotPasswordScreen extends StatefulWidget {
  const ForgotPasswordScreen({super.key});
  @override
  State<ForgotPasswordScreen> createState() => _FPState();
}

class _FPState extends State<ForgotPasswordScreen> {
  final _emailCtrl = TextEditingController();
  bool _loading = false, _sent = false;
  String? _emailErr;

  Future<void> _send() async {
    setState(() {
      _emailErr = _emailCtrl.text.trim().isEmpty ? 'Email is required'
          : !RegExp(r'^[\w-.]+@([\w-]+\.)+[\w-]{2,4}$').hasMatch(_emailCtrl.text.trim())
          ? 'Enter a valid email' : null;
    });
    if (_emailErr != null) return;
    setState(() => _loading = true);
    try {
      await ApiService().forgotPassword(_emailCtrl.text.trim());
    } catch (_) {
      // Always show success — don't reveal if email exists
    } finally {
      if (mounted) setState(() { _loading = false; _sent = true; });
    }
  }

  @override
  Widget build(BuildContext context) {
    return AuthLayout(child: _sent ? _sentView() : _formView());
  }

  Widget _formView() => Column(children: [
    Container(width: 72, height: 72,
        decoration: BoxDecoration(color: AppTheme.primaryCyan.withOpacity(0.1), borderRadius: BorderRadius.circular(36)),
        child: const Icon(Icons.lock_reset_outlined, color: AppTheme.primaryCyan, size: 36)),
    const SizedBox(height: 24),
    const Text('Forgot Password', style: TextStyle(fontSize: 24, fontWeight: FontWeight.w700, color: AppTheme.textDark)),
    const SizedBox(height: 8),
    const Text("Enter your email and we'll send you a link to reset your password.",
        style: TextStyle(fontSize: 14, color: AppTheme.textGray), textAlign: TextAlign.center),
    const SizedBox(height: 28),
    TextField(
      controller: _emailCtrl,
      keyboardType: TextInputType.emailAddress,
      decoration: AppTheme.inputDecoration('Email Address', icon: Icons.email_outlined).copyWith(errorText: _emailErr),
    ),
    const SizedBox(height: 22),
    SizedBox(
      width: double.infinity, height: 50,
      child: ElevatedButton(
        onPressed: _loading ? null : _send,
        style: ElevatedButton.styleFrom(
          backgroundColor: AppTheme.primaryCyan, foregroundColor: Colors.white,
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
          disabledBackgroundColor: AppTheme.primaryCyan.withOpacity(0.5),
        ),
        child: _loading
            ? const SizedBox(width: 22, height: 22, child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2.5))
            : const Text('Send Reset Link', style: TextStyle(fontSize: 16, fontWeight: FontWeight.w700)),
      ),
    ),
    const SizedBox(height: 24),
    GestureDetector(
        onTap: () => context.go('/login'),
        child: const Text('← Back to Sign In',
            style: TextStyle(fontSize: 14, color: AppTheme.primaryCyan, fontWeight: FontWeight.w600))),
  ]);

  Widget _sentView() => Column(children: [
    Container(width: 80, height: 80,
        decoration: BoxDecoration(color: AppTheme.successGreen.withOpacity(0.1), borderRadius: BorderRadius.circular(40)),
        child: const Icon(Icons.check_circle_outlined, color: AppTheme.successGreen, size: 44)),
    const SizedBox(height: 24),
    const Text('Email Sent!', style: TextStyle(fontSize: 26, fontWeight: FontWeight.w700, color: AppTheme.textDark)),
    const SizedBox(height: 10),
    const Text("If this email is registered, a reset link has been sent. Please check your inbox.",
        style: TextStyle(fontSize: 14, color: AppTheme.textGray), textAlign: TextAlign.center),
    const SizedBox(height: 32),
    SizedBox(
      width: double.infinity, height: 50,
      child: ElevatedButton(
        onPressed: () => context.go('/login'),
        style: ElevatedButton.styleFrom(
            backgroundColor: AppTheme.primaryCyan, foregroundColor: Colors.white,
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12))),
        child: const Text('Back to Sign In', style: TextStyle(fontSize: 16, fontWeight: FontWeight.w700)),
      ),
    ),
    const SizedBox(height: 18),
    GestureDetector(
        onTap: () => setState(() => _sent = false),
        child: const Text('Resend Email',
            style: TextStyle(fontSize: 14, color: AppTheme.primaryCyan, fontWeight: FontWeight.w600))),
  ]);

  @override
  void dispose() { _emailCtrl.dispose(); super.dispose(); }
}