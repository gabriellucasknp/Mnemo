# Modelo do FLASHCARD (Etapa 5) — a saída-núcleo do MVP.
# Par pergunta/resposta, ligado à aula de origem e com a origem marcada
# (mesma regra de provenance da transcrição): estes flashcards derivam da
# FALA DO PROFESSOR, então origem=PROFESSOR. Complementos futuros da IA
# entrarão com origem=IA, exibidos em seção separada.
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.transcription import Origem


class Flashcard(Base):
    __tablename__ = "flashcards"

    id: Mapped[int] = mapped_column(primary_key=True)
    aula_id: Mapped[int] = mapped_column(ForeignKey("aulas.id"), index=True)
    categoria: Mapped[str] = mapped_column(String(40), default="conceito")
    pergunta: Mapped[str] = mapped_column(Text)
    resposta: Mapped[str] = mapped_column(Text)
    explicacao: Mapped[str | None] = mapped_column(Text)  # contexto extra (opcional)
    origem: Mapped[Origem] = mapped_column(
        Enum(Origem, name="origem", create_constraint=False), default=Origem.PROFESSOR
    )
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    aula = relationship("Aula", back_populates="flashcards")
