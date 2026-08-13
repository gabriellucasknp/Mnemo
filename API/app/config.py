import json

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # --- Banco ---
    database_url: str = "postgresql+psycopg://mnemo:mnemo@db:5432/mnemo"
    db_pool_size: int = 5
    db_max_overflow: int = 10

    # --- Whisper ---
    whisper_model: str = "base"

    # --- IA / flashcards (Google Gemini) ---
    gemini_api_key: str = ""
    gemini_model: str = "gemini-2.0-flash"

    # --- Armazenamento temporário ---
    storage_dir: str = "storage"

    # --- Segurança ---
    max_upload_mb: int = 200
    cors_origins: list[str] = ["*"]

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _parse_cors_origins(cls, value):
        """Aceita CORS_ORIGINS como JSON (`["https://app.onrender.com"]`)
        ou como lista separada por vírgula (`https://a.com,https://b.com`).

        Evita que um valor não-JSON quebre o boot do app em produção.
        """
        if isinstance(value, str):
            value = value.strip()
            if not value:
                return ["*"]
            try:
                parsed = json.loads(value)
                if isinstance(parsed, list):
                    return parsed
            except json.JSONDecodeError:
                pass
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    # --- Debug / Logging ---
    debug: bool = False
    log_level: str = "INFO"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def sqlalchemy_database_url(self) -> str:
        """URL normalizada pro SQLAlchemy.

        O único driver Postgres instalado é o psycopg 3 (`psycopg[binary]`),
        mas o SQLAlchemy assume psycopg2 quando a URL não traz driver explícito
        — tanto em `postgres://` quanto em `postgresql://`. O Render entrega a
        connection string sem driver, então sem esta normalização o boot morre
        com `ModuleNotFoundError: No module named 'psycopg2'`.

        Força `postgresql+psycopg://` nos dois casos; URLs que já declaram um
        driver (`postgresql+asyncpg://`, `sqlite://`, ...) passam intactas.
        """
        url = self.database_url
        for prefixo in ("postgres://", "postgresql://"):
            if url.startswith(prefixo):
                return f"postgresql+psycopg://{url[len(prefixo) :]}"
        return url


settings = Settings()
