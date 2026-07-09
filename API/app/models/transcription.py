# Modelo da TRANSCRIÇÃO (Etapa 4) — o dado primário, a fonte de verdade.
#
# REGRA DE NEGÓCIO CRÍTICA (SDD §5): cada registro carrega a ORIGEM do texto
# (provenance). No MVP só existe uma origem ("fala do professor"), mas o campo
# já existe pra que, nas fases futuras, o complemento da IA entre marcado como
# secundário sem precisar refazer o banco.
import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Origem(enum.Enum):
    """De onde a informação veio. O professor sempre 'vence' (SDD §5)."""

    PROFESSOR = "professor"  # transcrição da fala — fonte de verdade
    IA = "ia"                # complemento gerado por IA — secundário, marcado


class Transcricao(Base):
    __tablename__ = "transcricoes"

    id: Mapped[int] = mapped_column(primary_key=True)
    aula_id: Mapped[int] = mapped_column(ForeignKey("aulas.id"), index=True)
    texto: Mapped[str] = mapped_column(Text)
    idioma: Mapped[str | None] = mapped_column(String(10))
    # A origem marcada desde o dia 1 — é isso que prepara o banco pras fases futuras.
    origem: Mapped[Origem] = mapped_column(
        Enum(Origem, name="origem"), default=Origem.PROFESSOR
    )
    criada_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    aula = relationship("Aula", back_populates="transcricao")
