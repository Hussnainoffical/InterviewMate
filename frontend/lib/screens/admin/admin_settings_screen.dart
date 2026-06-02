import 'package:flutter/material.dart';
import '../../theme/app_theme.dart';
import '../../services/auth_service.dart';
import '../../services/api_service.dart';

class AdminSettingsScreen extends StatefulWidget {
  const AdminSettingsScreen({super.key});
  @override
  State<AdminSettingsScreen> createState() => _AdminSettingsScreenState();
}

class _AdminSettingsScreenState extends State<AdminSettingsScreen> {
  final _nameCtrl  = TextEditingController();
  final _emailCtrl = TextEditingController();
  final _phoneCtrl = TextEditingController();
  bool _loading = true;

  @override
  void initState() { super.initState(); _loadAdminData(); }

  Future<void> _loadAdminData() async {
    setState(() => _loading = true);
    final uid = AuthService().uid;
    if (uid == null) { setState(() => _loading = false); return; }
    try {
      final data = await ApiService().getProfile(uid);
      if (!mounted) return;
      setState(() {
        _nameCtrl.text  = data['fullName']    ?? '';
        _emailCtrl.text = data['email']       ?? '';
        _phoneCtrl.text = data['phoneNumber'] ?? '';
        _loading = false;
      });
    } catch (_) {
      if (!mounted) return;
      setState(() {
        _nameCtrl.text  = AuthService().fullName ?? '';
        _emailCtrl.text = AuthService().email    ?? '';
        _loading = false;
      });
    }
  }

  Future<void> _saveSettings() async {
    final uid = AuthService().uid;
    if (uid == null) return;
    try {
      await ApiService().updateProfile(uid, {
        'fullName':    _nameCtrl.text.trim(),
        'phoneNumber': _phoneCtrl.text.trim(),
      });
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Settings updated successfully'), backgroundColor: AppTheme.successGreen));
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Error: $e'), backgroundColor: AppTheme.errorRed));
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_loading) return const Center(child: CircularProgressIndicator(color: AppTheme.primaryCyan));

    return SingleChildScrollView(
      padding: const EdgeInsets.all(32),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        // Profile section
        Container(decoration: AppTheme.glassCard, padding: const EdgeInsets.all(32),
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              const Text('Profile Information',
                  style: TextStyle(fontSize: 18, fontWeight: FontWeight.w700, color: AppTheme.textDark)),
              const SizedBox(height: 24),

              // Avatar
              Row(children: [
                Container(width: 100, height: 100,
                    decoration: BoxDecoration(gradient: AppTheme.primaryGradient, borderRadius: BorderRadius.circular(50),
                        border: Border.all(color: AppTheme.primaryCyan.withOpacity(0.3), width: 3)),
                    child: const Icon(Icons.person, size: 50, color: Colors.white)),
                const SizedBox(width: 24),
                Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                  const Text('Profile Picture', style: TextStyle(fontSize: 16, fontWeight: FontWeight.w600, color: AppTheme.textDark)),
                  const SizedBox(height: 8),
                  const Text('Profile picture upload available in Phase 3', style: TextStyle(fontSize: 13, color: AppTheme.textGray)),
                  const SizedBox(height: 12),
                  ElevatedButton.icon(
                    onPressed: () => ScaffoldMessenger.of(context).showSnackBar(
                        const SnackBar(content: Text('Image upload coming in Phase 3'), backgroundColor: AppTheme.textGray)),
                    icon: const Icon(Icons.upload_outlined, size: 18),
                    label: const Text('Upload New Picture'),
                    style: ElevatedButton.styleFrom(
                        backgroundColor: AppTheme.primaryCyan.withOpacity(0.12), foregroundColor: AppTheme.primaryCyan,
                        elevation: 0, padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10))),
                  ),
                ])),
              ]),
              const SizedBox(height: 32),

              _buildTextField('Full Name',     _nameCtrl,  Icons.person_outline),
              const SizedBox(height: 20),
              _buildTextField('Email Address', _emailCtrl, Icons.email_outlined, readOnly: true),
              const SizedBox(height: 20),
              _buildTextField('Phone Number',  _phoneCtrl, Icons.phone_outlined),
              const SizedBox(height: 32),

              Row(children: [
                ElevatedButton(onPressed: _saveSettings,
                    style: ElevatedButton.styleFrom(backgroundColor: AppTheme.primaryCyan, foregroundColor: Colors.white,
                        padding: const EdgeInsets.symmetric(horizontal: 32, vertical: 16),
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12))),
                    child: const Text('Save Changes', style: TextStyle(fontSize: 14, fontWeight: FontWeight.w600))),
                const SizedBox(width: 12),
                TextButton(onPressed: _loadAdminData,
                    style: TextButton.styleFrom(foregroundColor: AppTheme.textGray,
                        padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 16)),
                    child: const Text('Reset', style: TextStyle(fontSize: 14, fontWeight: FontWeight.w600))),
              ]),
            ])),
        const SizedBox(height: 24),

        // Security section
        Container(decoration: AppTheme.glassCard, padding: const EdgeInsets.all(32),
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              const Text('Security', style: TextStyle(fontSize: 18, fontWeight: FontWeight.w700, color: AppTheme.textDark)),
              const SizedBox(height: 16),
              _buildSecurityOption('Change Password', 'Update your password to keep your account secure', Icons.lock_outline),
              const SizedBox(height: 12),
              _buildSecurityOption('Two-Factor Authentication', 'Add an extra layer of security to your account', Icons.security_outlined),
            ])),
      ]),
    );
  }

  Widget _buildTextField(String label, TextEditingController ctrl, IconData icon, {bool readOnly = false}) =>
      Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Text(label, style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w600, color: AppTheme.textDark)),
        const SizedBox(height: 8),
        TextField(controller: ctrl, readOnly: readOnly,
            decoration: InputDecoration(
              prefixIcon: Icon(icon, color: AppTheme.primaryCyan, size: 20),
              filled: true, fillColor: readOnly ? Colors.grey.shade100 : Colors.white.withOpacity(0.7),
              border:        OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: BorderSide(color: Colors.grey.shade200)),
              enabledBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: BorderSide(color: Colors.grey.shade200)),
              focusedBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(12), borderSide: const BorderSide(color: AppTheme.primaryCyan, width: 2)),
              contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
            )),
      ]);

  Widget _buildSecurityOption(String title, String subtitle, IconData icon) =>
      Container(padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(color: Colors.white.withOpacity(0.7), borderRadius: BorderRadius.circular(12), border: Border.all(color: Colors.grey.shade200)),
          child: Row(children: [
            Container(width: 48, height: 48,
                decoration: BoxDecoration(color: AppTheme.primaryCyan.withOpacity(0.1), borderRadius: BorderRadius.circular(12)),
                child: Icon(icon, color: AppTheme.primaryCyan, size: 24)),
            const SizedBox(width: 16),
            Expanded(child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              Text(title, style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w600, color: AppTheme.textDark)),
              const SizedBox(height: 4),
              Text(subtitle, style: const TextStyle(fontSize: 12, color: AppTheme.textGray)),
            ])),
            const Icon(Icons.chevron_right, color: AppTheme.textGray, size: 20),
          ]));

  @override
  void dispose() { _nameCtrl.dispose(); _emailCtrl.dispose(); _phoneCtrl.dispose(); super.dispose(); }
}