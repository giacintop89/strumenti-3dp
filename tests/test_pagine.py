"""Il guscio comune: chi entra, chi viene rimandato indietro, la home e la
barra in alto."""

import pytest

ROTTE_PROTETTE = ["/", "/admin/profilo", "/admin/utenti"]


@pytest.mark.parametrize("rotta", ROTTE_PROTETTE)
def test_senza_accesso_si_viene_rimandati_al_login(client, rotta):
    risposta = client.get(rotta, follow_redirects=False)
    assert risposta.status_code == 303
    assert risposta.headers["location"].startswith("/login")


def test_la_pagina_di_accesso_si_apre_senza_essere_autenticati(client):
    risposta = client.get("/login")
    assert risposta.status_code == 200


def test_dopo_l_accesso_la_home_si_apre(auth_client):
    risposta = auth_client.get("/")
    assert risposta.status_code == 200
    assert "Strumenti 3DP" in risposta.text


def test_un_indirizzo_sbagliato_e_una_pagina_non_un_json(auth_client):
    risposta = auth_client.get("/non-esiste")
    assert risposta.status_code == 404
    assert "text/html" in risposta.headers["content-type"]


def test_la_tendina_utente_mostra_l_email(auth_client, utente):
    testo = auth_client.get("/").text
    assert utente.email in testo
