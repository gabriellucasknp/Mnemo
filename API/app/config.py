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
    # Token exigido nos endpoints administrativos (treino de modelos).
    # Vazio = endpoints de treino ficam bloqueados (503) — seguro por padrão.
    admin_token: str = ""
    # Rate limiting dos endpoints caros (upload/IA). Desligável em testes.
    rate_limit_enabled: bool = True

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
                return f"postgresql+psycopg://{url[len(prefixo):]}"
        return url


settings = Settings()
