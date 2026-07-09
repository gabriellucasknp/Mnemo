# Reexporta os modelos pra que `from app.models import Aula, ...` funcione
# e pra que o Base.metadata conheça todas as tabelas na hora do create_all.
from app.models.flashcard import Flashcard
from app.models.session import Aula
from app.models.transcription import Origem, Transcricao

__all__ = ["Aula", "Transcricao", "Flashcard", "Origem"]
