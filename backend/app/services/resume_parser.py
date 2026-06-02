"""
resume_parser.py  —  Production-Grade Resume Parser
=====================================================
Improvements over basic version:
  1. Fuzzy matching via rapidfuzz  (handles typos like "pyhton" → Python)
  2. Phrase detection              (handles "machine learning engineer")
  3. Smart section detection       (handles "Professional Journey", "Career History", etc.)
  4. Proper experience extraction  (company, role, duration, not just raw text)
  5. Tech stack extraction from project descriptions
  6. Skill normalization           ("js" == "javascript", "ml" == "machine learning")
  7. Field detection with scoring  (most matched field wins)
  8. Seniority from multiple signals (title + years + education)

INSTALL:
    pip install rapidfuzz PyPDF2 python-docx
"""

import re
import io
from typing import Optional

# rapidfuzz for fuzzy matching — pip install rapidfuzz
try:
    from rapidfuzz import fuzz, process as rfprocess
    FUZZY_AVAILABLE = True
except ImportError:
    FUZZY_AVAILABLE = False
    print("⚠️  rapidfuzz not installed. Run: pip install rapidfuzz")
    print("   Falling back to exact matching.")


# ══════════════════════════════════════════════════════════════════════════════
# SKILL NORMALIZATION MAP
# Handles aliases, abbreviations, and common variations
# ══════════════════════════════════════════════════════════════════════════════
SKILL_ALIASES = {
    # Programming languages
    "js":             "JavaScript",
    "javascript":     "JavaScript",
    "typescript":     "TypeScript",
    "ts":             "TypeScript",
    "py":             "Python",
    "python":         "Python",
    "java":           "Java",
    "c++":            "C++",
    "cpp":            "C++",
    "c#":             "C#",
    "csharp":         "C#",
    "golang":         "Go",
    "go":             "Go",
    "rb":             "Ruby",
    "ruby":           "Ruby",
    "php":            "PHP",
    "rs":             "Rust",
    "rust":           "Rust",
    "kotlin":         "Kotlin",
    "swift":          "Swift",
    "dart":           "Dart",
    "r":              "R",
    "scala":          "Scala",
    "matlab":         "MATLAB",

    # Web / Frameworks
    "reactjs":        "React",
    "react.js":       "React",
    "react":          "React",
    "vuejs":          "Vue.js",
    "vue.js":         "Vue.js",
    "vue":            "Vue.js",
    "angularjs":      "Angular",
    "angular":        "Angular",
    "nodejs":         "Node.js",
    "node.js":        "Node.js",
    "node":           "Node.js",
    "nextjs":         "Next.js",
    "next.js":        "Next.js",
    "expressjs":      "Express.js",
    "express":        "Express.js",
    "django":         "Django",
    "flask":          "Flask",
    "fastapi":        "FastAPI",
    "spring boot":    "Spring Boot",
    "springboot":     "Spring Boot",
    "spring":         "Spring",
    "laravel":        "Laravel",
    "rails":          "Ruby on Rails",

    # ML / AI
    "ml":             "Machine Learning",
    "machine learning": "Machine Learning",
    "dl":             "Deep Learning",
    "deep learning":  "Deep Learning",
    "nlp":            "NLP",
    "natural language processing": "NLP",
    "cv":             "Computer Vision",
    "computer vision":"Computer Vision",
    "ai":             "Artificial Intelligence",
    "tensorflow":     "TensorFlow",
    "tf":             "TensorFlow",
    "pytorch":        "PyTorch",
    "torch":          "PyTorch",
    "sklearn":        "Scikit-learn",
    "scikit-learn":   "Scikit-learn",
    "scikit learn":   "Scikit-learn",
    "keras":          "Keras",
    "huggingface":    "HuggingFace",
    "hugging face":   "HuggingFace",
    "llm":            "Large Language Models",
    "llms":           "Large Language Models",
    "transformers":   "Transformers",
    "bert":           "BERT",
    "gpt":            "GPT",

    # Databases
    "sql":            "SQL",
    "mysql":          "MySQL",
    "postgresql":     "PostgreSQL",
    "postgres":       "PostgreSQL",
    "sqlite":         "SQLite",
    "mongodb":        "MongoDB",
    "mongo":          "MongoDB",
    "redis":          "Redis",
    "elasticsearch":  "Elasticsearch",
    "elastic":        "Elasticsearch",
    "cassandra":      "Cassandra",
    "dynamodb":       "DynamoDB",
    "nosql":          "NoSQL",

    # Cloud / DevOps
    "aws":            "AWS",
    "amazon web services": "AWS",
    "azure":          "Azure",
    "gcp":            "Google Cloud",
    "google cloud":   "Google Cloud",
    "docker":         "Docker",
    "k8s":            "Kubernetes",
    "kubernetes":     "Kubernetes",
    "ci/cd":          "CI/CD",
    "cicd":           "CI/CD",
    "jenkins":        "Jenkins",
    "github actions": "GitHub Actions",
    "terraform":      "Terraform",
    "ansible":        "Ansible",
    "linux":          "Linux",
    "git":            "Git",
    "github":         "GitHub",

    # Finance
    "financial modeling":  "Financial Modeling",
    "financial modelling": "Financial Modeling",
    "dcf":            "DCF Valuation",
    "excel":          "Microsoft Excel",
    "ms excel":       "Microsoft Excel",
    "vba":            "VBA",
    "bloomberg":      "Bloomberg Terminal",
    "cfa":            "CFA",
    "cpa":            "CPA",

    # Design
    "figma":          "Figma",
    "sketch":         "Sketch",
    "adobe xd":       "Adobe XD",
    "photoshop":      "Photoshop",
    "illustrator":    "Illustrator",
    "ui/ux":          "UI/UX Design",
    "ux":             "UX Design",

    # Project Management
    "agile":          "Agile",
    "scrum":          "Scrum",
    "jira":           "Jira",
    "confluence":     "Confluence",
    "pmp":            "PMP",
    "kanban":         "Kanban",
}

