"""Comandi di amministrazione.

    python -m app.cli create-admin
"""

from __future__ import annotations

import getpass
import sys

from sqlalchemy import select

from app.auth import hash_password
from app.config import get_settings
from app.db import get_session_factory
from app.identity import normalizza_email, problema_email, problema_nome, problema_password
from app.models import User


def create_admin() -> int:
    get_settings().ensure_dirs()
    email = normalizza_email(input("Email: "))
    if problem := problema_email(email):
        print(problem, file=sys.stderr)
        return 1
    full_name = input("Nome e cognome: ").strip()
    if problem := problema_nome(full_name):
        print(problem, file=sys.stderr)
        return 1
    password = getpass.getpass("Password: ")
    if problem := problema_password(password):
        print(problem, file=sys.stderr)
        return 1
    if password != getpass.getpass("Ripeti la password: "):
        print("Le due password non coincidono.", file=sys.stderr)
        return 1

    with get_session_factory()() as sessione:
        if sessione.scalar(select(User).where(User.email == email)):
            print(f"L'utente {email} esiste già.", file=sys.stderr)
            return 1
        sessione.add(User(
            email=email,
            full_name=full_name,
            password_hash=hash_password(password),
            role="admin",
        ))
        sessione.commit()
    print(f"Creato l'amministratore {email}.")
    return 0


COMANDI = {"create-admin": create_admin}


def main(argv: list[str] | None = None) -> int:
    argomenti = (argv if argv is not None else sys.argv[1:])
    if not argomenti or argomenti[0] not in COMANDI:
        print("Comandi: " + ", ".join(COMANDI), file=sys.stderr)
        return 2
    return COMANDI[argomenti[0]]()


if __name__ == "__main__":
    raise SystemExit(main())
