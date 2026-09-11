"""Regole di identità condivise fra i due strumenti."""

import re


EMAIL_RE = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
ROLES = {"admin": "Amministratore", "user": "Utente"}


def normalizza_email(valore: str) -> str:
    return valore.strip().lower()


def problema_email(valore: str) -> str | None:
    email = normalizza_email(valore)
    if not email:
        return "L'email è obbligatoria."
    if len(email) > 160:
        return "L'email non può superare 160 caratteri."
    if EMAIL_RE.fullmatch(email) is None:
        return "Inserisci un indirizzo email valido."
    return None


def problema_password(valore: str) -> str | None:
    if len(valore) < 8:
        return "La password deve avere almeno 8 caratteri."
    return None


def problema_nome(valore: str) -> str | None:
    nome = valore.strip()
    if not nome:
        return "Il nome e cognome sono obbligatori."
    if len(nome) > 120:
        return "Il nome e cognome non possono superare 120 caratteri."
    return None


def iniziali(nome: str) -> str:
    parti = nome.strip().split()
    if len(parti) >= 2:
        return (parti[0][0] + parti[1][0]).upper()
    return parti[0][:2].upper() if parti else ""


def nome_breve(nome: str) -> str:
    parti = nome.strip().split()
    return parti[0] if parti else ""
