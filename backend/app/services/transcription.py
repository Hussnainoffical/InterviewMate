"""Audio transcription pipeline: noise reduction -> VAD -> Whisper.

Flow:
  1. Load raw audio, check basic quality (duration, amplitude).
  2. Noise reduction (noisereduce) - suppress background hum/static.
  3. Silero VAD - detect speech segments, discard silence/noise gaps.
  4. Concatenate speech segments with short silence pads between them.
  5. Chunk (if long) and send to Whisper for transcription.
"""

from __future__ import annotations

import logging
import os
import tempfile
import threading
from pathlib import Path
from typing import Any

import numpy as np


BACKEND_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_WHISPER_MODEL = BACKEND_ROOT / "models" / "whisper-large-paksouth"
LOCAL_ENV_FILES = [BACKEND_ROOT / ".env", BACKEND_ROOT / "env"]
CACHE_DIR = BACKEND_ROOT / ".cache" / "huggingface"
CACHE_DIR.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("HF_HOME", str(CACHE_DIR))

log = logging.getLogger("interviewmate.transcription")

SAMPLE_RATE = 16_000
CHUNK_SECONDS = 25
CHUNK_OVERLAP_SECONDS = 1
MIN_AUDIO_SECONDS = 1.5
MIN_AUDIO_PEAK = 0.01
MIN_AUDIO_RMS = 0.002

VAD_THRESHOLD = 0.35
VAD_MIN_SPEECH_MS = 250
VAD_MIN_SILENCE_MS = 300
VAD_PAD_MS = 150
MIN_SPEECH_RATIO = 0.05

NOISE_REDUCE_STATIONARY = True
NOISE_REDUCE_PROP_DECREASE = 0.75

_model = None
_processor = None
_torch = None
_device = "cpu"
_dtype = None
_load_error: str | None = None

_vad_model = None
_vad_utils: dict[str, Any] | None = None
_vad_lock = threading.Lock()


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
            audio, noise_reduced = _reduce_noise(audio)
            audio, speech_stats = _apply_vad(audio)
            if audio is None or len(audio) == 0:
                return _transcription_error(
                    "No clear speech was detected. Please speak clearly and try again."
                )
            speech_duration = len(audio) / SAMPLE_RATE
            if speech_duration < MIN_AUDIO_SECONDS:
                return _transcription_error(
                    f"Only {speech_duration:.1f}s of speech detected. "
                    "Please give a more complete answer."
                )
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
            "speechDurationSec": round(speech_stats.get("speech_duration", 0), 2),
            "totalDurationSec": round(speech_stats.get("total_duration", 0), 2),
            "speechSegments": speech_stats.get("segment_count", 0),
            "noiseReduced": noise_reduced,
        }
    except Exception as exc:
        _load_error = str(exc)
        log.exception("Transcription failed")
        return _mock_transcript(_load_error)


def _reduce_noise(audio: np.ndarray) -> tuple[np.ndarray, bool]:
    """Return (audio, applied). `applied` is False when noise reduction was
    skipped (library missing) or failed, so callers can report it accurately."""
    try:
        import noisereduce as nr
        cleaned = nr.reduce_noise(
            y=audio, sr=SAMPLE_RATE,
            stationary=NOISE_REDUCE_STATIONARY,
            prop_decrease=NOISE_REDUCE_PROP_DECREASE,
            n_fft=2048, hop_length=512,
        )
        log.debug("Noise reduction applied successfully")
        return np.asarray(cleaned, dtype="float32"), True
    except ImportError:
        log.warning("noisereduce not installed, skipping")
        return audio, False
    except Exception as exc:
        log.warning("Noise reduction failed: %s", exc)
        return audio, False


def _ensure_vad_loaded():
    global _vad_model, _vad_utils
    if _vad_model is not None:
        return
    with _vad_lock:
        if _vad_model is not None:
            return
        import torch
        model, utils = torch.hub.load(
            repo_or_dir="snakers4/silero-vad",
            model="silero_vad", force_reload=False,
            onnx=False, trust_repo=True,
        )
        _vad_model = model
        _vad_utils = {
            "get_speech_timestamps": utils[0],
            "save_audio": utils[1],
            "read_audio": utils[2],
            "VADIterator": utils[3],
            "collect_chunks": utils[4],
        }
        log.info("Silero VAD loaded")