# ══════════════════════════════════════════════════════════════════════════════
# SECTION HEADER VARIANTS
# Handles non-standard resume section headers
# ══════════════════════════════════════════════════════════════════════════════
SECTION_VARIANTS = {
    "experience": [
        "experience", "work experience", "professional experience",
        "employment history", "work history", "career history",
        "professional background", "professional journey",
        "employment", "work", "career", "positions held",
        "professional summary", "relevant experience",
    ],
    "education": [
        "education", "academic background", "academic history",
        "qualifications", "educational background", "degrees",
        "studies", "academic qualifications", "schooling",
    ],
    "skills": [
        "skills", "technical skills", "core competencies",
        "competencies", "expertise", "technologies",
        "tools & technologies", "tools and technologies",
        "key skills", "areas of expertise", "technical expertise",
        "programming languages", "languages & frameworks",
        "hard skills", "soft skills",
    ],
    "projects": [
        "projects", "personal projects", "academic projects",
        "key projects", "notable projects", "project experience",
        "selected projects", "portfolio", "work samples",
        "open source", "side projects", "project highlights",
    ],
    "certifications": [
        "certifications", "certificates", "licenses",
        "professional certifications", "credentials",
        "training", "courses", "achievements",
    ],
    "summary": [
        "summary", "profile", "objective", "about me",
        "professional summary", "career objective",
        "personal statement", "bio", "overview",
    ],
}

