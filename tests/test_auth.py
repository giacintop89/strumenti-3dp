import pytest

from app.auth import authenticate, hash_password, verify_password
from app.models import User


@pytest.fixture
def utente(db):
    u = User(email="gp@example.com", full_name="Giacinto Pappalardo",
             password_hash=hash_password("segreto"), role="admin")
    db.add(u)
    db.commit()
    return u


def test_una_password_giusta_entra(db, utente):
    assert authenticate(db, "gp@example.com", "segreto") is not None


def test_una_password_sbagliata_non_entra(db, utente):
    assert authenticate(db, "gp@example.com", "sbagliata") is None


def test_l_email_non_e_sensibile_alle_maiuscole(db, utente):
    assert authenticate(db, "  GP@EXAMPLE.COM  ", "segreto") is not None


def test_un_utente_disattivato_non_entra(db, utente):
    utente.active = False
    db.commit()
    assert authenticate(db, "gp@example.com", "segreto") is None


def test_una_password_oltre_i_72_byte_e_rifiutata():
    """bcrypt tronca in silenzio a 72 byte: accettarne una più lunga vorrebbe
    dire che solo i primi 72 byte contano, e nessuno lo saprebbe."""
    with pytest.raises(ValueError):
        hash_password("x" * 73)
    assert verify_password("x" * 73, hash_password("x" * 72)) is False


def test_un_login_riuscito_registra_l_ultimo_accesso(client, utente, db):
    assert utente.last_login_at is None
    risposta = client.post(
        "/login", data={"email": " GP@EXAMPLE.COM ", "password": "segreto"},
        follow_redirects=False,
    )
    assert risposta.status_code == 303
    db.refresh(utente)
    assert utente.last_login_at is not None


def test_un_login_fallito_non_registra_l_ultimo_accesso(client, utente, db):
    client.post("/login", data={"email": utente.email, "password": "sbagliata"})
    db.refresh(utente)
    assert utente.last_login_at is None


def test_un_login_fallito_risponde_401_con_il_modulo(client, utente):
    risposta = client.post(
        "/login", data={"email": utente.email, "password": "sbagliata"},
        follow_redirects=False,
    )
    assert risposta.status_code == 401
    assert b"Credenziali non valide" in risposta.data


def test_la_pagina_di_accesso_segnala_l_assenza_di_utenti(client):
    risposta = client.get("/login")
    assert b"Nessun utente presente" in risposta.data


def test_il_logout_cancella_la_sessione(auth_client):
    risposta = auth_client.post("/logout", follow_redirects=False)
    assert risposta.status_code == 303
    with auth_client.session_transaction() as sess:
        assert "user_id" not in sess


def test_next_esterno_viene_ignorato(client, utente):
    risposta = client.post(
        "/login",
        data={"email": utente.email, "password": "segreto", "next": "//evil.example"},
        follow_redirects=False,
    )
    assert risposta.headers["Location"] == "/"
