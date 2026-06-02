import 'package:flutter/material.dart';
import '../../theme/app_theme.dart';
import '../../services/auth_service.dart';
import '../../services/api_service.dart';

extension _LMI<T> on List<T> {
  List<R> mapIndexed<R>(R Function(int i, T item) f) =>
      List.generate(length, (i) => f(i, this[i]));
}

class ProfileSettingsScreen extends StatefulWidget {
  const ProfileSettingsScreen({super.key});
  @override
  State<ProfileSettingsScreen> createState() => _PSState();
}

class _PSState extends State<ProfileSettingsScreen> {
  final _nameCtrl  = TextEditingController();
  final _emailCtrl = TextEditingController();
  final _phoneCtrl = TextEditingController();
  final _titleCtrl = TextEditingController();
  final _cityCtrl  = TextEditingController();
  final _skillCtrl = TextEditingController();

  bool _notifications = true, _emailNotif = true, _darkMode = false;
  int  _selectedTab = 0;
  bool _loading = true;
  List<String> _skills = [];

  @override
  void initState() { super.initState(); _loadUserData(); }

  Future<void> _loadUserData() async {
    final uid = AuthService().uid;
    if (uid == null) { setState(() => _loading = false); return; }
    try {
      final data = await ApiService().getProfile(uid);
      if (!mounted) return;
      setState(() {
        _nameCtrl.text  = data['fullName']    ?? '';
        _emailCtrl.text = data['email']       ?? '';
        _phoneCtrl.text = data['phoneNumber'] ?? '';
        _titleCtrl.text = data['jobTitle']    ?? '';
        _cityCtrl.text  = data['city']        ?? '';
        _skills = List<String>.from(data['skills'] ?? []);
        _loading = false;
      });
    } catch (_) {
      // Pre-fill from local session if backend is unavailable
      if (!mounted) return;
      setState(() {
        _nameCtrl.text  = AuthService().fullName ?? '';
        _emailCtrl.text = AuthService().email    ?? '';
        _loading = false;
      });
    }
  }

  Future<void> _saveProfile() async {
    final uid = AuthService().uid;
    if (uid == null) return;
    try {
      await ApiService().updateProfile(uid, {
        'fullName':    _nameCtrl.text.trim(),
        'phoneNumber': _phoneCtrl.text.trim(),
        'jobTitle':    _titleCtrl.text.trim(),
        'city':        _cityCtrl.text.trim(),
        'skills':      _skills,
      });
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Profile updated successfully!'), backgroundColor: AppTheme.successGreen));
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Error: $e'), backgroundColor: AppTheme.errorRed));
    }
  }

  void _addSkill() {
    final s = _skillCtrl.text.trim();
    if (s.isEmpty || _skills.contains(s)) return;
    setState(() { _skills.add(s); _skillCtrl.clear(); });
  }

  void _removeSkill(String s) => setState(() => _skills.remove(s));

