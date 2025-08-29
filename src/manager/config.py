"""Configuration management for AI Manager."""

from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Database Configuration
    manager_db_url: str = Field(
        default="sqlite:///./manager.db",
        description="Database connection URL",
    )

    # Worker Execution Limits
    run_cpu_secs: int = Field(
        default=300,
        description="CPU time limit for worker processes (seconds)",
    )
    run_mem_mb: int = Field(
        default=512,
        description="Memory limit for worker processes (MB)",
    )
    run_timeout_secs: int = Field(
        default=1800,
        description="Wall clock timeout for worker processes (seconds)",
    )

    # Security Settings
    no_net: bool = Field(
        default=True,
        description="Disable network access for workers",
    )
    worker_sandbox: bool = Field(
        default=True,
        description="Enable worker sandboxing",
    )

    # API Configuration
    api_host: str = Field(
        default="0.0.0.0",
        description="API server host",
    )
    api_port: int = Field(
        default=8000,
        description="API server port",
    )

    # Logging
    log_level: str = Field(
        default="INFO",
        description="Logging level",
    )
    log_format: str = Field(
        default="json",
        description="Log format (json or text)",
    )

    # Artifacts
    max_artifact_size_mb: int = Field(
        default=100,
        description="Maximum artifact size (MB)",
    )
    artifact_retention_days: int = Field(
        default=30,
        description="Artifact retention period (days)",
    )

    # Development
    dev_mode: bool = Field(
        default=False,
        description="Enable development mode",
    )

    # Paths
    runs_dir: Path = Field(
        default=Path("runs"),
        description="Directory for run artifacts",
    )
    artifacts_dir: Path = Field(
        default=Path("artifacts"),
        description="Directory for persistent artifacts",
    )
    logs_dir: Path = Field(
        default=Path("logs"),
        description="Directory for log files",
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Ensure directories exist
        for dir_path in [self.runs_dir, self.artifacts_dir, self.logs_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)


# Global settings instance
settings = Settings()