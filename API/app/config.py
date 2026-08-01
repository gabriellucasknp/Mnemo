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

    # --- Debug / Logging ---
    debug: bool = False
    log_level: str = "INFO"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def sqlalchemy_database_url(self) -> str:
        """URL normalizada pro SQLAlchemy.

        O Render entrega a connection string como `postgres://...` (sem driver).
        O SQLAlchemy precisa do esquema `postgresql+psycopg://` — normaliza aqui
        pra funcionar igual no Docker local e no deploy.
        """
        url = self.database_url
        if url.startswith("postgres://"):
            return url.replace("postgres://", "postgresql+psycopg://", 1)
        return url


settings = Settings()
