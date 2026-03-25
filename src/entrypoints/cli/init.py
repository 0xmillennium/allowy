import typer

from src.entrypoints.cli.client import create_client, request, resolve_base_url

app = typer.Typer(help="Application initialization.")


@app.command("run")
def run(ctx: typer.Context) -> None:
    """Seed IP sources from config and initialize scheduler."""
    base_url = resolve_base_url(ctx.obj)
    client = create_client(base_url)
    request(client, "POST", "/initialize")
    typer.echo("Application initialized successfully.")
