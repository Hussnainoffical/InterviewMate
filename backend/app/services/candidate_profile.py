def parse_resume_file(file_bytes: bytes, filename: str) -> dict:
    try:
        from app.services.resume_parser import extract_text_from_file, parse_resume

        text = extract_text_from_file(file_bytes, filename)
        profile = parse_resume(text)
        profile["raw_text_length"] = len(text or "")
        return profile
    except Exception as exc:
        return {
            "field": "General",
            "seniority": "Beginner",
            "years_of_experience": 0,
            "skills": [],
            "education": [],
            "experience": [],
            "projects": [],
            "certifications": [],
            "summary": "",
            "error": str(exc),
        }


async def analyze_github_profile(username_or_url: str) -> dict:
    try:
        from app.services.github_analyzer import analyze_github

        return await analyze_github(username_or_url)
    except Exception as exc:
        username = username_or_url.strip().rstrip("/").split("/")[-1]
        return {
            "username": username,
            "field": "Software Engineering",
            "seniority": "Beginner",
            "languages": [],
            "significant_projects": [],
            "skills_for_interview": [],
            "repo_count": 0,
            "error": str(exc),
        }


def skill_names_from_profile(profile: dict) -> list[str]:
    names: list[str] = []

    for item in profile.get("skills") or []:
        if isinstance(item, str):
            names.append(item)
        elif isinstance(item, dict) and item.get("name"):
            names.append(item["name"])

    for item in profile.get("skills_for_interview") or []:
        if isinstance(item, str):
            names.append(item)
        elif isinstance(item, dict) and item.get("name"):
            names.append(item["name"])

    for item in profile.get("languages") or []:
        if isinstance(item, dict) and item.get("name"):
            names.append(item["name"])

    seen = set()
    cleaned = []
    for name in names:
        normalized = str(name).strip()
        key = normalized.lower()
        if normalized and key not in seen:
            seen.add(key)
            cleaned.append(normalized)
    return cleaned
