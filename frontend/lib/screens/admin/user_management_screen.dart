import 'package:flutter/material.dart';
import '../../theme/app_theme.dart';
import '../../services/auth_service.dart';
import '../../services/api_service.dart';

class UserManagementScreen extends StatefulWidget {
  const UserManagementScreen({super.key});
  @override
  State<UserManagementScreen> createState() => _UMState();
}

class _UMState extends State<UserManagementScreen> {
  final _searchCtrl = TextEditingController();
  List<Map<String, dynamic>> _users = [];
  bool _loading = true;
  String _filter = 'All';

  @override
  void initState() { super.initState(); _fetchUsers(); }

  Future<void> _fetchUsers() async {
    setState(() => _loading = true);
    try {
      final res = await ApiService().getAdminUsers();
      _users = (res['users'] as List).cast<Map<String, dynamic>>();
    } catch (e) {
      debugPrint('fetchUsers error: $e');
    }
    if (mounted) setState(() => _loading = false);
  }

  Future<void> _changeRole(String uid, String newRole) async {
    try {
      await ApiService().updateUserRole(uid, newRole);
      setState(() {
        final u = _users.firstWhere((u) => u['uid'] == uid);
        u['role'] = newRole;
      });
    } catch (e) {
      debugPrint('changeRole error: $e');
    }
  }

  List<Map<String, dynamic>> get _filtered => _users.where((u) {
    final name  = (u['fullName'] ?? '').toString().toLowerCase();
    final email = (u['email']    ?? '').toString().toLowerCase();
    final q = _searchCtrl.text.trim().toLowerCase();
    return (q.isEmpty || name.contains(q) || email.contains(q)) &&
        (_filter == 'All' || u['role'] == _filter);
  }).toList();

