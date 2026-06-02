import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import '../../theme/app_theme.dart';
import '../../widgets/auth_widgets.dart';
import '../../services/auth_service.dart';
import '../../services/api_service.dart';

class SignupScreen extends StatefulWidget {
  const SignupScreen({super.key});
  @override
  State<SignupScreen> createState() => _SignupScreenState();
}

class _SignupScreenState extends State<SignupScreen> {
  final _nameCtrl  = TextEditingController();
  final _emailCtrl = TextEditingController();
  final _phoneCtrl = TextEditingController();
  final _passCtrl  = TextEditingController();
  final _confCtrl  = TextEditingController();

  bool _showPass = false, _showConf = false;
  bool _terms = false, _loading = false;
  String? _nameErr, _emailErr, _phoneErr, _passErr, _confErr;
  int _strength = 0;

  void _calcStrength() {
    final p = _passCtrl.text;
    int s = 0;
    if (p.length >= 8) s++;
    if (p.contains(RegExp(r'[A-Z]'))) s++;
    if (p.contains(RegExp(r'[a-z]'))) s++;
    if (p.contains(RegExp(r'[0-9]'))) s++;
    if (p.contains(RegExp(r'[!@#$%^&*]'))) s++;
    setState(() => _strength = s.clamp(0, 4));
  }

  String get _strengthLabel => ['', 'Weak', 'Fair', 'Good', 'Strong'][_strength];
  Color  get _strengthColor  => [Colors.transparent, AppTheme.errorRed, Colors.orange, Colors.blue, AppTheme.successGreen][_strength];

  bool _validateForm() {
    setState(() {
      _nameErr = _nameCtrl.text.trim().length < 3 ? 'Name must be at least 3 characters' : null;
      _emailErr = _emailCtrl.text.trim().isEmpty ? 'Email is required'
          : !RegExp(r'^[\w-.]+@([\w-]+\.)+[\w-]{2,4}$').hasMatch(_emailCtrl.text.trim()) ? 'Enter a valid email' : null;
      final phone = _phoneCtrl.text.trim();
      _phoneErr = phone.isNotEmpty && !RegExp(r'^\+?[\d]{10,15}$').hasMatch(phone) ? 'Enter a valid phone number' : null;
      _passErr = _passCtrl.text.length < 8 ? 'Password must be at least 8 characters'
          : !_passCtrl.text.contains(RegExp(r'[A-Z]')) ? 'Must include an uppercase letter'
          : !_passCtrl.text.contains(RegExp(r'[a-z]')) ? 'Must include a lowercase letter'
          : !_passCtrl.text.contains(RegExp(r'[0-9]')) ? 'Must include a number' : null;
      _confErr = _passCtrl.text != _confCtrl.text ? 'Passwords do not match' : null;
    });
    return _nameErr == null && _emailErr == null && _phoneErr == null && _passErr == null && _confErr == null;
  }

  Future<void> _createAccount() async {
    if (!_validateForm()) return;
    if (!_terms) {
      ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Please accept Terms & Conditions'), backgroundColor: AppTheme.errorRed));
      return;
    }
    setState(() => _loading = true);
    try {
      await AuthService().register(
        fullName: _nameCtrl.text.trim(),
        email: _emailCtrl.text.trim(),
        password: _passCtrl.text,
        phoneNumber: _phoneCtrl.text.trim().isNotEmpty ? _phoneCtrl.text.trim() : null,
      );
      if (!mounted) return;
      final role = AuthService().role;
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(
        content: Text(role == 'admin' ? 'Welcome! You are the platform admin.' : 'Account created successfully!'),
        backgroundColor: AppTheme.successGreen,
      ));
      context.go(role == 'admin' ? '/admin/dashboard' : '/dashboard');
    } on ApiException catch (e) {
      if (!mounted) return;
      if (e.statusCode == 409) setState(() => _emailErr = 'An account with this email already exists.');
      else setState(() => _emailErr = e.message);
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
          title: 'Create Account',
          subtitle: 'Join thousands of professionals preparing for interviews',
        ),

        // Name
        TextField(controller: _nameCtrl,
            decoration: AppTheme.inputDecoration('Full Name', icon: Icons.person_outlined).copyWith(errorText: _nameErr)),
        const SizedBox(height: 14),

        // Email
        TextField(controller: _emailCtrl, keyboardType: TextInputType.emailAddress,
            decoration: AppTheme.inputDecoration('Email Address', icon: Icons.email_outlined).copyWith(errorText: _emailErr)),
        const SizedBox(height: 14),

