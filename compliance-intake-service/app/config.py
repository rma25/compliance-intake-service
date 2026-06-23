"""Application settings, loaded from environment variables (.env supported).

For a C# dev: this is the Options pattern. `pydantic-settings` reads env vars
(prefixed CIS_), validates/coerces types, and hands you a typed settings object.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_prefix="CIS_", extra="ignore")

    # Pluggable backends: storage = "local" | "s3", audit = "jsonl" | "dynamodb"
    storage_backend: str = "local"
    audit_backend: str = "jsonl"

    # Local backend paths (used when backends are local/jsonl)
    documents_dir: str = "./_data/documents"
    audit_log_path: str = "./_data/audit_log.jsonl"
    watchlist_path: str = "app/data/watchlist.json"

    # AWS config (used only when backends are s3/dynamodb)
    aws_region: str = "us-east-1"
    s3_bucket: str = ""
    dynamodb_table: str = "compliance-audit"

    # Screening rules (USD)
    review_threshold: float = 3_000_000
    blocked_countries: tuple[str, ...] = ("IR", "KP", "SY", "CU")
    high_risk_countries: tuple[str, ...] = ("RU", "VE", "MM")


@lru_cache
def get_settings() -> Settings:
    return Settings()
