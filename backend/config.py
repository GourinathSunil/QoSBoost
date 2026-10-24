"""
QoSBoost Backend Configuration Settings.
Uses pydantic-settings for type-safe environment and default configuration.
"""

import os
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment or defaults."""

    app_name: str = "QoSBoost API"
    app_version: str = "1.0.0"
    debug: bool = False

    # Server host & ports
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # Ryu SDN Controller endpoints
    controller_host: str = "127.0.0.1"
    controller_openflow_port: int = 6653
    controller_rest_port: int = 8080
    controller_rest_url: str = "http://127.0.0.1:8080"

    # SQLite Database
    db_filename: str = "qosboost.db"

    # CORS
    cors_origins: List[str] = ["*"]

    # Telemetry
    telemetry_interval_sec: float = 1.0
    telemetry_buffer_size: int = 120

    model_config = SettingsConfigDict(env_prefix="QOSBOOST_", env_file=".env", extra="ignore")

    @property
    def sqlite_url(self) -> str:
        db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", self.db_filename))
        return f"sqlite:///{db_path}"


settings = Settings()
