"""
question_generator.py
=====================
Hybrid interview question generator for InterviewMate.

Combines two strategies:
  1. STRUCTURED QUESTION BANK — covers all major fields, always reliable
  2. FINE-TUNED FLAN-T5 MODEL  — generates contextual follow-up questions
                                from candidate's actual experience/projects

DEFAULT MIX for a 5-question interview:
  Q1-Q3  → from question bank (technical, field+seniority specific)
  Q4     → from question bank (behavioral)
  Q5     → from fine-tuned T5 (project-specific, contextual)

If T5 model is missing/broken/disabled, falls back to 100% bank.

USAGE:
    from question_generator import generate_questions, load_t5_model

    # Optional: load T5 once at app startup
    load_t5_model("/path/to/interviewmate_flanT5_final")

    # Generate questions for a candidate
    questions = generate_questions(
        skills    = ["Python", "FastAPI", "PostgreSQL"],
        field     = "Software Engineering",
        seniority = "Mid-Level",
        projects  = [
            {"name": "interviewmate", "description": "AI-powered mock interview backend",
             "tech": ["FastAPI", "PostgreSQL", "Docker"]},
        ],
        experience = [
            {"title": "Backend Engineer", "company": "Careem",
             "responsibilities": ["Built REST APIs handling 10K req/sec"]},
        ],
        num_questions = 5,
        interview_type = "mixed",
        use_t5         = True,   # set False for pure bank mode
        n_t5_questions = 1,
    )

    for q in questions:
        print(q.question_text, "  (source:", q.source, ")")
"""

import os
import random
import uuid
from dataclasses import dataclass, field
from typing import Optional, Union


# ══════════════════════════════════════════════════════════════════════════════
# DATA CLASS — replaces dependency on app.models for portability
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class InterviewQuestion:
    question_id: str
    question_text: str
    skill_tag: str
    category: str       # "technical" | "behavioral" | "project" | "experience"
    source: str         # "bank" | "t5_model" | "t5_fallback"


# ══════════════════════════════════════════════════════════════════════════════
# T5 MODEL — lazy-loaded, optional
# ══════════════════════════════════════════════════════════════════════════════

_t5_model = None
_t5_tokenizer = None
_t5_device = "cpu"
_t5_loaded = False


def load_t5_model(model_path: str = "./models/flan_t5_qgen") -> bool:
    """
    Load the fine-tuned FLAN-T5 model. Call once at app startup.

    Returns True if loaded successfully, False otherwise.
    Failure is silent — generator falls back to bank automatically.
    """
    global _t5_model, _t5_tokenizer, _t5_device, _t5_loaded

    if not os.path.exists(model_path):
        print(f"[question_generator] T5 model not found at {model_path}")
        print("[question_generator] Will use question bank only.")
        return False

    try:
        import torch
        from transformers import T5ForConditionalGeneration, AutoTokenizer

        _t5_device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"[question_generator] Loading T5 from {model_path} on {_t5_device}...")

        _t5_tokenizer = AutoTokenizer.from_pretrained(model_path)
        _t5_model = T5ForConditionalGeneration.from_pretrained(model_path)
        _t5_model.eval()
        if _t5_device == "cuda":
            _t5_model = _t5_model.cuda()

        _t5_loaded = True
        print(f"[question_generator] T5 model loaded successfully.")
        return True

    except Exception as e:
        print(f"[question_generator] T5 load failed: {e}")
        print("[question_generator] Will use question bank only.")
        _t5_loaded = False
        return False


def is_t5_loaded() -> bool:
    return _t5_loaded


