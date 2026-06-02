"""
seed.py
-------
Creates demo admin + user accounts on first startup if DB is empty.
Only runs once — if users already exist, does nothing.
"""

from datetime import datetime
import uuid
from sqlalchemy.orm import Session
from app import crud


def seed_demo_data(db: Session):
    # Skip if users already exist
    if crud.count_users(db) > 0:
        return

    print("🌱 Seeding demo data...")

    admin_uid = str(uuid.uuid4())
    user_uid  = str(uuid.uuid4())

    # Admin account
    crud.create_user(db, admin_uid, {
        "uid":         admin_uid,
        "fullName":    "Muhammad Shahzaib",
        "email":       "admin@interviewmate.com",
        "password":    "Admin@123",
        "phoneNumber": "+92 300 1234567",
        "role":        "admin",
        "jobTitle":    "Platform Administrator",
        "city":        "Lahore",
        "skills":      ["Python", "Flutter", "FastAPI"],
        "createdAt":   datetime.utcnow(),
    })

    # Regular user account
    crud.create_user(db, user_uid, {
        "uid":         user_uid,
        "fullName":    "Test User",
        "email":       "user@interviewmate.com",
        "password":    "User@123",
        "phoneNumber": "+92 321 9876543",
        "role":        "user",
        "jobTitle":    "Software Engineer",
        "city":        "Karachi",
        "skills":      ["Python", "Flutter", "Firebase", "SQL"],
        "createdAt":   datetime.utcnow(),
    })

    # Demo session for the test user
    session_id = str(uuid.uuid4())
    report_id  = str(uuid.uuid4())

    from app.db_models import InterviewSession, PerformanceReport
    session = InterviewSession(
        sessionId = session_id,
        userId    = user_uid,
        skills    = ["Python", "Flutter"],
        questions = [
            {"questionId": "q1", "questionText": "Explain the difference between lists and tuples in Python.", "skillTag": "Python"},
            {"questionId": "q2", "questionText": "What is the difference between StatelessWidget and StatefulWidget?", "skillTag": "Flutter"},
        ],
        answers   = {},
        status    = "completed",
        score     = 82.0,
        summary   = "Overall performance: 82%. Strong answers overall.",
        startTime = datetime(2026, 1, 30, 10, 0, 0),
        endTime   = datetime(2026, 1, 30, 10, 18, 0),
    )
    report = PerformanceReport(
        reportId      = report_id,
        userId        = user_uid,
        sessionId     = session_id,
        overallScore  = 82.0,
        summary       = "Overall performance: 82%. 3 strong answers, 1 needs improvement.",
        strengths     = ["Clear communication", "Good technical depth"],
        improvements  = ["Quantify results with metrics"],
        questionScores= [],
        createdAt     = datetime(2026, 1, 30, 10, 20, 0),
    )

    db_session = db
    db_session.add(session)
    db_session.add(report)
    db_session.commit()

    print("✅ Demo accounts created:")
    print("   Admin: admin@interviewmate.com / Admin@123")
    print("   User:  user@interviewmate.com  / User@123")