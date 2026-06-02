import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import '../../theme/app_theme.dart';
import '../../widgets/auth_widgets.dart';
import '../../services/auth_service.dart';
import '../../services/api_service.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});
  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _emailCtrl = TextEditingController();
  final _passCtrl  = TextEditingController();
  bool _showPass = false;
  bool _loading  = false;
  String? _emailErr, _passErr;

  void _validate() {
    setState(() {
      _emailErr = _emailCtrl.text.trim().isEmpty
          ? 'Email is required'
          : !RegExp(r'^[\w-.]+@([\w-]+\.)+[\w-]{2,4}$').hasMatch(_emailCtrl.text.trim())
          ? 'Enter a valid email'
          : null;
      _passErr = _passCtrl.text.isEmpty ? 'Password is required' : null;
    });
  }

  Future<void> _signIn() async {
    _validate();
    if (_emailErr != null || _passErr != null) return;
    setState(() => _loading = true);
    try {
      await AuthService().login(
        email: _emailCtrl.text.trim(),
        password: _passCtrl.text,
      );
      if (!mounted) return;
      final role = AuthService().role;
      context.go(role == 'admin' ? '/admin/dashboard' : '/dashboard');
    } on ApiException catch (e) {
      if (!mounted) return;
      setState(() => _emailErr = e.message);
    } catch (e) {
      if (!mounted) return;
      setState(() => _emailErr = 'Cannot connect to server. Is the backend running?');
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return AuthLayout(
      child: Column(children: [
        const AuthHeader(
          title: 'Welcome Back',
          subtitle: 'Sign in to continue your interview practice',
        ),

        // Email
        TextField(
          controller: _emailCtrl,
          keyboardType: TextInputType.emailAddress,
          decoration: AppTheme.inputDecoration('Email Address', icon: Icons.email_outlined)
              .copyWith(errorText: _emailErr),
        ),
        const SizedBox(height: 14),

        // Password
        TextField(
          controller: _passCtrl,
          obscureText: !_showPass,
          decoration: AppTheme.inputDecoration('Password', icon: Icons.lock_outlined)
              .copyWith(
            errorText: _passErr,
            suffixIcon: IconButton(
              icon: Icon(_showPass ? Icons.visibility_off_outlined : Icons.visibility_outlined,
                  color: AppTheme.textGray),
              onPressed: () => setState(() => _showPass = !_showPass),
            ),
          ),
        ),
        const SizedBox(height: 10),

        // Remember me + Forgot
        Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [
          const SizedBox(),
          GestureDetector(
            onTap: () => context.go('/forgot-password'),
            child: const Text('Forgot Password?',
                style: TextStyle(fontSize: 13, color: AppTheme.primaryCyan, fontWeight: FontWeight.w600)),
          ),
        ]),
        const SizedBox(height: 22),

        // Sign In button
        SizedBox(
          width: double.infinity, height: 50,
          child: ElevatedButton(
            onPressed: _loading ? null : _signIn,
            style: ElevatedButton.styleFrom(
              backgroundColor: AppTheme.primaryCyan,
              foregroundColor: Colors.white,
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
              disabledBackgroundColor: AppTheme.primaryCyan.withOpacity(0.5),
            ),
            child: _loading
                ? const SizedBox(width: 22, height: 22,
                child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2.5))
                : const Text('Sign In', style: TextStyle(fontSize: 16, fontWeight: FontWeight.w700)),
          ),
        ),
        const SizedBox(height: 20),
        const OrDivider(),
        const SizedBox(height: 16),
        GoogleButton(
          label: 'Sign in with Google',
          onPressed: () => ScaffoldMessenger.of(context).showSnackBar(
              const SnackBar(content: Text('Google Sign In — coming in Phase 4'), backgroundColor: AppTheme.textGray)),
        ),
        const SizedBox(height: 24),

        Row(mainAxisAlignment: MainAxisAlignment.center, children: [
          const Text("Don't have an account? ", style: TextStyle(fontSize: 14, color: AppTheme.textGray)),
          GestureDetector(
            onTap: () => context.go('/signup'),
            child: const Text('Sign Up',
                style: TextStyle(fontSize: 14, color: AppTheme.primaryCyan, fontWeight: FontWeight.w700)),
          ),
        ]),
      ]),
    );
  }

  @override
  void dispose() { _emailCtrl.dispose(); _passCtrl.dispose(); super.dispose(); }
}