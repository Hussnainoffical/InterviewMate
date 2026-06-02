from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app import crud

router = APIRouter()


@router.get("/stats")
async def system_stats(db: Session = Depends(get_db)):
    return {
        "totalUsers":        crud.count_users(db),
        "totalSessions":     crud.count_sessions(db),
        "totalReports":      crud.count_reports(db),
        "activeSessionsToday": crud.count_active_sessions(db),
        "avgScore":          crud.get_avg_score(db),
        "serverUptime":      "99.9%",
    }


@router.get("/users")
async def list_users(db: Session = Depends(get_db)):
    users = crud.get_all_users(db)
    result = [{
        "uid":         u.uid,
        "fullName":    u.fullName,
        "email":       u.email,
        "role":        u.role,
        "phoneNumber": u.phoneNumber,
        "jobTitle":    u.jobTitle,
        "city":        u.city,
        "skills":      u.skills or [],
        "createdAt":   u.createdAt.isoformat() if u.createdAt else None,
    } for u in users]
    return {"users": result, "total": len(result)}


@router.put("/users/{uid}/role")
async def update_role(uid: str, payload: dict, db: Session = Depends(get_db)):
    role = payload.get("role")
    if role not in ("user", "admin"):
        raise HTTPException(status_code=400, detail="Role must be 'user' or 'admin'")
    user = crud.update_user(db, uid, {"role": role})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": f"User {uid} role updated to {role}"}


@router.delete("/users/{uid}")
async def delete_user(uid: str, db: Session = Depends(get_db)):
    deleted = crud.delete_user(db, uid)
    if not deleted:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": f"User {uid} deleted"}