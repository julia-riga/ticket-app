from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, declarative_base

from .config import settings

connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}

engine = create_engine(settings.database_url, connect_args=connect_args)


if settings.database_url.startswith("sqlite"):
    @event.listens_for(engine, "connect")
    def _register_sqlite_functions(dbapi_connection, connection_record):
        # Встроенный lower() в SQLite умеет только ASCII, а заявки на русском.
        # Регистрируем свою функцию, чтобы поиск был регистронезависимым.
        dbapi_connection.create_function(
            "py_lower", 1, lambda value: value.lower() if value else value, deterministic=True
        )


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
