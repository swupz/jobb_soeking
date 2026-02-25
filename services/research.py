"""
Uses Claude's built-in web search to research a company for a job application.
Claude searches the web autonomously and returns a structured summary.
"""
import os

import anthropic
from dotenv import load_dotenv

from models import Job

load_dotenv()


def research_company(job: Job) -> str:
    """
    Ask Claude to research the company using its built-in web search tool.
    Returns a structured summary string to be stored in Research.summary.
    """
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY not set in .env")

    client = anthropic.Anthropic(api_key=api_key)

    job_context = f"Job title: {job.title}\n"
    if job.description:
        job_context += f"\nJob description excerpt:\n{job.description[:800]}"

    prompt = f"""Research the company "{job.company}" for a job applicant who is applying for the role of {job.title}.

{job_context}

Search for and gather:
1. What the company does — products, services, industry, size, customers
2. Company culture, values, and work environment
3. Recent news or developments (last 12 months)
4. Technology stack or tools they use (if relevant to this role)
5. Reputation as an employer — Glassdoor ratings or employee sentiment if available
6. Key leadership, notable projects, or recent milestones

Then write a structured research summary with clear sections. Be specific and factual — only include what you found. This summary will be used when writing a tailored CV and cover letter for this job application."""

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        tools=[{
            "type": "web_search_20250305",
            "name": "web_search",
            "max_uses": 5,
        }],
        messages=[{"role": "user", "content": prompt}],
    )

    # Extract the final text response — skip server_tool_use and web_search_tool_result blocks
    text_parts = [block.text for block in response.content if block.type == "text"]
    return "\n\n".join(text_parts).strip()
