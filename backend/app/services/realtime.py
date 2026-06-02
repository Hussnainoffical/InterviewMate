from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass
from pathlib import Path

import httpx


BACKEND_ROOT = Path(__file__).resolve().parents[2]
LOCAL_ENV_FILES = [BACKEND_ROOT / ".env", BACKEND_ROOT / "env"]
OPENAI_REALTIME_URL = "https://api.openai.com/v1/realtime/calls"
DEFAULT_REALTIME_MODEL = "gpt-realtime-mini"
DEFAULT_REALTIME_VOICE = "marin"


@dataclass(frozen=True)
class RealtimeSessionConfig:
    model: str
    voice: str
    instructions: str
    safety_identifier: str


class RealtimeConfigurationError(RuntimeError):
    pass


def build_interview_instructions(
    *,
    questions: list[dict],
    current_index: int,
    candidate_profile: dict | None = None,
) -> str:
    question_text = ""
    if 0 <= current_index < len(questions):
        question_text = str(
            questions[current_index].get("questionText")
            or questions[current_index].get("question_text")
            or ""
        ).strip()

    profile_bits = []
    if candidate_profile:
        for key in ("field", "seniority", "interviewType"):
            value = candidate_profile.get(key)
            if value:
                profile_bits.append(f"{key}: {value}")

    profile_text = "; ".join(profile_bits) if profile_bits else "No extra profile context."
    return (
        "You are InterviewMate, a professional AI interviewer in a live mock interview. "
        "This is an interview-only session: discuss only the current interview question, "
        "the candidate's answer, and concise interview follow-ups. "
        "Keep your tone calm, direct, and realistic. Ask only interview-relevant follow-up "
        "questions. Do not answer the interview question for the candidate. "
        "If the candidate asks to repeat, repeat the current question verbatim and stop. "
        "If the candidate is silent, says random words, speaks off-topic, or asks an unrelated "
        "question, politely redirect them to answer the current interview question. "
        "If audio is unclear, ask them to repeat once. If they finish a meaningful answer, "
        "briefly acknowledge it and either ask one concise follow-up or tell them to continue "
        "to the next question. Keep responses under 35 words unless clarification is needed. "
        f"Candidate context: {profile_text} Current question: {question_text}"
    )


def build_realtime_session_config(
    *,
    questions: list[dict],
    current_index: int,
    user_id: str,
    candidate_profile: dict | None = None,
) -> RealtimeSessionConfig:
    model = os.getenv("OPENAI_REALTIME_MODEL", DEFAULT_REALTIME_MODEL).strip() or DEFAULT_REALTIME_MODEL
    voice = os.getenv("OPENAI_REALTIME_VOICE", DEFAULT_REALTIME_VOICE).strip() or DEFAULT_REALTIME_VOICE
    return RealtimeSessionConfig(
        model=model,
        voice=voice,
        instructions=build_interview_instructions(
            questions=questions,
            current_index=current_index,
            candidate_profile=candidate_profile,
        ),
        safety_identifier=hashlib.sha256(user_id.encode("utf-8")).hexdigest()[:32],
    )


def build_openai_session_payload(config: RealtimeSessionConfig) -> str:
    return json.dumps({
        "type": "realtime",
        "model": config.model,
        "instructions": config.instructions,
        "audio": {
            "input": {
                "transcription": {
                    "model": "gpt-realtime-whisper",
                    "language": "en",
                    "delay": "low",
                },
                "turn_detection": {
                    "type": "semantic_vad",
                    "eagerness": "low",
                    "create_response": True,
                    "interrupt_response": True,
                },
            },
            "output": {"voice": config.voice},
        },
        "tracing": "auto",
    })


async def create_realtime_answer_sdp(
    *,
    offer_sdp: str,
    config: RealtimeSessionConfig,
    api_key: str | None = None,
) -> str:
    key = (api_key or resolve_openai_api_key()).strip()
    if not key:
        raise RealtimeConfigurationError("OPENAI_API_KEY is not configured")
    if not offer_sdp.strip():
        raise ValueError("SDP offer is required")

    files = {
        "sdp": (None, offer_sdp, "application/sdp"),
        "session": (None, build_openai_session_payload(config), "application/json"),
    }
    headers = {
        "Authorization": f"Bearer {key}",
        "OpenAI-Safety-Identifier": config.safety_identifier,
    }
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(OPENAI_REALTIME_URL, headers=headers, files=files)

    if response.status_code >= 400:
        detail = response.text.strip() or f"OpenAI Realtime HTTP {response.status_code}"
        raise RuntimeError(detail)
    return response.text


def resolve_openai_api_key() -> str:
    return (
        os.getenv("OPENAI_API_KEY")
        or os.getenv("OPENAI_SECRET_KEY")
        or _read_local_env_value("OPENAI_API_KEY")
        or _read_local_env_value("OPENAI_SECRET_KEY")
        or ""
    ).strip()


def _read_local_env_value(key: str) -> str | None:
    for env_file in LOCAL_ENV_FILES:
        try:
            lines = env_file.read_text(encoding="utf-8").splitlines()
        except OSError:
            continue
        for line in lines:
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or "=" not in stripped:
                continue
            name, value = stripped.split("=", 1)
            if name.strip() == key:
                return value.strip().strip('"').strip("'")
    return None