  @override
  Widget build(BuildContext context) {
    if (_loading) return const Center(child: CircularProgressIndicator(color: AppTheme.primaryCyan));

    return SingleChildScrollView(
      padding: const EdgeInsets.all(24),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        _glassCard(padding: 22, child: const Text('Profile & Settings',
            style: TextStyle(fontSize: 22, fontWeight: FontWeight.w800, color: AppTheme.textDark))),
        const SizedBox(height: 20),
        LayoutBuilder(builder: (ctx, constraints) {
          if (constraints.maxWidth < 600) {
            return Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              _leftPanel(), const SizedBox(height: 20), _rightPanel()]);
          }
          return Row(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Expanded(flex: 2, child: _leftPanel()),
            const SizedBox(width: 20),
            Expanded(flex: 3, child: _rightPanel()),
          ]);
        }),
      ]),
    );
  }

  Widget _leftPanel() => Column(children: [
    _glassCard(padding: 22, child: Column(children: [
      Container(width: 80, height: 80,
          decoration: BoxDecoration(gradient: AppTheme.primaryGradient, borderRadius: BorderRadius.circular(40)),
          child: const Icon(Icons.person_outlined, color: Colors.white, size: 40)),
      const SizedBox(height: 12),
      Text(_nameCtrl.text.isEmpty ? 'User' : _nameCtrl.text,
          style: const TextStyle(fontSize: 17, fontWeight: FontWeight.w700, color: AppTheme.textDark)),
      Text(_emailCtrl.text, style: const TextStyle(fontSize: 13, color: AppTheme.textGray)),
      const SizedBox(height: 8),
      Container(
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
          decoration: BoxDecoration(color: AppTheme.primaryCyan.withOpacity(0.1), borderRadius: BorderRadius.circular(14)),
          child: const Text('Free Plan', style: TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: AppTheme.primaryCyan))),
    ])),
    const SizedBox(height: 14),
    ...[
      ['Profile', Icons.person_outlined],
      ['Interview Preferences', Icons.mic_outlined],
      ['Notifications', Icons.notifications_outlined],
      ['Security', Icons.lock_outlined],
    ].mapIndexed((i, tab) => Padding(
      padding: const EdgeInsets.only(bottom: 4),
      child: GestureDetector(
        onTap: () => setState(() => _selectedTab = i),
        child: Container(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
          decoration: BoxDecoration(
            color: i == _selectedTab ? AppTheme.primaryCyan.withOpacity(0.08) : Colors.white.withOpacity(0.6),
            borderRadius: BorderRadius.circular(12),
            border: i == _selectedTab ? Border.all(color: AppTheme.primaryCyan.withOpacity(0.22)) : Border.all(color: Colors.grey.shade200),
          ),
          child: Row(children: [
            Icon(tab[1] as IconData, size: 19, color: i == _selectedTab ? AppTheme.primaryCyan : AppTheme.textGray),
            const SizedBox(width: 10),
            Expanded(child: Text(tab[0] as String, overflow: TextOverflow.ellipsis,
                style: TextStyle(fontSize: 14, fontWeight: FontWeight.w600,
                    color: i == _selectedTab ? AppTheme.primaryCyan : AppTheme.textDark))),
          ]),
        ),
      ),
    )),
  ]);

  Widget _rightPanel() => _selectedTab == 0 ? _profileTab()
      : _selectedTab == 1 ? _preferencesTab()
      : _selectedTab == 2 ? _notificationsTab()
      : _securityTab();

  Widget _profileTab() => _glassCard(padding: 24, child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
    const Text('Personal Information', style: TextStyle(fontSize: 17, fontWeight: FontWeight.w700, color: AppTheme.textDark)),
    const SizedBox(height: 20),
    LayoutBuilder(builder: (ctx, c) => c.maxWidth < 400
        ? Column(children: [_field('Full Name', _nameCtrl, Icons.person_outlined), const SizedBox(height: 14), _field('Email Address', _emailCtrl, Icons.email_outlined)])
        : Row(children: [Expanded(child: _field('Full Name', _nameCtrl, Icons.person_outlined)), const SizedBox(width: 16), Expanded(child: _field('Email Address', _emailCtrl, Icons.email_outlined))])),
    const SizedBox(height: 14),
    LayoutBuilder(builder: (ctx, c) => c.maxWidth < 400
        ? Column(children: [_field('Phone Number', _phoneCtrl, Icons.phone_outlined), const SizedBox(height: 14), _field('Job Title', _titleCtrl, Icons.work_outlined)])
        : Row(children: [Expanded(child: _field('Phone Number', _phoneCtrl, Icons.phone_outlined)), const SizedBox(width: 16), Expanded(child: _field('Job Title', _titleCtrl, Icons.work_outlined))])),
    const SizedBox(height: 14),
    _field('City', _cityCtrl, Icons.location_on_outlined),
    const SizedBox(height: 22),
    const Divider(),
    const SizedBox(height: 18),
    const Text('Skills', style: TextStyle(fontSize: 16, fontWeight: FontWeight.w700, color: AppTheme.textDark)),
    const SizedBox(height: 10),
    Row(children: [
      Expanded(child: TextField(controller: _skillCtrl, decoration: AppTheme.inputDecoration('Add a skill'), onSubmitted: (_) => _addSkill())),
      const SizedBox(width: 8),
      IconButton(onPressed: _addSkill, icon: const Icon(Icons.add_circle, color: AppTheme.primaryCyan, size: 32)),
    ]),
    const SizedBox(height: 12),
    if (_skills.isEmpty)
      const Text('No skills added yet.', style: TextStyle(fontSize: 13, color: AppTheme.textGray))
    else
      Wrap(spacing: 8, runSpacing: 8, children: _skills.map((s) => Container(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
        decoration: BoxDecoration(color: AppTheme.primaryCyan.withOpacity(0.1), border: Border.all(color: AppTheme.primaryCyan), borderRadius: BorderRadius.circular(18)),
        child: Row(mainAxisSize: MainAxisSize.min, children: [
          Text(s, style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w600, color: AppTheme.primaryCyan)),
          const SizedBox(width: 6),
          GestureDetector(onTap: () => _removeSkill(s), child: const Icon(Icons.close, size: 16, color: AppTheme.primaryCyan)),
        ]),
      )).toList()),
    const SizedBox(height: 22),
    ElevatedButton(onPressed: _saveProfile,
        style: ElevatedButton.styleFrom(backgroundColor: AppTheme.primaryCyan, foregroundColor: Colors.white,
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
            padding: const EdgeInsets.symmetric(horizontal: 32, vertical: 12)),
        child: const Text('Save Changes', style: TextStyle(fontSize: 15, fontWeight: FontWeight.w600))),
  ]));

  Widget _preferencesTab() => _glassCard(padding: 24, child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
    const Text('Interview Preferences', style: TextStyle(fontSize: 17, fontWeight: FontWeight.w700, color: AppTheme.textDark)),
    const SizedBox(height: 20),
    _prefRow('Default Interview Type', 'Behavioral'),
    _prefRow('Default Role', 'Software Engineer'),
    _prefRow('Experience Level', 'Mid-Level'),
    _prefRow('Language', 'Pakistani English'),
    _prefRow('Session Duration', '20 minutes'),
    _prefRow('Difficulty', 'Medium'),
  ]));

  Widget _notificationsTab() => _glassCard(padding: 24, child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
    const Text('Notification Settings', style: TextStyle(fontSize: 17, fontWeight: FontWeight.w700, color: AppTheme.textDark)),
    const SizedBox(height: 20),
    _toggleRow('Push Notifications', 'Receive alerts for streaks and reminders', _notifications, (v) => setState(() => _notifications = v)),
    const SizedBox(height: 16),
    _toggleRow('Email Notifications', 'Get weekly reports and tips via email', _emailNotif, (v) => setState(() => _emailNotif = v)),
    const SizedBox(height: 16),
    _toggleRow('Dark Mode', 'Switch to dark theme', _darkMode, (v) => setState(() => _darkMode = v)),
  ]));

  Widget _securityTab() => _glassCard(padding: 24, child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
    const Text('Security', style: TextStyle(fontSize: 17, fontWeight: FontWeight.w700, color: AppTheme.textDark)),
    const SizedBox(height: 20),
    _secRow('Change Password', 'Last changed 30 days ago', Icons.lock_outlined),
    _secRow('Two-Factor Auth', 'Not enabled', Icons.security_outlined),
    _secRow('Active Sessions', '1 active session', Icons.devices_outlined),
    _secRow('Delete Account', 'Permanently remove your account', Icons.delete_outlined),
  ]));

  Widget _field(String label, TextEditingController ctrl, IconData icon) =>
      TextField(controller: ctrl, decoration: AppTheme.inputDecoration(label, icon: icon));

  Widget _prefRow(String key, String value) => Padding(padding: const EdgeInsets.only(bottom: 10),
      child: Container(decoration: BoxDecoration(color: Colors.white.withOpacity(0.5), borderRadius: BorderRadius.circular(10)),
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 13),
          child: Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [
            Expanded(child: Text(key, style: const TextStyle(fontSize: 14, color: AppTheme.textDark))),
            const SizedBox(width: 12),
            Text(value, style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w600, color: AppTheme.primaryCyan)),
          ])));

  Widget _toggleRow(String title, String subtitle, bool value, Function(bool) onChange) =>
      Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [
        Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
          Text(title, style: const TextStyle(fontSize: 15, fontWeight: FontWeight.w600, color: AppTheme.textDark)),
          Text(subtitle, style: const TextStyle(fontSize: 13, color: AppTheme.textGray)),
        ])),
        Switch(value: value, onChanged: onChange, activeColor: AppTheme.primaryCyan),
      ]);

  Widget _secRow(String title, String subtitle, IconData icon) => Padding(padding: const EdgeInsets.only(bottom: 8),
      child: Container(decoration: BoxDecoration(color: Colors.white.withOpacity(0.5), borderRadius: BorderRadius.circular(10)),
          padding: const EdgeInsets.all(14),
          child: Row(children: [
            Container(width: 38, height: 38, decoration: BoxDecoration(color: AppTheme.primaryCyan.withOpacity(0.08), borderRadius: BorderRadius.circular(8)), child: Icon(icon, color: AppTheme.primaryCyan, size: 19)),
            const SizedBox(width: 12),
            Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Text(title, style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w600, color: AppTheme.textDark)),
              Text(subtitle, style: const TextStyle(fontSize: 12, color: AppTheme.textGray)),
            ])),
            const Icon(Icons.chevron_right, color: AppTheme.textGray),
          ])));

  @override
  void dispose() { _nameCtrl.dispose(); _emailCtrl.dispose(); _phoneCtrl.dispose(); _titleCtrl.dispose(); _cityCtrl.dispose(); _skillCtrl.dispose(); super.dispose(); }
}

Widget _glassCard({required Widget child, double padding = 20}) => Container(
    decoration: BoxDecoration(color: Colors.white.withOpacity(0.75), borderRadius: BorderRadius.circular(18),
        border: Border.all(color: Colors.white.withOpacity(0.8), width: 1.5),
        boxShadow: [BoxShadow(color: Colors.black.withOpacity(0.08), blurRadius: 24, offset: const Offset(0, 6))]),
    padding: EdgeInsets.all(padding), child: child);