def _t5_generate(context: str, answer: str, max_new_tokens: int = 96) -> Optional[str]:
    """Generate a single question using T5. Returns None on failure."""
    if not _t5_loaded:
        return None

    try:
        import torch
        prompt = f"generate question: {answer} context: {context}"
        inputs = _t5_tokenizer(
            prompt, return_tensors="pt", max_length=512, truncation=True
        )
        if _t5_device == "cuda":
            inputs = {k: v.cuda() for k, v in inputs.items()}

        with torch.no_grad():
            out = _t5_model.generate(
                inputs["input_ids"],
                max_new_tokens=max_new_tokens,
                num_beams=4,
                early_stopping=True,
                no_repeat_ngram_size=3,
            )
        question = _t5_tokenizer.decode(out[0], skip_special_tokens=True).strip()

        # Quality gate — reject obviously broken output
        if len(question) < 15:
            return None
        if not (question.endswith("?") or question[0].isupper()):
            return None
        # Reject if T5 just echoed the answer back
        if question.lower().strip("?. ") == answer.lower().strip():
            return None

        # Force question mark
        if not question.endswith("?"):
            question = question.rstrip(".") + "?"
        return question

    except Exception as e:
        print(f"[question_generator] T5 generation failed: {e}")
        return None


# ══════════════════════════════════════════════════════════════════════════════
# QUESTION BANK
# ══════════════════════════════════════════════════════════════════════════════

