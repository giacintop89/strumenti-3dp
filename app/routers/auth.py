"""Accesso e uscita, comuni ai due strumenti."""

from __future__ import annotations

from datetime import datetime

from flask import Blueprint, Response, redirect, request
from sqlalchemy import func, select

from app.auth import authenticate, login_user, logout_user
from app.db import get_db
from app.models import User
from app.templating import render

router = Blueprint("auth", __name__)


def _destinazione_sicura(next_: str | None) -> str:
    """Un `next` costruito ad arte manderebbe l'utente fuori dal sito subito
    dopo aver digitato la password, che è il momento in cui si fida di più.
    Si accetta solo un percorso interno: `/qualcosa`, mai `//altrove`."""
    if next_ and next_.startswith("/") and not next_.startswith("//"):
        return next_
    return "/"


@router.get("/login")
def mostra_login() -> Response:
    db = get_db()
    # Se non c'è nessun utente la pagina lo dice, invece di lasciare provare
    # password a vuoto: è il primo avvio, e il rimedio è un comando.
    nessun_utente = db.scalar(select(func.count()).select_from(User)) == 0
    return render(request, "shared/auth/login.html", user=None,
                  next=_destinazione_sicura(request.args.get("next", "/")),
                  no_users=nessun_utente)


@router.post("/login")
def esegui_login() -> Response:
    db = get_db()
    email = request.form.get("email", "")
    password = request.form.get("password", "")
    next_ = request.form.get("next", "/")
    utente = authenticate(db, email, password)
    if utente is None:
        return render(request, "shared/auth/login.html", user=None, status_code=401,
                      error="Credenziali non valide.", email=email,
                      next=_destinazione_sicura(next_))
    utente.last_login_at = datetime.now()
    db.commit()
    login_user(utente)
    return redirect(_destinazione_sicura(next_), code=303)


@router.post("/logout")
def esegui_logout() -> Response:
    # POST e non GET: il logout cambia stato sul server, e un <a> lo renderebbe
    # raggiungibile dal prefetch del browser o da un'immagine remota.
    logout_user()
    return redirect("/login", code=303)
