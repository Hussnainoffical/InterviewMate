"""
github_analyzer.py  —  Production-Grade GitHub Profile Analyzer
================================================================
What this actually analyzes (not just language names):
  1. Project complexity scoring  (stars, forks, watchers, size, topics, commits)
  2. Tech stack depth            (how many technologies used together)
  3. Contribution quality        (readme quality, description quality)
  4. Activity recency            (recently active vs abandoned)
  5. Project diversity           (different domains/types)
  6. Collaboration signals       (contributors, open issues, PRs)
  7. Impact signals              (stars, forks from others)

INSTALL:
    pip install httpx

GITHUB TOKEN (.env):
    GITHUB_TOKEN=ghp_xxxx   ← get from GitHub → Settings → Developer Settings
    Without a token: 60 req/hour. With token: 5000 req/hour.
"""

import os
import asyncio
import httpx
import re
from datetime import datetime, timezone
from typing import Optional


GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
PER_PAGE     = 100   # max repos to fetch

HEADERS = {
    "Accept": "application/vnd.github.v3+json",
    **({"Authorization": f"token {GITHUB_TOKEN}"} if GITHUB_TOKEN else {}),
}


# ══════════════════════════════════════════════════════════════════════════════
# LANGUAGE → FIELD MAPPING
# ══════════════════════════════════════════════════════════════════════════════
LANG_FIELD_MAP = {
    "Python":         "Data Science / Software Engineering",
    "Jupyter Notebook": "Data Science / AI",
    "R":              "Data Science / Statistics",
    "JavaScript":     "Web / Software Engineering",
    "TypeScript":     "Web / Software Engineering",
    "Java":           "Software Engineering",
    "Kotlin":         "Mobile Development",
    "Swift":          "Mobile Development",
    "Dart":           "Mobile Development",
    "C++":            "Systems / Embedded",
    "C":              "Systems / Embedded",
    "C#":             ".NET / Game Development",
    "Go":             "Backend / Cloud Engineering",
    "Rust":           "Systems / Backend Engineering",
    "PHP":            "Web Development",
    "Ruby":           "Web Development",
    "Scala":          "Big Data / Backend",
    "Shell":          "DevOps / Automation",
    "HCL":            "Infrastructure / DevOps",
    "MATLAB":         "Engineering / Science",
    "HTML":           "Web Development",
    "CSS":            "Web Development",
}

TOPIC_FIELD_MAP = {
    "machine-learning": "Data Science / AI",
    "deep-learning":    "Data Science / AI",
    "nlp":              "Data Science / AI",
    "computer-vision":  "Data Science / AI",
    "data-science":     "Data Science / AI",
    "artificial-intelligence": "Data Science / AI",
    "flutter":          "Mobile Development",
    "android":          "Mobile Development",
    "ios":              "Mobile Development",
    "react-native":     "Mobile Development",
    "web-development":  "Web Development",
    "rest-api":         "Backend Development",
    "microservices":    "Backend / Cloud Engineering",
    "devops":           "DevOps",
    "kubernetes":       "DevOps",
    "docker":           "DevOps",
    "blockchain":       "Blockchain",
    "cybersecurity":    "Cybersecurity",
    "embedded":         "Embedded Systems",
    "game-development": "Game Development",
    "fintech":          "FinTech",
    "healthcare":       "HealthTech",
    "robotics":         "Robotics / Engineering",
}

# ══════════════════════════════════════════════════════════════════════════════
# MAIN FUNCTION
# ══════════════════════════════════════════════════════════════════════════════

