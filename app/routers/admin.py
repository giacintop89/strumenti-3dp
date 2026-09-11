"""Amministrazione: utenti e profilo. Guscio comune, non di uno strumento —
sta sotto `/admin`, non sotto il prefisso di un domani strumento.

`user_delete_blockers` guarda le tabelle in cui uno strumento firma il proprio
storico con `user_id`. `_TABELLE_STORICO` è vuota finché non c'è ancora nessun
strumento: un domani, ogni strumento importato ci aggiunge la propria — vedi
`app/routers/admin.py` di strumenti-cnc per il caso con due strumenti.
"""

from flask import Blueprint, Response, abort, redirect, request
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import sorting
from app.auth import current_user, hash_password, require_admin, verify_password
from app.db import get_db
from app.forms import clean, parse_choice
from app.identity import ROLES, normalizza_email, problema_email, problema_nome, problema_password
from app.models import User
from app.templating import flash, render

router = Blueprint("admin", __name__, url_prefix="/admin")

USER_SORTS = {
    "email": sorting.Column((User.email,)),
    "full_name": sorting.Column((User.full_name, User.email)),
    "role": sorting.Column((User.role, User.email)),
    "active": sorting.Column((User.active, User.email), desc_first=True),
    "last_login_at": sorting.Column((User.last_login_at, User.email), desc_first=True),
}

# Le tabelle che tengono la firma di chi ha lavorato, con l'etichetta da
# mostrare nel messaggio di blocco. Vuota finché non c'è ancora uno strumento.
_TABELLE_STORICO: tuple[tuple[type, str], ...] = ()


def user_delete_blockers(db: Session) -> dict[int, dict[str, int]]:
    blockers: dict[int, dict[str, int]] = {}
    for modello, etichetta in _TABELLE_STORICO:
        righe = db.execute(
            select(modello.user_id, func.count())
            .where(modello.user_id.is_not(None))
            .group_by(modello.user_id)
        ).all()
        for user_id, count in righe:
            blockers.setdefault(user_id, {})[etichetta] = count
    return blockers


def _target(db: Session, user_id: int) -> User:
    target = db.get(User, user_id)
    if target is None:
        abort(404)
    return target


@router.get("/utenti")
def users_list() -> Response:
    db = get_db()
    user = require_admin()
    sort = sorting.of(request, USER_SORTS, default="email")
    users = list(db.scalars(sort.apply(select(User))))
    return render(request, "shared/admin/users.html", user=user, users=users,
                  sort=sort, blockers=user_delete_blockers(db))


@router.post("/utenti")
def user_create() -> Response:
    db = get_db()
    require_admin()
    email = request.form.get("email", "")
    full_name = request.form.get("full_name", "")
    password = request.form.get("password", "")
    role = request.form.get("role", "user")
    address = normalizza_email(email)
    name = clean(full_name, 120)
    for problem in (problema_email(address), problema_nome(name), problema_password(password)):
        if problem:
            flash(request, problem, "error")
            return redirect("/admin/utenti", code=303)
    try:
        new_user = User(email=address, full_name=name,
                        password_hash=hash_password(password),
                        role=parse_choice(role, ROLES, "user"))
    except ValueError as exc:
        flash(request, str(exc), "error")
        return redirect("/admin/utenti", code=303)
    db.add(new_user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        flash(request, f"L'email «{address}» esiste già.", "error")
        return redirect("/admin/utenti", code=303)
    flash(request, f"Utente «{address}» creato.")
    return redirect("/admin/utenti", code=303)


@router.post("/utenti/<int:user_id>/password")
def user_reset_password(user_id: int) -> Response:
    db = get_db()
    require_admin()
    password = request.form.get("password", "")
    target = _target(db, user_id)
    if problem := problema_password(password):
        flash(request, problem, "error")
        return redirect("/admin/utenti", code=303)
    try:
        target.password_hash = hash_password(password)
    except ValueError as exc:
        flash(request, str(exc), "error")
        return redirect("/admin/utenti", code=303)
    db.commit()
    flash(request, f"Password di «{target.email}» aggiornata.")
    return redirect("/admin/utenti", code=303)


@router.post("/utenti/<int:user_id>/stato")
def user_toggle_active(user_id: int) -> Response:
    db = get_db()
    user = require_admin()
    target = _target(db, user_id)
    if target.id == user.id:
        flash(request, "Non puoi disattivare il tuo stesso account.", "error")
        return redirect("/admin/utenti", code=303)
    if target.active and target.is_admin:
        remaining = db.scalar(select(func.count()).select_from(User).where(
            User.role == "admin", User.active.is_(True), User.id != target.id
        ))
        if not remaining:
            flash(request, "Deve restare almeno un amministratore attivo.", "error")
            return redirect("/admin/utenti", code=303)
    target.active = not target.active
    db.commit()
    flash(request, f"Utente «{target.email}» {'attivato' if target.active else 'disattivato'}.")
    return redirect("/admin/utenti", code=303)


@router.post("/utenti/<int:user_id>/elimina")
def user_delete(user_id: int) -> Response:
    db = get_db()
    user = require_admin()
    target = _target(db, user_id)
    if target.id == user.id:
        flash(request, "Non puoi eliminare il tuo stesso account.", "error")
        return redirect("/admin/utenti", code=303)
    blockers = user_delete_blockers(db).get(target.id, {})
    if blockers:
        detail = ", ".join(f"{count} {label}" for label, count in blockers.items())
        flash(request, f"Impossibile eliminare «{target.email}»: ha {detail}. "
              "Disattivalo invece: non potrà più entrare e il suo storico resterà leggibile.",
              "error")
        return redirect("/admin/utenti", code=303)
    email = target.email
    db.delete(target)
    db.commit()
    flash(request, f"Utente «{email}» eliminato.")
    return redirect("/admin/utenti", code=303)


@router.get("/profilo")
def profile() -> Response:
    user = current_user()
    return render(request, "shared/admin/profile.html", user=user)


@router.post("/profilo/nome")
def change_own_name() -> Response:
    db = get_db()
    user = current_user()
    full_name = request.form.get("full_name", "")
    name = clean(full_name, 120)
    if problem := problema_nome(name):
        flash(request, problem, "error")
        return redirect("/admin/profilo", code=303)
    user.full_name = name
    db.commit()
    flash(request, "Nome e cognome aggiornati.")
    return redirect("/admin/profilo", code=303)


@router.post("/profilo/password")
def change_own_password() -> Response:
    db = get_db()
    user = current_user()
    current_password = request.form.get("current_password", "")
    new_password = request.form.get("new_password", "")
    confirm_password = request.form.get("confirm_password", "")
    if not verify_password(current_password, user.password_hash):
        flash(request, "Password attuale errata.", "error")
        return redirect("/admin/profilo", code=303)
    if new_password != confirm_password:
        flash(request, "Le due password nuove non coincidono.", "error")
        return redirect("/admin/profilo", code=303)
    if problem := problema_password(new_password):
        flash(request, problem, "error")
        return redirect("/admin/profilo", code=303)
    try:
        user.password_hash = hash_password(new_password)
    except ValueError as exc:
        flash(request, str(exc), "error")
        return redirect("/admin/profilo", code=303)
    db.commit()
    flash(request, "Password aggiornata.")
    return redirect("/admin/profilo", code=303)
