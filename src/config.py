"""Application settings, seed source configuration, and logging setup."""

import logging.config
from pathlib import Path

import yaml
from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Database
    database_url: str = "sqlite+aiosqlite:///./config/database.db"

    # File Output
    output_dir: Path = Path("./outputs")

    # Scheduler
    scheduler_timezone: str = "UTC"

    # Server
    server_port: int = 8000

    # HTTP Client
    http_timeout: int = 30

    # Logging
    log_config_path: Path = Path("./config/logging.yaml")

    # Seed Sources
    seed_sources_path: Path = Path("./config/sources.yaml")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )


class SeedSource(BaseModel):
    name: str
    url: str
    source_type: str
    sync_interval: int


class SourcesConfig(BaseModel):
    sources: list[SeedSource] = []


def load_sources_config(path: Path) -> SourcesConfig:
    if not path.exists():
        return SourcesConfig()
    with open(path) as f:
        data = yaml.safe_load(f) or {}
    return SourcesConfig(**data)


def setup_logging(config_path: Path) -> None:
    if config_path.exists():
        with open(config_path) as f:
            config = yaml.safe_load(f)

        # Ensure log directories exist before configuring
        if "handlers" in config:
            for handler in config["handlers"].values():
                if "filename" in handler:
                    Path(handler["filename"]).parent.mkdir(parents=True, exist_ok=True)

        logging.config.dictConfig(config)
    else:
        logging.basicConfig(level=logging.INFO)


settings = Settings()
setup_logging(settings.log_config_path)
sources_config = load_sources_config(settings.seed_sources_path)
