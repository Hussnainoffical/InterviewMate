import os
from pathlib import Path
import httpx


D_ID_API_URL = "https://api.d-id.com"
BACKEND_ROOT = Path(__file__).resolve().parents[2]

try:
    from dotenv import load_dotenv

    load_dotenv(BACKEND_ROOT / ".env")
    load_dotenv(BACKEND_ROOT / "env")
except Exception:
    pass


def _auth_header(api_key: str) -> str:
    if ":" in api_key:
        return f"Basic {api_key}"
    return f"Basic {api_key}"


def _raise_did_error(resp: httpx.Response) -> None:
    if resp.is_success:
        return
    try:
        detail = resp.json()
    except Exception:
        detail = resp.text
    raise RuntimeError(f"D-ID HTTP {resp.status_code}: {detail}")


async def create_avatar_talk(text: str, presenter_id: str | None = None) -> dict:
    if os.getenv("D_ID_ENABLED", "").lower() not in {"1", "true", "yes"}:
        return {
            "provider": "local-demo",
            "configured": False,
            "videoUrl": None,
            "message": "Local avatar mode is active. Set D_ID_ENABLED=true only when you want to spend D-ID credits.",
        }

    api_key = os.getenv("D_ID_API_KEY") or os.getenv("DID_API_KEY")
    if not api_key:
        return {
            "provider": "d-id",
            "configured": False,
            "videoUrl": None,
            "message": "Set D_ID_API_KEY to enable avatar video generation.",
        }

    payload = {
        "script": {
            "type": "text",
            "input": text,
            "provider": {"type": "microsoft", "voice_id": "en-US-JennyNeural"},
        },
        "config": {"fluent": True, "pad_audio": 0.0},
    }
    if presenter_id:
        payload["presenter_id"] = presenter_id
    else:
        payload["source_url"] = os.getenv(
            "D_ID_SOURCE_URL",
            "https://create-images-results.d-id.com/DefaultPresenters/Noelle_f/image.png",
        )

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            f"{D_ID_API_URL}/talks",
            headers={
                "Authorization": _auth_header(api_key),
                "Content-Type": "application/json",
            },
            json=payload,
        )
        _raise_did_error(resp)
        data = resp.json()
        return {
            "provider": "d-id",
            "configured": True,
            "talkId": data.get("id"),
            "status": data.get("status"),
            "videoUrl": data.get("result_url"),
            "raw": data,
        }


async def get_avatar_talk(talk_id: str) -> dict:
    if os.getenv("D_ID_ENABLED", "").lower() not in {"1", "true", "yes"}:
        return {
            "provider": "local-demo",
            "configured": False,
            "talkId": talk_id,
            "videoUrl": None,
            "message": "Local avatar mode is active.",
        }

    api_key = os.getenv("D_ID_API_KEY") or os.getenv("DID_API_KEY")
    if not api_key:
        return {
            "provider": "d-id",
            "configured": False,
            "talkId": talk_id,
            "videoUrl": None,
            "message": "Set D_ID_API_KEY to enable avatar video generation.",
        }

    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(
            f"{D_ID_API_URL}/talks/{talk_id}",
            headers={"Authorization": _auth_header(api_key)},
        )
        _raise_did_error(resp)
        data = resp.json()
        return {
            "provider": "d-id",
            "configured": True,
            "talkId": data.get("id"),
            "status": data.get("status"),
            "videoUrl": data.get("result_url"),
            "raw": data,
        }
