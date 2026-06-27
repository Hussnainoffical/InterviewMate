"""Interview answer evaluation — OpenAI-powered semantic scoring with local fallback."""

from __future__ import annotations
import json, logging, os, re
from pathlib import Path
from statistics import mean
from typing import Any

log = logging.getLogger("interviewmate.evaluation")
BACKEND_ROOT = Path(__file__).resolve().parents[2]
LOCAL_ENV_FILES = [BACKEND_ROOT / ".env", BACKEND_ROOT / "env"]

STOPWORDS = {
    "a","an","and","are","as","at","be","by","for","from","how",
    "i","in","is","it","of","on","or","that","the","this","to",
    "was","what","when","where","why","with","you","your",
}
MIN_MEANINGFUL_WORDS = 8
MIN_KEYWORD_CHARS = 4
NON_ANSWERS = {"thank","thanks","you","okay","ok","yes","no","hello","hi","testing","test","mic","microphone","silence"}
EVAL_MODEL = "gpt-4o-mini"

def evaluate_answer(question: dict, transcript: str) -> dict:
    question_text = question.get("questionText") or question.get("question_text") or ""
    skill_tag = question.get("skillTag") or question.get("skill_tag") or ""
    category = question.get("category") or "technical"
    transcript = (transcript or "").strip()
    api_key = _resolve_openai_api_key()
    if api_key:
        try:
            result = _openai_evaluate(question_text, transcript, skill_tag, category, api_key)
            if result:
                result["questionId"] = question.get("questionId") or question.get("question_id")
                result["questionText"] = question_text
                result["transcript"] = transcript
                return result
        except Exception as exc:
            log.warning("OpenAI evaluation failed, using fallback: %s", exc)
    return _keyword_evaluate(question, transcript)

def validate_answer_transcript(transcript: str) -> tuple[bool, str | None]:
    transcript = (transcript or "").strip()
    words = re.findall(r"[a-zA-Z][a-zA-Z'-]*", transcript.lower())
    meaningful = [w for w in words if len(w) >= MIN_KEYWORD_CHARS and w not in STOPWORDS and w not in NON_ANSWERS]
    if len(words) < MIN_MEANINGFUL_WORDS or len(meaningful) < 3:
        return False, "No meaningful answer was detected. Please record a complete spoken answer before continuing."
    return True, None

def summarize_session(question_scores: list[dict]) -> dict:
    if not question_scores:
        return {"overallScore":0.0,"summary":"No answers were submitted.","strengths":[],"improvements":["Submit answers for each interview question."],"detailedFeedback":""}
    overall = round(mean(s.get("overallScore", 0.0) for s in question_scores), 1)
    api_key = _resolve_openai_api_key()
    if api_key:
        try:
            result = _openai_summarize_session(question_scores, overall, api_key)
            if result:
                return result
        except Exception as exc:
            log.warning("OpenAI session summary failed: %s", exc)
    return _keyword_summarize(question_scores, overall)

def _openai_evaluate(question_text, transcript, skill_tag, category, api_key):
    import httpx
    is_technical = category in ("technical","problem_solving","project")
    system_prompt = (
        "You are an expert interview evaluator for InterviewMate. Evaluate the candidate's answer. Score each dimension 0-100.\n"
        "Dimensions: relevanceScore, completenessScore, clarityScore"
        + (", correctnessScore" if is_technical else "")
        + "\nAlso provide: feedback (1-2 sentences), keyStrength, keyImprovement, keywordsMatched (list).\n"
        "Return ONLY valid JSON."
    )
    user_prompt = f"Question: {question_text}\nSkill: {skill_tag}\nCategory: {category}\n\nAnswer:\n{transcript}\n\nEvaluate and return JSON."
    response = httpx.post("https://api.openai.com/v1/chat/completions",
        headers={"Authorization":f"Bearer {api_key}","Content-Type":"application/json"},
        json={"model":os.getenv("INTERVIEWMATE_EVAL_MODEL",EVAL_MODEL),
              "messages":[{"role":"system","content":system_prompt},{"role":"user","content":user_prompt}],
              "temperature":0.3,"max_tokens":500,"response_format":{"type":"json_object"}},
        timeout=15)
    response.raise_for_status()
    result = json.loads(response.json()["choices"][0]["message"]["content"])
    relevance = _clamp(float(result.get("relevanceScore",0)))
    completeness = _clamp(float(result.get("completenessScore",0)))
    clarity = _clamp(float(result.get("clarityScore",0)))
    correctness = _clamp(float(result.get("correctnessScore",0))) if is_technical else None
    if is_technical:
        overall = round(relevance*0.25+completeness*0.25+clarity*0.20+correctness*0.30, 1)
    else:
        overall = round(relevance*0.35+completeness*0.35+clarity*0.30, 1)
    eval_result = {"relevanceScore":round(relevance,1),"completenessScore":round(completeness,1),"clarityScore":round(clarity,1),
        "overallScore":overall,"feedback":str(result.get("feedback","")),"keyStrength":str(result.get("keyStrength","")),
        "keyImprovement":str(result.get("keyImprovement","")),"keywordsMatched":result.get("keywordsMatched",[])[:12],"evaluationSource":"openai"}
    if is_technical and correctness is not None:
        eval_result["correctnessScore"] = round(correctness, 1)
    return eval_result

