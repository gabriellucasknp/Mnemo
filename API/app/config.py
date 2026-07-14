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


settings = Settings()