QUESTION_BANK = {
    "behavioral": {
        "all": [
            "Tell me about yourself and walk me through your professional journey.",
            "Describe a challenging situation you faced at work and how you handled it.",
            "Tell me about a time you had to meet a tight deadline. How did you manage it?",
            "Describe a situation where you had to work with a difficult colleague or client.",
            "Tell me about a project you are most proud of. What was your contribution?",
            "Describe a time you made a mistake at work. How did you handle it?",
            "Tell me about a time you had to learn a new skill quickly.",
            "Describe a situation where you showed leadership even without a formal title.",
            "Tell me about a time you disagreed with your manager. What did you do?",
            "Where do you see yourself professionally in the next five years?",
            "What is your greatest professional strength and how have you used it?",
            "What is an area you are actively working to improve?",
            "Tell me about a time you had to juggle multiple priorities.",
            "Describe a time you received critical feedback. How did you respond?",
            "Tell me about a time you went above and beyond what was expected.",
        ],
        "Senior": [
            "Describe how you have built and developed high-performing teams.",
            "Tell me about a strategic decision you made that had significant business impact.",
            "How have you managed stakeholder expectations on a complex project?",
            "Describe a time you drove organizational change. What was your approach?",
            "How do you mentor junior team members while balancing your own workload?",
            "Tell me about a time you had to influence without direct authority.",
        ],
    },

    "Software Engineering": {
        "Beginner": [
            "What is the difference between a list and an array?",
            "Explain what version control is and why it is important.",
            "What is the difference between front-end and back-end development?",
            "Explain what an API is and give an example of how it is used.",
            "What is the difference between SQL and NoSQL databases?",
            "Explain the concept of object-oriented programming with an example.",
            "What does DRY stand for in software development and why is it important?",
            "Explain what a bug is and describe your process for debugging code.",
            "What is the difference between a function and a method?",
            "What is the purpose of a README file in a project?",
        ],
        "Mid-Level": [
            "Explain the SOLID principles and give an example of each.",
            "What is the difference between REST and GraphQL APIs?",
            "Explain microservices architecture and when you would use it over monoliths.",
            "How do you approach writing unit tests? What makes a good test?",
            "What is CI/CD and how have you implemented it in a project?",
            "Explain database indexing and when would you use it.",
            "What design patterns have you used and in what context?",
            "How do you handle authentication and authorization in a web application?",
            "Explain the difference between synchronous and asynchronous programming.",
            "How do you approach code reviews — both giving and receiving feedback?",
            "What is technical debt and how do you manage it?",
            "Explain caching strategies and when you would apply them.",
        ],
        "Senior": [
            "How do you design a system for high availability and fault tolerance?",
            "Explain CAP theorem and its practical implications.",
            "How would you architect a system to handle 1 million concurrent users?",
            "What is your approach to system observability — logging, monitoring, tracing?",
            "How do you make build vs buy decisions for infrastructure?",
            "Describe how you have dealt with a critical production incident.",
            "How do you evaluate and introduce new technologies into your stack?",
            "What is your approach to database sharding and replication?",
            "How do you ensure security across the entire software development lifecycle?",
            "Describe your experience with event-driven architectures.",
        ],
    },

    "Data Science / AI": {
        "Beginner": [
            "What is the difference between supervised and unsupervised learning?",
            "Explain the bias-variance tradeoff in simple terms.",
            "What is the purpose of splitting data into training and test sets?",
            "What is a confusion matrix and what does it tell you?",
            "Explain overfitting and how you would prevent it.",
            "What is the difference between classification and regression?",
            "What is cross-validation and why is it used?",
            "Explain what a feature is in machine learning.",
            "What is the difference between precision and recall?",
            "Why is data preprocessing important before building a model?",
        ],
        "Mid-Level": [
            "Explain gradient descent and how learning rate affects training.",
            "What is the difference between bagging and boosting?",
            "How do you handle imbalanced datasets?",
            "Explain the difference between L1 and L2 regularization.",
            "What are embeddings and how are they used in NLP?",
            "How would you evaluate a recommendation system?",
            "Explain the transformer architecture at a high level.",
            "What is feature engineering and describe a technique you have used?",
            "How do you detect and handle data leakage?",
            "Explain dimensionality reduction and when you would use PCA.",
            "What is A/B testing and how do you design an experiment?",
            "How do you deploy a machine learning model to production?",
        ],
        "Senior": [
            "How do you ensure reproducibility in machine learning experiments?",
            "Describe your approach to MLOps and model lifecycle management.",
            "How do you handle concept drift in deployed models?",
            "What is your approach to building fair and unbiased ML systems?",
            "Explain how you have scaled ML training to large datasets.",
            "How do you decide between building a custom model vs using a pre-trained one?",
            "Describe your experience with distributed training.",
            "How do you communicate model uncertainty to non-technical stakeholders?",
        ],
    },

    "Finance / Accounting": {
        "Beginner": [
            "What are the three main financial statements and what does each show?",
            "What is the difference between cash and accrual accounting?",
            "Explain what working capital is.",
            "What is EBITDA and why is it used as a metric?",
            "What is the time value of money?",
            "Explain the difference between assets, liabilities, and equity.",
            "What is depreciation and why does it matter?",
            "What is the difference between gross profit and net profit?",
        ],
        "Mid-Level": [
            "Walk me through a DCF valuation.",
            "How do you build a three-statement financial model?",
            "What are the key drivers of a company's valuation?",
            "Explain the difference between enterprise value and equity value.",
            "How do you assess a company's liquidity position?",
            "What is a leveraged buyout and how does it work?",
            "Explain interest rate risk and how it is managed.",
            "How do you analyze a company's debt capacity?",
            "What is working capital management and why does it matter?",
            "Explain the difference between systematic and unsystematic risk.",
        ],
        "Senior": [
            "How do you approach capital allocation decisions?",
            "Describe your experience with M&A transactions — due diligence, valuation.",
            "How do you build and manage relationships with investors?",
            "What is your approach to financial risk management at an enterprise level?",
            "How have you improved financial reporting processes in your organization?",
        ],
    },

    "Healthcare / Medical": {
        "Beginner": [
            "What does patient-centered care mean to you?",
            "How do you handle a situation where a patient is non-compliant with treatment?",
            "What is the importance of documentation in healthcare?",
            "Explain infection control measures you apply in your daily practice.",
            "How do you prioritize tasks when caring for multiple patients?",
            "What does informed consent mean and why is it important?",
            "Describe your approach to communicating a difficult diagnosis to a patient.",
            "What is the difference between diagnosis and prognosis?",
        ],
        "Mid-Level": [
            "How do you stay current with evidence-based practice in your specialty?",
            "Describe a complex case you managed and your clinical reasoning process.",
            "How do you handle disagreements with a colleague about a patient's treatment?",
            "Explain how you use clinical data to inform treatment decisions.",
            "What is your approach to multidisciplinary team collaboration?",
            "How do you manage a patient who presents with comorbidities?",
            "Describe your experience with quality improvement initiatives.",
        ],
        "Senior": [
            "How have you led clinical quality improvement initiatives?",
            "Describe your approach to mentoring junior clinicians.",
            "How do you manage resource constraints while maintaining quality of care?",
            "What is your approach to implementing clinical protocols and guidelines?",
            "How have you managed patient safety incidents?",
        ],
    },

    "Marketing / Sales": {
        "Beginner": [
            "What is the difference between B2B and B2C marketing?",
            "Explain what a marketing funnel is.",
            "What is SEO and why does it matter?",
            "What metrics would you track for a social media campaign?",
            "What is the difference between a lead and a prospect?",
            "Explain what conversion rate optimization means.",
            "What is content marketing and how does it generate leads?",
            "What is the difference between organic and paid traffic?",
        ],
        "Mid-Level": [
            "How do you build a go-to-market strategy for a new product?",
            "Describe a campaign you ran from planning to execution.",
            "How do you segment a target audience?",
            "What is your approach to A/B testing in marketing?",
            "How do you measure the ROI of a marketing campaign?",
            "Describe your experience with CRM systems and how you have used them.",
            "How do you align marketing and sales teams?",
            "What is your approach to competitor analysis?",
        ],
        "Senior": [
            "How do you build a brand strategy from the ground up?",
            "Describe how you have grown revenue through marketing-led initiatives.",
            "How do you manage a marketing team with diverse specializations?",
            "What is your approach to building long-term customer loyalty?",
        ],
    },

    "Cybersecurity": {
        "Beginner": [
            "What is the difference between authentication and authorization?",
            "Explain what a firewall does and how it works.",
            "What is phishing and how would you educate employees about it?",
            "What is the CIA triad in security?",
            "What is the difference between symmetric and asymmetric encryption?",
        ],
        "Mid-Level": [
            "Explain how you would conduct a vulnerability assessment.",
            "What is the OWASP Top 10 and how do you address them?",
            "Describe your approach to incident response.",
            "What is a zero-trust security model?",
            "How do you perform a penetration test? Walk me through your methodology.",
            "What is the difference between IDS and IPS?",
            "How do you secure a cloud environment?",
        ],
        "Senior": [
            "How do you build a security program from scratch?",
            "Describe your approach to threat modeling.",
            "How do you manage security across a large enterprise with multiple teams?",
            "How have you communicated security risk to C-level executives?",
        ],
    },

    "project_based": [
        "Walk me through this project: {project_name}. What was your role and what did you build?",
        "What was the biggest technical challenge you faced in {project_name} and how did you solve it?",
        "How did you decide on the tech stack for {project_name}?",
        "What would you do differently if you rebuilt {project_name} today?",
        "How did you handle testing and quality assurance in {project_name}?",
        "How did you measure the success of {project_name}?",
        "What did you learn from working on {project_name}?",
    ],
}


