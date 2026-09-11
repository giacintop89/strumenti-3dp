"""Amministrazione: utenti e profilo, condivisi fra gli strumenti."""

from sqlalchemy import select

from app.auth import hash_password, verify_password
from app.models import User


def make_user(db, email="mario@example.com", role="user"):
    user = User(email=email, full_name="Mario Rossi",
                password_hash=hash_password("password123"), role=role)
    db.add(user)
    db.commit()
    return user


def test_un_admin_crea_reimposta_e_disattiva_un_utente(auth_client, db):
    response = auth_client.post("/admin/utenti", data={
        "email": " MARIO@EXAMPLE.COM ", "full_name": "Mario Rossi",
        "password": "password123", "role": "user",
    })
    assert "mario@example.com" in response.text
    target = db.scalar(select(User).where(User.email == "mario@example.com"))
    assert target is not None

    auth_client.post(f"/admin/utenti/{target.id}/password",
                     data={"password": "nuovapassword"})
    db.refresh(target)
    assert verify_password("nuovapassword", target.password_hash)

    auth_client.post(f"/admin/utenti/{target.id}/stato")
    db.refresh(target)
    assert target.active is False


def test_non_puoi_disattivare_ne_eliminare_te_stesso(auth_client, db, utente):
    assert "il tuo stesso account" in auth_client.post(
        f"/admin/utenti/{utente.id}/stato"
    ).text
    assert "il tuo stesso account" in auth_client.post(
        f"/admin/utenti/{utente.id}/elimina"
    ).text
    db.refresh(utente)
    assert utente.active is True


def test_deve_restare_un_amministratore_attivo(auth_client, db):
    target = make_user(db, "secondo@example.com", role="admin")
    # L'admin della sessione è ancora attivo: il secondo può essere disattivato.
    auth_client.post(f"/admin/utenti/{target.id}/stato")
    db.refresh(target)
    assert target.active is False


def test_si_elimina_un_utente_senza_storico(auth_client, db):
    clean = make_user(db, "pulito@example.com")
    auth_client.post(f"/admin/utenti/{clean.id}/elimina")
    assert db.get(User, clean.id) is None


def test_un_utente_normale_non_accede_alla_gestione(client, db):
    target = make_user(db)
    client.post("/login", data={"email": target.email, "password": "password123"})
    assert client.get("/admin/utenti").status_code == 403
    assert client.get("/admin/profilo").status_code == 200


def test_il_profilo_modifica_nome_e_password(auth_client, db, utente):
    auth_client.post("/admin/profilo/nome", data={"full_name": "Giacinto Pappalardo"})
    db.refresh(utente)
    assert utente.full_name == "Giacinto Pappalardo"

    auth_client.post("/admin/profilo/password", data={
        "current_password": "segreto", "new_password": "nuovapassword",
        "confirm_password": "nuovapassword",
    })
    db.refresh(utente)
    assert verify_password("nuovapassword", utente.password_hash)

    auth_client.post("/admin/profilo/password", data={
        "current_password": "nuovapassword", "new_password": "terzapassword",
        "confirm_password": "diversa123",
    })
    db.refresh(utente)
    assert verify_password("nuovapassword", utente.password_hash)


def test_la_tendina_mostra_utenti_solo_all_amministratore(auth_client, client, db):
    testo_admin = auth_client.get("/").text
    assert 'href="/admin/profilo"' in testo_admin
    assert 'href="/admin/utenti"' in testo_admin

    normale = make_user(db, "normale@example.com")
    client.post("/login", data={"email": normale.email, "password": "password123"})
    testo_normale = client.get("/").text
    assert 'href="/admin/profilo"' in testo_normale
    assert 'href="/admin/utenti"' not in testo_normale
