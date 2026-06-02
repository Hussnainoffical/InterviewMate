import re
from statistics import mean


STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "how",
    "i", "in", "is", "it", "of", "on", "or", "that", "the", "this", "to",
    "was", "what", "when", "where", "why", "with", "you", "your",
}

MIN_MEANINGFUL_WORDS = 8
MIN_KEYWORD_CHARS = 4
NON_ANSWERS = {
    "thank", "thanks", "you", "okay", "ok", "yes", "no", "hello", "hi",
    "testing", "test", "mic", "microphone", "silence",
}


def evaluate_answer(question: dict, transcript: str) -> dict:
    question_text = question.get("questionText") or question.get("question_text") or ""
    skill_tag = question.get("skillTag") or question.get("skill_tag") or ""
    transcript = (transcript or "").strip()

    question_terms = _keywords(question_text + " " + skill_tag)
    answer_terms = _keywords(transcript)
    matched = sorted(question_terms & answer_terms)

    relevance = _clamp((len(matched) / max(len(question_terms), 1)) * 100)
    word_count = len(re.findall(r"\w+", transcript))
    completeness = _clamp((word_count / 80) * 100)
    clarity = _clarity_score(transcript)

    score = round((relevance * 0.4) + (completeness * 0.35) + (clarity * 0.25), 1)
    feedback = _feedback(score, word_count, matched)

    return {
        "questionId": question.get("questionId") or question.get("question_id"),
        "questionText": question_text,
        "transcript": transcript,
        "relevanceScore": round(relevance, 1),
        "clarityScore": round(clarity, 1),
        "completenessScore": round(completeness, 1),
        "overallScore": score,
        "keywordsMatched": matched[:12],
        "feedback": feedback,
    }


def validate_answer_transcript(transcript: str) -> tuple[bool, str | None]:
    transcript = (transcript or "").strip()
    words = re.findall(r"[a-zA-Z][a-zA-Z'-]*", transcript.lower())
    meaningful = [
        w for w in words
        if len(w) >= MIN_KEYWORD_CHARS and w not in STOPWORDS and w not in NON_ANSWERS
    ]

    if len(words) < MIN_MEANINGFUL_WORDS or len(meaningful) < 3:
        return False, (
            "No meaningful answer was detected. Please record a complete spoken answer "
            "before continuing."
        )

    return True, None


def summarize_session(question_scores: list[dict]) -> dict:
    if not question_scores:
        return {
            "overallScore": 0.0,
            "summary": "No answers were submitted.",
            "strengths": [],
            "improvements": ["Submit answers for each interview question."],
        }

    overall = round(mean(s.get("overallScore", 0.0) for s in question_scores), 1)
    strengths = []
    improvements = []

    if mean(s.get("clarityScore", 0.0) for s in question_scores) >= 70:
        strengths.append("Clear communication")
    if mean(s.get("relevanceScore", 0.0) for s in question_scores) >= 55:
        strengths.append("Answers stayed connected to the question")
    if mean(s.get("completenessScore", 0.0) for s in question_scores) >= 70:
        strengths.append("Good answer depth")

    if mean(s.get("relevanceScore", 0.0) for s in question_scores) < 55:
        improvements.append("Use more keywords and examples directly related to the question.")
    if mean(s.get("completenessScore", 0.0) for s in question_scores) < 70:
        improvements.append("Add more detail: situation, action, tools, and measurable result.")
    if mean(s.get("clarityScore", 0.0) for s in question_scores) < 70:
        improvements.append("Use shorter, structured answers with fewer filler words.")

    if not strengths:
        strengths.append("Completed the interview flow")
    if not improvements:
        improvements.append("Add more quantified impact to make answers stronger.")

    return {
        "overallScore": overall,
        "summary": f"Overall performance: {overall}%. Evaluated {len(question_scores)} answers.",
        "strengths": strengths,
        "improvements": improvements,
    }


def _keywords(text: str) -> set[str]:
    words = re.findall(r"[a-zA-Z][a-zA-Z+#.-]{2,}", text.lower())
    return {w.strip(".") for w in words if w not in STOPWORDS}


def _clarity_score(text: str) -> float:
    if not text:
        return 0.0
    words = re.findall(r"\w+", text)
    sentences = [s for s in re.split(r"[.!?]+", text) if s.strip()]
    avg_sentence = len(words) / max(len(sentences), 1)
    filler_count = sum(1 for w in words if w.lower() in {"um", "uh", "like", "basically"})
    score = 90
    if avg_sentence > 28:
        score -= min((avg_sentence - 28) * 1.5, 25)
    score -= min(filler_count * 4, 20)
    if len(words) < 20:
        score -= 20
    return _clamp(score)


def _feedback(score: float, word_count: int, matched: list[str]) -> str:
    if score >= 80:
        return "Strong answer with relevant detail and clear delivery."
    if score >= 60:
        return "Solid answer. Add more concrete examples, metrics, or implementation detail."
    if word_count < 35:
        return "Answer is too short. Expand with a specific example and outcome."
    if not matched:
        return "Answer needs to connect more directly to the question."
    return "Answer has useful pieces but needs clearer structure and stronger evidence."


def _clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
    return max(low, min(high, value))