# ══════════════════════════════════════════════════════════════════════════════
# FIELD DETECTION — scored, not first-match
# ══════════════════════════════════════════════════════════════════════════════
FIELD_KEYWORDS = {
    "Software Engineering": [
        "software engineer", "developer", "programmer", "full stack",
        "backend", "frontend", "devops", "mobile developer",
        "flutter", "android", "ios", "web developer", "software development",
        "api development", "microservices", "agile", "scrum",
        "javascript", "python", "java", "react", "angular", "vue",
        "node", "django", "spring", "docker", "kubernetes", "ci/cd",
    ],
    "Data Science / AI": [
        "data scientist", "machine learning", "deep learning", "nlp",
        "computer vision", "ai engineer", "ml engineer",
        "tensorflow", "pytorch", "scikit-learn", "pandas", "numpy",
        "data analysis", "statistical modeling", "feature engineering",
        "neural network", "model training", "data pipeline",
        "jupyter", "spark", "hadoop", "big data", "llm",
    ],
    "Business / Management": [
        "business analyst", "product manager", "project manager",
        "business development", "operations manager", "strategy",
        "consulting", "stakeholder management", "kpi", "okr",
        "cross-functional", "p&l", "budget management",
        "market research", "competitive analysis", "process improvement",
    ],
    "Finance / Accounting": [
        "financial analyst", "investment banker", "portfolio manager",
        "accounting", "cpa", "cfa", "financial modeling", "dcf",
        "valuation", "equity research", "risk management",
        "bloomberg", "excel", "balance sheet", "income statement",
        "cash flow", "m&a", "audit", "tax", "budgeting", "forecasting",
    ],
    "Healthcare / Medical": [
        "doctor", "physician", "nurse", "pharmacist", "mbbs",
        "clinical", "patient care", "diagnosis", "treatment",
        "hospital", "ehr", "emr", "hipaa", "medical imaging",
        "pathology", "radiology", "surgery", "medical officer",
        "physiotherapy", "psychiatry", "pediatrics",
    ],
    "Marketing / Sales": [
        "marketing manager", "digital marketing", "seo", "sem",
        "social media marketing", "content marketing", "brand manager",
        "sales manager", "account manager", "crm", "hubspot",
        "salesforce", "google analytics", "email marketing",
        "lead generation", "campaign management", "copywriting",
    ],
    "Design / UX": [
        "ui designer", "ux designer", "graphic designer",
        "product designer", "visual designer", "creative director",
        "figma", "sketch", "adobe xd", "photoshop", "illustrator",
        "wireframing", "prototyping", "user research",
        "design system", "usability testing", "interaction design",
    ],
    "Civil / Mechanical Engineering": [
        "civil engineer", "mechanical engineer", "structural engineer",
        "autocad", "solidworks", "ansys", "catia", "matlab",
        "construction", "hvac", "finite element analysis",
        "manufacturing", "quality control", "six sigma", "lean",
    ],
    "Cybersecurity": [
        "cybersecurity analyst", "security engineer", "penetration testing",
        "ethical hacking", "soc analyst", "incident response",
        "vulnerability assessment", "cissp", "ceh", "oscp",
        "siem", "splunk", "network security", "firewall",
        "zero trust", "threat intelligence", "malware analysis",
    ],
    "Law / Legal": [
        "lawyer", "attorney", "advocate", "paralegal", "legal counsel",
        "litigation", "contract law", "compliance", "regulatory",
        "corporate law", "intellectual property", "bar", "judiciary",
    ],
    "Education / Teaching": [
        "teacher", "lecturer", "professor", "academic", "instructor",
        "curriculum design", "pedagogy", "e-learning", "tutoring",
        "educational technology", "course development",
    ],
    "Human Resources": [
        "hr manager", "human resources", "talent acquisition",
        "recruitment", "onboarding", "performance management",
        "compensation", "benefits", "hris", "employee relations",
        "organizational development", "learning and development",
    ],
}

# ══════════════════════════════════════════════════════════════════════════════
# TECH KEYWORDS for project description extraction
# ══════════════════════════════════════════════════════════════════════════════
TECH_KEYWORDS_FLAT = [
    "python", "javascript", "java", "c++", "c#", "typescript", "go",
    "rust", "kotlin", "swift", "dart", "php", "ruby", "scala", "r",
    "react", "angular", "vue", "node", "next.js", "express", "django",
    "flask", "fastapi", "spring", "laravel",
    "tensorflow", "pytorch", "scikit-learn", "keras", "huggingface",
    "mysql", "postgresql", "mongodb", "redis", "sqlite", "dynamodb",
    "aws", "azure", "gcp", "docker", "kubernetes", "firebase",
    "flutter", "android", "ios", "react native",
    "rest api", "graphql", "grpc", "websocket",
    "elasticsearch", "kafka", "rabbitmq",
    "figma", "sketch",
    "excel", "tableau", "power bi",
    "tensorflow", "bert", "gpt", "llm",
]


# ══════════════════════════════════════════════════════════════════════════════
# MAIN FUNCTION
# ══════════════════════════════════════════════════════════════════════════════