SKILL_QUESTIONS = {
    "python": [
        "Explain the difference between lists and tuples in Python.",
        "What are Python decorators and when would you use them?",
        "How does Python's GIL affect multithreaded programs?",
        "What is the difference between shallow copy and deep copy?",
        "Explain Python generators and when to use them over lists.",
        "How does Python handle memory management?",
    ],
    "javascript": [
        "Explain event delegation in JavaScript.",
        "What is the difference between == and === in JavaScript?",
        "How does async/await work? How is it different from Promises?",
        "What is closure in JavaScript? Give a practical example.",
        "Explain the JavaScript event loop.",
        "What are arrow functions and how do they differ from regular functions?",
    ],
    "react": [
        "What are React hooks and why were they introduced?",
        "Explain the virtual DOM and how React uses it.",
        "What is the difference between controlled and uncontrolled components?",
        "How does useEffect work and what are the dependency array rules?",
        "When would you use Context API vs Redux?",
        "How do you optimize performance in a React application?",
    ],
    "flutter": [
        "Explain the difference between StatelessWidget and StatefulWidget.",
        "How do you manage state in a Flutter app? What approaches have you used?",
        "What is the widget tree in Flutter?",
        "How do you make HTTP calls and handle async operations in Flutter?",
        "What is the difference between hot reload and hot restart?",
        "How do you handle navigation in Flutter?",
    ],
    "sql": [
        "What is the difference between INNER JOIN and LEFT JOIN?",
        "Explain database normalization — what are the normal forms?",
        "What are database indexes and how do they improve query performance?",
        "What is the difference between HAVING and WHERE?",
        "Explain ACID properties in database transactions.",
        "How would you optimize a slow-running query?",
    ],
    "docker": [
        "What is the difference between a Docker image and a container?",
        "What is a Dockerfile? Explain the key instructions.",
        "What is Docker Compose and when would you use it?",
        "How do Docker volumes work and why are they important?",
        "How would you reduce the size of a Docker image?",
    ],
    "kubernetes": [
        "What is the difference between a Pod and a Deployment?",
        "Explain how Services expose Pods in Kubernetes.",
        "What is a ConfigMap vs a Secret?",
        "How do you handle rolling updates in Kubernetes?",
    ],
    "aws": [
        "What is the difference between EC2 and Lambda?",
        "Explain how IAM roles and policies work.",
        "What is S3 and what use cases is it good for?",
        "How do you design a fault-tolerant system on AWS?",
    ],
    "fastapi": [
        "Why would you choose FastAPI over Flask or Django?",
        "How do you handle dependency injection in FastAPI?",
        "Explain how Pydantic models work in FastAPI.",
        "How do you handle authentication in a FastAPI application?",
    ],
    "machine learning": [
        "Explain overfitting and how you would prevent it.",
        "What is cross-validation and why is it used?",
        "Explain gradient descent and how learning rate affects it.",
        "What is the difference between precision and recall?",
        "How do you handle missing data in a dataset?",
        "What is regularization and why is it important?",
    ],
    "tensorflow": [
        "What is the difference between TensorFlow 1.x and 2.x?",
        "Explain how Keras integrates with TensorFlow.",
        "How do you save and load a TensorFlow model?",
    ],
    "pytorch": [
        "What is the difference between PyTorch and TensorFlow?",
        "Explain autograd in PyTorch.",
        "How do you write a custom Dataset class in PyTorch?",
    ],
    "leadership": [
        "How do you set goals and track performance for your team?",
        "Describe your approach to giving performance feedback.",
        "How do you handle a low-performing team member?",
        "What is your leadership style and how has it evolved?",
    ],
}


