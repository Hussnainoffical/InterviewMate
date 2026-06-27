from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool
from app.database import get_db, SessionLocal
from app.models import StartInterviewRequest, StartInterviewResponse, InterviewQuestion, SubmitAnswerResponse
from app import crud
from app.services.question_generation import generate_interview_questions
from app.services.question_bank import dataset_size
from app.services.transcription import transcribe_audio
from app.services.evaluation import evaluate_answer, summarize_session, validate_answer_transcript
from app.services.realtime import (
    RealtimeConfigurationError,
    build_realtime_session_config,
    create_realtime_answer_sdp,
)
from datetime import datetime
import uuid

router = APIRouter()


AGENT_EVENT_TYPES = [
    "agent_greeting",
    "agent_question",
    "agent_speaking_start",
    "agent_speaking_end",
    "user_speech_start",
    "user_speech_partial",
    "user_speech_final",
    "user_thinking",
    "answer_completed",
    "next_question",
    "repeat_question",
    "interview_ending_confirmation",
    "interview_ended",
    "evaluation_started",
    "evaluation_completed",
    "error_recovery",
]


@router.get("/question-bank/stats")
async def question_bank_stats():
    return {"questions": dataset_size(), "source": "backend_dataset_bank"}


@router.websocket("/ws/interview-agent/{session_id}")
async def interview_agent_ws(websocket: WebSocket, session_id: str):
    await websocket.accept()
    db = SessionLocal()
    try:
        session = crud.get_session(db, session_id)
        if not session:
            await websocket.send_json({
                "type": "error_recovery",
                "state": "error_recovery",
                "message": "Session not found",
            })
            await websocket.close(code=4404)
            return
        if session.status != "active":
            await websocket.send_json({
                "type": "error_recovery",
                "state": "error_recovery",
                "message": "Interview session is not active",
            })
            await websocket.close(code=4409)
            return

        questions = session.questions or []
        first_question = questions[0] if questions else {}
        await websocket.send_json({
            "type": "agent_greeting",
            "state": "greeting",
            "message": "Welcome to your live InterviewMate session. Are you ready to start?",
            "eventTypes": AGENT_EVENT_TYPES,
        })
        if first_question:
            await websocket.send_json({
                "type": "agent_question",
                "state": "asking_question",
                "questionIndex": 0,
                "questionId": first_question.get("questionId"),
                "questionText": first_question.get("questionText") or first_question.get("question_text"),
            })

        while True:
            message = await websocket.receive_json()
            message_type = str(message.get("type", "unknown"))
            if message_type == "end_interview":
                await websocket.send_json({
                    "type": "interview_ending_confirmation",
                    "state": "ending_confirmation",
                    "message": "Are you sure you want to end the interview?",
                })
            elif message_type == "confirm_end":
                await websocket.send_json({
                    "type": "interview_ended",
                    "state": "ended",
                    "message": "Interview ended.",
                })
                await websocket.close()
                return
            elif message_type == "repeat_question":
                try:
                    question_index = int(message.get("questionIndex", 0))
                except (TypeError, ValueError):
                    await websocket.send_json({
                        "type": "error_recovery",
                        "state": "error_recovery",
                        "message": "Question index must be a number",
                    })
                    continue
                question = questions[question_index] if 0 <= question_index < len(questions) else {}
                await websocket.send_json({
                    "type": "repeat_question",
                    "state": "asking_question",
                    "questionIndex": question_index,
                    "questionText": question.get("questionText") or question.get("question_text") or "",
                })
            else:
                await websocket.send_json({
                    "type": "error_recovery",
                    "state": "error_recovery",
                    "message": f"Unsupported event type: {message_type}",
                })
    except WebSocketDisconnect:
        return
    finally:
        db.close()

def _session_to_dict(s) -> dict:
    return {
        "sessionId": s.sessionId, "userId": s.userId,
        "skills": s.skills or [], "questions": s.questions or [],
        "answers": s.answers or {}, "status": s.status,
        "score": s.score, "summary": s.summary,
        "startTime": s.startTime.isoformat() if s.startTime else None,
        "endTime":   s.endTime.isoformat()   if s.endTime   else None,
    }


