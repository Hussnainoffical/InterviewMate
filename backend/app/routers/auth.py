from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from datetime import datetime
import uuid

from app.database import get_db
from app.models import RegisterRequest, LoginRequest, ForgotPasswordRequest, TokenResponse
from app import crud

router = APIRouter()


@router.post("/register", response_model=TokenResponse)
async def register(body: RegisterRequest, db: Session = Depends(get_db)):
    if crud.get_user_by_email(db, body.email):
        raise HTTPException(status_code=409, detail="Email already registered")

    uid  = str(uuid.uuid4())
    role = "admin" if crud.count_users(db) == 0 else "user"

    crud.create_user(db, uid, {
        "uid":         uid,
        "fullName":    body.fullName,
        "email":       body.email.lower(),
        "password":    body.password,
        "phoneNumber": body.phoneNumber or "",
        "role":        role,
        "jobTitle":    "",
        "city":        "",
        "skills":      [],
        "createdAt":   datetime.utcnow(),
    })

    return TokenResponse(
        access_token=f"token_{uid}",
        uid=uid, role=role,
        fullName=body.fullName,
        email=body.email,
    )


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, db: Session = Depends(get_db)):
    user = crud.get_user_by_email(db, body.email)
    if not user or user.password != body.password:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    return TokenResponse(
        access_token=f"token_{user.uid}",
        uid=user.uid, role=user.role,
        fullName=user.fullName,
        email=user.email,
    )


@router.post("/forgot-password")
async def forgot_password(body: ForgotPasswordRequest):
    # Phase 4: send real reset email
    return {"message": "If this email is registered, a reset link has been sent."}


@router.get("/me")
async def get_me(uid: str = "", db: Session = Depends(get_db)):
    if not uid:
        raise HTTPException(status_code=400, detail="uid required")
    user = crud.get_user(db, uid)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {
        "uid": user.uid, "fullName": user.fullName, "email": user.email,
        "phoneNumber": user.phoneNumber, "role": user.role,
        "jobTitle": user.jobTitle, "city": user.city, "skills": user.skills,
    }