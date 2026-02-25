import typer
from rich.prompt import Prompt
from rich.table import Table
from rich import print as rprint
from core.db import get_session
from models import Profile, WorkExperience, Education, Skill

app = typer.Typer(help="Manage your personal profile.")


def _require_profile(session):
    profile = session.query(Profile).first()
    if not profile:
        rprint("[red]No profile found. Run 'jobb profile setup' first.[/red]")
        raise typer.Exit(1)
    return profile


@app.command("setup")
def setup_profile():
    """Create or update your basic profile info."""
    with get_session() as session:
        profile = session.query(Profile).first()
        is_new = profile is None
        if is_new:
            profile = Profile()

        rprint("[bold]Profile setup[/bold] (press Enter to keep existing)\n")
        profile.full_name = Prompt.ask("Full name", default=profile.full_name or "")
        profile.email = Prompt.ask("Email", default=profile.email or "")
        profile.phone = Prompt.ask("Phone", default=profile.phone or "") or None
        profile.location = Prompt.ask("Location (city, country)", default=profile.location or "") or None
        profile.linkedin_url = Prompt.ask("LinkedIn URL", default=profile.linkedin_url or "") or None
        profile.github_url = Prompt.ask("GitHub URL", default=profile.github_url or "") or None

        rprint("\n[dim]Write a short personal summary — this gets tailored per application by Claude.[/dim]")
        profile.summary = Prompt.ask("Summary", default=profile.summary or "") or None

        rprint("\n[dim]Hobbies, sports, volunteer work, anything that makes you a person.[/dim]")
        profile.interests = Prompt.ask("Interests", default=profile.interests or "") or None

        if is_new:
            session.add(profile)
        session.commit()
        rprint("\n[green]Profile saved.[/green]")


@app.command("show")
def show_profile():
    """Show your full profile."""
    with get_session() as session:
        profile = session.query(Profile).first()
        if not profile:
            rprint("[yellow]No profile found. Run 'jobb profile setup' to create one.[/yellow]")
            raise typer.Exit()

        rprint(f"\n[bold cyan]{profile.full_name}[/bold cyan]  {profile.email}  {profile.phone or ''}")
        if profile.location:
            rprint(f"[dim]{profile.location}[/dim]")
        if profile.linkedin_url:
            rprint(f"LinkedIn: {profile.linkedin_url}")
        if profile.github_url:
            rprint(f"GitHub:   {profile.github_url}")
        if profile.summary:
            rprint(f"\n[bold]Summary[/bold]\n{profile.summary}")
        if profile.interests:
            rprint(f"\n[bold]Interests[/bold]\n{profile.interests}")

        if profile.work_experiences:
            rprint("\n[bold]Work Experience[/bold]")
            for w in profile.work_experiences:
                end = str(w.end_date) if w.end_date else "present"
                rprint(f"  [{w.start_date} – {end}] [cyan]{w.title}[/cyan] @ {w.company}")
                if w.description:
                    rprint(f"    {w.description}")

        if profile.educations:
            rprint("\n[bold]Education[/bold]")
            for e in profile.educations:
                end = str(e.end_date) if e.end_date else "present"
                field = f", {e.field}" if e.field else ""
                rprint(f"  [{e.start_date} – {end}] [cyan]{e.degree}{field}[/cyan] @ {e.institution}")

        if profile.skills:
            rprint("\n[bold]Skills[/bold]")
            by_cat: dict[str, list[str]] = {}
            for s in profile.skills:
                cat = s.category or "General"
                by_cat.setdefault(cat, []).append(s.name)
            for cat, names in by_cat.items():
                rprint(f"  [cyan]{cat}[/cyan]: {', '.join(names)}")


@app.command("add-experience")
def add_experience():
    """Add a work experience entry."""
    with get_session() as session:
        profile = _require_profile(session)

        rprint("[bold]Add work experience[/bold]\n")
        company = Prompt.ask("Company")
        title = Prompt.ask("Job title")
        start = Prompt.ask("Start date (YYYY-MM-DD)")
        end_str = Prompt.ask("End date (YYYY-MM-DD, leave blank if current)", default="")
        rprint("[dim]Describe your role, responsibilities, and achievements:[/dim]")
        description = Prompt.ask("Description") or None

        from datetime import date
        exp = WorkExperience(
            profile_id=profile.id,
            company=company,
            title=title,
            start_date=date.fromisoformat(start),
            end_date=date.fromisoformat(end_str) if end_str else None,
            description=description,
        )
        session.add(exp)
        session.commit()
        rprint("[green]Experience added.[/green]")


@app.command("add-education")
def add_education():
    """Add an education entry."""
    with get_session() as session:
        profile = _require_profile(session)

        rprint("[bold]Add education[/bold]\n")
        institution = Prompt.ask("Institution")
        degree = Prompt.ask("Degree (e.g. Bachelor, Master, PhD)")
        field = Prompt.ask("Field of study (optional)", default="") or None
        start = Prompt.ask("Start date (YYYY-MM-DD)")
        end_str = Prompt.ask("End date (YYYY-MM-DD, blank if ongoing)", default="")

        from datetime import date
        edu = Education(
            profile_id=profile.id,
            institution=institution,
            degree=degree,
            field=field,
            start_date=date.fromisoformat(start),
            end_date=date.fromisoformat(end_str) if end_str else None,
        )
        session.add(edu)
        session.commit()
        rprint("[green]Education added.[/green]")


@app.command("add-skill")
def add_skill():
    """Add a skill."""
    with get_session() as session:
        profile = _require_profile(session)

        name = Prompt.ask("Skill name")
        category = Prompt.ask(
            "Category (e.g. Programming, Language, Tool, Soft skill)",
            default="General"
        ) or None

        skill = Skill(profile_id=profile.id, name=name, category=category)
        session.add(skill)
        session.commit()
        rprint(f"[green]Skill '{name}' added.[/green]")


@app.command("add-skills")
def add_skills():
    """Add multiple skills at once (comma-separated)."""
    with get_session() as session:
        profile = _require_profile(session)

        category = Prompt.ask(
            "Category for all these skills",
            default="General"
        ) or None
        raw = Prompt.ask("Skills (comma-separated)")
        names = [n.strip() for n in raw.split(",") if n.strip()]

        for name in names:
            session.add(Skill(profile_id=profile.id, name=name, category=category))
        session.commit()
        rprint(f"[green]{len(names)} skills added.[/green]")
