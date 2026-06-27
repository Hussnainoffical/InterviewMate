from pydantic import BaseModel
from typing import Any, Optional, List


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
    fullName: str
    email: str


class UpdateProfileRequest(BaseModel):
    fullName: Optional[str] = None
    phoneNumber: Optional[str] = None
    jobTitle: Optional[str] = None
    city: Optional[str] = None
    skills: Optional[List[str]] = None


class SkillItem(BaseModel):
    name: str
    source: str
    verified: bool = True


class UpdateSkillsRequest(BaseModel):
    skills: List[str]


class ResumeUploadResponse(BaseModel):
    resumeUrl: str
    extractedSkills: List[SkillItem]
    message: str
    candidateProfile: Optional[dict[str, Any]] = None


class GitHubSkillsRequest(BaseModel):
    githubUsername: str


class GitHubSkillsResponse(BaseModel):
    username: str
    skills: List[SkillItem]
    repoCount: int
    candidateProfile: Optional[dict[str, Any]] = None


class InterviewQuestion(BaseModel):
    questionId: str
    questionText: str
    skillTag: str
    category: Optional[str] = None
    source: Optional[str] = None


class StartInterviewRequest(BaseModel):
    skills: List[str]
    candidateProfile: Optional[dict[str, Any]] = None
    questionCount: int = 5


class StartInterviewResponse(BaseModel):
    sessionId: str
    questions: List[InterviewQuestion]
    avatarVideoUrl: Optional[str] = None


class SubmitAnswerResponse(BaseModel):
    questionId: str
    transcript: str
    message: str
    transcriptionSource: Optional[str] = None
    transcriptionError: Optional[str] = None
    evaluation: Optional[dict[str, Any]] = None


class QuestionScore(BaseModel):
    questionId: str
    questionText: str
    transcript: str
    relevanceScore: float
    clarityScore: float
    completenessScore: float
    keywordsMatched: List[str]
    feedback: str
