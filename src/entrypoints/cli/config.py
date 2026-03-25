import typer

from src.entrypoints.cli.client import create_client, request, resolve_base_url

app = typer.Typer(help="View generated configurations.")


@app.command()
def nginx(ctx: typer.Context) -> None:
    """Get generated Nginx configuration."""
    base_url = resolve_base_url(ctx.obj)
    client = create_client(base_url)
    response = request(client, "GET", "/configs/nginx")
    typer.echo(response.text)


@app.command()
def traefik(ctx: typer.Context) -> None:
    """Get generated Traefik configuration."""
    base_url = resolve_base_url(ctx.obj)
    client = create_client(base_url)
    response = request(client, "GET", "/configs/traefik")
    typer.echo(response.text)


@app.command()
def raw(ctx: typer.Context) -> None:
    """Get raw IP ranges."""
    base_url = resolve_base_url(ctx.obj)
    client = create_client(base_url)
    response = request(client, "GET", "/configs/raw")
    typer.echo(response.text)
