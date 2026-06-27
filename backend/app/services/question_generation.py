from pathlib import Path
import os
import re
from app.services.local_env import local_env_value
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

    question_model = local_env_value(
        "INTERVIEWMATE_QUESTION_MODEL",
        default="qwen",
        root=BACKEND_ROOT,
    ).strip().lower()
    if question_model == "qwen":
        try:
            from app.services.qwen_question_generator import generate_qwen_questions

            qwen_questions = generate_qwen_questions(
                skills=skills,
                candidate_profile=candidate_profile,
                count=count,
                interview_mode=str(candidate_profile.get("interview_mode") or "mixed"),
                difficulty=str(candidate_profile.get("difficulty") or "adaptive"),
            )
            if len(qwen_questions) >= count:
                return qwen_questions[:count]
            if qwen_questions:
                qwen_questions.extend(_fallback_questions(
                    skills,
                    count - len(qwen_questions),
                    candidate_profile=candidate_profile,
                    exclude_texts={q["questionText"] for q in qwen_questions},
                ))
                return qwen_questions[:count]
        except Exception:
            pass

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
        "dart": "How does Dart's async/await and isolate model shape how you structure app logic?",
        "firebase": "How do you structure Firestore data and lock it down with security rules?",
        "machine learning": "How do you evaluate whether a machine learning model is generalizing well?",
        "deep learning": "How do you decide on an architecture and prevent overfitting in a deep model?",
        "tensorflow": "Walk me through building and training a model in TensorFlow end to end.",
        "pytorch": "How do you debug a training loop in PyTorch when the loss won't converge?",
        "pandas": "How do you clean and reshape messy, missing data in a large Pandas dataframe?",
        "numpy": "Where does vectorizing with NumPy matter, and how have you used it for speed?",
        "fastapi": "How do you structure a FastAPI backend for validation, routing, and database access?",
        "django": "How do you organize a Django project and run migrations safely in production?",
        "flask": "How would you structure a Flask app for testability and configuration management?",
        "node": "How do you handle async errors and avoid blocking the Node.js event loop?",
        "node.js": "How do you handle async errors and avoid blocking the Node.js event loop?",
        "express": "How do you structure middleware and error handling in an Express API?",
        "react": "How do you manage state and avoid unnecessary re-renders in a React app?",
        "react native": "How do you handle navigation and native modules in a React Native app?",
        "javascript": "Explain closures and the event loop in JavaScript with a concrete example.",
        "typescript": "How does TypeScript's type system catch bugs plain JavaScript wouldn't?",
        "java": "How do you manage memory and avoid leaks in a long-running Java service?",
        "spring": "How do you structure a Spring Boot service for dependency injection and testing?",
        "kotlin": "Which Kotlin features do you rely on to write safer, more concise code?",
        "swift": "How do you manage memory and avoid retain cycles in Swift?",
        "c++": "How do you manage memory and avoid undefined behavior in modern C++?",
        "c#": "How do you use async/await and LINQ effectively in C#?",
        "go": "How do you use goroutines and channels safely to handle concurrency in Go?",
        "golang": "How do you use goroutines and channels safely to handle concurrency in Go?",
        "rust": "How does Rust's ownership model prevent data races, and where did it help you?",
        "php": "How do you structure a maintainable PHP application and handle dependencies?",
        "laravel": "How do you use Laravel's Eloquent and migrations to model and evolve your data?",
        "ruby": "How do you keep a Ruby on Rails codebase clean as it grows?",
        "sql": "How would you optimize a slow SQL query in production?",
        "postgresql": "How do you design indexes and read query plans in PostgreSQL?",
        "mysql": "How do you diagnose and fix a slow MySQL query under load?",
        "mongodb": "How do you model data and design indexes for a MongoDB collection?",
        "docker": "How do you keep Docker images small and your builds reproducible?",
        "kubernetes": "How do you handle rolling deployments and resource limits in Kubernetes?",
        "aws": "Which AWS services would you combine for a scalable, fault-tolerant backend, and why?",
        "azure": "Which Azure services would you use to build and deploy a resilient service?",
        "gcp": "Which GCP services would you pick to run a scalable backend, and why?",
        "terraform": "How do you structure Terraform and manage state across environments?",
        "git": "How do you resolve a tricky merge conflict and keep history clean?",
        "redis": "When do you reach for Redis, and how do you avoid stale or inconsistent cache?",
        "graphql": "What are the tradeoffs of GraphQL versus REST for an API you've built?",
        "kafka": "How do you reason about delivery guarantees and ordering with Kafka?",
    }
    # Seniority-aware generic questions so a junior and a senior get different prompts.
    seniority = str((candidate_profile or {}).get("seniority", "")).strip().lower()
    if seniority in ("beginner", "junior", "entry", "entry-level", "fresh", "fresher"):
        defaults = [
            "Walk me through a project from your studies or portfolio and your exact role in it.",
            "When you get stuck on a problem, what steps do you take to work through it?",
            "Tell me about something technical you taught yourself recently and how you did it.",
            "How do you check that your code actually works before you call it done?",
            "What area are you most excited to grow in during your first year on the job?",
        ]
    elif seniority in ("senior", "lead", "principal", "staff", "architect"):
        defaults = [
            "Tell me about a complex system you designed and the key architectural tradeoffs you made.",
            "Describe a time you led a project through significant technical or organizational risk.",
            "How do you mentor engineers and raise the technical bar across a team?",
            "Walk me through a hard production incident you owned and what you changed afterward.",
            "How do you decide when to take on technical debt versus invest in doing it right?",
        ]
    else:
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

    # Shared extra pool so the fallback can always reach `count` (up to 15)
    # even when no skill or dataset question matched.
    extra_generic = [
        "Tell me about a project you enjoyed and what your specific contribution was.",
        "What is a technical decision you made that you would approach differently now?",
        "How do you go about learning a tool or technology you have not used before?",
        "Describe a bug that was hard to track down and how you finally found it.",
        "How do you prioritize when you have more tasks than time?",
        "Tell me about working with someone whose style was different from yours.",
        "How do you make sure your work is reliable before you consider it finished?",
        "What does good quality mean to you in your work, and how do you uphold it?",
        "Tell me about a piece of feedback that changed how you work.",
        "How do you handle it when requirements change midway through your work?",
        "What is something you built that you are proud of, and why?",
        "How do you explain a technical tradeoff to someone non-technical?",
    ]
    for text in defaults + extra_generic:
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
