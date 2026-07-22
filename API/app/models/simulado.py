from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Simulado(Base):
    __tablename__ = "simulados"

    id: Mapped[int] = mapped_column(primary_key=True)
    titulo: Mapped[str] = mapped_column(String(255))
    materia: Mapped[str | None] = mapped_column(String(120))
    quantidade_questoes: Mapped[int] = mapped_column(Integer, default=10)
    dificuldade: Mapped[str] = mapped_column(String(20), default="medio")
    aula_id: Mapped[int | None] = mapped_column(ForeignKey("aulas.id"), index=True)
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    aula = relationship("Aula", back_populates="simulados")
    questoes = relationship(
        "QuestaoSimulado", back_populates="simulado", cascade="all, delete-orphan"
    )
    respostas = relationship(
        "RespostaSimulado", back_populates="simulado", cascade="all, delete-orphan"
    )


class QuestaoSimulado(Base):
    __tablename__ = "questoes_simulado"

    id: Mapped[int] = mapped_column(primary_key=True)
    simulado_id: Mapped[int] = mapped_column(
        ForeignKey("simulados.id"), index=True
    )
    enunciado: Mapped[str] = mapped_column(Text)
    alternativas: Mapped[dict] = mapped_column(JSON)
    gabarito: Mapped[str] = mapped_column(String(1))
    explicacao: Mapped[str | None] = mapped_column(Text)
    dificuldade: Mapped[str] = mapped_column(String(20), default="medio")
    disciplina: Mapped[str | None] = mapped_column(String(80))
    fonte: Mapped[str] = mapped_column(String(20), default="ia")

    simulado = relationship("Simulado", back_populates="questoes")


class RespostaSimulado(Base):
    __tablename__ = "respostas_simulado"

    id: Mapped[int] = mapped_column(primary_key=True)
    simulado_id: Mapped[int] = mapped_column(
        ForeignKey("simulados.id"), index=True
    )
    questao_id: Mapped[int] = mapped_column(
        ForeignKey("questoes_simulado.id"), index=True
    )
    alternativa_marcada: Mapped[str | None] = mapped_column(String(1))
    acertou: Mapped[bool] = mapped_column(default=False)
    respondida_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    simulado = relationship("Simulado", back_populates="respostas")
    questao = relationship("QuestaoSimulado")
