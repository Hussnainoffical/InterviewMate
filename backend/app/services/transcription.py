from pathlib import Path
import os
import tempfile


BACKEND_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_WHISPER_MODEL = BACKEND_ROOT / "models" / "whisper-large-paksouth"
LOCAL_ENV_FILES = [BACKEND_ROOT / ".env", BACKEND_ROOT / "env"]
CACHE_DIR = BACKEND_ROOT / ".cache" / "huggingface"
CACHE_DIR.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("HF_HOME", str(CACHE_DIR))
SAMPLE_RATE = 16_000
CHUNK_SECONDS = 25
CHUNK_OVERLAP_SECONDS = 1
MIN_AUDIO_SECONDS = 1.5
MIN_AUDIO_PEAK = 0.01
MIN_AUDIO_RMS = 0.002

_model = None
_processor = None
_torch = None
_device = "cpu"
_dtype = None
_load_error = None


def transcribe_audio(file_bytes: bytes, filename: str = "answer.wav") -> dict:
    global _load_error

    model_path = os.getenv("WHISPER_MODEL_PATH", str(DEFAULT_WHISPER_MODEL))
    if _is_whisper_disabled():
        return _mock_transcript("Whisper disabled by environment.")

    try:
        suffix = Path(filename).suffix or ".wav"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(file_bytes)
            tmp_path = tmp.name

        try:
            _ensure_model_loaded(model_path)
            audio = _load_audio(tmp_path)
            quality_error = _audio_quality_error(audio)
            if quality_error:
                return _transcription_error(quality_error)
            text = _transcribe_array(audio)
        finally:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass

        return {
            "transcript": text.strip(),
            "transcriptionSource": "whisper",
            "transcriptionError": None,
        }
    except Exception as exc:
        _load_error = str(exc)
        return _mock_transcript(_load_error)


def _ensure_model_loaded(model_path: str):
    global _model, _processor, _torch, _device, _dtype

    if _model is not None and _processor is not None:
        return

    import torch
    from transformers import WhisperForConditionalGeneration, WhisperProcessor

    _torch = torch
    _device = "cuda" if torch.cuda.is_available() else "cpu"
    _dtype = torch.float16 if _device == "cuda" else torch.float32

    _processor = WhisperProcessor.from_pretrained(model_path)
    _model = WhisperForConditionalGeneration.from_pretrained(
        model_path,
        torch_dtype=_dtype,
        low_cpu_mem_usage=True,
    ).to(_device)
    _model.eval()

    _model.config.forced_decoder_ids = None
    _model.generation_config.forced_decoder_ids = None


def _load_audio(path: str):
    import librosa
    import numpy as np

    audio, _ = librosa.load(path, sr=SAMPLE_RATE, mono=True)
    return np.asarray(audio, dtype="float32")


def _transcribe_array(audio) -> str:
    if len(audio) == 0:
        return ""

    texts = []
    for chunk in _chunk_audio(audio):
        inputs = _processor.feature_extractor(
            chunk,
            sampling_rate=SAMPLE_RATE,
            return_tensors="pt",
        ).input_features.to(_device, dtype=_dtype)

        with _torch.no_grad():
            predicted_ids = _model.generate(
                inputs,
                task="transcribe",
                language=os.getenv("WHISPER_LANGUAGE", "en"),
                max_new_tokens=160,
            )

        text = _processor.tokenizer.batch_decode(
            predicted_ids,
            skip_special_tokens=True,
        )[0].strip()
        if text:
            texts.append(text)

    return " ".join(texts)


def _chunk_audio(audio):
    chunk_size = SAMPLE_RATE * CHUNK_SECONDS
    overlap = SAMPLE_RATE * CHUNK_OVERLAP_SECONDS
    step = max(1, chunk_size - overlap)

    if len(audio) <= chunk_size:
        return [audio]

    chunks = []
    start = 0
    while start < len(audio):
        end = min(start + chunk_size, len(audio))
        chunks.append(audio[start:end])
        if end >= len(audio):
            break
        start += step
    return chunks


def _audio_quality_error(audio) -> str | None:
    sample_count = len(audio)
    duration = sample_count / SAMPLE_RATE
    if duration < MIN_AUDIO_SECONDS:
        return "Recording is too short. Please record a complete answer."

    if sample_count == 0:
        return "No audio samples were found in the recording."

    peak = 0.0
    square_sum = 0.0
    for sample in audio:
        value = abs(float(sample))
        peak = max(peak, value)
        square_sum += value * value
    rms = (square_sum / sample_count) ** 0.5

    if peak < MIN_AUDIO_PEAK or rms < MIN_AUDIO_RMS:
        return "No clear speech was detected in the recording."

    return None


def _is_whisper_disabled() -> bool:
    local_value = _read_local_env_value("INTERVIEWMATE_DISABLE_WHISPER")
    raw = local_value if local_value is not None else os.getenv("INTERVIEWMATE_DISABLE_WHISPER", "")
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def _read_local_env_value(key: str) -> str | None:
    value = None
    prefix = f"{key}="
    for env_file in LOCAL_ENV_FILES:
        try:
            lines = env_file.read_text(encoding="utf-8").splitlines()
        except OSError:
            continue
        for line in lines:
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or not stripped.startswith(prefix):
                continue
            value = stripped[len(prefix):].strip().strip('"').strip("'")
    return value


def _transcription_error(reason: str) -> dict:
    return {
        "transcript": "",
        "transcriptionSource": "whisper",
        "transcriptionError": reason,
    }


def _mock_transcript(reason: str) -> dict:
    return {
        "transcript": (
            "I have hands-on experience with this topic. I used it in a real project, "
            "handled implementation details, tested the result, and improved it based on feedback."
        ),
        "transcriptionSource": "mock",
        "transcriptionError": reason,
    }