# ══════════════════════════════════════════════════════════════════════════════
# HELPERS — handle different input shapes from resume_parser / github_analyzer
# ══════════════════════════════════════════════════════════════════════════════

def _normalize_skills(skills) -> list[str]:
    """Accept skills as list of strings OR list of dicts with 'name' key."""
    if not skills:
        return []
    if isinstance(skills[0], str):
        return skills
    if isinstance(skills[0], dict):
        return [s.get("name", "") for s in skills if s.get("name")]
    return []


def _build_t5_context(
    skill_or_topic: str,
    field: str,
    seniority: str,
    experience: list,
    projects: list,
) -> str:
    """Build context string for T5 from candidate profile."""
    # Look for the skill in experience first (richer context)
    for exp in experience or []:
        title = exp.get("title", "")
        for resp in exp.get("responsibilities", []):
            if skill_or_topic.lower() in resp.lower():
                return (
                    f"The candidate worked as {title} and used {skill_or_topic} for: "
                    f"{resp[:200]}"
                )

    # Look in project descriptions
    for proj in projects or []:
        desc = proj.get("description", "")
        tech_list = proj.get("tech", [])
        if skill_or_topic.lower() in desc.lower() or skill_or_topic in tech_list:
            return (
                f"The candidate built {proj.get('name', 'a project')}: {desc[:200]}. "
                f"Tech: {', '.join(tech_list[:5])}"
            )

    # Generic fallback
    level_desc = {
        "Beginner": "fresh graduate-level",
        "Mid-Level": "3-5 years of professional",
        "Senior": "extensive senior-level",
    }.get(seniority, "professional")
    return (
        f"The candidate is a {seniority} {field} professional with "
        f"{level_desc} experience in {skill_or_topic}."
    )