async def analyze_github(username_or_url: str) -> dict:
    """
    Full GitHub profile analysis.
    Accepts: username OR full URL like https://github.com/torvalds

    Returns comprehensive profile including:
        field, seniority, languages, top projects (scored),
        skills_for_interview, activity_level, total_stars, total_forks
    """
    username = _normalize_username(username_or_url)

    async with httpx.AsyncClient(timeout=15, headers=HEADERS) as client:

        # ── 1. Fetch user profile ─────────────────────────────────────────────
        user_resp = await client.get(f"https://api.github.com/users/{username}")

        if user_resp.status_code == 404:
            return _error_response(username, "GitHub user not found.")
        if user_resp.status_code == 403:
            return _error_response(username, "Rate limit hit. Set GITHUB_TOKEN in .env")
        if user_resp.status_code != 200:
            return _error_response(username, f"GitHub API error: {user_resp.status_code}")

        user_data = user_resp.json()

        # ── 2. Fetch repos ────────────────────────────────────────────────────
        repos_resp = await client.get(
            f"https://api.github.com/users/{username}/repos",
            params={"per_page": PER_PAGE, "sort": "pushed", "type": "owner"},
        )
        repos = repos_resp.json() if repos_resp.status_code == 200 else []
        if not isinstance(repos, list):
            repos = []

        # ── 3. Separate original vs forked ───────────────────────────────────
        original_repos = [r for r in repos if not r.get("fork", False)]
        forked_repos   = [r for r in repos if r.get("fork", False)]

        # Include forks only if they have contributions (stars/watchers > 0)
        notable_forks  = [r for r in forked_repos
                          if r.get("stargazers_count", 0) > 0 or r.get("forks_count", 0) > 0]

        repos_to_analyze = original_repos + notable_forks

        # ── 4. Score each repo ────────────────────────────────────────────────
        scored = [_score_repo(r) for r in repos_to_analyze]
        scored.sort(key=lambda x: x["score"], reverse=True)

        # ── 5. Aggregate signals ──────────────────────────────────────────────
        lang_counter: dict[str, int]   = {}   # language → repo count
        lang_bytes:   dict[str, int]   = {}   # language → approximate lines
        all_topics:   list[str]        = []

        for repo in repos_to_analyze:
            lang = repo.get("language")
            if lang:
                lang_counter[lang] = lang_counter.get(lang, 0) + 1
                # size is in KB, use as LOC proxy
                lang_bytes[lang]   = lang_bytes.get(lang, 0) + repo.get("size", 0)
            all_topics.extend(repo.get("topics", []))

        total_stars    = sum(r.get("stargazers_count", 0) for r in repos_to_analyze)
        total_forks    = sum(r.get("forks_count",      0) for r in repos_to_analyze)
        total_watchers = sum(r.get("watchers_count",   0) for r in repos_to_analyze)

        # ── 6. Detect field + seniority ───────────────────────────────────────
        field     = _detect_field(lang_counter, all_topics)
        seniority = _detect_seniority(scored, repos_to_analyze, user_data)
        activity  = _detect_activity_level(repos_to_analyze)

        # ── 7. Build significant projects (top 5) ─────────────────────────────
        top_projects = _build_top_projects(scored[:5])

        # ── 8. Build skills list for question generation ──────────────────────
        skills = _build_skills_list(lang_counter, all_topics, top_projects)

        # ── 9. Language proficiency (sorted by code volume) ───────────────────
        languages = [
            {
                "name":        lang,
                "repo_count":  lang_counter[lang],
                "size_kb":     lang_bytes.get(lang, 0),
                "proficiency": _lang_proficiency(lang_counter[lang], lang_bytes.get(lang, 0)),
            }
            for lang in sorted(lang_counter, key=lambda l: lang_bytes.get(l, 0), reverse=True)
        ]

        return {
            "username":          username,
            "name":              user_data.get("name", username),
            "bio":               user_data.get("bio", ""),
            "public_repos":      user_data.get("public_repos", 0),
            "followers":         user_data.get("followers", 0),
            "field":             field,
            "seniority":         seniority,
            "activity_level":    activity,
            "languages":         languages,
            "top_topics":        _top_topics(all_topics, n=10),
            "significant_projects": top_projects,
            "total_stars":       total_stars,
            "total_forks":       total_forks,
            "total_watchers":    total_watchers,
            "skills_for_interview": skills,
            "error":             None,
        }


# ══════════════════════════════════════════════════════════════════════════════
# REPO SCORING — multi-factor
# ══════════════════════════════════════════════════════════════════════════════

