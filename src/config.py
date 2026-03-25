"""Application settings, seed source configuration, and logging setup."""

import yaml
import logging.config
from pathlib import Path
from pydantic import BaseModel
from pydantic_settings import BaseSettings


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

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


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
        logging.config.dictConfig(config)
    else:
        logging.basicConfig(level=logging.INFO)


settings = Settings()
setup_logging(settings.log_config_path)
sources_config = load_sources_config(settings.seed_sources_path)