@router.post("/start", response_model=StartInterviewResponse)
def start_interview(body: StartInterviewRequest, uid: str = "",
                          db: Session = Depends(get_db)):
    if not body.skills:
        raise HTTPException(status_code=400, detail="No skills provided")
    if not uid or not crud.get_user(db, uid):
        raise HTTPException(status_code=404, detail="Valid user id required to start interview")

    count = min(max(body.questionCount, 1), 15)
    question_dicts = generate_interview_questions(
        body.skills,
        candidate_profile=body.candidateProfile,
        count=count,
    )
    questions = [InterviewQuestion(**q) for q in question_dicts]
    session_id = str(uuid.uuid4())

    crud.create_session(db, {
        "sessionId": session_id,
        "userId":    uid,
        "skills":    body.skills,
        "questions": [q.model_dump() for q in questions],
        "answers":   {},
        "status":    "active",
        "score":     0.0,
        "summary":   "",
        "startTime": datetime.utcnow(),
    })

    return StartInterviewResponse(sessionId=session_id, questions=questions)


@router.post("/submit-answer", response_model=SubmitAnswerResponse)
async def submit_answer(
    sessionId:  str = Form(...),
    questionId: str = Form(...),
    uid:        str = Form(""),
    audio: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    session = crud.get_session(db, sessionId)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if uid and uid != session.userId:
        raise HTTPException(status_code=403, detail="Session does not belong to this user")
    if session.status != "active":
        raise HTTPException(status_code=409, detail="Interview session is already completed")

    question = next(
        (q for q in (session.questions or []) if q.get("questionId") == questionId),
        None,
    )
    if question is None:
        raise HTTPException(status_code=400, detail="Question does not belong to this session")

    audio_bytes = await audio.read()
    transcription = await run_in_threadpool(transcribe_audio, audio_bytes, audio.filename or "answer.wav")
    transcript = transcription["transcript"]
    if transcription.get("transcriptionSource") != "whisper" or transcription.get("transcriptionError"):
        raise HTTPException(
            status_code=422,
            detail=f"Could not transcribe answer audio: {transcription.get('transcriptionError') or 'transcription failed'}",
        )
    if not transcript.strip():
        raise HTTPException(status_code=422, detail="No speech was detected in the answer audio")
    valid_answer, invalid_reason = validate_answer_transcript(transcript)
    if not valid_answer:
        raise HTTPException(status_code=422, detail=invalid_reason)

    evaluation = await run_in_threadpool(evaluate_answer, question, transcript)

    answers = dict(session.answers or {})
    previous = answers.get(questionId) if isinstance(answers.get(questionId), dict) else {}
    attempt_number = int(previous.get("attemptNumber", 0)) + 1 if previous else 1
    answers[questionId] = {
        "transcript":           transcript,
        "transcriptionSource":  transcription["transcriptionSource"],
        "transcriptionError":   transcription["transcriptionError"],
        "evaluation":           evaluation,
        "submittedAt":          datetime.utcnow().isoformat(),
        "attemptNumber":        attempt_number,
    }
    crud.update_session(db, sessionId, {"answers": answers})

    return SubmitAnswerResponse(
        questionId=questionId,
        transcript=transcript,
        message="Answer recorded successfully",
        transcriptionSource=transcription["transcriptionSource"],
        transcriptionError=transcription["transcriptionError"],
        evaluation=evaluation,
    )


@router.post("/submit-transcript")
def submit_transcript_answer(payload: dict, db: Session = Depends(get_db)):
    session_id = payload.get("sessionId")
    question_id = payload.get("questionId")
    uid = payload.get("uid", "")
    transcript = str(payload.get("transcript") or "").strip()
    source = str(payload.get("source") or "realtime").strip() or "realtime"

    session = crud.get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if uid and uid != session.userId:
        raise HTTPException(status_code=403, detail="Session does not belong to this user")
    if session.status != "active":
        raise HTTPException(status_code=409, detail="Interview session is already completed")

    question = next(
        (q for q in (session.questions or []) if q.get("questionId") == question_id),
        None,
    )
    if question is None:
        raise HTTPException(status_code=400, detail="Question does not belong to this session")

    valid_answer, invalid_reason = validate_answer_transcript(transcript)
    if not valid_answer:
        raise HTTPException(status_code=422, detail=invalid_reason)

    evaluation = evaluate_answer(question, transcript)
    answers = dict(session.answers or {})
    previous = answers.get(question_id) if isinstance(answers.get(question_id), dict) else {}
    attempt_number = int(previous.get("attemptNumber", 0)) + 1 if previous else 1
    answers[question_id] = {
        "transcript": transcript,
        "transcriptionSource": source,
        "transcriptionError": None,
        "evaluation": evaluation,
        "submittedAt": datetime.utcnow().isoformat(),
        "attemptNumber": attempt_number,
    }
    crud.update_session(db, session_id, {"answers": answers})

    return {
        "questionId": question_id,
        "transcript": transcript,
        "message": "Live answer recorded successfully",
        "transcriptionSource": source,
        "transcriptionError": None,
        "evaluation": evaluation,
    }


@router.post("/realtime/session")
async def create_realtime_session(payload: dict, db: Session = Depends(get_db)):
    session_id = payload.get("sessionId")
    uid = payload.get("uid", "")
    offer_sdp = str(payload.get("offerSdp") or "")
    try:
        question_index = int(payload.get("questionIndex", 0))
    except (TypeError, ValueError):
        raise HTTPException(status_code=400, detail="Question index must be a number")
    candidate_profile = payload.get("candidateProfile") if isinstance(payload.get("candidateProfile"), dict) else None

    session = crud.get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if uid and uid != session.userId:
        raise HTTPException(status_code=403, detail="Session does not belong to this user")
    if session.status != "active":
        raise HTTPException(status_code=409, detail="Interview session is already completed")
    if not offer_sdp.strip():
        raise HTTPException(status_code=400, detail="SDP offer is required")

    questions = session.questions or []
    if question_index < 0 or question_index >= len(questions):
        raise HTTPException(status_code=400, detail="Question index is outside this session")

    config = build_realtime_session_config(
        questions=questions,
        current_index=question_index,
        user_id=session.userId,
        candidate_profile=candidate_profile,
    )

    try:
        answer_sdp = await create_realtime_answer_sdp(
            offer_sdp=offer_sdp,
            config=config,
        )
    except RealtimeConfigurationError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"OpenAI Realtime session failed: {exc}")

    return {
        "answerSdp": answer_sdp,
        "model": config.model,
        "voice": config.voice,
    }