def _build_project_context(project: dict) -> tuple[str, str]:
    """Return (context, answer) for a T5 project-based question."""
    name = project.get("name", "the project")
    desc = project.get("description", "")
    tech = ", ".join(project.get("tech", [])[:5])
    stars = project.get("stars")

    parts = [f"The candidate built {name}"]
    if desc:
        parts.append(f": {desc[:200]}")
    if tech:
        parts.append(f". Technologies: {tech}")
    if stars:
        parts.append(f". The project has {stars} GitHub stars")

    context = "".join(parts) + "."
    answer = name
    return context, answer


# ══════════════════════════════════════════════════════════════════════════════
# MAIN GENERATION FUNCTION
# ══════════════════════════════════════════════════════════════════════════════

def generate_questions(
    skills,
    field: str = "Software Engineering",
    seniority: str = "Mid-Level",
    projects: Optional[list] = None,
    experience: Optional[list] = None,
    num_questions: int = 5,
    interview_type: str = "mixed",   # "technical" | "behavioral" | "mixed"
    use_t5: bool = True,
    n_t5_questions: int = 1,
    seed: Optional[int] = None,
) -> list[InterviewQuestion]:
    """
    Generate a tailored interview question list.

    Args:
        skills:          list of skill strings OR list of {"name": ...} dicts
        field:           detected professional field
        seniority:       "Beginner" | "Mid-Level" | "Senior"
        projects:        list of {"name", "description", "tech", ...} dicts
        experience:      list of {"title", "company", "responsibilities", ...} dicts
        num_questions:   total questions to return (default 5)
        interview_type:  "technical" | "behavioral" | "mixed"
        use_t5:          if True and model loaded, last n_t5_questions come from T5
        n_t5_questions:  how many of num_questions to generate via T5
        seed:            optional random seed for reproducibility

    Returns:
        list of InterviewQuestion (length == num_questions)
    """
    if seed is not None:
        random.seed(seed)

    skills = _normalize_skills(skills)
    projects = projects or []
    experience = experience or []

    # Decide split: bank questions + T5 questions
    n_t5 = n_t5_questions if (use_t5 and _t5_loaded) else 0
    n_bank = num_questions - n_t5

    # ── Build the question pool from the bank ────────────────────────────────
    bank_questions = _select_from_bank(
        skills=skills,
        field=field,
        seniority=seniority,
        projects=projects,
        num_questions=n_bank,
        interview_type=interview_type,
    )

    # ── Build T5-generated questions ─────────────────────────────────────────
    t5_questions = []
    if n_t5 > 0:
        t5_questions = _generate_t5_questions(
            skills=skills,
            field=field,
            seniority=seniority,
            projects=projects,
            experience=experience,
            n=n_t5,
        )

    # If T5 silently fell back, top up with extra bank questions
    if len(t5_questions) < n_t5:
        deficit = n_t5 - len(t5_questions)
        extra = _select_from_bank(
            skills=skills,
            field=field,
            seniority=seniority,
            projects=projects,
            num_questions=deficit,
            interview_type=interview_type,
            exclude_texts={q.question_text for q in bank_questions},
        )
        bank_questions.extend(extra)

    # T5 questions go LAST — they're the contextual deep-dive
    return bank_questions + t5_questions


# ── BANK SELECTION ────────────────────────────────────────────────────────────

