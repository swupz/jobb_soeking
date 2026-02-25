import re
from datetime import datetime
import typer
from rich import print as rprint
from rich.progress import Progress, SpinnerColumn, TextColumn

from core.db import get_session
from models import Job, Profile, Application, Document, Research
from services.generation import generate_application
from services.pdf import render_cv, render_cover_letter

def _safe_dirname(company: str, title: str, job_id: int) -> str:
    raw = f"{company}_{title}_{job_id}"
    base = re.sub(r"[^\w\-]", "_", raw).lower()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{base}_{timestamp}"


def apply(
    job_id: int = typer.Argument(..., help="ID of the job to apply for"),
    feedback: str = typer.Option(None, "--feedback", "-f", help="Feedback to improve the cover letter (e.g. 'make it less formal')"),
):
    """Generate CV and cover letter PDF for a job."""
    with get_session() as session:
        job = session.get(Job, job_id)
        if not job:
            rprint(f"[red]Job {job_id} not found.[/red]")
            raise typer.Exit(1)

        profile = session.query(Profile).first()
        if not profile:
            rprint("[red]No profile found. Run 'jobb profile setup' first.[/red]")
            raise typer.Exit(1)

        research = session.query(Research).filter_by(job_id=job_id).first()
        if not research:
            rprint("[yellow]No research found for this job — generating without company context.[/yellow]")
            rprint("[dim]Tip: run 'jobb research <job-id>' first for better results.[/dim]\n")

        rprint(f"[bold]Generating application:[/bold] {job.title} @ {job.company}  [{job.language}]\n")
        if feedback:
            rprint(f"[dim]Cover letter feedback: {feedback}[/dim]\n")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            task = progress.add_task("Asking Claude to write your CV and cover letter...", total=None)
            result = generate_application(profile, job, research, feedback=feedback)
            progress.update(task, description="Rendering HTML and PDFs...")

            subdir = _safe_dirname(job.company, job.title, job_id)
            cv_pdf, cv_html = render_cv(result.cv, subdir)
            cl_pdf, cl_html = render_cover_letter(
                result.cv, result.cover_letter, job.title, job.company, subdir
            )

        # Persist to DB
        application = session.query(Application).filter_by(job_id=job_id).first()
        if not application:
            application = Application(job_id=job_id, status="draft")
            session.add(application)
            session.flush()

        session.add(Document(
            application_id=application.id,
            type="cv",
            language=job.language,
            markdown_content=result.cv.summary,
            pdf_path=str(cv_pdf),
        ))
        session.add(Document(
            application_id=application.id,
            type="cover_letter",
            language=job.language,
            markdown_content=result.cover_letter,
            pdf_path=str(cl_pdf),
        ))
        session.commit()

        rprint("[green]Done.[/green]")
        rprint(f"  CV PDF:              [cyan]{cv_pdf}[/cyan]")
        rprint(f"  CV HTML:             [cyan]{cv_html}[/cyan]")
        rprint(f"  Cover letter PDF:    [cyan]{cl_pdf}[/cyan]")
        rprint(f"  Cover letter HTML:   [cyan]{cl_html}[/cyan]")
        rprint(f"\n[dim]Edit the HTML then run 'jobb render <html-file>' to re-export as PDF.[/dim]")
        rprint(f"[dim]Run 'jobb apply {job_id} --feedback \"your notes\"' to regenerate with guidance.[/dim]")
        rprint(f"[dim]Run 'jobb status update {job_id} --status sent' when you send it.[/dim]")
