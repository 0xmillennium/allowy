"""HTTP client utilities for CLI commands."""

import os
import sys

import httpx
import typer

from src.config import settings

DEFAULT_TIMEOUT = 10


def resolve_base_url(base_url: str | None) -> str:
    if base_url:
        return base_url.rstrip("/")
    env_url = os.environ.get("ALLOWY_BASE_URL")
    if env_url:
        return env_url.rstrip("/")
    return f"http://localhost:{settings.server_port}"


def create_client(base_url: str) -> httpx.Client:
    return httpx.Client(base_url=base_url, timeout=DEFAULT_TIMEOUT)


def handle_error(response: httpx.Response) -> None:
    try:
        data = response.json()
        msg = data.get("msg", response.text)
    except Exception:
        msg = response.text
    typer.echo(f"Error: {msg}", err=True)
    raise typer.Exit(1)


def request(
    client: httpx.Client,
    method: str,
    url: str,
    **kwargs,
) -> httpx.Response:
    try:
        response = client.request(method, url, **kwargs)
    except httpx.ConnectError:
        typer.echo(
            f"Error: Cannot connect to service at {client.base_url}",
            err=True,
        )
        raise typer.Exit(1)
    except httpx.TimeoutException:
        typer.echo("Error: Request timed out", err=True)
        raise typer.Exit(1)

    if not response.is_success:
        handle_error(response)

    return response
