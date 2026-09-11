"""Engine, sessione e PRAGMA."""

import sqlite3

from flask import current_app, g, has_app_context
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import get_settings


class Base(DeclarativeBase):
    pass


def _configure_connection(dbapi_conn, _record) -> None:
    """I PRAGMA si impostano per connessione, non una volta per database."""
    if not isinstance(dbapi_conn, sqlite3.Connection):
        return
    cur = dbapi_conn.cursor()
    cur.execute("PRAGMA journal_mode=WAL")
    cur.execute("PRAGMA synchronous=NORMAL")
    cur.execute("PRAGMA foreign_keys=ON")
    cur.execute("PRAGMA busy_timeout=5000")
    cur.close()


def build_engine(url: str | None = None, **kwargs) -> Engine:
    if url is None:
        settings = get_settings()
        settings.ensure_dirs()
        url = settings.database_url
    engine = create_engine(url, **kwargs)
    event.listen(engine, "connect", _configure_connection)
    return engine


_engine: Engine | None = None
_session_factory: sessionmaker[Session] | None = None


def get_engine() -> Engine:
    global _engine
    if _engine is None:
        _engine = build_engine()
    return _engine


def get_session_factory() -> sessionmaker[Session]:
    global _session_factory
    if _session_factory is None:
        _session_factory = sessionmaker(
            bind=get_engine(), autoflush=False, expire_on_commit=False
        )
    return _session_factory


def get_db() -> Session:
    """La sessione SQLAlchemy della richiesta corrente.

    Nei test ``DB_SESSION`` permette al client Flask e alla fixture di vedere
    la stessa transazione sul database in memoria. In produzione la sessione
    viene creata pigramente e chiusa da ``close_db`` a fine richiesta.
    """
    if has_app_context():
        configured = current_app.config.get("DB_SESSION")
        if configured is not None:
            return configured
        if "db" not in g:
            g.db = get_session_factory()()
        return g.db
    return get_session_factory()()


def close_db(_error: BaseException | None = None) -> None:
    session = g.pop("db", None)
    if session is not None:
        session.close()
