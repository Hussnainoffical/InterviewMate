"""
db_models.py
------------
SQLAlchemy ORM models — one class = one database table.
"""

from sqlalchemy import Column, String, Float, Integer, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class User(Base):
    __tablename__ = "users"

    uid         = Column(String, primary_key=True, index=True)
    fullName    = Column(String, nullable=False)
    email       = Column(String, unique=True, index=True, nullable=False)
    password    = Column(String, nullable=False)   # plain for now, Phase 4 adds hashing
    phoneNumber = Column(String, default="")
    role        = Column(String, default="user")   # "user" | "admin"
    jobTitle    = Column(String, default="")
    city        = Column(String, default="")
    skills      = Column(JSON, default=list)       # ["Python", "Flutter", ...]
    createdAt   = Column(DateTime, default=datetime.utcnow)
    updatedAt   = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    sessions = relationship("InterviewSession", back_populates="user", cascade="all, delete-orphan")
    reports  = relationship("PerformanceReport", back_populates="user", cascade="all, delete-orphan")


class InterviewSession(Base):
    __tablename__ = "interview_sessions"

    sessionId  = Column(String, primary_key=True, index=True)
    userId     = Column(String, ForeignKey("users.uid"), nullable=False, index=True)
    skills     = Column(JSON, default=list)       # ["Python", "Flutter"]
    questions  = Column(JSON, default=list)       # list of question dicts
    answers    = Column(JSON, default=dict)       # {questionId: {transcript, submittedAt}}
    status     = Column(String, default="active") # "active" | "completed"
    score      = Column(Float, default=0.0)
    summary    = Column(Text, default="")
    startTime  = Column(DateTime, default=datetime.utcnow)
    endTime    = Column(DateTime, nullable=True)

    user    = relationship("User", back_populates="sessions")
    reports = relationship("PerformanceReport", back_populates="session", cascade="all, delete-orphan")


class PerformanceReport(Base):
    __tablename__ = "performance_reports"

    reportId      = Column(String, primary_key=True, index=True)
    userId        = Column(String, ForeignKey("users.uid"), nullable=False, index=True)
    sessionId     = Column(String, ForeignKey("interview_sessions.sessionId"), nullable=False)
    overallScore  = Column(Float, default=0.0)
    summary       = Column(Text, default="")
    strengths     = Column(JSON, default=list)
    improvements  = Column(JSON, default=list)
    questionScores= Column(JSON, default=list)
    createdAt     = Column(DateTime, default=datetime.utcnow)

    user    = relationship("User", back_populates="reports")
    session = relationship("InterviewSession", back_populates="reports")