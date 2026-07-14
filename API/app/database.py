import logging

from sqlalchemy import create_engine, event
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import settings

logger = logging.getLogger("mnemo.db")

engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_size=settings.db_pool_size,
    max_overflow=settings.db_max_overflow,
    pool_recycle=3600,
    echo=settings.debug,
)

if settings.debug:

    @event.listens_for(engine, "checkout")
    def _on_checkout(dbapi_conn, connection_rec, connection_proxy):
        logger.debug("DB pool checkout: %s", id(dbapi_conn))

    @event.listens_for(engine, "checkin")
    def _on_checkin(dbapi_conn, connection_rec):
        logger.debug("DB pool checkin: %s", id(dbapi_conn))


SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
