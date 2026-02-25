import typer
from datetime import date
from rich import print as rprint
from rich.prompt import Prompt, Confirm
from rich.table import Table
from core.db import get_session
from models import Job

app = typer.Typer(help="Manage job listings.")


@app.command("add")
def add_job():
    """Manually add a job you want to apply for."""
    with get_session() as session:
        rprint("[bold]Add a new job[/bold]\n")

        company = Prompt.ask("Company name")
        title = Prompt.ask("Job title")
        url = Prompt.ask("Job posting URL (optional)", default="") or None
        language = Prompt.ask("Language", choices=["NO", "EN"], default="NO")
        deadline_str = Prompt.ask("Deadline (YYYY-MM-DD, optional)", default="") or None
        deadline = date.fromisoformat(deadline_str) if deadline_str else None

        rprint("\nPaste the job description below. When done, enter a line with just [bold]END[/bold]:")
        lines = []
        while True:
            line = input()
            if line.strip() == "END":
                break
            lines.append(line)
        description = "\n".join(lines)

        notes = Prompt.ask("\nNotes (optional)", default="") or None

        job = Job(
            company=company,
            title=title,
            description=description,
            url=url,
            language=language,
            deadline=deadline,
            notes=notes,
        )
        session.add(job)
        session.commit()
        session.refresh(job)

        rprint(f"\n[green]Job saved with ID {job.id}.[/green]")
        rprint(f"Next: [cyan]uv run jobb research {job.id}[/cyan]")


@app.command("list")
def list_jobs():
    """List all saved jobs."""
    with get_session() as session:
        jobs = session.query(Job).all()
        if not jobs:
            rprint("[yellow]No jobs found. Run 'jobb job add' to add one.[/yellow]")
            raise typer.Exit()

        table = Table(title="Jobs")
        table.add_column("ID", style="bold")
        table.add_column("Company")
        table.add_column("Title")
        table.add_column("Lang")
        table.add_column("Deadline")
        table.add_column("Applied?")

        for j in jobs:
            applied = "[green]Yes[/green]" if j.application else "No"
            table.add_row(
                str(j.id),
                j.company,
                j.title,
                j.language,
                str(j.deadline) if j.deadline else "—",
                applied,
            )

        rprint(table)
