"""
store.py — Single in-memory data store.
All data lives here during the server session.
Phase 2: swap these dicts for real DB calls — nothing else changes.
"""
from datetime import datetime
from typing import Dict, Any

# ── Users  { uid: {...user data...} } ─────────────────────────────────────────
users: Dict[str, Dict[str, Any]] = {}

# ── Email index  { email: uid } ──────────────────────────────────────────────
email_index: Dict[str, str] = {}

# ── Sessions  { session_id: {...session data...} } ────────────────────────────
sessions: Dict[str, Dict[str, Any]] = {}

# ── Reports  { report_id: {...report data...} } ───────────────────────────────
reports: Dict[str, Dict[str, Any]] = {}


# ── Helpers ───────────────────────────────────────────────────────────────────

def get_user_by_uid(uid: str) -> Dict | None:
    return users.get(uid)


def get_user_by_email(email: str) -> Dict | None:
    uid = email_index.get(email.lower())
    if uid is None:
        return None
    return users.get(uid)


def create_user(uid: str, data: dict):
    users[uid] = data
    email_index[data["email"].lower()] = uid


def update_user(uid: str, data: dict):
    if uid in users:
        users[uid].update(data)


def get_sessions_for_user(uid: str):
    return [s for s in sessions.values() if s.get("userId") == uid]


def get_reports_for_user(uid: str):
    return [r for r in reports.values() if r.get("userId") == uid]


def seed_demo_data():
    """Seed one admin + one user so you can test without registering every restart."""
    import uuid
    if not users:
        admin_uid = "admin_001"
        user_uid  = "user_001"

        create_user(admin_uid, {
            "uid": admin_uid, "fullName": "Muhammad Shahzaib",
            "email": "admin@interviewmate.com", "password": "Admin@123",
            "phoneNumber": "+92 300 1234567", "role": "admin",
            "jobTitle": "Administrator", "city": "Lahore",
            "skills": [], "createdAt": datetime.utcnow().isoformat(),
        })
        create_user(user_uid, {
            "uid": user_uid, "fullName": "Test User",
            "email": "user@interviewmate.com", "password": "User@123",
            "phoneNumber": "+92 321 9876543", "role": "user",
            "jobTitle": "Software Engineer", "city": "Karachi",
            "skills": ["Python", "Flutter", "Firebase"],
            "createdAt": datetime.utcnow().isoformat(),
        })

        # Demo sessions & report for the test user
        s_id = "session_demo_001"
        r_id = "report_demo_001"

        sessions[s_id] = {
            "sessionId": s_id, "userId": user_uid,
            "skills": ["Python", "Flutter"],
            "status": "completed", "score": 82,
            "startTime": "2026-01-30T10:00:00",
            "endTime":   "2026-01-30T10:18:00",
            "summary": "Strong answers overall. Improve on quantifying results.",
        }
        reports[r_id] = {
            "reportId": r_id, "userId": user_uid,
            "sessionId": s_id, "overallScore": 82,
            "summary": "Overall performance: 82%. 3 strong answers, 1 needs improvement.",
            "strengths": ["Clear communication", "Good technical depth"],
            "improvements": ["Quantify results with metrics"],
            "questionScores": [],
            "createdAt": datetime.utcnow().isoformat(),
        }