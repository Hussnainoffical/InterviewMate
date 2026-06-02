import hashlib
import os
import subprocess
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[2]
PIPER_DIR = BASE_DIR / "models" / "piper"
PIPER_EXE = Path(os.getenv("PIPER_EXE_PATH", PIPER_DIR / "piper" / "piper.exe"))
PIPER_MODEL = Path(os.getenv("PIPER_MODEL_PATH", PIPER_DIR / "en_US-amy-medium.onnx"))
TTS_CACHE_DIR = Path(os.getenv("TTS_CACHE_DIR", BASE_DIR / "storage" / "tts"))


def synthesize_question(text: str) -> Path:
    clean = " ".join(text.strip().split())
    if not clean:
        raise ValueError("Text is required")
    if not PIPER_EXE.exists():
        raise FileNotFoundError(f"Piper executable not found: {PIPER_EXE}")
    if not PIPER_MODEL.exists():
        raise FileNotFoundError(f"Piper model not found: {PIPER_MODEL}")

    TTS_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_key = hashlib.sha256(clean.encode("utf-8")).hexdigest()[:24]
    output_path = TTS_CACHE_DIR / f"question_{cache_key}.wav"
    if output_path.exists() and output_path.stat().st_size > 44:
        return output_path

    result = subprocess.run(
        [str(PIPER_EXE), "--model", str(PIPER_MODEL), "--output_file", str(output_path)],
        input=clean,
        text=True,
        capture_output=True,
        cwd=str(PIPER_EXE.parent),
        timeout=45,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip() or "Piper failed")
    if not output_path.exists() or output_path.stat().st_size <= 44:
        raise RuntimeError("Piper did not generate usable audio")
    return output_path
