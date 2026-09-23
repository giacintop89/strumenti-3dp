# Allinea 3DP alla nuova mappa porte

- Completion time: 2026-09-23 22:13:21 CEST
- Sequence: `salva-rapido`

## Summary

Allinea 3DP alla nuova mappa porte.

## Principal changes

- `app/config.py`
- `config/.env.example`
- `deploy/strumenti-3dp.service`

## Verification

- `.venv/bin/python -m pytest -q -c config/pyproject.toml` — passed.
- `git diff --check` — passed.
