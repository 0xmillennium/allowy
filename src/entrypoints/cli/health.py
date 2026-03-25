import typer

from src.entrypoints.cli.client import create_client, resolve_base_url

app = typer.Typer(help="Health check commands.")


@app.command()
def live(ctx: typer.Context) -> None:
    """Check service liveness."""
    base_url = resolve_base_url(ctx.obj)
    client = create_client(base_url)

    try:
        response = client.get("/health/live")
    except Exception:
        typer.echo("Error: Cannot connect to service", err=True)
        raise typer.Exit(1)

    if response.is_success:
        typer.echo("OK")
    else:
        typer.echo("UNHEALTHY", err=True)
        raise typer.Exit(1)


@app.command()
def ready(ctx: typer.Context) -> None:
    """Check service readiness."""
    base_url = resolve_base_url(ctx.obj)
    client = create_client(base_url)

    try:
        response = client.get("/health/ready")
    except Exception:
        typer.echo("Error: Cannot connect to service", err=True)
        raise typer.Exit(1)

    data = response.json()

    for component in data.get("components", []):
        name = component["name"]
        status = component["status"]
        detail = component.get("detail") or ""
        line = f"  {name}: {status}"
        if detail:
            line += f" ({detail})"
        typer.echo(line)

    typer.echo(f"Status: {data['status']}")

    if response.status_code != 200:
        raise typer.Exit(1)