def _apply_vad(audio: np.ndarray) -> tuple[np.ndarray | None, dict]:
    total_duration = len(audio) / SAMPLE_RATE
    stats: dict[str, Any] = {
        "total_duration": total_duration,
        "speech_duration": 0, "segment_count": 0,
    }
    try:
        _ensure_vad_loaded()
    except Exception as exc:
        log.warning("VAD load failed, skipping: %s", exc)
        stats["speech_duration"] = total_duration
        stats["segment_count"] = 1
        return audio, stats

    import torch
    audio_tensor = torch.from_numpy(audio).float()
    try:
        get_ts = _vad_utils["get_speech_timestamps"]
        timestamps = get_ts(
            audio_tensor, _vad_model,
            threshold=VAD_THRESHOLD,
            min_speech_duration_ms=VAD_MIN_SPEECH_MS,
            min_silence_duration_ms=VAD_MIN_SILENCE_MS,
            sampling_rate=SAMPLE_RATE,
            return_seconds=False,
        )
    except Exception as exc:
        log.warning("VAD inference failed: %s", exc)
        stats["speech_duration"] = total_duration
        stats["segment_count"] = 1
        return audio, stats

    if not timestamps:
        log.info("VAD found no speech in %.1fs of audio", total_duration)
        return None, stats

    pad_samples = int(VAD_PAD_MS * SAMPLE_RATE / 1000)
    segments = []
    speech_samples = 0
    for ts in timestamps:
        start = max(0, ts["start"] - pad_samples)
        end = min(len(audio), ts["end"] + pad_samples)
        segments.append(audio[start:end])
        speech_samples += ts["end"] - ts["start"]

    speech_ratio = speech_samples / max(len(audio), 1)
    if speech_ratio < MIN_SPEECH_RATIO:
        log.info("Speech ratio %.1f%% below threshold", speech_ratio * 100)
        return None, stats

    gap = np.zeros(int(0.1 * SAMPLE_RATE), dtype="float32")
    parts = []
    for i, seg in enumerate(segments):
        if i > 0:
            parts.append(gap)
        parts.append(seg)
    speech_audio = np.concatenate(parts)
    speech_duration = speech_samples / SAMPLE_RATE
    stats["speech_duration"] = speech_duration
    stats["segment_count"] = len(timestamps)
    log.info("VAD: %d segments, %.1fs speech / %.1fs total (%.0f%%)",
             len(timestamps), speech_duration, total_duration, speech_ratio * 100)
    return speech_audio, stats


def _ensure_model_loaded(model_path: str):
    global _model, _processor, _torch, _device, _dtype
    if _model is not None and _processor is not None:
        return
    import torch
    from transformers import WhisperForConditionalGeneration, WhisperProcessor
    _torch = torch
    _pref = (os.getenv("WHISPER_DEVICE") or _read_local_env_value("WHISPER_DEVICE") or "").strip().lower()
    if _pref in ("cpu", "cuda"):
        _device = "cuda" if (_pref == "cuda" and torch.cuda.is_available()) else "cpu"
    else:
        _device = "cuda" if torch.cuda.is_available() else "cpu"
    _dtype = torch.float16 if _device == "cuda" else torch.float32
    _processor = WhisperProcessor.from_pretrained(model_path)
    _model = WhisperForConditionalGeneration.from_pretrained(
        model_path, torch_dtype=_dtype, low_cpu_mem_usage=True,
    ).to(_device)
    _model.eval()
    _model.config.forced_decoder_ids = None
    _model.generation_config.forced_decoder_ids = None


def _load_audio(path: str) -> np.ndarray:
    import librosa
    audio, _ = librosa.load(path, sr=SAMPLE_RATE, mono=True)
    return np.asarray(audio, dtype="float32")


def _transcribe_array(audio: np.ndarray) -> str:
    if len(audio) == 0:
        return ""
    texts = []
    for chunk in _chunk_audio(audio):
        inputs = _processor.feature_extractor(
            chunk, sampling_rate=SAMPLE_RATE, return_tensors="pt",
        ).input_features.to(_device, dtype=_dtype)
        with _torch.no_grad():
            predicted_ids = _model.generate(
                inputs, task="transcribe",
                language=os.getenv("WHISPER_LANGUAGE", "en"),
                max_new_tokens=160,
            )
        text = _processor.tokenizer.batch_decode(
            predicted_ids, skip_special_tokens=True,
        )[0].strip()
        if text:
            texts.append(text)
    return _merge_chunk_texts(texts)


def _merge_chunk_texts(texts: list[str], max_overlap_words: int = 14) -> str:
    """Join per-chunk transcripts, removing words duplicated at the seam.

    Adjacent chunks overlap by CHUNK_OVERLAP_SECONDS, so Whisper transcribes the
    overlap region twice. A plain join would repeat those words. Here we detect
    the largest word run that is both a suffix of the accumulated text and a
    prefix of the next chunk, and drop it from the next chunk before appending.
    """
    def norm(word: str) -> str:
        return word.strip(".,!?;:\"'").lower()

    merged: list[str] = []
    for text in texts:
        text = text.strip()
        if not text:
            continue
        words = text.split()
        if not merged:
            merged = words
            continue
        limit = min(max_overlap_words, len(merged), len(words))
        best = 0
        for k in range(limit, 0, -1):
            tail = [norm(w) for w in merged[-k:]]
            head = [norm(w) for w in words[:k]]
            if tail == head:
                best = k
                break
        merged.extend(words[best:])
    return " ".join(merged).strip()


def _chunk_audio(audio: np.ndarray) -> list[np.ndarray]:
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


def _audio_quality_error(audio: np.ndarray) -> str | None:
    sample_count = len(audio)
    duration = sample_count / SAMPLE_RATE
    if sample_count == 0:
        return "No audio samples were found in the recording."
    if duration < MIN_AUDIO_SECONDS:
        return "Recording is too short. Please record a complete answer."
    peak = float(np.max(np.abs(audio)))
    rms = float(np.sqrt(np.mean(audio ** 2)))
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