@router.post("/complete")
def complete_interview(payload: dict, db: Session = Depends(get_db)):
    session_id = payload.get("sessionId")
    uid        = payload.get("uid", "")

    session = crud.get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if uid and uid != session.userId:
        raise HTTPException(status_code=403, detail="Session does not belong to this user")
    if session.status != "active":
        raise HTTPException(status_code=409, detail="Interview session is already completed")

    existing_report = crud.get_report_by_session(db, session_id)
    if existing_report:
        raise HTTPException(status_code=409, detail="A report already exists for this session")

    answers = session.answers or {}
    if not answers:
        raise HTTPException(status_code=400, detail="Cannot complete an interview with no submitted answers")

    question_lookup = {q.get("questionId"): q for q in (session.questions or [])}
    missing_questions = [
        qid for qid in question_lookup
        if qid and qid not in answers
    ]
    if missing_questions:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot complete interview before answering all questions. Missing: {', '.join(missing_questions)}",
        )

    question_scores = []
    for question_id, answer in answers.items():
        existing = answer.get("evaluation") if isinstance(answer, dict) else None
        if existing:
            question_scores.append(existing)
        else:
            question_scores.append(evaluate_answer(
                question_lookup.get(question_id, {"questionId": question_id}),
                answer.get("transcript", "") if isinstance(answer, dict) else "",
            ))

    summary = summarize_session(question_scores)
    score = summary["overallScore"]

    crud.update_session(db, session_id, {
        "status":  "completed",
        "endTime": datetime.utcnow(),
        "score":   float(score),
        "summary": summary["summary"],
    })

    report_id = str(uuid.uuid4())
    crud.create_report(db, {
        "reportId":      report_id,
        "userId":        uid or session.userId,
        "sessionId":     session_id,
        "overallScore":  float(score),
        "summary":       summary["summary"],
        "strengths":     summary["strengths"],
        "improvements":  summary["improvements"],
        "questionScores":question_scores,
        "createdAt":     datetime.utcnow(),
    })

    return {
        "message":            "Interview completed successfully",
        "sessionId":          session_id,
        "reportId":           report_id,
        "score":              score,
        "interviewReadiness": summary.get("interviewReadiness"),
        "topicGaps":          summary.get("topicGaps", []),
        "communicationNotes": summary.get("communicationNotes", ""),
        "evaluationSource":   summary.get("evaluationSource", "keyword"),
    }


@router.get("/history")
async def interview_history(uid: str = "", db: Session = Depends(get_db)):
    sessions = crud.get_user_sessions(db, uid) if uid else []
    return {"sessions": [_session_to_dict(s) for s in sessions]}


@router.get("/session/{session_id}")
async def get_session(session_id: str, db: Session = Depends(get_db)):
    session = crud.get_session(db, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return _session_to_dict(session)