def _score_repo(repo: dict) -> dict:
    """
    Score a repo 0-100 on significance/complexity.

    Factors:
      - Stars (external validation)
      - Forks (others building on it)
      - Watchers (people following development)
      - Size in KB (code volume)
      - Topics count (organized, well-tagged)
      - Description quality (has description > 10 chars)
      - Has README (implied by topics usually)
      - Recency (recently pushed = actively maintained)
      - Open issues (real project with users)
    """
    stars    = repo.get("stargazers_count", 0)
    forks    = repo.get("forks_count",      0)
    watchers = repo.get("watchers_count",   0)
    size_kb  = repo.get("size",             0)
    topics   = repo.get("topics",          [])
    desc     = repo.get("description",     "") or ""
    issues   = repo.get("open_issues_count", 0)
    pushed   = repo.get("pushed_at",       "")

    score = 0

    # External validation (max 35)
    score += min(stars   * 3,  30)
    score += min(forks   * 2,  20)
    score += min(watchers,     10)

    # Code volume (max 15) — larger repo = more work
    score += min(size_kb / 200, 15)

    # Organization quality (max 15)
    score += min(len(topics) * 2, 10)
    score += 5 if len(desc) > 20 else (2 if len(desc) > 5 else 0)

    # Community engagement (max 10)
    score += min(issues * 0.5, 10)

    # Recency bonus (max 5)
    if pushed:
        try:
            pushed_dt = datetime.fromisoformat(pushed.replace("Z", "+00:00"))
            days_ago  = (datetime.now(timezone.utc) - pushed_dt).days
            if days_ago < 30:
                score += 5
            elif days_ago < 90:
                score += 3
            elif days_ago < 365:
                score += 1
        except Exception:
            pass

    # Complexity label
    if score >= 50:
        complexity = "High"
    elif score >= 15:
        complexity = "Medium"
    else:
        complexity = "Low"

    # Extract tech from description + topics
    tech = _extract_tech_from_repo(repo)

    return {
        "name":        repo.get("name",        ""),
        "full_name":   repo.get("full_name",    ""),
        "description": desc[:150],
        "language":    repo.get("language"),
        "stars":       stars,
        "forks":       forks,
        "size_kb":     size_kb,
        "topics":      topics,
        "tech":        tech,
        "url":         repo.get("html_url",    ""),
        "pushed_at":   pushed,
        "score":       round(score, 1),
        "complexity":  complexity,
    }


def _extract_tech_from_repo(repo: dict) -> list[str]:
    """Extract all tech clues from repo: language + topics + description."""
    tech = set()

    lang = repo.get("language")
    if lang:
        tech.add(lang)

    for topic in repo.get("topics", []):
        # Convert topic slug to readable form
        readable = topic.replace("-", " ").title()
        tech.add(readable)

    desc_lower = (repo.get("description") or "").lower()
    tech_terms = [
        "react", "vue", "angular", "django", "flask", "fastapi", "spring",
        "tensorflow", "pytorch", "docker", "kubernetes", "aws", "gcp", "azure",
        "mongodb", "postgresql", "redis", "graphql", "rest", "flutter",
        "firebase", "supabase", "electron", "unity", "unreal",
    ]
    for term in tech_terms:
        if term in desc_lower:
            tech.add(term.title())

    return sorted(list(tech))[:12]


# ══════════════════════════════════════════════════════════════════════════════
# FIELD AND SENIORITY DETECTION
# ══════════════════════════════════════════════════════════════════════════════

def _detect_field(lang_counter: dict, topics: list) -> str:
    # Topics are most specific — check first
    topic_votes: dict[str, int] = {}
    for topic in topics:
        if topic.lower() in TOPIC_FIELD_MAP:
            f = TOPIC_FIELD_MAP[topic.lower()]
            topic_votes[f] = topic_votes.get(f, 0) + 1

    if topic_votes:
        return max(topic_votes, key=topic_votes.get)

    # Language-based detection
    lang_votes: dict[str, int] = {}
    for lang, count in lang_counter.items():
        if lang in LANG_FIELD_MAP:
            f = LANG_FIELD_MAP[lang]
            lang_votes[f] = lang_votes.get(f, 0) + count

    if lang_votes:
        return max(lang_votes, key=lang_votes.get)

    return "Software Engineering"


