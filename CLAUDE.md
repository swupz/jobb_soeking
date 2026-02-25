# Jobb Søking — Job Application Assistant

A Python CLI tool to manage the entire job application process:
- Store and organize personal info, work history, and skills
- Manually add jobs you want to apply for
- Research companies by scraping their website, news, and reviews
- Auto-generate tailored CVs and cover letters as PDFs (Norwegian or English)
- Track application statuses and follow-ups

## Stack

- **Language**: Python 3.12+
- **CLI**: Typer
- **Database**: SQLite via SQLAlchemy + Alembic
- **Scraping**: Playwright + BeautifulSoup (for company/role research, not job boards)
- **AI generation**: Anthropic Claude API (for writing CVs and cover letters)
- **PDF generation**: WeasyPrint (markdown → PDF)
- **Package manager**: uv

## Project Structure (target)

```
jobb_soeking/
├── cli/              # Typer CLI commands (entry points)
├── models/           # SQLAlchemy models
├── schemas/          # Pydantic schemas
├── services/
│   ├── research.py   # Scrape company websites, news, Glassdoor, LinkedIn, etc.
│   ├── generation.py # Claude API calls to write CVs and cover letters
│   ├── pdf.py        # Render markdown → PDF via WeasyPrint
│   └── tracker.py    # Application status management
├── templates/        # Markdown templates for CV and cover letter (NO/EN)
├── data/
│   ├── db.sqlite     # Application database
│   └── output/       # Generated PDFs per application
├── tests/
├── alembic/
├── pyproject.toml
└── CLAUDE.md
```

## Key Concepts

- **Profile**: The user's master data — name, contact info, work experience, education, skills, languages
- **Job**: A manually entered job listing — company, title, description, URL, deadline, language (NO/EN)
- **Research**: Scraped intel about the company — culture, news, products, people, Glassdoor reviews — used as context when generating documents
- **Application**: Links a Profile + Job + Research + generated documents + status (draft / sent / interview / rejected / offer)
- **Document**: A generated CV or cover letter as PDF, tailored to the job and written in the correct language

## Commands

> To be defined as the project evolves. Likely:

- `uv run cli profile` — set up or edit your personal profile
- `uv run cli job add` — manually add a job you want to apply for
- `uv run cli research <job-id>` — scrape company info to build context for the application
- `uv run cli apply <job-id>` — generate CV + cover letter as PDF, in the job's language
- `uv run cli status` — list all applications and their current status
- `uv run cli update <job-id> --status interview` — update application status

## Working Style

- **Collaborative**: Discuss approach and trade-offs before writing code
- Propose architecture before implementing new features
- Ask before adding new dependencies
- Keep the codebase simple — avoid over-engineering

## Conventions

- Snake_case everywhere
- Services handle all business logic; CLI commands are thin wrappers
- All DB access goes through SQLAlchemy (no raw SQL unless necessary)
- Generated documents saved as markdown and/or PDF in `data/`
- Secrets and API keys in `.env` (never committed)
- Write tests for services, not for routes

## Assumptions to revisit

- [ ] What sources should research scrape? (company website, LinkedIn, Glassdoor, news articles?)
- [ ] Should the CV be a fixed template or fully AI-generated each time?
- [ ] How much of the user's profile is structured data vs. free-text?
