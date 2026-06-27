from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import engine, SessionLocal
from app.db_models import Base
from app.routers import admin, auth, avatar, github, interview, profile, report, resume
from app.seed import seed_demo_data


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    print("Database tables ready -> interviewmate.db")

    db = SessionLocal()
    try:
        seed_demo_data(db)
    finally:
        db.close()

    print("InterviewMate backend ready")
    print("   Swagger UI: http://localhost:8000/docs")
    yield
    print("Shutting down...")


app = FastAPI(
    title="InterviewMate API",
    description="AI-Powered Mock Interview Platform - Phase 2 (SQLite)",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1/auth", tags=["Auth"])
app.include_router(profile.router, prefix="/api/v1/profile", tags=["Profile"])
app.include_router(resume.router, prefix="/api/v1/resume", tags=["Resume"])
app.include_router(github.router, prefix="/api/v1/github", tags=["GitHub"])
app.include_router(interview.router, prefix="/api/v1/interview", tags=["Interview"])
app.include_router(report.router, prefix="/api/v1/report", tags=["Report"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["Admin"])
app.include_router(avatar.router, prefix="/api/v1/avatar", tags=["Avatar"])
app.add_api_websocket_route(
    "/ws/interview-agent/{session_id}",
    interview.interview_agent_ws,
    name="interview_agent_ws_root",
)


@app.get("/", tags=["Health"])
async def root():
    return {"status": "ok", "message": "InterviewMate API v2 - SQLite", "docs": "/docs"}


@app.get("/health", tags=["Health"])
async def health():
    return {"status": "healthy", "version": "2.0.0", "database": "SQLite"}
