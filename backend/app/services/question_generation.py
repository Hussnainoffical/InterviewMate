from pathlib import Path
import os
import re
from app.services.question_bank import search_questions


BACKEND_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_T5_MODEL = BACKEND_ROOT / "models" / "interviewmate_flanT5_final"
CACHE_DIR = BACKEND_ROOT / ".cache" / "huggingface"
CACHE_DIR.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("HF_HOME", str(CACHE_DIR))

_load_attempted = False


def _ensure_t5_loaded() -> bool:
    global _load_attempted
    if os.getenv("INTERVIEWMATE_DISABLE_T5", "").lower() in {"1", "true", "yes"}:
        return False
    if _load_attempted:
        try:
            from app.services.question_generator import is_t5_loaded

            return bool(is_t5_loaded())
        except Exception:
            return False

    _load_attempted = True
    try:
        from app.services.question_generator import load_t5_model, is_t5_loaded

        model_path = os.getenv("FLAN_T5_MODEL_PATH", str(DEFAULT_T5_MODEL))
        load_t5_model(model_path)
        return bool(is_t5_loaded())
    except Exception:
        return False


def generate_interview_questions(
    skills: list[str],
    candidate_profile: dict | None = None,
    count: int = 5,
) -> list[dict]:
    candidate_profile = candidate_profile or {}

    dataset_first = os.getenv("INTERVIEWMATE_T5_FIRST", "").lower() not in {"1", "true", "yes"}
    if dataset_first:
        dataset_questions = search_questions(skills, candidate_profile=candidate_profile, count=count)
        if len(dataset_questions) >= count:
            return dataset_questions[:count]

    _ensure_t5_loaded()

    try:
        from app.services.question_generator import generate_questions
        seniority = _normalize_seniority(candidate_profile.get("seniority", "Mid-Level"))

        generated = generate_questions(
            skills=skills,
            field=candidate_profile.get("field", "Software Engineering"),
            seniority=seniority,
            projects=candidate_profile.get("projects")
            or candidate_profile.get("significant_projects")
            or [],
            experience=candidate_profile.get("experience") or [],
            num_questions=count,
            interview_type="mixed",
            use_t5=True,
            n_t5_questions=1,
        )

        questions = [
            {
                "questionId": q.question_id,
                "questionText": q.question_text,
                "skillTag": q.skill_tag,
                "category": q.category,
                "source": q.source,
            }
            for q in generated
            if _looks_valid_question(q.question_text)
        ]
        if len(questions) < count:
            questions.extend(_fallback_questions(
                skills,
                count - len(questions),
                candidate_profile=candidate_profile,
                exclude_texts={q["questionText"] for q in questions},
            ))
        return questions[:count]
    except Exception:
        return _fallback_questions(skills, count, candidate_profile=candidate_profile)


def _normalize_seniority(value: str) -> str:
    normalized = str(value or "").strip().lower()
    if normalized in {"junior", "entry", "entry-level", "beginner", "fresh"}:
        return "Beginner"
    if normalized in {"senior", "lead", "principal"}:
        return "Senior"
    return "Mid-Level"


def _fallback_questions(
    skills: list[str],
    count: int,
    candidate_profile: dict | None = None,
    exclude_texts: set[str] | None = None,
) -> list[dict]:
    import uuid

    dataset_questions = search_questions(
        skills,
        candidate_profile=candidate_profile,
        count=count,
        exclude_texts=exclude_texts,
    )
    if len(dataset_questions) >= count:
        return dataset_questions[:count]

    bank = {
        "python": "Explain a Python project you built and the main technical tradeoff you made.",
        "flutter": "How do you manage state and async API calls in a Flutter application?",
        "machine learning": "How do you evaluate whether a machine learning model is generalizing well?",
        "fastapi": "How do you structure a FastAPI backend for validation, routing, and database access?",
        "sql": "How would you optimize a slow SQL query in production?",
    }
    defaults = [
        "Walk me through one project you are proud of and your exact contribution.",
        "Describe a difficult technical problem you solved recently.",
        "How do you test your work before shipping it?",
        "Tell me about a time you received feedback and improved your work.",
        "What would you improve in your strongest project if you had more time?",
    ]

    questions = [(q["questionText"], q["skillTag"], q.get("source", "dataset_bank"))
                 for q in dataset_questions]
    seen = {q[0].lower() for q in questions}
    for skill in skills:
        text = bank.get(skill.lower())
        if text and text.lower() not in seen:
            questions.append((text, skill, "fallback_bank"))
            seen.add(text.lower())
        if len(questions) >= count:
            break

    for text in defaults:
        if len(questions) >= count:
            break
        if text.lower() not in seen:
            questions.append((text, "general", "fallback_bank"))
            seen.add(text.lower())

    return [
        {
            "questionId": str(uuid.uuid4()),
            "questionText": text,
            "skillTag": tag,
            "category": "technical" if tag != "general" else "behavioral",
            "source": source,
        }
        for text, tag, source in questions[:count]
    ]


def _looks_valid_question(text: str) -> bool:
    text = (text or "").strip()
    if len(text) < 15 or len(text) > 240:
        return False
    ascii_ratio = sum(1 for ch in text if ord(ch) < 128) / max(len(text), 1)
    if ascii_ratio < 0.92:
        return False
    words = re.findall(r"[A-Za-z][A-Za-z'-]*", text.lower())
    if len(words) < 4:
        return False
    repeated = sum(1 for prev, cur in zip(words, words[1:]) if prev == cur)
    if repeated >= 2:
        return False
    question_markers = {"what", "why", "how", "when", "where", "which", "who", "explain", "describe", "tell", "walk"}
    return text.endswith("?") or bool(question_markers & set(words[:4]))
