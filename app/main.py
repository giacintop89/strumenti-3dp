"""L'applicazione web Flask. Espone soltanto il guscio comune: gli strumenti
arriveranno con la loro importazione, ognuno sotto il proprio prefisso."""

from datetime import timedelta
from urllib.parse import quote

from flask import Flask, Response, redirect, request

from app.auth import NotAuthenticated, NotAuthorized
from app.config import get_settings
from app.db import close_db
from app.routers import admin, auth, home
from app.templating import configure_jinja, render


def create_app() -> Flask:
    settings = get_settings()
    settings.ensure_dirs()

    app = Flask(__name__, static_folder="static", template_folder="templates")
    app.config.update(
        SECRET_KEY=settings.secret_key,
        SESSION_COOKIE_NAME="strumenti_3dp_session",
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=settings.secure_cookies,
        PERMANENT_SESSION_LIFETIME=timedelta(days=14),
    )
    configure_jinja(app)
    app.teardown_appcontext(close_db)

    app.register_blueprint(auth.router)
    app.register_blueprint(admin.router)
    app.register_blueprint(home.router)

    @app.errorhandler(NotAuthenticated)
    def _non_autenticato(_exc: NotAuthenticated) -> Response:
        target = quote(request.path)
        return redirect(f"/login?next={target}", code=303)

    @app.errorhandler(NotAuthorized)
    def _non_autorizzato(_exc: NotAuthorized) -> Response:
        return render(request, "shared/errors/403.html", status_code=403, user=None)

    @app.errorhandler(404)
    def _non_trovato(_exc: Exception) -> Response:
        """Un indirizzo sbagliato è una pagina, non un corpo generico."""
        return render(request, "shared/errors/404.html", status_code=404,
                      user=None, path=request.path)

    return app


app = create_app()
