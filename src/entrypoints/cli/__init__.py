from typing import Optional

import typer

from src.config import settings
from src.entrypoints.cli.config import app as config_app
from src.entrypoints.cli.health import app as health_app
from src.entrypoints.cli.init import app as init_app
from src.entrypoints.cli.source import app as source_app
from src.entrypoints.cli.sync import app as sync_app

app = typer.Typer(name="allowy", help="Allowy CLI.", no_args_is_help=True)


@app.callback()
def main(
    ctx: typer.Context,
    base_url: Optional[str] = typer.Option(
        None, "--base-url", help="Base URL of the running service."
    ),
) -> None:
    ctx.ensure_object(dict)
    ctx.obj = base_url


@app.command()
def serve(
    host: str = typer.Option("0.0.0.0", help="Bind host."),
    port: int = typer.Option(settings.server_port, help="Bind port."),
) -> None:
    """Start the HTTP server."""
    import uvicorn

    uvicorn.run("src.main:app", host=host, port=port)


@app.command()
def version() -> None:
    """Show version information."""
    typer.echo("allowy v0.1.0")


app.add_typer(health_app, name="health")
app.add_typer(source_app, name="source")
app.add_typer(config_app, name="config")
app.add_typer(sync_app, name="sync")
app.add_typer(init_app, name="init")
