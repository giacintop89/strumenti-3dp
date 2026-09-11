import bcrypt
from datetime import datetime

from flask import session
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.identity import normalizza_email
from app.models import User

# bcrypt silently truncates at 72 bytes; rejecting longer input is clearer than
# accepting a password only the first 72 bytes of which matter.
MAX_PASSWORD_BYTES = 72
SESSION_KEY = "user_id"


class NotAuthenticated(Exception):
    """Raised by the access guard; the handler redirects to /login."""


class NotAuthorized(Exception):
    """Authenticated but lacking the required role."""


def hash_password(password: str) -> str:
    encoded = password.encode("utf-8")
    if len(encoded) > MAX_PASSWORD_BYTES:
        raise ValueError("La password non può superare i 72 byte.")
    return bcrypt.hashpw(encoded, bcrypt.gensalt()).decode("ascii")


def verify_password(password: str, password_hash: str) -> bool:
    encoded = password.encode("utf-8")
    if len(encoded) > MAX_PASSWORD_BYTES:
        return False
    try:
        return bcrypt.checkpw(encoded, password_hash.encode("ascii"))
    except ValueError:
        # Malformed or empty hash in the DB.
        return False


def authenticate(db: Session, email: str, password: str) -> User | None:
    user = db.scalar(select(User).where(User.email == normalizza_email(email)))
    if user is None or not user.active:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


def login_user(user: User) -> None:
    session.clear()
    session[SESSION_KEY] = user.id
    session.permanent = True


def logout_user() -> None:
    session.clear()


def current_user() -> User:
    db = get_db()
    user_id = session.get(SESSION_KEY)
    if not user_id:
        raise NotAuthenticated
    user = db.get(User, user_id)
    if user is None or not user.active:
        session.clear()
        raise NotAuthenticated
    # Una sessione emessa prima dell'introduzione di `last_login_at` è ancora
    # una prova di credenziali valide. Registriamo il primo accesso che la
    # riutilizza, così gli account già autenticati non restano con «—» per
    # sempre nella pagina Utenti.
    if user.last_login_at is None:
        user.last_login_at = datetime.now()
        db.commit()
    return user


def require_admin() -> User:
    user = current_user()
    if not user.is_admin:
        raise NotAuthorized
    return user
