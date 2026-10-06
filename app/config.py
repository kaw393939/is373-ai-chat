from pathlib import Path

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    app_env: str = "development"
    base_url: str = "http://localhost:8000"
    database_url: str = "sqlite+aiosqlite:///./.state/local.db"
    jwt_secret: str = "development-only-change-this-key-before-deploying"
    access_minutes: int = 10
    refresh_days: int = 7
    registration_policy: str = "approval"
    provider: str = "mock"
    provider_model: str = "gpt-4.1-mini"
    provider_base_url: str = "https://api.openai.com/v1"
    openai_api_key: str = ""
    provider_expires_at: str = ""
    static_dir: str = "frontend/dist"
    metrics_path: str = "/metrics/host.json"
    commit_sha: str = "development"
    global_concurrency: int = 4
    email_provider: str = "disabled"
    resend_api_key: str = ""
    email_from: str = "accounts@notify.firehose360.com"
    email_reply_to: str = "keith@firehose360.com"
    email_encryption_key: str = ""

    @model_validator(mode="after")
    def production_contract(self):
        if self.registration_policy not in {"approval", "open"}:
            raise ValueError("Choose approval or open registration")
        if self.provider not in {"mock", "openai", "compatible"}:
            raise ValueError("Unsupported provider")
        if self.email_provider not in {"disabled", "mock", "resend"}:
            raise ValueError("Unsupported email provider")
        if self.email_provider != "disabled":
            from cryptography.fernet import Fernet

            Fernet(self.email_encryption_key.encode())
        if self.email_provider == "resend" and not self.resend_api_key:
            raise ValueError("Resend requires its sending API key")
        if self.app_env == "production":
            if self.email_provider == "mock":
                raise ValueError("Production cannot use mock email delivery")
            if len(self.jwt_secret) < 48 or self.jwt_secret.startswith("development"):
                raise ValueError("Production requires a randomly generated JWT key")
            if not self.base_url.startswith("https://"):
                raise ValueError("Production requires HTTPS")
            if not self.database_url.startswith("postgresql+asyncpg://"):
                raise ValueError("Production requires PostgreSQL")
            if not self.provider_base_url.startswith("https://"):
                raise ValueError("Production provider endpoints require HTTPS")
        return self

    @property
    def secure_cookie(self):
        return self.app_env == "production"

    @property
    def assets(self):
        return Path(self.static_dir)
