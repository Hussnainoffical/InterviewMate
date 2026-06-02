import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';
import '../services/auth_service.dart';
import '../widgets/sidebar.dart';
import '../widgets/admin_sidebar.dart';
import '../screens/auth/welcome_screen.dart';
import '../screens/auth/login_screen.dart';
import '../screens/auth/signup_screen.dart';
import '../screens/auth/forgot_password_screen.dart';
import '../screens/user/dashboard_screen.dart';
import '../screens/user/resume_upload_screen.dart';
import '../screens/user/interview_session_screen.dart';
import '../screens/user/performance_report_screen.dart';
import '../screens/user/interview_history_screen.dart';
import '../screens/user/profile_settings_screen.dart';
import '../screens/admin/admin_dashboard_screen.dart';
import '../screens/admin/user_management_screen.dart';
import '../screens/admin/system_statistics_screen.dart';
import '../screens/admin/admin_settings_screen.dart';
import '../screens/admin/plan_settings_screen.dart';

// ── Guards (no Firebase — pure AuthService) ───────────────────────────────────

String? _userGuard(BuildContext context, GoRouterState state) {
  if (!AuthService().isLoggedIn) return '/login';
  return null;
}

String? _adminGuard(BuildContext context, GoRouterState state) {
  if (!AuthService().isLoggedIn) return '/login';
  if (AuthService().role != 'admin') return '/dashboard';
  return null;
}

class AppRoutes {
  static final router = GoRouter(
    initialLocation: '/',
    redirect: (ctx, state) {
      // If already logged in and hitting root/login/signup → go to dashboard
      final loggedIn = AuthService().isLoggedIn;
      final onPublic = state.matchedLocation == '/' ||
          state.matchedLocation == '/login' ||
          state.matchedLocation == '/signup';
      if (loggedIn && onPublic) {
        return AuthService().role == 'admin' ? '/admin/dashboard' : '/dashboard';
      }
      return null;
    },
    routes: [
      // ── Public ────────────────────────────────────────────────────────
      GoRoute(path: '/',               builder: (c, s) => const WelcomeScreen()),
      GoRoute(path: '/login',          builder: (c, s) => const LoginScreen()),
      GoRoute(path: '/signup',         builder: (c, s) => const SignupScreen()),
      GoRoute(path: '/forgot-password',builder: (c, s) => const ForgotPasswordScreen()),

      // ── User shell ────────────────────────────────────────────────────
      ShellRoute(
        builder: (c, s, child) => AppShell(body: child),
        routes: [
          GoRoute(path: '/dashboard',         redirect: _userGuard, builder: (c, s) => const UserDashboardScreen()),
          GoRoute(path: '/resume-upload',     redirect: _userGuard, builder: (c, s) => const ResumeUploadScreen()),
          GoRoute(path: '/interview-session', redirect: _userGuard, builder: (c, s) => const InterviewSessionScreen()),
          GoRoute(path: '/performance-report',redirect: _userGuard, builder: (c, s) => const PerformanceReportScreen()),
          GoRoute(path: '/interview-history', redirect: _userGuard, builder: (c, s) => const InterviewHistoryScreen()),
          GoRoute(path: '/profile-settings',  redirect: _userGuard, builder: (c, s) => const ProfileSettingsScreen()),
        ],
      ),

      // ── Admin shell ───────────────────────────────────────────────────
      ShellRoute(
        builder: (c, s, child) => AdminShell(body: child),
        routes: [
          GoRoute(path: '/admin/dashboard',         redirect: _adminGuard, builder: (c, s) => const AdminDashboardScreen()),
          GoRoute(path: '/admin/user-management',   redirect: _adminGuard, builder: (c, s) => const UserManagementScreen()),
          GoRoute(path: '/admin/system-statistics', redirect: _adminGuard, builder: (c, s) => const SystemStatisticsScreen()),
          GoRoute(path: '/admin/settings',          redirect: _adminGuard, builder: (c, s) => const AdminSettingsScreen()),
          GoRoute(path: '/admin/plan-settings',     redirect: _adminGuard, builder: (c, s) => const PlanSettingsScreen()),
        ],
      ),
    ],
  );
}