        // Phone
        TextField(controller: _phoneCtrl, keyboardType: const TextInputType.numberWithOptions(signed: true),
            decoration: AppTheme.inputDecoration('Phone Number (optional)', icon: Icons.phone_outlined).copyWith(errorText: _phoneErr)),
        const SizedBox(height: 14),

        // Password
        TextField(
          controller: _passCtrl, obscureText: !_showPass,
          onChanged: (_) => _calcStrength(),
          decoration: AppTheme.inputDecoration('Password', icon: Icons.lock_outlined).copyWith(
            errorText: _passErr,
            suffixIcon: IconButton(
                icon: Icon(_showPass ? Icons.visibility_off_outlined : Icons.visibility_outlined, color: AppTheme.textGray),
                onPressed: () => setState(() => _showPass = !_showPass)),
          ),
        ),

        // Strength bar
        const SizedBox(height: 8),
        Row(children: [
          Expanded(child: Row(children: List.generate(4, (i) => Expanded(child: Padding(
            padding: EdgeInsets.only(right: i < 3 ? 4 : 0),
            child: SizedBox(height: 4, child: Container(decoration: BoxDecoration(
                color: i < _strength ? _strengthColor : Colors.grey.shade200,
                borderRadius: BorderRadius.circular(2)))),
          ))))),
          const SizedBox(width: 10),
          if (_strength > 0) Text(_strengthLabel, style: TextStyle(fontSize: 11, fontWeight: FontWeight.w600, color: _strengthColor)),
        ]),
        const SizedBox(height: 14),

        // Confirm password
        TextField(
          controller: _confCtrl, obscureText: !_showConf,
          decoration: AppTheme.inputDecoration('Confirm Password', icon: Icons.lock_outlined).copyWith(
            errorText: _confErr,
            suffixIcon: IconButton(
                icon: Icon(_showConf ? Icons.visibility_off_outlined : Icons.visibility_outlined, color: AppTheme.textGray),
                onPressed: () => setState(() => _showConf = !_showConf)),
          ),
        ),
        const SizedBox(height: 16),

        // Terms
        Row(children: [
          SizedBox(width: 20, height: 20, child: Checkbox(
            value: _terms, onChanged: (v) => setState(() => _terms = v!),
            activeColor: AppTheme.primaryCyan,
            materialTapTargetSize: MaterialTapTargetSize.shrinkWrap,
          )),
          const SizedBox(width: 6),
          const Expanded(child: Text.rich(TextSpan(children: [
            TextSpan(text: 'I agree to the ', style: TextStyle(fontSize: 13, color: AppTheme.textGray)),
            TextSpan(text: 'Terms & Conditions', style: TextStyle(fontSize: 13, color: AppTheme.primaryCyan, fontWeight: FontWeight.w600)),
            TextSpan(text: ' and ', style: TextStyle(fontSize: 13, color: AppTheme.textGray)),
            TextSpan(text: 'Privacy Policy', style: TextStyle(fontSize: 13, color: AppTheme.primaryCyan, fontWeight: FontWeight.w600)),
          ]))),
        ]),
        const SizedBox(height: 22),

        // Create Account button
        SizedBox(
          width: double.infinity, height: 50,
          child: ElevatedButton(
            onPressed: _loading ? null : _createAccount,
            style: ElevatedButton.styleFrom(
              backgroundColor: AppTheme.primaryCyan, foregroundColor: Colors.white,
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
              disabledBackgroundColor: AppTheme.primaryCyan.withOpacity(0.5),
            ),
            child: _loading
                ? const SizedBox(width: 22, height: 22, child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2.5))
                : const Text('Create Account', style: TextStyle(fontSize: 16, fontWeight: FontWeight.w700)),
          ),
        ),
        const SizedBox(height: 20),
        const OrDivider(),
        const SizedBox(height: 16),
        GoogleButton(label: 'Sign up with Google', onPressed: () =>
            ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(content: Text('Google Sign Up — coming in Phase 4'), backgroundColor: AppTheme.textGray))),
        const SizedBox(height: 24),

        Row(mainAxisAlignment: MainAxisAlignment.center, children: [
          const Text('Already have an account? ', style: TextStyle(fontSize: 14, color: AppTheme.textGray)),
          GestureDetector(
              onTap: () => context.go('/login'),
              child: const Text('Sign In',
                  style: TextStyle(fontSize: 14, color: AppTheme.primaryCyan, fontWeight: FontWeight.w700))),
        ]),
      ]),
    );
  }

  @override
  void dispose() { _nameCtrl.dispose(); _emailCtrl.dispose(); _phoneCtrl.dispose(); _passCtrl.dispose(); _confCtrl.dispose(); super.dispose(); }
}