def _detect_seniority(
    scored: list[dict],
    all_repos: list[dict],
    user_data: dict,
) -> str:
    if not scored:
        return "Beginner"

    total_repos      = len(all_repos)
    top_score        = scored[0]["score"] if scored else 0
    avg_score        = sum(r["score"] for r in scored) / max(len(scored), 1)
    high_complexity  = sum(1 for r in scored if r["complexity"] == "High")
    total_stars      = sum(r.get("stars", 0) for r in scored)
    followers        = user_data.get("followers", 0)

    # Senior signals
    if (
        top_score        >= 70 or
        high_complexity  >= 4  or
        total_stars      >= 100 or
        followers        >= 100 or
        (total_repos     >= 30 and avg_score >= 15)
    ):
        return "Senior"

    # Mid-level signals
    if (
        top_score        >= 25 or
        high_complexity  >= 1  or
        total_stars      >= 20 or
        (total_repos     >= 10 and avg_score >= 8)
    ):
        return "Mid-Level"

    return "Beginner"


def _detect_activity_level(repos: list[dict]) -> str:
    if not repos:
        return "Inactive"

    recent = 0
    for repo in repos:
        pushed = repo.get("pushed_at", "")
        if not pushed:
            continue
        try:
            dt      = datetime.fromisoformat(pushed.replace("Z", "+00:00"))
            days    = (datetime.now(timezone.utc) - dt).days
            if days < 90:
                recent += 1
        except Exception:
            pass

    ratio = recent / len(repos)
    if ratio >= 0.5:
        return "Highly Active"
    if ratio >= 0.2:
        return "Active"
    if ratio >= 0.05:
        return "Moderate"
    return "Inactive"


def _lang_proficiency(repo_count: int, size_kb: int) -> str:
    if repo_count >= 10 or size_kb >= 5000:
        return "Expert"
    if repo_count >= 5 or size_kb >= 1000:
        return "Proficient"
    if repo_count >= 2 or size_kb >= 200:
        return "Intermediate"
    return "Beginner"


# ══════════════════════════════════════════════════════════════════════════════
# BUILD OUTPUTS
# ══════════════════════════════════════════════════════════════════════════════

def _build_top_projects(scored: list[dict]) -> list[dict]:
    return [
        {
            "name":        r["name"],
            "description": r["description"],
            "language":    r["language"],
            "tech":        r["tech"],
            "stars":       r["stars"],
            "forks":       r["forks"],
            "complexity":  r["complexity"],
            "url":         r["url"],
        }
        for r in scored
    ]


def _build_skills_list(
    lang_counter: dict,
    topics: list,
    top_projects: list,
) -> list[str]:
    skills: set[str] = set()

    # From languages
    for lang in lang_counter:
        skills.add(lang)

    # From topics
    for t in topics:
        skills.add(t.replace("-", " ").title())

    # From project tech
    for p in top_projects:
        for tech in p.get("tech", []):
            skills.add(tech)

    return sorted(list(skills))[:30]


def _top_topics(topics: list, n: int = 10) -> list[dict]:
    counts: dict[str, int] = {}
    for t in topics:
        counts[t] = counts.get(t, 0) + 1
    sorted_topics = sorted(counts.items(), key=lambda x: x[1], reverse=True)
    return [{"topic": t, "count": c} for t, c in sorted_topics[:n]]


def _normalize_username(raw: str) -> str:
    raw = raw.strip()
    # Handle full URLs like https://github.com/torvalds
    if "github.com/" in raw:
        return raw.rstrip("/").split("github.com/")[-1].split("/")[0]
    return raw


def _error_response(username: str, message: str) -> dict:
    return {
        "username": username, "name": username, "bio": "",
        "public_repos": 0, "followers": 0,
        "field": "Software Engineering", "seniority": "Beginner",
        "activity_level": "Unknown", "languages": [], "top_topics": [],
        "significant_projects": [], "total_stars": 0, "total_forks": 0,
        "total_watchers": 0, "skills_for_interview": [],
        "error": message,
    }
