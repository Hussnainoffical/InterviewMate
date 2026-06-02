from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app import crud

router = APIRouter()


def _report_to_dict(r) -> dict:
    return {
        "reportId":      r.reportId,
        "userId":        r.userId,
        "sessionId":     r.sessionId,
        "overallScore":  r.overallScore,
        "summary":       r.summary,
        "strengths":     r.strengths     or [],
        "improvements":  r.improvements  or [],
        "questionScores":r.questionScores or [],
        "createdAt":     r.createdAt.isoformat() if r.createdAt else None,
    }


@router.get("/list")
async def list_reports(uid: str = "", db: Session = Depends(get_db)):
    reports = crud.get_user_reports(db, uid) if uid else []
    return {"reports": [_report_to_dict(r) for r in reports]}


@router.get("/{report_id}")
async def get_report(report_id: str, db: Session = Depends(get_db)):
    report = crud.get_report(db, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return _report_to_dict(report)