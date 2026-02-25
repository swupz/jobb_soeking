from pathlib import Path

import typer
from rich import print as rprint

from services.pdf import html_to_pdf


def render(html_file: Path = typer.Argument(..., help="Path to the HTML file to convert")):
    """Convert an edited HTML file back to PDF with the same styling."""
    if not html_file.exists():
        rprint(f"[red]File not found: {html_file}[/red]")
        raise typer.Exit(1)
    if html_file.suffix.lower() != ".html":
        rprint("[red]File must be an .html file.[/red]")
        raise typer.Exit(1)

    rprint(f"Rendering [cyan]{html_file.name}[/cyan] → PDF...")
    pdf_path = html_to_pdf(html_file)
    rprint(f"[green]Done.[/green] PDF saved to [cyan]{pdf_path}[/cyan]")
