"""
crud.py
-------
All database read/write operations.
Routers call these functions — they never touch SQLAlchemy directly.
Phase 3/4: only this file changes when switching to PostgreSQL.
"""

from sqlalchemy.orm import Session
from sqlalchemy import desc
from datetime import datetime
from app.db_models import User, InterviewSession, PerformanceReport


# ── Users ─────────────────────────────────────────────────────────────────────

def get_user(db: Session, uid: str) -> User | None:
    return db.query(User).filter(User.uid == uid).first()


def get_user_by_email(db: Session, email: str) -> User | None:
    return db.query(User).filter(User.email == email.lower()).first()


def get_all_users(db: Session, limit: int = 200):
    return db.query(User).order_by(desc(User.createdAt)).limit(limit).all()


def count_users(db: Session) -> int:
    return db.query(User).count()


def create_user(db: Session, uid: str, data: dict) -> User:
    user = User(**data)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def update_user(db: Session, uid: str, data: dict) -> User | None:
    user = get_user(db, uid)
    if not user:
        return None
    for key, value in data.items():
        if hasattr(user, key):
            setattr(user, key, value)
    user.updatedAt = datetime.utcnow()
    db.commit()
    db.refresh(user)
    return user


def delete_user(db: Session, uid: str) -> bool:
    user = get_user(db, uid)
    if not user:
        return False
    db.delete(user)
    db.commit()
    return True


# ── Interview Sessions ────────────────────────────────────────────────────────

def create_session(db: Session, data: dict) -> InterviewSession:
    session = InterviewSession(**data)
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def get_session(db: Session, session_id: str) -> InterviewSession | None:
    return db.query(InterviewSession).filter(
        InterviewSession.sessionId == session_id).first()


def update_session(db: Session, session_id: str, data: dict) -> InterviewSession | None:
    session = get_session(db, session_id)
    if not session:
        return None
    for key, value in data.items():
        if hasattr(session, key):
            setattr(session, key, value)
    db.commit()
    db.refresh(session)
    return session


def get_user_sessions(db: Session, uid: str):
    return db.query(InterviewSession).filter(
        InterviewSession.userId == uid
    ).order_by(desc(InterviewSession.startTime)).all()


def count_sessions(db: Session) -> int:
    return db.query(InterviewSession).count()


def count_active_sessions(db: Session) -> int:
    return db.query(InterviewSession).filter(
        InterviewSession.status == "active").count()


# ── Reports ───────────────────────────────────────────────────────────────────

def create_report(db: Session, data: dict) -> PerformanceReport:
    report = PerformanceReport(**data)
    db.add(report)
    db.commit()
    db.refresh(report)
    return report


def get_report(db: Session, report_id: str) -> PerformanceReport | None:
    return db.query(PerformanceReport).filter(
        PerformanceReport.reportId == report_id).first()


def get_user_reports(db: Session, uid: str):
    return db.query(PerformanceReport).filter(
        PerformanceReport.userId == uid
    ).order_by(desc(PerformanceReport.createdAt)).all()


def get_report_by_session(db: Session, session_id: str) -> PerformanceReport | None:
    return db.query(PerformanceReport).filter(
        PerformanceReport.sessionId == session_id).first()


def count_reports(db: Session) -> int:
    return db.query(PerformanceReport).count()


def get_avg_score(db: Session) -> float:
    reports = db.query(PerformanceReport).all()
    if not reports:
        return 0.0
    return round(sum(r.overallScore for r in reports) / len(reports), 1)
