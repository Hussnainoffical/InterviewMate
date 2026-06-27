from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response
from pydantic import BaseModel

from app.services.avatar import create_avatar_talk, get_avatar_talk
from app.services.tts import synthesize_question
from starlette.concurrency import run_in_threadpool


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


def _wav_response(wav_path) -> Response:
    # Return the WAV bytes as a plain Response (CORS-friendly, unlike FileResponse).
    data = wav_path.read_bytes()
    return Response(
        content=data,
        media_type="audio/wav",
        headers={
            "Access-Control-Allow-Origin": "*",
            "Cache-Control": "no-store",
            "Content-Disposition": f'inline; filename="{wav_path.name}"',
        },
    )


@router.post("/speech")
async def avatar_speech(body: SpeechRequest):
    if not body.text.strip():
        raise HTTPException(status_code=400, detail="Text is required")
    try:
        wav_path = await run_in_threadpool(synthesize_question, body.text)
        return await run_in_threadpool(_wav_response, wav_path)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Piper TTS failed: {exc}")


@router.get("/speech")
async def avatar_speech_url(text: str = Query(..., min_length=1)):
    try:
        wav_path = await run_in_threadpool(synthesize_question, text)
        return await run_in_threadpool(_wav_response, wav_path)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Piper TTS failed: {exc}")
