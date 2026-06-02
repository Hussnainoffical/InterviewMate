import json
import math
import re
from collections import Counter
from pathlib import Path


BACKEND_ROOT = Path(__file__).resolve().parents[2]
QUESTION_BANK_PATH = BACKEND_ROOT / "app" / "data" / "interview_questions.json"

_records: list[dict] | None = None
_doc_freq: Counter | None = None
_parsed_records: list[dict] | None = None

STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "i",
    "in", "is", "it", "of", "on", "or", "that", "the", "this", "to",
    "was", "with", "you", "your", "task", "generate", "interview",
    "question", "skills", "education", "experience", "project", "projects",
    "app", "application", "system", "using", "used", "built", "build",
    "developer", "engineer", "software", "data", "work", "working",
    "candidate", "profile", "resume", "created", "made",
}


def search_questions(
    skills: list[str],
    candidate_profile: dict | None = None,
    count: int = 5,
    exclude_texts: set[str] | None = None,
) -> list[dict]:
    _ensure_loaded()
    candidate_profile = candidate_profile or {}
    exclude_texts = {q.lower() for q in (exclude_texts or set())}
    query = _build_query(skills, candidate_profile)
    query_terms = _tokenize(query)

    scored = []
    query_context = _query_context(skills, candidate_profile)
    for idx, rec in enumerate(_records or []):
        target = rec.get("target", "")
        if target.lower() in exclude_texts:
            continue
        parsed = (_parsed_records or [])[idx] if idx < len(_parsed_records or []) else {}
        score = _score_record(query_terms, rec, parsed, query_context)
        if score > 0:
            scored.append((score, idx, rec))

    scored.sort(key=lambda item: (-item[0], item[1]))
    selected = []
    seen = set(exclude_texts)
    for _, idx, rec in scored:
        question = rec.get("target", "").strip()
        if not question or question.lower() in seen:
            continue
        seen.add(question.lower())
        parsed = (_parsed_records or [])[idx] if idx < len(_parsed_records or []) else {}
        selected.append(_to_question(question, skills, "dataset_bank", parsed))
        if len(selected) >= count:
            break

    return selected


def dataset_size() -> int:
    _ensure_loaded()
    return len(_records or [])


def _ensure_loaded():
    global _records, _doc_freq, _parsed_records
    if _records is not None:
        return

    if not QUESTION_BANK_PATH.exists():
        _records = []
        _doc_freq = Counter()
        _parsed_records = []
        return

    _records = json.loads(QUESTION_BANK_PATH.read_text(encoding="utf-8"))
    _parsed_records = [_parse_input(rec.get("input", "")) for rec in _records]
    _doc_freq = Counter()
    for rec in _records:
        terms = set(_tokenize((rec.get("input", "") + " " + rec.get("target", ""))))
        _doc_freq.update(terms)


def _score_record(query_terms: list[str], rec: dict, parsed: dict, query_context: dict) -> float:
    if not query_terms:
        return 0

    haystack = (rec.get("input", "") + " " + rec.get("target", "")).lower()
    doc_terms = Counter(_tokenize(haystack))
    total_docs = max(len(_records or []), 1)
    score = 0.0

    for term in query_terms:
        tf = doc_terms.get(term, 0)
        if not tf:
            continue
        df = (_doc_freq or Counter()).get(term, 0)
        idf = math.log((total_docs + 1) / (df + 1)) + 1
        score += (1 + math.log(tf)) * idf

    skill_overlap = query_context["skill_terms"] & set(parsed.get("skill_terms", set()))
    project_overlap = query_context["project_terms"] & set(_tokenize(" ".join(parsed.get("projects", []))))
    role_overlap = query_context["role_terms"] & set(_tokenize(" ".join([
        str(parsed.get("role", "")), str(parsed.get("industry", ""))
    ])))

    if query_context["skill_terms"] and not skill_overlap:
        score *= 0.25
    if skill_overlap:
        score += 8.0 + (len(skill_overlap) * 3.0)
    if project_overlap:
        score += 5.0 + min(len(project_overlap), 6)
    if role_overlap:
        score += 3.0

    wanted_level = query_context.get("level")
    record_level = str(parsed.get("level", "")).lower()
    if wanted_level and record_level:
        if wanted_level == record_level or (wanted_level == "beginner" and record_level == "junior"):
            score += 2.0
        else:
            score -= 2.0

    if score < 3.0:
        return 0
    return score


