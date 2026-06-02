from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import UpdateProfileRequest
from app import crud

router = APIRouter()


def _user_to_dict(user) -> dict:
    return {
        "uid": user.uid, "fullName": user.fullName, "email": user.email,
        "phoneNumber": user.phoneNumber, "role": user.role,
        "jobTitle": user.jobTitle, "city": user.city, "skills": user.skills or [],
        "createdAt": user.createdAt.isoformat() if user.createdAt else None,
    }


@router.get("/{uid}")
async def get_profile(uid: str, db: Session = Depends(get_db)):
    user = crud.get_user(db, uid)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return _user_to_dict(user)


@router.put("/{uid}")
async def update_profile(uid: str, body: UpdateProfileRequest, db: Session = Depends(get_db)):
    updates = body.model_dump(exclude_none=True)
    user = crud.update_user(db, uid, updates)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return _user_to_dict(user)