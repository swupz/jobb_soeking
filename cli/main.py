import typer
from cli import profile, job, status
from cli.apply import apply
from cli.research import research
from cli.render import render

app = typer.Typer(
    name="jobb",
    help="Job application assistant — research, generate, track.",
    no_args_is_help=True,
)

app.add_typer(profile.app, name="profile")
app.add_typer(job.app, name="job")
app.command("research")(research)
app.command("apply")(apply)
app.command("render")(render)
app.add_typer(status.app, name="status")


if __name__ == "__main__":
    app()
