"""La pagina iniziale della suite: un indice verso i due strumenti.

Non è il «/» di nessuno dei due tool di origine — quello lo teneva la pagina
di conversione — perché qui i due convivono, ognuno sotto il proprio prefisso.
"""

from __future__ import annotations

from flask import Blueprint, Response, request

from app.auth import current_user
from app.templating import render

router = Blueprint("home", __name__)


@router.get("/")
def pagina() -> Response:
    user = current_user()
    return render(request, "shared/index.html", user=user)