def _select_from_bank(
    skills: list[str],
    field: str,
    seniority: str,
    projects: list,
    num_questions: int,
    interview_type: str,
    exclude_texts: Optional[set] = None,
) -> list[InterviewQuestion]:
    """Build and balance question pool from the structured bank."""
    if num_questions <= 0:
        return []

    exclude_texts = exclude_texts or set()
    pool = []

    # 1. Field + seniority technical questions
    if interview_type in ("technical", "mixed"):
        field_bank = QUESTION_BANK.get(field, QUESTION_BANK.get("Software Engineering", {}))
        level_qs = list(field_bank.get(seniority, []))
        if seniority == "Senior":
            level_qs += field_bank.get("Mid-Level", [])[:3]
        elif seniority == "Mid-Level":
            level_qs += field_bank.get("Beginner", [])[:2]
        for q in level_qs:
            pool.append({"text": q, "tag": field, "category": "technical"})

    # 2. Skill-specific questions
    if interview_type in ("technical", "mixed"):
        for skill in skills:
            sk_lower = skill.lower()
            for key, qs in SKILL_QUESTIONS.items():
                if key in sk_lower or sk_lower in key:
                    for q in qs:
                        pool.append({"text": q, "tag": skill, "category": "technical"})
                    break

    # 3. Behavioral questions
    if interview_type in ("behavioral", "mixed"):
        beh = QUESTION_BANK["behavioral"]["all"]
        if seniority == "Senior":
            beh = beh + QUESTION_BANK["behavioral"]["Senior"]
        for q in beh:
            pool.append({"text": q, "tag": "behavioral", "category": "behavioral"})

    # 4. Project-templated questions (bank version, T5 version comes separately)
    if projects and interview_type in ("technical", "mixed"):
        for proj in projects[:2]:
            pname = proj.get("name", "your project")
            for tmpl in QUESTION_BANK["project_based"][:3]:
                pool.append({
                    "text": tmpl.replace("{project_name}", pname),
                    "tag": "project",
                    "category": "project",
                })

    # Last-resort fallback to behavioral
    if not pool:
        pool = [{"text": q, "tag": "general", "category": "behavioral"}
                for q in QUESTION_BANK["behavioral"]["all"]]

    # Deduplicate and exclude
    seen = set(exclude_texts)
    unique = []
    for item in pool:
        if item["text"] not in seen:
            seen.add(item["text"])
            unique.append(item)

    # Balance categories if mixed
    if interview_type == "mixed":
        tech = [q for q in unique if q["category"] == "technical"]
        beh = [q for q in unique if q["category"] == "behavioral"]
        proj = [q for q in unique if q["category"] == "project"]
        random.shuffle(tech); random.shuffle(beh); random.shuffle(proj)

        n_tech = max(1, int(num_questions * 0.6))
        n_beh = max(1, int(num_questions * 0.3))
        n_proj = num_questions - n_tech - n_beh

        selected = tech[:n_tech] + beh[:n_beh] + proj[:max(0, n_proj)]
        if len(selected) < num_questions:
            remaining = [q for q in unique if q not in selected]
            random.shuffle(remaining)
            selected += remaining[:num_questions - len(selected)]
    else:
        random.shuffle(unique)
        selected = unique[:num_questions]

    return [
        InterviewQuestion(
            question_id=str(uuid.uuid4()),
            question_text=item["text"],
            skill_tag=item["tag"],
            category=item["category"],
            source="bank",
        )
        for item in selected[:num_questions]
    ]


# ── T5 GENERATION ─────────────────────────────────────────────────────────────

def _generate_t5_questions(
    skills: list[str],
    field: str,
    seniority: str,
    projects: list,
    experience: list,
    n: int,
) -> list[InterviewQuestion]:
    """Generate up to n contextual questions via T5. Skip silently on failure."""
    questions = []

    # Strategy: prefer project-based T5 questions (richer context).
    # Fall back to skill-based if no projects.
    contexts = []

    # Project-based contexts
    for proj in projects[:n]:
        ctx, ans = _build_project_context(proj)
        contexts.append((ctx, ans, proj.get("name", "project"), "project"))

    # Skill-based contexts to fill remaining slots
    for skill in skills[: max(0, n - len(contexts))]:
        ctx = _build_t5_context(skill, field, seniority, experience, projects)
        contexts.append((ctx, skill, skill, "technical"))

    for ctx, ans, tag, category in contexts[:n]:
        question_text = _t5_generate(ctx, ans)
        if question_text:
            questions.append(InterviewQuestion(
                question_id=str(uuid.uuid4()),
                question_text=question_text,
                skill_tag=tag,
                category=category,
                source="t5_model",
            ))

    return questions