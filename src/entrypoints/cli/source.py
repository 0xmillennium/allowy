"""CLI commands for managing IP sources."""

import typer

from src.entrypoints.cli.client import create_client, request, resolve_base_url

app = typer.Typer(help="Manage IP sources.")


def _get_client(ctx: typer.Context) -> tuple:
    base_url = resolve_base_url(ctx.obj)
    return create_client(base_url), base_url


@app.command("list")
def list_sources(ctx: typer.Context) -> None:
    """List all IP sources."""
    client, _ = _get_client(ctx)
    response = request(client, "GET", "/ip-sources")
    sources = response.json()

    if not sources:
        typer.echo("No sources found.")
        return

    headers = ["ID", "NAME", "TYPE", "STATUS", "INTERVAL"]
    rows = [
        [
            s["id"][:8],
            s["name"],
            s["source_type"],
            s["status"],
            f"{s['sync_interval']}m",
        ]
        for s in sources
    ]

    widths = [
        max(len(h), *(len(r[i]) for r in rows))
        for i, h in enumerate(headers)
    ]

    header_line = "  ".join(h.ljust(w) for h, w in zip(headers, widths))
    typer.echo(header_line)
    typer.echo("  ".join("-" * w for w in widths))
    for row in rows:
        typer.echo("  ".join(v.ljust(w) for v, w in zip(row, widths)))


@app.command()
def get(ctx: typer.Context, source_id: str = typer.Argument(help="Source ID.")) -> None:
    """Get details of an IP source."""
    client, _ = _get_client(ctx)
    response = request(client, "GET", f"/ip-sources/{source_id}")
    s = response.json()

    typer.echo(f"ID:            {s['id']}")
    typer.echo(f"Name:          {s['name']}")
    typer.echo(f"URL:           {s['url']}")
    typer.echo(f"Type:          {s['source_type']}")
    typer.echo(f"Interval:      {s['sync_interval']}m")
    typer.echo(f"Status:        {s['status']}")
    typer.echo(f"IP Ranges:     {len(s['ip_ranges'])}")
    typer.echo(f"Fetched At:    {s['fetched_at'] or 'never'}")
    typer.echo(f"Created At:    {s['created_at']}")
    typer.echo(f"Updated At:    {s['updated_at']}")


@app.command()
def create(
    ctx: typer.Context,
    name: str = typer.Option(..., help="Source name."),
    url: str = typer.Option(..., help="Source URL."),
    source_type: str = typer.Option(..., "--type", help="Source type."),
    sync_interval: int = typer.Option(..., "--interval", help="Sync interval in minutes."),
) -> None:
    """Create a new IP source."""
    client, _ = _get_client(ctx)
    request(
        client,
        "POST",
        "/ip-sources",
        params={
            "name": name,
            "url": url,
            "source_type": source_type,
            "sync_interval": sync_interval,
        },
    )
    typer.echo("Source created successfully.")


@app.command()
def delete(
    ctx: typer.Context,
    source_id: str = typer.Argument(help="Source ID."),
) -> None:
    """Delete an IP source."""
    client, _ = _get_client(ctx)
    request(client, "DELETE", f"/ip-sources/{source_id}")
    typer.echo("Source deleted successfully.")


@app.command("update-name")
def update_name(
    ctx: typer.Context,
    source_id: str = typer.Argument(help="Source ID."),
    name: str = typer.Option(..., "--name", help="New source name."),
) -> None:
    """Update name of an IP source."""
    client, _ = _get_client(ctx)
    request(
        client,
        "PATCH",
        f"/ip-sources/{source_id}/name",
        params={"name": name},
    )
    typer.echo("Source name updated successfully.")


@app.command("update-type")
def update_type(
    ctx: typer.Context,
    source_id: str = typer.Argument(help="Source ID."),
    source_type: str = typer.Option(..., "--type", help="New source type."),
) -> None:
    """Update source type of an IP source."""
    client, _ = _get_client(ctx)
    request(
        client,
        "PATCH",
        f"/ip-sources/{source_id}/source-type",
        params={"source_type": source_type},
    )
    typer.echo("Source type updated successfully.")


@app.command("update-interval")
def update_interval(
    ctx: typer.Context,
    source_id: str = typer.Argument(help="Source ID."),
    sync_interval: int = typer.Option(..., "--interval", help="New sync interval in minutes."),
) -> None:
    """Update sync interval of an IP source."""
    client, _ = _get_client(ctx)
    request(
        client,
        "PATCH",
        f"/ip-sources/{source_id}/interval",
        params={"sync_interval": sync_interval},
    )
    typer.echo("Sync interval updated successfully.")


@app.command()
def pause(
    ctx: typer.Context,
    source_id: str = typer.Argument(help="Source ID."),
) -> None:
    """Pause an IP source."""
    client, _ = _get_client(ctx)
    request(client, "POST", f"/ip-sources/{source_id}/pause")
    typer.echo("Source paused successfully.")


@app.command()
def resume(
    ctx: typer.Context,
    source_id: str = typer.Argument(help="Source ID."),
) -> None:
    """Resume an IP source."""
    client, _ = _get_client(ctx)
    request(client, "POST", f"/ip-sources/{source_id}/resume")
    typer.echo("Source resumed successfully.")


@app.command("pause-all")
def pause_all(ctx: typer.Context) -> None:
    """Pause all IP sources."""
    client, _ = _get_client(ctx)
    request(client, "POST", "/ip-sources/pause-all")
    typer.echo("All sources paused successfully.")


@app.command("resume-all")
def resume_all(ctx: typer.Context) -> None:
    """Resume all IP sources."""
    client, _ = _get_client(ctx)
    request(client, "POST", "/ip-sources/resume-all")
    typer.echo("All sources resumed successfully.")
