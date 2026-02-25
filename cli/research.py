from datetime import datetime, timezone

import typer
from rich import print as rprint
from rich.progress import Progress, SpinnerColumn, TextColumn

from core.db import get_session
from models import Job, Research
from services.research import research_company

app = typer.Typer(help="Research a company using web search.")


def research(job_id: int = typer.Argument(..., help="ID of the job to research")):
    """Search the web and build a company research summary for a job."""
    with get_session() as session:
        job = session.get(Job, job_id)
        if not job:
            rprint(f"[red]Job {job_id} not found.[/red]")
            raise typer.Exit(1)

        rprint(f"[bold]Researching:[/bold] {job.company} — {job.title}\n")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            progress.add_task("Searching the web with Claude...", total=None)
            summary = research_company(job)

        record = session.query(Research).filter_by(job_id=job_id).first()
        if not record:
            record = Research(job_id=job_id)
            session.add(record)

        record.summary = summary
        record.scraped_at = datetime.now(timezone.utc)
        session.commit()

        rprint("[green]Research complete.[/green]\n")
        preview = summary[:700] + "\n[dim]...[/dim]" if len(summary) > 700 else summary
        rprint(preview)
        rprint(f"\n[dim]Run 'jobb apply {job_id}' to generate your application.[/dim]")
