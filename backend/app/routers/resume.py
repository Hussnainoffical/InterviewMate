from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import ResumeUploadResponse, SkillItem, UpdateSkillsRequest
from app import crud
from app.services.candidate_profile import parse_resume_file, skill_names_from_profile

router = APIRouter()

_TECH_SKILLS = {
    "python", "java", "javascript", "typescript", "dart", "flutter", "react",
    "nodejs", "node.js", "fastapi", "django", "flask", "firebase", "mysql",
    "postgresql", "mongodb", "redis", "docker", "kubernetes", "git", "aws",
    "machine learning", "deep learning", "nlp", "tensorflow", "pytorch",
    "scikit-learn", "pandas", "numpy", "rest api", "graphql", "html", "css",
    "sql", "kotlin", "swift", "c++", "c#", "golang", "android", "ios",
}


def _extract_skills_from_text(text: str):
    text_lower = text.lower()
    return [SkillItem(name=skill, source="resume", verified=True)
            for skill in _TECH_SKILLS if skill in text_lower]


@router.post("/upload", response_model=ResumeUploadResponse)
async def upload_resume(uid: str = "", file: UploadFile = File(...),
                        db: Session = Depends(get_db)):
    allowed = [
        "application/pdf",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ]
    filename = file.filename or ""
    extension = filename.lower().rsplit(".", 1)[-1] if "." in filename else ""
    if file.content_type not in allowed and extension not in {"pdf", "doc", "docx"}:
        raise HTTPException(status_code=400, detail="Only PDF/DOC/DOCX accepted")

    file_bytes = await file.read()
    profile = parse_resume_file(file_bytes, file.filename or "resume")
    skill_names = skill_names_from_profile(profile)
    skills = [SkillItem(name=name, source="resume", verified=True) for name in skill_names]

    # Save extracted skills to user in DB
    if uid:
        user = crud.get_user(db, uid)
        if user:
            existing = set(user.skills or [])
            merged   = list(existing | {s.name for s in skills})
            crud.update_user(db, uid, {"skills": merged})

    return ResumeUploadResponse(
        resumeUrl=f"uploads/resumes/{file.filename}",
        extractedSkills=skills,
        message=(
            f"Resume uploaded. {len(skills)} skills extracted. "
            f"Detected {profile.get('field', 'General')} / {profile.get('seniority', 'Beginner')}."
            + (" Add skills manually if extraction missed them." if not skills else "")
        ),
        candidateProfile=profile,
    )


@router.get("/skills/{uid}")
async def get_skills(uid: str, db: Session = Depends(get_db)):
    user = crud.get_user(db, uid)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"skills": [SkillItem(name=s, source="profile", verified=True)
                       for s in (user.skills or [])], "uid": uid}


@router.put("/skills/{uid}")
async def update_skills(uid: str, body: UpdateSkillsRequest,
                        db: Session = Depends(get_db)):
    user = crud.update_user(db, uid, {"skills": body.skills})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "Skills updated", "skills": body.skills}
