from pydantic import BaseModel
from typing import Optional, List


# ── Auth Models ───────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    fullName: str
    email: str
    password: str
    phoneNumber: Optional[str] = None


class LoginRequest(BaseModel):
    email: str
    password: str


class ForgotPasswordRequest(BaseModel):
    email: str


class TokenResponse(BaseModel):
    access_token: str
    uid: str
    role: str


# ── Skill Models ──────────────────────────────────────────────────────────────

class SkillItem(BaseModel):
    name: str
    source: str          # "resume" | "github"
    verified: bool = True


# ── Resume Models ─────────────────────────────────────────────────────────────

class ResumeUploadResponse(BaseModel):
    resumeUrl: str
    extractedSkills: List[SkillItem]
    message: str


# ── GitHub Models ─────────────────────────────────────────────────────────────

class GitHubSkillsRequest(BaseModel):
    githubUsername: str


class GitHubSkillsResponse(BaseModel):
    username: str
    skills: List[SkillItem]
    repoCount: int


# ── Interview Models ──────────────────────────────────────────────────────────

class InterviewQuestion(BaseModel):
    questionId: str
    questionText: str
    skillTag: str


class StartInterviewRequest(BaseModel):
    skills: List[str]


class StartInterviewResponse(BaseModel):
    sessionId: str
    questions: List[InterviewQuestion]
    avatarVideoUrl: Optional[str] = None


class SubmitAnswerResponse(BaseModel):
    questionId: str
    transcript: str
    message: str


# ── Report Models ─────────────────────────────────────────────────────────────

class QuestionScore(BaseModel):
    questionId: str
    questionText: str
    transcript: str
    relevanceScore: float
    clarityScore: float
    completenessScore: float
    keywordsMatched: List[str]
    feedback: str