  @override
  Widget build(BuildContext context) {
    final list  = _filtered;
    final myUid = AuthService().uid;

    return SingleChildScrollView(
      padding: const EdgeInsets.all(32),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        // Search + filter
        Wrap(spacing: 12, runSpacing: 12, children: [
          SizedBox(
            width: 300,
            child: TextField(
              controller: _searchCtrl,
              onChanged: (_) => setState(() {}),
              decoration: AppTheme.inputDecoration('Search users...', icon: Icons.search)
                  .copyWith(contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10)),
            ),
          ),
          ...['All', 'admin', 'user'].map((f) => GestureDetector(
            onTap: () => setState(() => _filter = f),
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
              decoration: BoxDecoration(
                color: _filter == f ? AppTheme.primaryCyan : Colors.white.withOpacity(0.8),
                border: Border.all(color: _filter == f ? AppTheme.primaryCyan : Colors.grey.shade200),
                borderRadius: BorderRadius.circular(18),
              ),
              child: Text(f == 'All' ? 'All' : (f[0].toUpperCase() + f.substring(1)),
                  style: TextStyle(fontSize: 12, fontWeight: FontWeight.w600,
                      color: _filter == f ? Colors.white : AppTheme.textGray)),
            ),
          )),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
            decoration: BoxDecoration(color: Colors.white.withOpacity(0.8), borderRadius: BorderRadius.circular(18)),
            child: Text('${_users.length} total users', style: const TextStyle(fontSize: 12, color: AppTheme.textGray)),
          ),
          // Refresh button
          GestureDetector(
            onTap: _fetchUsers,
            child: Container(
              padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
              decoration: BoxDecoration(color: AppTheme.primaryCyan.withOpacity(0.1), borderRadius: BorderRadius.circular(18), border: Border.all(color: AppTheme.primaryCyan.withOpacity(0.3))),
              child: const Row(mainAxisSize: MainAxisSize.min, children: [
                Icon(Icons.refresh, size: 16, color: AppTheme.primaryCyan),
                SizedBox(width: 6),
                Text('Refresh', style: TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: AppTheme.primaryCyan)),
              ]),
            ),
          ),
        ]),
        const SizedBox(height: 18),

        if (_loading)
          const Center(child: Padding(padding: EdgeInsets.all(40), child: CircularProgressIndicator(color: AppTheme.primaryCyan)))
        else
          SingleChildScrollView(
            scrollDirection: Axis.horizontal,
            child: Container(
              decoration: AppTheme.glassCard,
              child: Column(children: [
                // Header
                Container(
                  color: Colors.white.withOpacity(0.5),
                  padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
                  child: Row(children: [
                    const SizedBox(width: 38),
                    _headerCell('Name', 200),
                    _headerCell('Email', 240),
                    _headerCell('Role', 100),
                    _headerCell('Joined', 140),
                    const SizedBox(width: 120),
                  ]),
                ),
                const Divider(height: 1, color: Colors.grey),

                // Rows
                ...list.map((u) {
                  final isMe = u['uid'] == myUid;
                  final role = (u['role'] as String? ?? 'user');
                  final roleColor = role == 'admin' ? AppTheme.errorRed : AppTheme.primaryCyan;
                  final createdAt = u['createdAt']?.toString().split('T').first ?? '—';

                  return Container(
                    padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 12),
                    decoration: BoxDecoration(border: Border(bottom: BorderSide(color: Colors.grey.shade100))),
                    child: Row(children: [
                      // Avatar
                      Container(width: 34, height: 34,
                          decoration: BoxDecoration(gradient: AppTheme.primaryGradient, borderRadius: BorderRadius.circular(17)),
                          child: Center(child: Text(
                              ((u['fullName'] as String? ?? '?').isNotEmpty ? (u['fullName'] as String)[0] : '?').toUpperCase(),
                              style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w700, color: Colors.white)))),
                      const SizedBox(width: 4),

                      // Name
                      SizedBox(width: 200, child: Row(children: [
                        Flexible(child: Text(u['fullName'] ?? '—',
                            overflow: TextOverflow.ellipsis,
                            style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w600, color: AppTheme.textDark))),
                        if (isMe) ...[const SizedBox(width: 6),
                          Container(padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                              decoration: BoxDecoration(color: Colors.grey.shade100, borderRadius: BorderRadius.circular(8)),
                              child: const Text('You', style: TextStyle(fontSize: 10, fontWeight: FontWeight.w700, color: AppTheme.textGray)))],
                      ])),

                      // Email
                      SizedBox(width: 240, child: Text(u['email'] ?? '—',
                          overflow: TextOverflow.ellipsis,
                          style: const TextStyle(fontSize: 13, color: AppTheme.textGray))),

                      // Role badge
                      SizedBox(width: 100, child: Container(
                          padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                          decoration: BoxDecoration(color: roleColor.withOpacity(0.1), borderRadius: BorderRadius.circular(14)),
                          child: Text(role == 'admin' ? 'Admin' : 'User',
                              textAlign: TextAlign.center,
                              style: TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: roleColor)))),

                      // Joined
                      SizedBox(width: 140, child: Text(createdAt,
                          style: const TextStyle(fontSize: 13, color: AppTheme.textGray))),

                      // Action
                      SizedBox(width: 120, child: isMe ? const SizedBox() :
                      ElevatedButton(
                          onPressed: () => _changeRole(u['uid'], role == 'admin' ? 'user' : 'admin'),
                          style: ElevatedButton.styleFrom(
                            backgroundColor: role == 'admin' ? Colors.grey.shade200 : AppTheme.primaryCyan.withOpacity(0.12),
                            foregroundColor: role == 'admin' ? AppTheme.textGray : AppTheme.primaryCyan,
                            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 6),
                          ),
                          child: Text(role == 'admin' ? 'Demote' : 'Promote',
                              style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600)))),
                    ]),
                  );
                }),

                if (list.isEmpty)
                  const Padding(padding: EdgeInsets.all(40),
                      child: Center(child: Text('No users found', style: TextStyle(color: AppTheme.textGray)))),
              ]),
            ),
          ),
      ]),
    );
  }

  Widget _headerCell(String label, double width) => SizedBox(width: width,
      child: Text(label, style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w700, color: AppTheme.textGray, letterSpacing: 0.5)));

  @override
  void dispose() { _searchCtrl.dispose(); super.dispose(); }
}