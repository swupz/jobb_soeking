import typer
from rich import print as rprint
from rich.table import Table
from core.db import get_session
from models import Application

app = typer.Typer(help="Track application statuses.")

STATUS_COLORS = {
    "draft": "dim",
    "sent": "cyan",
    "interview": "yellow",
    "rejected": "red",
    "offer": "green",
}


@app.command("list")
def list_status():
    """Show all applications and their current status."""
    with get_session() as session:
        applications = session.query(Application).all()
        if not applications:
            rprint("[yellow]No applications yet. Run 'jobb apply <job-id>' to generate one.[/yellow]")
            raise typer.Exit()

        table = Table(title="Applications")
        table.add_column("ID", style="bold")
        table.add_column("Company")
        table.add_column("Title")
        table.add_column("Status")
        table.add_column("Updated")

        for app in applications:
            color = STATUS_COLORS.get(app.status, "white")
            table.add_row(
                str(app.id),
                app.job.company,
                app.job.title,
                f"[{color}]{app.status}[/{color}]",
                str(app.updated_at.date()),
            )

        rprint(table)


@app.command("update")
def update_status(
    job_id: int = typer.Argument(..., help="Job ID"),
    status: str = typer.Option(..., help="New status: draft, sent, interview, rejected, offer"),
):
    """Update the status of an application."""
    valid = ["draft", "sent", "interview", "rejected", "offer"]
    if status not in valid:
        rprint(f"[red]Invalid status. Choose from: {', '.join(valid)}[/red]")
        raise typer.Exit(1)

    with get_session() as session:
        app = session.query(Application).filter_by(job_id=job_id).first()
        if not app:
            rprint(f"[red]No application found for job {job_id}.[/red]")
            raise typer.Exit(1)

        app.status = status
        session.commit()
        rprint(f"[green]Status updated to '{status}'.[/green]")
