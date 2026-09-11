"""Fixture condivise. Il database è in memoria con StaticPool, così una sola
connessione è condivisa fra le sessioni e le tabelle create restano visibili."""

import pytest
from flask.testing import FlaskClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import models  # noqa: F401
from app.auth import hash_password
from app.config import get_settings
from app.db import Base
from app.models import User


class TestClient(FlaskClient):
    """Piccolo adattatore per i nomi usati dai test HTTP esistenti."""

    def open(self, *args, params=None, files=None, **kwargs):
        kwargs.setdefault("follow_redirects", True)
        if params is not None:
            kwargs["query_string"] = params
        if files:
            data = dict(kwargs.pop("data", {}))
            for name, (filename, stream, content_type) in files.items():
                data[name] = (stream, filename, content_type)
            kwargs["data"] = data
        return super().open(*args, **kwargs)


@pytest.fixture
def db():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    with factory() as sessione:
        yield sessione


@pytest.fixture
def impostazioni(tmp_path, monkeypatch):
    """Le impostazioni vere, ma con i dati in una cartella temporanea.

    `get_settings` è in cache e i moduli la chiamano direttamente invece di
    leggerla da `app.config`: si sposta l'unico campo che scrive su disco. Il
    `monkeypatch` lo rimette a posto a fine test, che altrimenti il primo test
    lascerebbe l'istanza in cache puntata su una cartella cancellata.
    """
    settings = get_settings()
    monkeypatch.setattr(settings, "data_dir", tmp_path)
    settings.ensure_dirs()
    return settings


@pytest.fixture
def client(db, impostazioni):
    """Un client HTTP che parla con **la stessa sessione** della fixture `db`.

    Condividere la sessione è ciò che permette a un test di scrivere una riga
    con `db` e poi rileggerla attraverso una rotta: con due sessioni diverse su
    un database in memoria la rotta non vedrebbe niente.
    """
    from app.main import app

    app.config.update(TESTING=True, DB_SESSION=db, SERVER_NAME="testserver")
    app.test_client_class = TestClient
    with app.test_client() as istanza:
        yield istanza
    app.config.pop("DB_SESSION", None)
    app.config.pop("SERVER_NAME", None)


@pytest.fixture
def utente(db):
    persona = User(
        email="giacinto@example.com", full_name="Giacinto Pappalardo",
        password_hash=hash_password("segreto"), role="admin", active=True,
    )
    db.add(persona)
    db.commit()
    return persona


@pytest.fixture
def auth_client(client, utente):
    risposta = client.post(
        "/login", data={"email": utente.email, "password": "segreto"},
        follow_redirects=False,
    )
    assert risposta.status_code == 303, "l'accesso della fixture non è riuscito"
    return client
