import 'package:flutter/material.dart';
import '../../theme/app_theme.dart';

class PlanSettingsScreen extends StatefulWidget {
  const PlanSettingsScreen({super.key});
  @override
  State<PlanSettingsScreen> createState() => _PlanSettingsScreenState();
}

class _PlanSettingsScreenState extends State<PlanSettingsScreen> {
  final _priceControllers = <String, TextEditingController>{};
  bool _loading = false;

  final Map<String, Map<String, dynamic>> _plans = {
    'free':         {'name': 'Free Plan',         'price': 'Rs.0',     'period': '/month', 'color': Colors.grey,              'features': ['5 interview sessions', 'Basic analytics', 'Email support', 'Community access']},
    'basic':        {'name': 'Basic Plan',        'price': 'Rs.999',   'period': '/month', 'color': const Color(0xFF06B6D4),  'features': ['50 interview sessions', 'Basic analytics', 'Email support', 'Standard features', 'Export results']},
    'professional': {'name': 'Professional Plan', 'price': 'Rs.2,499', 'period': '/month', 'color': AppTheme.primaryCyan,     'features': ['Unlimited sessions', 'Advanced analytics', 'Priority support', 'All standard features', 'API access', 'Custom branding']},
    'enterprise':   {'name': 'Enterprise Plan',   'price': 'Rs.9,999', 'period': '/month', 'color': AppTheme.primaryPurple,   'features': ['Unlimited everything', 'Premium analytics', '24/7 phone support', 'All professional features', 'Dedicated manager', 'Custom integrations', 'SLA guarantee']},
  };

  @override
  void initState() {
    super.initState();
    _plans.forEach((key, value) =>
    _priceControllers[key] = TextEditingController(text: value['price']));
  }

  Future<void> _savePlanPricing() async {
    setState(() => _loading = true);
    // In Phase 2: POST to /api/v1/admin/plans
    await Future.delayed(const Duration(milliseconds: 800));
    _priceControllers.forEach((key, ctrl) => _plans[key]!['price'] = ctrl.text);
    if (mounted) {
      setState(() => _loading = false);
      ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Plan pricing updated successfully'), backgroundColor: AppTheme.successGreen));
    }
  }

  @override
  Widget build(BuildContext context) {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(32),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        // Stats
        Container(decoration: AppTheme.glassCard, padding: const EdgeInsets.all(24),
            child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
              const Text('Plan Statistics', style: TextStyle(fontSize: 18, fontWeight: FontWeight.w700, color: AppTheme.textDark)),
              const SizedBox(height: 20),
              Row(children: [
                Expanded(child: _statBox('Free Users',   '423', Colors.grey)),
                const SizedBox(width: 16),
                Expanded(child: _statBox('Basic Users',  '187', const Color(0xFF06B6D4))),
                const SizedBox(width: 16),
                Expanded(child: _statBox('Pro Users',     '89', AppTheme.primaryCyan)),
                const SizedBox(width: 16),
                Expanded(child: _statBox('Enterprise',    '12', AppTheme.primaryPurple)),
              ]),
            ])),
        const SizedBox(height: 32),

        // Plans header
        Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [
          const Text('Manage User Plans', style: TextStyle(fontSize: 20, fontWeight: FontWeight.w700, color: AppTheme.textDark)),
          ElevatedButton.icon(
            onPressed: _loading ? null : _savePlanPricing,
            icon: _loading
                ? const SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white))
                : const Icon(Icons.save_outlined, size: 18),
            label: const Text('Save Pricing'),
            style: ElevatedButton.styleFrom(
                backgroundColor: AppTheme.primaryCyan, foregroundColor: Colors.white,
                padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 14),
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12))),
          ),
        ]),
        const SizedBox(height: 16),

        // Plans grid
        LayoutBuilder(builder: (context, constraints) {
          if (constraints.maxWidth < 900) {
            return Column(children: _plans.entries.map((e) => Padding(
                padding: const EdgeInsets.only(bottom: 16), child: _buildPlanCard(e.key, e.value))).toList());
          }
          return Wrap(spacing: 16, runSpacing: 16, children: _plans.entries.map((e) =>
              SizedBox(width: (constraints.maxWidth - 48) / 4, child: _buildPlanCard(e.key, e.value))).toList());
        }),
      ]),
    );
  }

  Widget _statBox(String label, String value, Color color) => Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(color: Colors.white.withOpacity(0.7), borderRadius: BorderRadius.circular(12), border: Border.all(color: Colors.grey.shade200)),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Text(value, style: TextStyle(fontSize: 24, fontWeight: FontWeight.w800, color: color)),
        const SizedBox(height: 4),
        Text(label, style: const TextStyle(fontSize: 12, color: AppTheme.textGray)),
      ]));

  Widget _buildPlanCard(String planId, Map<String, dynamic> plan) {
    final color = plan['color'] as Color;
    return Container(
      decoration: BoxDecoration(color: Colors.white.withOpacity(0.7), borderRadius: BorderRadius.circular(16), border: Border.all(color: Colors.grey.shade200)),
      padding: const EdgeInsets.all(20),
      child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [
          Text(plan['name'], style: TextStyle(fontSize: 16, fontWeight: FontWeight.w700, color: color)),
          Container(padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
              decoration: BoxDecoration(color: color.withOpacity(0.1), borderRadius: BorderRadius.circular(12)),
              child: Text(planId.toUpperCase(), style: TextStyle(fontSize: 10, fontWeight: FontWeight.w700, color: color))),
        ]),
        const SizedBox(height: 16),
        TextField(
          controller: _priceControllers[planId],
          decoration: InputDecoration(
              labelText: 'Monthly Price', prefixText: 'Rs.',
              filled: true, fillColor: Colors.white.withOpacity(0.9),
              border:        OutlineInputBorder(borderRadius: BorderRadius.circular(10), borderSide: BorderSide(color: Colors.grey.shade300)),
              enabledBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(10), borderSide: BorderSide(color: Colors.grey.shade300)),
              focusedBorder: OutlineInputBorder(borderRadius: BorderRadius.circular(10), borderSide: BorderSide(color: color, width: 2)),
              contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10)),
          keyboardType: TextInputType.number,
        ),
        const SizedBox(height: 16),
        const Divider(),
        const SizedBox(height: 12),
        ...((plan['features'] as List<String>).map((f) => Padding(
            padding: const EdgeInsets.only(bottom: 8),
            child: Row(children: [
              Icon(Icons.check_circle, color: color, size: 16),
              const SizedBox(width: 8),
              Expanded(child: Text(f, style: const TextStyle(fontSize: 12, color: AppTheme.textDark))),
            ])))),
      ]),
    );
  }

  @override
  void dispose() { _priceControllers.forEach((_, c) => c.dispose()); super.dispose(); }
}