"""CLI commands for triggering sync operations."""

import typer

from src.entrypoints.cli.client import create_client, request, resolve_base_url

app = typer.Typer(help="Trigger sync operations.")


@app.command("trigger")
def trigger_sync(
    ctx: typer.Context,
    source_id: str = typer.Argument(help="Source ID to sync."),
) -> None:
    """Trigger sync for an IP source."""
    base_url = resolve_base_url(ctx.obj)
    client = create_client(base_url)
    request(client, "POST", f"/sync/{source_id}")
    typer.echo("Sync triggered successfully.")
