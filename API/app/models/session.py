# Modelo da AULA / SESSÃO (Etapa 4).
# Representa um encontro capturado: data, título, etc.
# É o "pai" ao qual transcrição e flashcards se ligam.
from datetime import datetime

from sqlalchemy import DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Aula(Base):
    __tablename__ = "aulas"

    id: Mapped[int] = mapped_column(primary_key=True)
    titulo: Mapped[str] = mapped_column(String(255), default="Aula sem título")
    materia: Mapped[str | None] = mapped_column(String(120))  # inferida pela IA (Etapa 5)
    duracao_segundos: Mapped[int | None] = mapped_column(Integer)
    criada_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relações: uma aula tem UMA transcrição (MVP), N flashcards e M simulados.
    transcricao = relationship(
        "Transcricao", back_populates="aula", uselist=False, cascade="all, delete-orphan"
    )
    flashcards = relationship(
        "Flashcard", back_populates="aula", cascade="all, delete-orphan"
    )
    simulados = relationship(
        "Simulado", back_populates="aula", cascade="all, delete-orphan"
    )
