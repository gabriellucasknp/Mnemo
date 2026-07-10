# Configuração central da aplicação (Etapa 4 em diante).
# Lê variáveis de ambiente (DATABASE_URL, modelo do Whisper, chave de API de IA...)
# usando pydantic-settings, pra nada sensível ficar escrito no código.
# Os valores reais vêm do .env / do compose.yml — veja .env.example.
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # --- Banco (Etapa 4) ---
    # Host "db" = nome do serviço no compose (NÃO use localhost entre containers).
    database_url: str = "postgresql+psycopg://mnemo:mnemo@db:5432/mnemo"

    # --- Whisper (Etapa 2/3) ---
    # Tamanhos: tiny/base/small/medium/large. "base" = bom equilíbrio pra CPU.
    whisper_model: str = "base"

    # --- IA / flashcards (Etapa 5) ---
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-opus-4-8"

    # --- Armazenamento temporário dos áudios enviados ---
    storage_dir: str = "storage"

    # --- Segurança: teto de upload (MB) ---
    # Sem limite, um único request gigante enche o disco/memória do servidor.
    max_upload_mb: int = 200

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
