"""
Uses Claude to generate tailored CV content and cover letters.

Claude receives a full profile + job description and returns structured JSON
with content ready to be dropped into the HTML template.
"""
import json
import os
from dataclasses import dataclass
from pathlib import Path

import anthropic
from dotenv import load_dotenv

from models import Profile, Job, Research

GUIDELINES_PATH = Path(__file__).parent.parent / "data" / "guidelines" / "cover_letter_style.md"


def _load_guidelines() -> str | None:
    if GUIDELINES_PATH.exists():
        return GUIDELINES_PATH.read_text(encoding="utf-8").strip()
    return None

load_dotenv()


@dataclass
class CVContent:
    name: str
    email: str
    phone: str
    location: str
    linkedin_url: str
    github_url: str
    language: str              # "NO" or "EN"
    summary: str               # tailored professional summary
    experiences: list[dict]    # [{company, title, period, bullets: [str]}]
    educations: list[dict]     # [{institution, degree, field, period}]
    skills: list[dict]         # [{category, names: [str]}]
    interests: str


@dataclass
class GeneratedApplication:
    cv: CVContent
    cover_letter: str          # plain text / markdown paragraphs


def _serialize_profile(profile: Profile) -> str:
    lines = [
        f"Name: {profile.full_name}",
        f"Email: {profile.email}",
        f"Phone: {profile.phone or 'N/A'}",
        f"Location: {profile.location or 'N/A'}",
        f"LinkedIn: {profile.linkedin_url or 'N/A'}",
        f"GitHub: {profile.github_url or 'N/A'}",
        f"Summary: {profile.summary or 'N/A'}",
        f"Interests/Hobbies: {profile.interests or 'N/A'}",
        "",
        "## Work Experience",
    ]
    for w in profile.work_experiences:
        end = str(w.end_date) if w.end_date else "present"
        lines.append(f"- {w.title} at {w.company} ({w.start_date} – {end})")
        if w.description:
            lines.append(f"  {w.description}")

    lines.append("")
    lines.append("## Education")
    for e in profile.educations:
        end = str(e.end_date) if e.end_date else "present"
        field = f" in {e.field}" if e.field else ""
        lines.append(f"- {e.degree}{field} at {e.institution} ({e.start_date} – {end})")

    lines.append("")
    lines.append("## Skills")
    by_cat: dict[str, list[str]] = {}
    for s in profile.skills:
        by_cat.setdefault(s.category or "General", []).append(s.name)
    for cat, names in by_cat.items():
        lines.append(f"- {cat}: {', '.join(names)}")

    return "\n".join(lines)


def _build_cv_prompt(profile_text: str, job: Job, research_summary: str | None, language: str) -> str:
    lang_instruction = (
        "Write everything in Norwegian (Bokmål)." if language == "NO"
        else "Write everything in English."
    )

    research_section = (
        f"\n\n## Company Research\n{research_summary}" if research_summary
        else ""
    )

    return f"""You are an expert career coach and CV writer.

{lang_instruction}

Given the candidate's profile and the job description, generate a tailored CV in JSON format.

The CV should:
- Highlight experiences and skills most relevant to this specific job
- Rewrite the work experience descriptions as 2–4 concise bullet points per role, tailored to the job
- Write a sharp 2–3 sentence professional summary specifically for this role
- Be honest — do not invent skills or experience

Return ONLY valid JSON, no markdown code fences, with this exact structure:
{{
  "summary": "tailored professional summary",
  "experiences": [
    {{
      "company": "Company Name",
      "title": "Job Title",
      "period": "Jan 2020 – present",
      "bullets": ["Achievement or responsibility", "..."]
    }}
  ],
  "educations": [
    {{
      "institution": "University Name",
      "degree": "Master",
      "field": "Computer Science",
      "period": "2015 – 2019"
    }}
  ],
  "skills": [
    {{
      "category": "Programming",
      "names": ["Python", "JavaScript"]
    }}
  ],
  "interests": "short interests text"
}}

---

## Candidate Profile
{profile_text}

## Job Description
Title: {job.title}
Company: {job.company}
{research_section}

Description:
{job.description}
"""


def _build_cover_letter_prompt(
    profile_text: str,
    job: Job,
    cv_summary: str,
    research_summary: str | None,
    language: str,
    feedback: str | None = None,
) -> str:
    lang_instruction = (
        "Write the cover letter in Norwegian (Bokmål)." if language == "NO"
        else "Write the cover letter in English."
    )
    research_section = (
        f"\n\n## Company Research\n{research_summary}" if research_summary
        else ""
    )
    guidelines = _load_guidelines()
    guidelines_section = (
        f"\n\n## Writing Style Guidelines (from previous cover letters — use as inspiration, not a template)\n{guidelines}"
        if guidelines else ""
    )
    feedback_section = (
        f"\n\n## Specific Feedback to Apply\n{feedback}"
        if feedback else ""
    )

    return f"""You are an expert career coach.

{lang_instruction}

Write a compelling, genuine cover letter for this job application. It should:
- Be 3–4 paragraphs, conversational but professional
- Open with a strong hook — not "I am applying for..."
- Reference specific things about the company that make this candidate a good fit
- Connect the candidate's actual experience to the job's needs
- Close with confidence, not desperation
- Sound like a real person, not a template
{guidelines_section}
{feedback_section}

Return ONLY the cover letter text. No subject line, no date, no salutation header needed.

---

## Candidate Profile
{profile_text}

## Tailored Summary (already generated for CV)
{cv_summary}

## Job
Title: {job.title}
Company: {job.company}
{research_section}

Description:
{job.description}
"""


def generate_application(profile: Profile, job: Job, research: Research | None = None, feedback: str | None = None) -> GeneratedApplication:
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY not set in .env")

    client = anthropic.Anthropic(api_key=api_key)
    language = job.language or "NO"
    profile_text = _serialize_profile(profile)
    research_summary = research.summary if research else None

    # Step 1: generate CV content
    cv_prompt = _build_cv_prompt(profile_text, job, research_summary, language)
    cv_response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        messages=[{"role": "user", "content": cv_prompt}],
    )
    cv_json = json.loads(cv_response.content[0].text)

    # Step 2: generate cover letter
    cl_prompt = _build_cover_letter_prompt(
        profile_text, job, cv_json["summary"], research_summary, language, feedback=feedback
    )
    cl_response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2048,
        messages=[{"role": "user", "content": cl_prompt}],
    )
    cover_letter_text = cl_response.content[0].text.strip()

    # Build skills grouped
    skills_grouped = [
        {"category": s["category"], "names": s["names"]}
        for s in cv_json.get("skills", [])
    ]

    cv_content = CVContent(
        name=profile.full_name,
        email=profile.email,
        phone=profile.phone or "",
        location=profile.location or "",
        linkedin_url=profile.linkedin_url or "",
        github_url=profile.github_url or "",
        language=language,
        summary=cv_json["summary"],
        experiences=cv_json.get("experiences", []),
        educations=cv_json.get("educations", []),
        skills=skills_grouped,
        interests=cv_json.get("interests", profile.interests or ""),
    )

    return GeneratedApplication(cv=cv_content, cover_letter=cover_letter_text)
