"""Coercizione dei valori che arrivano dal form.

Tutto ciò che arriva da un `<form>` è una stringa, e può essere qualunque
stringa. Qui si trasforma in numeri, e la virgola decimale italiana si accetta
perché è come la si digita su una tastiera in officina.
"""

from __future__ import annotations


def clean(value: str | None, max_length: int | None = None) -> str:
    testo = (value or "").strip()
    return testo[:max_length] if max_length else testo


def parse_float(value: str | None, default: float | None = None) -> float | None:
    """`"62,5"` e `"62.5"` sono lo stesso numero. Vuoto o illeggibile: default.

    Non solleva: un campo scritto male non deve far esplodere una pagina, deve
    tornare al suo valore di riposo e lasciare che sia la validazione a dire
    che cosa manca.
    """
    testo = (value or "").strip().replace(",", ".")
    if not testo:
        return default
    try:
        return float(testo)
    except ValueError:
        return default


def parse_int(value: str | None, default: int, minimo: int, massimo: int) -> int:
    testo = (value or "").strip()
    try:
        numero = int(testo)
    except ValueError:
        return default
    return max(minimo, min(massimo, numero))


def parse_bool(value: str | None) -> bool:
    """Una casella di spunta non spuntata non compare affatto nel POST."""
    return (value or "").strip().lower() in ("on", "true", "1", "si", "sì")


def parse_choice(value: str | None, allowed, default: str) -> str:
    testo = (value or "").strip()
    return testo if testo in allowed else default
