"""Jinja, i filtri, i messaggi di passaggio e l'elenco delle altre app."""

from __future__ import annotations

from pathlib import Path

from flask import Request, Response, render_template, session

from app.config import get_settings
from app.identity import ROLES, iniziali, nome_breve

STATIC_DIR = Path(__file__).parent / "static"
FLASH_KEY = "_flash"


def _asset_version() -> str:
    """Marca temporale degli asset, letta una volta all'avvio.

    Un tablet che ha `app.css` in cache se lo tiene volentieri attraverso un
    aggiornamento, e la segnalazione che arriva dopo è un difetto di
    impaginazione già corretto. Il servizio riparte a ogni aggiornamento, che
    è quando questa viene letta.
    """
    piu_recente = 0.0
    for nome in ("app.css", "menus.js"):
        percorso = STATIC_DIR / nome
        if percorso.exists():
            piu_recente = max(piu_recente, percorso.stat().st_mtime)
    return str(int(piu_recente))


def quota(valore, decimali: int = 2) -> str:
    """Una quota in mm: decimali **fissi**, virgola italiana.

    Diverso da `num`, che gli zeri in coda li toglie. Su un elenco di quote gli
    zeri servono: «2,60» e «2,6» sono lo stesso numero, ma incolonnati sotto
    «10,00» il secondo fa sbagliare la lettura, ed è proprio la colonna di
    quote che si legge confrontandola con se stessa.
    """
    if valore is None:
        return ""
    return f"{valore:.{decimali}f}".replace(".", ",")


def numero(valore, decimali: int = 3) -> str:
    """Un numero da leggere, non da rimettere in un file: virgola italiana."""
    if valore is None:
        return ""
    return f"{valore:.{decimali}f}".rstrip("0").rstrip(".").replace(".", ",") or "0"


def configure_jinja(app) -> None:
    app.jinja_env.filters.update(iniziali=iniziali, nome_breve=nome_breve,
                                 num=numero, quota=quota)
    app.jinja_env.globals.update(ASSET_VERSION=_asset_version(), USER_ROLES=ROLES)


def flash(request: Request, message: str, level: str = "success") -> None:
    messages = session.get(FLASH_KEY, [])
    messages.append({"message": message, "level": level})
    session[FLASH_KEY] = messages


def pop_flashes(request: Request) -> list[dict[str, str]]:
    return session.pop(FLASH_KEY, [])


def tool_aziendali(request: Request) -> list[dict]:
    """Le altre app, con l'indirizzo costruito sull'host di *questa* richiesta.

    Chi guarda è arrivato qui in qualche modo — `pi5studio.local`, l'IP della
    LAN, il nome che gli dà la VPN — e quello stesso host, cambiando porta, è
    l'unico che lo porta anche sulle altre. Un indirizzo scritto in
    configurazione vale solo dalla rete in cui è stato scritto.
    """
    host = request.host.split(":", 1)[0] or "localhost"
    voci = []
    for voce_config in get_settings().app_aziendali:
        voce = dict(voce_config)
        if voce.get("corrente"):
            voce["url"] = "/"
        elif not voce.get("url"):
            voce["url"] = f"http://{host}:{voce.get('porta')}"
        voci.append(voce)
    return voci


def render(request: Request, template: str, status_code: int = 200, **context) -> Response:
    context.setdefault("settings", get_settings())
    context.setdefault("tool_aziendali", tool_aziendali(request))
    context.setdefault("flashes", pop_flashes(request))
    return Response(render_template(template, **context), status=status_code,
                    content_type="text/html; charset=utf-8")


def render_partial(request: Request, template: str, **context) -> Response:
    """Frammento per gli scambi HTMX: non consuma i flash.

    `render` svuota la coda dei messaggi, e un frammento non ha dove
    disegnarli: uno scambio che avviene mentre un messaggio aspetta se lo
    mangia, e quel messaggio non si vede mai più.
    """
    context.setdefault("settings", get_settings())
    context.setdefault("tool_aziendali", tool_aziendali(request))
    return Response(render_template(template, **context),
                    content_type="text/html; charset=utf-8")
