from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel

from app.services.avatar import create_avatar_talk, get_avatar_talk
from app.services.tts import synthesize_question


router = APIRouter()


class AvatarTalkRequest(BaseModel):
    text: str
    presenterId: str | None = None


class SpeechRequest(BaseModel):
    text: str


@router.post("/talk")
async def avatar_talk(body: AvatarTalkRequest):
    if not body.text.strip():
        raise HTTPException(status_code=400, detail="Text is required")
    try:
        return await create_avatar_talk(body.text.strip(), body.presenterId)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"D-ID request failed: {exc}")


@router.get("/talk/{talk_id}")
async def avatar_talk_status(talk_id: str):
    if not talk_id.strip():
        raise HTTPException(status_code=400, detail="Talk id is required")
    try:
        return await get_avatar_talk(talk_id.strip())
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"D-ID status request failed: {exc}")


@router.post("/speech")
async def avatar_speech(body: SpeechRequest):
    if not body.text.strip():
        raise HTTPException(status_code=400, detail="Text is required")
    try:
        wav_path = synthesize_question(body.text)
        return FileResponse(
            wav_path,
            media_type="audio/wav",
            filename=wav_path.name,
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Piper TTS failed: {exc}")


@router.get("/speech")
async def avatar_speech_url(text: str = Query(..., min_length=1)):
    try:
        wav_path = synthesize_question(text)
        return FileResponse(
            wav_path,
            media_type="audio/wav",
            filename=wav_path.name,
        )
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Piper TTS failed: {exc}")