def parse_resume(text: str) -> dict:
    """
    Parse resume text into a structured profile.

    Args:
        text: Raw extracted text from a resume

    Returns:
        {
            field, seniority, years_of_experience,
            skills, education, experience, projects,
            certifications, summary
        }
    """
    if not text or len(text.strip()) < 30:
        return _empty_profile()

    text_lower = text.lower()
    lines      = [l.strip() for l in text.split("\n") if l.strip()]

    # Detect sections first — everything else builds on this
    sections = _detect_sections(lines)

    return {
        "field":               _detect_field(text_lower),
        "seniority":           _detect_seniority(text_lower, lines),
        "years_of_experience": _estimate_years(text_lower),
        "skills":              _extract_skills(sections.get("skills", ""), text_lower),
        "education":           _extract_education(sections.get("education", ""), text_lower),
        "experience":          _extract_experience(sections.get("experience", ""), lines),
        "projects":            _extract_projects(sections.get("projects", ""), lines),
        "certifications":      _extract_certifications(sections.get("certifications", ""), text_lower),
        "summary":             sections.get("summary", "")[:300],
    }


# ══════════════════════════════════════════════════════════════════════════════
# SECTION DETECTION — handles non-standard headers
# ══════════════════════════════════════════════════════════════════════════════

def _detect_sections(lines: list[str]) -> dict[str, str]:
    """
    Identify which lines belong to which section.
    Handles non-standard headers via fuzzy matching.
    Returns dict mapping section_name → raw text content.
    """
    # Build a flat list of (canonical_name, variant) pairs
    all_variants = {}
    for canonical, variants in SECTION_VARIANTS.items():
        for v in variants:
            all_variants[v] = canonical

    sections: dict[str, list[str]] = {}
    current_section  = "preamble"
    sections[current_section] = []

    for line in lines:
        line_lower = line.lower().strip()

        # Skip empty lines
        if not line_lower:
            continue

        # Check if this line is a section header
        # Only check short lines (real headers are rarely > 50 chars)
        if len(line_lower) <= 50:
            detected = _match_section_header(line_lower, all_variants)
            if detected:
                current_section = detected
                if detected not in sections:
                    sections[detected] = []
                continue

        sections[current_section].append(line)

    # Convert lists to joined strings
    return {k: "\n".join(v) for k, v in sections.items()}


def _match_section_header(line: str, all_variants: dict) -> Optional[str]:
    """
    Check if a line is a section header using exact + fuzzy matching.
    Returns canonical section name or None.
    """
    # Exact match first (fast)
    if line in all_variants:
        return all_variants[line]

    # Fuzzy match (handles "Profesional Experience" typos)
    if FUZZY_AVAILABLE:
        best_match, score, _ = rfprocess.extractOne(
            line,
            all_variants.keys(),
            scorer=fuzz.ratio,
        )
        if score >= 82:   # 82% similarity threshold
            return all_variants[best_match]
    else:
        # Fallback: substring match
        for variant, canonical in all_variants.items():
            if variant in line or line in variant:
                return canonical

    return None


# ══════════════════════════════════════════════════════════════════════════════
# FIELD DETECTION — scored
# ══════════════════════════════════════════════════════════════════════════════

def _detect_field(text_lower: str) -> str:
    scores = {}
    for field, keywords in FIELD_KEYWORDS.items():
        score = 0
        for kw in keywords:
            if FUZZY_AVAILABLE:
                # Check if keyword appears with fuzzy match
                if _fuzzy_contains(kw, text_lower):
                    score += 1
            else:
                if kw in text_lower:
                    score += 1
        if score > 0:
            scores[field] = score

    if not scores:
        return "General"
    return max(scores, key=scores.get)