def _openai_summarize_session(question_scores, overall, api_key):
    import httpx
    qa_summaries = []
    for i, qs in enumerate(question_scores, 1):
        qa_summaries.append(f"Q{i}: \"{qs.get('questionText','N/A')[:100]}\" Score:{qs.get('overallScore',0)}% Feedback:{qs.get('feedback','N/A')}")
    system_prompt = "You are an interview coach generating a report. Return JSON: summary (2-3 sentences), strengths (2-4 items), improvements (2-4 items), interviewReadiness (not_ready/needs_work/almost_ready/ready), topicGaps (array), communicationNotes (1 sentence)."
    user_prompt = f"Overall: {overall}%\nQuestions: {len(question_scores)}\n\n" + "\n".join(qa_summaries)
    response = httpx.post("https://api.openai.com/v1/chat/completions",
        headers={"Authorization":f"Bearer {api_key}","Content-Type":"application/json"},
        json={"model":os.getenv("INTERVIEWMATE_EVAL_MODEL",EVAL_MODEL),
              "messages":[{"role":"system","content":system_prompt},{"role":"user","content":user_prompt}],
              "temperature":0.4,"max_tokens":800,"response_format":{"type":"json_object"}},
        timeout=20)
    response.raise_for_status()
    result = json.loads(response.json()["choices"][0]["message"]["content"])
    return {"overallScore":overall,"summary":str(result.get("summary",f"Overall: {overall}%.")),"strengths":result.get("strengths",[]),
        "improvements":result.get("improvements",[]),"interviewReadiness":str(result.get("interviewReadiness","needs_work")),
        "topicGaps":result.get("topicGaps",[]),"communicationNotes":str(result.get("communicationNotes","")),"detailedFeedback":"","evaluationSource":"openai"}

def _keyword_evaluate(question, transcript):
    question_text = question.get("questionText") or question.get("question_text") or ""
    skill_tag = question.get("skillTag") or question.get("skill_tag") or ""
    transcript = (transcript or "").strip()
    question_terms = _keywords(question_text + " " + skill_tag)
    answer_terms = _keywords(transcript)
    matched = sorted(question_terms & answer_terms)
    relevance = _clamp((len(matched)/max(len(question_terms),1))*100)
    word_count = len(re.findall(r"\w+", transcript))
    completeness = _clamp((word_count/80)*100)
    clarity = _clarity_score(transcript)
    score = round((relevance*0.4)+(completeness*0.35)+(clarity*0.25), 1)
    feedback = _feedback(score, word_count, matched)
    return {"questionId":question.get("questionId") or question.get("question_id"),"questionText":question_text,"transcript":transcript,
        "relevanceScore":round(relevance,1),"clarityScore":round(clarity,1),"completenessScore":round(completeness,1),
        "overallScore":score,"keywordsMatched":matched[:12],"feedback":feedback,"evaluationSource":"keyword"}

def _keyword_summarize(question_scores, overall):
    strengths, improvements = [], []
    if mean(s.get("clarityScore",0.0) for s in question_scores) >= 70: strengths.append("Clear communication")
    if mean(s.get("relevanceScore",0.0) for s in question_scores) >= 55: strengths.append("Answers stayed connected to the question")
    if mean(s.get("completenessScore",0.0) for s in question_scores) >= 70: strengths.append("Good answer depth")
    if mean(s.get("relevanceScore",0.0) for s in question_scores) < 55: improvements.append("Use more keywords and examples directly related to the question.")
    if mean(s.get("completenessScore",0.0) for s in question_scores) < 70: improvements.append("Add more detail: situation, action, tools, and measurable result.")
    if mean(s.get("clarityScore",0.0) for s in question_scores) < 70: improvements.append("Use shorter, structured answers with fewer filler words.")
    if not strengths: strengths.append("Completed the interview flow")
    if not improvements: improvements.append("Add more quantified impact to make answers stronger.")
    return {"overallScore":overall,"summary":f"Overall performance: {overall}%. Evaluated {len(question_scores)} answers.",
        "strengths":strengths,"improvements":improvements,"detailedFeedback":"","evaluationSource":"keyword"}

def _keywords(text):
    words = re.findall(r"[a-zA-Z][a-zA-Z+#.-]{2,}", text.lower())
    return {w.strip(".") for w in words if w not in STOPWORDS}

def _clarity_score(text):
    if not text: return 0.0
    words = re.findall(r"\w+", text)
    sentences = [s for s in re.split(r"[.!?]+", text) if s.strip()]
    avg_sentence = len(words)/max(len(sentences),1)
    filler_count = sum(1 for w in words if w.lower() in {"um","uh","like","basically"})
    score = 90
    if avg_sentence > 28: score -= min((avg_sentence-28)*1.5, 25)
    score -= min(filler_count*4, 20)
    if len(words) < 20: score -= 20
    return _clamp(score)

def _feedback(score, word_count, matched):
    if score >= 80: return "Strong answer with relevant detail and clear delivery."
    if score >= 60: return "Solid answer. Add more concrete examples, metrics, or implementation detail."
    if word_count < 35: return "Answer is too short. Expand with a specific example and outcome."
    if not matched: return "Answer needs to connect more directly to the question."
    return "Answer has useful pieces but needs clearer structure and stronger evidence."

def _clamp(value, low=0.0, high=100.0): return max(low, min(high, value))

def _resolve_openai_api_key():
    return (os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_SECRET_KEY")
        or _read_local_env_value("OPENAI_API_KEY") or _read_local_env_value("OPENAI_SECRET_KEY") or "").strip()

def _read_local_env_value(key):
    for env_file in LOCAL_ENV_FILES:
        try: lines = env_file.read_text(encoding="utf-8").splitlines()
        except OSError: continue
        for line in lines:
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or "=" not in stripped: continue
            name, value = stripped.split("=", 1)
            if name.strip() == key: return value.strip().strip('"').strip("'")
    return None