def _build_query(skills: list[str], profile: dict) -> str:
    parts = []
    parts.extend(skills or [])
    for key in ("field", "industry", "role", "jobTitle", "seniority", "summary"):
        value = profile.get(key)
        if value:
            parts.append(str(value))

    for item in profile.get("skills") or []:
        if isinstance(item, dict):
            parts.append(str(item.get("name", "")))
        else:
            parts.append(str(item))

    for item in profile.get("experience") or []:
        if isinstance(item, dict):
            parts.extend(str(item.get(k, "")) for k in ("title", "company", "duration"))
            parts.extend(str(v) for v in item.get("responsibilities", [])[:3])

    projects = profile.get("projects") or profile.get("significant_projects") or []
    for item in projects:
        if isinstance(item, dict):
            parts.extend(str(item.get(k, "")) for k in ("name", "description", "impact"))
            parts.extend(str(v) for v in item.get("tech", [])[:8])

    return " ".join(parts)


def _query_context(skills: list[str], profile: dict) -> dict:
    all_skills = list(skills or [])
    for item in profile.get("skills") or []:
        all_skills.append(str(item.get("name", "")) if isinstance(item, dict) else str(item))

    project_parts = []
    projects = profile.get("projects") or profile.get("significant_projects") or []
    for item in projects:
        if isinstance(item, dict):
            project_parts.extend(str(item.get(k, "")) for k in ("name", "description", "impact"))
            project_parts.extend(str(v) for v in item.get("tech", [])[:8])
        else:
            project_parts.append(str(item))

    role_parts = [
        str(profile.get("field", "")),
        str(profile.get("industry", "")),
        str(profile.get("role", "")),
        str(profile.get("jobTitle", "")),
    ]

    return {
        "skill_terms": set(_tokenize(" ".join(all_skills))),
        "project_terms": set(_tokenize(" ".join(project_parts))),
        "role_terms": set(_tokenize(" ".join(role_parts))),
        "level": str(profile.get("seniority", "")).lower().strip(),
    }


def _parse_input(text: str) -> dict:
    parsed: dict[str, object] = {}
    for line in text.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        key = key.strip().lower()
        value = value.strip()
        if key == "skills":
            skills = [s.strip() for s in value.split(",") if s.strip()]
            parsed["skills"] = skills
            parsed["skill_terms"] = set(_tokenize(" ".join(skills)))
        elif key in {"role", "industry", "level", "section", "type", "education", "experience"}:
            parsed[key] = value
        elif key.startswith("project"):
            parsed.setdefault("projects", []).append(value)
    parsed.setdefault("skill_terms", set())
    parsed.setdefault("projects", [])
    return parsed


def _tokenize(text: str) -> list[str]:
    words = re.findall(r"[a-zA-Z][a-zA-Z+#.-]{1,}", text.lower())
    return [w.strip(".") for w in words if w not in STOPWORDS and len(w) > 1]


def _to_question(text: str, skills: list[str], source: str, parsed: dict | None = None) -> dict:
    import uuid

    parsed = parsed or {}
    record_terms = set(parsed.get("skill_terms", set()))
    skill_tag = "general"
    for skill in skills:
        if set(_tokenize(skill)) & record_terms:
            skill_tag = skill
            break
    if skill_tag == "general" and parsed.get("skills"):
        skill_tag = str(parsed["skills"][0])
    elif skill_tag == "general" and skills:
        skill_tag = skills[0]
    return {
        "questionId": str(uuid.uuid4()),
        "questionText": text,
        "skillTag": skill_tag,
        "category": "technical",
        "source": source,
    }