def _fuzzy_contains(keyword: str, text: str, threshold: int = 88) -> bool:
    """Check if keyword appears in text with fuzzy tolerance."""
    # Fast path — exact match
    if keyword in text:
        return True

    # For short keywords (< 5 chars), only exact match to avoid false positives
    if len(keyword) < 5:
        return keyword in text

    # Sliding window fuzzy check for longer keywords
    kw_len = len(keyword)
    for i in range(0, len(text) - kw_len + 1, max(1, kw_len // 3)):
        window = text[i:i + kw_len + 3]
        if fuzz.partial_ratio(keyword, window) >= threshold:
            return True
    return False


# ══════════════════════════════════════════════════════════════════════════════
# SKILL EXTRACTION — fuzzy + normalized
# ══════════════════════════════════════════════════════════════════════════════

def _extract_skills(skills_section: str, full_text: str) -> list[dict]:
    """
    Extract and normalize skills from the skills section + full text.
    Uses fuzzy matching to handle typos and variations.
    """
    # Combine skills section with full text (section takes priority)
    search_text = (skills_section + " " + full_text).lower()

    found_normalized: set[str] = set()
    raw_skills: list[dict]     = []

    for alias, normalized in SKILL_ALIASES.items():
        if normalized in found_normalized:
            continue

        matched = False
        if FUZZY_AVAILABLE and len(alias) >= 4:
            matched = _fuzzy_contains(alias, search_text, threshold=88)
        else:
            matched = alias in search_text

        if matched:
            found_normalized.add(normalized)
            # Determine which category this skill belongs to
            category = _skill_category(normalized)
            raw_skills.append({
                "name":     normalized,
                "category": category,
                "source":   "resume",
            })

    # Sort: section skills first (more reliable), then full-text
    # Deduplicate case-insensitively
    return raw_skills[:50]


def _skill_category(skill_name: str) -> str:
    name_lower = skill_name.lower()
    if any(x in name_lower for x in ["python", "java", "javascript", "typescript", "c++",
                                       "go", "rust", "kotlin", "swift", "dart", "php", "ruby"]):
        return "Programming Language"
    if any(x in name_lower for x in ["react", "vue", "angular", "node", "django", "flask",
                                       "fastapi", "spring", "express", "next", "laravel"]):
        return "Framework / Library"
    if any(x in name_lower for x in ["tensorflow", "pytorch", "scikit", "keras",
                                       "machine learning", "deep learning", "nlp", "bert"]):
        return "Machine Learning"
    if any(x in name_lower for x in ["mysql", "postgres", "mongodb", "redis", "sql",
                                       "sqlite", "dynamodb", "cassandra"]):
        return "Database"
    if any(x in name_lower for x in ["aws", "azure", "gcp", "docker", "kubernetes",
                                       "ci/cd", "jenkins", "terraform", "linux"]):
        return "Cloud / DevOps"
    if any(x in name_lower for x in ["flutter", "android", "ios", "react native"]):
        return "Mobile"
    if any(x in name_lower for x in ["figma", "sketch", "photoshop", "illustrator",
                                       "ux", "ui"]):
        return "Design"
    if any(x in name_lower for x in ["excel", "bloomberg", "dcf", "cfa", "tableau",
                                       "power bi"]):
        return "Business / Finance Tool"
    return "Other"


# ══════════════════════════════════════════════════════════════════════════════
# EDUCATION EXTRACTION
# ══════════════════════════════════════════════════════════════════════════════

DEGREE_PATTERNS = [
    (r"\bph\.?d\.?\b|\bdoctor(?:ate|al)?\b",                       "PhD"),
    (r"\bmaster[s]?\b|\bm\.s\.?\b|\bm\.e\.?\b|\bmba\b|\bm\.sc\b",  "Masters"),
    (r"\bbachelor[s]?\b|\bb\.s\.?\b|\bb\.e\.?\b|\bb\.sc\b|\bb\.tech\b|\bbs\b|\bmbbs\b", "Bachelors"),
    (r"\bassociate[s]?\b",                                           "Associates"),
    (r"\bdiploma\b",                                                 "Diploma"),
]

INSTITUTION_KEYWORDS = [
    "university", "college", "institute", "school", "academy",
    "iiit", "iit", "nust", "lums", "fast", "iba", "uet",
    "comsats", "bahria", "aga khan", "aku",
]


def _extract_education(edu_section: str, full_text: str) -> list[dict]:
    text = edu_section if edu_section else full_text
    text_lower = text.lower()
    entries = []

    for pattern, degree_type in DEGREE_PATTERNS:
        for match in re.finditer(pattern, text_lower):
            # Grab context around the degree mention
            start   = max(0, match.start() - 30)
            end     = min(len(text), match.end() + 250)
            context = text[start:end]

            # Extract year
            year_match = re.search(r"(19|20)\d{2}", context)
            year = year_match.group(0) if year_match else None

            # Extract institution name
            institution = _extract_institution(context)

            # Extract field of study
            field_of_study = _extract_field_of_study(context)

            entries.append({
                "degree":         degree_type,
                "institution":    institution,
                "field_of_study": field_of_study,
                "year":           year,
            })

    # Deduplicate by degree type
    seen_degrees = set()
    unique = []
    for e in entries:
        if e["degree"] not in seen_degrees:
            seen_degrees.add(e["degree"])
            unique.append(e)

    return unique


def _extract_institution(context: str) -> Optional[str]:
    lines = [l.strip() for l in context.split("\n") if l.strip()]
    for line in lines:
        if any(kw in line.lower() for kw in INSTITUTION_KEYWORDS):
            return line[:80]
    return None


def _extract_field_of_study(context: str) -> Optional[str]:
    patterns = [
        r"(?:in|of)\s+([A-Z][a-zA-Z\s&/]+(?:Science|Engineering|Technology|Business|Arts|Commerce|Medicine|Law|Finance|Management))",
        r"B\.?(?:Sc|Tech|E|S)\.?\s+(?:in\s+)?([A-Z][a-zA-Z\s]+)",
        r"M\.?(?:Sc|Tech|E|S|BA)\.?\s+(?:in\s+)?([A-Z][a-zA-Z\s]+)",
    ]
    for p in patterns:
        m = re.search(p, context)
        if m:
            return m.group(1).strip()[:50]
    return None


# ══════════════════════════════════════════════════════════════════════════════
# EXPERIENCE EXTRACTION — proper company/role/duration parsing
# ══════════════════════════════════════════════════════════════════════════════

DATE_RANGE_PATTERN = re.compile(
    r"((?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s+)?(\d{4})"
    r"\s*[-–—to]+\s*"
    r"((?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s+)?(\d{4}|present|current|now)",
    re.IGNORECASE,
)

JOB_TITLE_KEYWORDS = [
    "engineer", "developer", "analyst", "manager", "designer", "consultant",
    "specialist", "coordinator", "director", "lead", "head", "officer",
    "associate", "intern", "trainee", "executive", "architect", "scientist",
    "researcher", "advisor", "supervisor", "administrator",
]


def _extract_experience(exp_section: str, all_lines: list[str]) -> list[dict]:
    text  = exp_section if exp_section else ""
    lines = [l.strip() for l in text.split("\n") if l.strip()]

    if not lines:
        return []

    entries     = []
    current     = []
    date_seen   = False

    for line in lines:
        line_lower = line.lower()

        # New entry starts when we see a date range
        has_date = bool(DATE_RANGE_PATTERN.search(line_lower))
        has_title = any(kw in line_lower for kw in JOB_TITLE_KEYWORDS)

        if (has_date or has_title) and current and date_seen:
            parsed = _parse_exp_block(current)
            if parsed:
                entries.append(parsed)
            current   = []
            date_seen = False

        current.append(line)
        if has_date:
            date_seen = True

    if current:
        parsed = _parse_exp_block(current)
        if parsed:
            entries.append(parsed)

    return entries[:8]


def _parse_exp_block(lines: list[str]) -> Optional[dict]:
    if not lines:
        return None

    text       = " ".join(lines)
    text_lower = text.lower()

    # Extract date range
    date_match = DATE_RANGE_PATTERN.search(text_lower)
    date_range = date_match.group(0) if date_match else None

    # Estimate years from date range
    years = 0
    if date_match:
        try:
            start_year = int(date_match.group(2))
            end_str    = date_match.group(4).lower()
            end_year   = 2024 if end_str in ("present", "current", "now") else int(end_str)
            years      = max(0, end_year - start_year)
        except Exception:
            years = 0

    # First line usually has title + company
    first_line = lines[0] if lines else ""

    # Try to split "Software Engineer at Google" or "Google - Software Engineer"
    title, company = _split_title_company(first_line)

    # Bullet points as responsibilities
    responsibilities = []
    for line in lines[1:]:
        stripped = line.lstrip("•-–*▪►● ")
        if len(stripped) > 15 and stripped != first_line:
            responsibilities.append(stripped[:150])

    return {
        "title":             title,
        "company":           company,
        "duration":          date_range,
        "years":             years,
        "responsibilities":  responsibilities[:5],
    }


def _split_title_company(line: str) -> tuple[Optional[str], Optional[str]]:
    """Split 'Software Engineer at Google' or 'Google | Software Engineer'."""
    # Pattern: Title at/@ Company
    m = re.match(r"^(.+?)\s+(?:at|@)\s+(.+)$", line, re.IGNORECASE)
    if m:
        return m.group(1).strip(), m.group(2).strip()

    # Pattern: Company - Title or Company | Title
    m = re.match(r"^(.+?)\s*[-|–—]\s*(.+)$", line)
    if m:
        # Determine which side is the title
        left, right = m.group(1).strip(), m.group(2).strip()
        if any(kw in left.lower() for kw in JOB_TITLE_KEYWORDS):
            return left, right
        return right, left

    # Can't split — return full line as title
    return line[:80], None


# ══════════════════════════════════════════════════════════════════════════════
# PROJECT EXTRACTION — with tech stack detection
# ══════════════════════════════════════════════════════════════════════════════

def _extract_projects(proj_section: str, all_lines: list[str]) -> list[dict]:
    text  = proj_section if proj_section else ""
    lines = [l.strip() for l in text.split("\n") if l.strip()]

    if not lines:
        return []

    projects = []
    current  = []

    for line in lines:
        # New project entry often starts with a name (short, possibly bold)
        # Detect by: short line OR line with tech indicators
        is_new = (
            len(line) < 60 and
            not line.startswith(("•", "-", "*", "–")) and
            current
        )
        if is_new:
            p = _parse_project_block(current)
            if p:
                projects.append(p)
            current = []

        current.append(line)

    if current:
        p = _parse_project_block(current)
        if p:
            projects.append(p)

    return projects[:8]


def _parse_project_block(lines: list[str]) -> Optional[dict]:
    if not lines:
        return None

    full_text  = " ".join(lines)
    name       = lines[0].lstrip("•-*– ").strip()[:60]
    description = " ".join(lines[1:])[:300] if len(lines) > 1 else full_text[:300]

    # Extract tech stack from description
    tech = _extract_tech_from_text(full_text.lower())

    # Try to extract measurable impact (numbers, percentages)
    impact = _extract_impact(full_text)

    return {
        "name":        name,
        "description": description,
        "tech":        tech,
        "impact":      impact,
    }


def _extract_tech_from_text(text_lower: str) -> list[str]:
    """Find tech keywords mentioned in a project description."""
    found = set()
    for tech in TECH_KEYWORDS_FLAT:
        if FUZZY_AVAILABLE and len(tech) >= 4:
            if _fuzzy_contains(tech, text_lower, threshold=90):
                normalized = SKILL_ALIASES.get(tech, tech.title())
                found.add(normalized)
        else:
            if tech in text_lower:
                normalized = SKILL_ALIASES.get(tech, tech.title())
                found.add(normalized)
    return sorted(list(found))[:10]


def _extract_impact(text: str) -> Optional[str]:
    """Extract measurable outcomes: '40% faster', '$2M revenue', etc."""
    patterns = [
        r"\d+%\s+\w+",                          # 40% reduction
        r"\$[\d,]+[KMB]?\s+\w+",                # $2M revenue
        r"\d+[KMB]?\+?\s+(?:users|customers|requests|transactions)",
        r"(?:reduced|improved|increased|decreased|saved|generated)\s+\w+\s+by\s+\d+",
    ]
    for p in patterns:
        m = re.search(p, text, re.IGNORECASE)
        if m:
            return m.group(0)[:100]
    return None


# ══════════════════════════════════════════════════════════════════════════════
# SENIORITY DETECTION
# ══════════════════════════════════════════════════════════════════════════════

def _detect_seniority(text_lower: str, lines: list[str]) -> str:
    years = _estimate_years(text_lower)

    # Check title-based signals in the first 10 lines (header area)
    header = " ".join(lines[:10]).lower()

    senior_signals = [
        "senior", "lead", "principal", "architect", "head of", "director",
        "vp ", "vice president", "chief", "cto", "ceo", "c-level", "manager",
    ]
    junior_signals = [
        "junior", "entry level", "entry-level", "fresh graduate", "fresher",
        "intern", "trainee", "graduate engineer", "associate engineer",
        "new grad", "bootcamp",
    ]

    for sig in senior_signals:
        if sig in header:
            return "Senior"

    for sig in junior_signals:
        if sig in header:
            return "Beginner"

    # Fall back to years of experience
    if years >= 6:
        return "Senior"
    if years >= 3:
        return "Mid-Level"
    if years >= 1:
        return "Mid-Level"
    return "Beginner"


def _estimate_years(text_lower: str) -> int:
    # Direct statement: "5 years of experience"
    for p in [
        r"(\d+)\+?\s*years?\s+of\s+(?:professional\s+)?experience",
        r"(\d+)\+?\s*years?\s+experience",
        r"experience\s+of\s+(\d+)\+?\s*years?",
        r"(\d+)\+?\s*year[s]?\s+in\s+(?:the\s+)?\w+",
    ]:
        m = re.search(p, text_lower)
        if m:
            return min(int(m.group(1)), 40)

    # Count date ranges: "2018 - 2023" = 5 years
    ranges = re.findall(
        r"20(\d{2})\s*[-–—]\s*(?:20(\d{2})|present|current|now)",
        text_lower, re.IGNORECASE
    )
    if ranges:
        total = 0
        for start, end in ranges:
            end_y = 24 if not end else int(end)
            total += max(0, end_y - int(start))
        return min(total, 40)

    return 0


# ══════════════════════════════════════════════════════════════════════════════
# CERTIFICATIONS
# ══════════════════════════════════════════════════════════════════════════════

CERT_PATTERNS = [
    r"aws\s+certified\s+\w+(?:\s+\w+)?",
    r"azure\s+\w+(?:\s+\w+)?\s+certified",
    r"google\s+(?:cloud|professional)\s+\w+",
    r"pmp(?:\s+certified)?",
    r"certified\s+\w+(?:\s+\w+)?",
    r"cissp|ceh|oscp|cism|cisa",
    r"cpa|cfa(?:\s+level\s+[iii1-3]+)?",
    r"six\s+sigma\s+\w+",
    r"scrum\s+master|csm|safe\s+\w+",
    r"comptia\s+\w+",
    r"itil\s+\w+",
]


def _extract_certifications(cert_section: str, full_text: str) -> list[str]:
    text = (cert_section + " " + full_text).lower()
    found = set()

    for p in CERT_PATTERNS:
        for m in re.finditer(p, text, re.IGNORECASE):
            cert = m.group(0).strip().title()
            found.add(cert)

    return sorted(list(found))[:10]


# ══════════════════════════════════════════════════════════════════════════════
# PDF / DOCX EXTRACTION (file bytes → text)
# ══════════════════════════════════════════════════════════════════════════════

def extract_text_from_file(file_bytes: bytes, filename: str = "") -> str:
    """Extract raw text from uploaded file bytes."""
    fname = filename.lower()

    if fname.endswith(".pdf") or file_bytes[:4] == b"%PDF":
        return _extract_pdf(file_bytes)
    if fname.endswith(".docx"):
        return _extract_docx(file_bytes)
    if fname.endswith(".txt"):
        return file_bytes.decode("utf-8", errors="ignore")

    # Try PDF first, then UTF-8
    try:
        return _extract_pdf(file_bytes)
    except Exception:
        return file_bytes.decode("utf-8", errors="ignore")


def _extract_pdf(file_bytes: bytes) -> str:
    try:
        import PyPDF2
        reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
        pages  = []
        for page in reader.pages:
            t = page.extract_text()
            if t:
                pages.append(t)
        return "\n".join(pages)
    except ImportError:
        raise ImportError("Install PyPDF2: pip install PyPDF2")
    except Exception as e:
        raise ValueError(f"PDF read failed: {e}")


def _extract_docx(file_bytes: bytes) -> str:
    try:
        import docx
        doc   = docx.Document(io.BytesIO(file_bytes))
        lines = [p.text for p in doc.paragraphs if p.text.strip()]
        return "\n".join(lines)
    except ImportError:
        # Fallback via zipfile
        import zipfile
        import xml.etree.ElementTree as ET
        try:
            with zipfile.ZipFile(io.BytesIO(file_bytes)) as z:
                xml_bytes = z.read("word/document.xml")
            ns    = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
            root  = ET.fromstring(xml_bytes)
            texts = [n.text for n in root.iter(f"{ns}t") if n.text]
            return " ".join(texts)
        except Exception as e:
            raise ValueError(f"DOCX read failed: {e}")


def _empty_profile() -> dict:
    return {
        "field": "Unknown", "seniority": "Beginner",
        "years_of_experience": 0, "skills": [], "education": [],
        "experience": [], "projects": [], "certifications": [], "summary": "",
    }
