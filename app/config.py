"""Configurazione del guscio comune. Le costanti di uno strumento andranno nel
suo pacchetto sotto ``core/``, non qui: questo file vale per il guscio e per
tutto quello che gli strumenti condivideranno (accesso, utenti, menu della
suite)."""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file="config/.env", extra="ignore")

    secret_key: str = "dev-only-insecure-key-change-me"
    data_dir: Path = Path("./data")

    max_upload_mb: int = 8

    # La barra «tool aziendali»: le altre app su questo stesso Pi. Si scrive
    # la **porta**, non l'indirizzo intero: `pi5studio.local` è un nome mDNS,
    # vive sulla rete locale e attraverso una VPN non risolve. L'host giusto è
    # quello da cui la richiesta è arrivata, e lo sa il server a ogni richiesta.
    app_aziendali: list[dict[str, object]] = [
        {"nome": "Gestionale azienda", "porta": 8080},
        {"nome": "Note condivise", "porta": 8082},
        {"nome": "Scanner bandi", "porta": 8081},
        {"nome": "Strumenti CNC", "porta": 8083},
        {"nome": "Strumenti 3DP", "porta": 8084, "corrente": True},
    ]

    # Marca il cookie di sessione `Secure`. Va acceso solo quando ogni strada
    # per arrivare qui è HTTPS: con Gunicorn ancora raggiungibile sulla sua
    # porta, un `true` scollega chiunque usi quell'indirizzo e il sintomo è
    # identico a una password sbagliata.
    secure_cookies: bool = False

    @property
    def db_path(self) -> Path:
        return self.data_dir / "strumenti-3dp.db"

    @property
    def database_url(self) -> str:
        return f"sqlite:///{self.db_path}"

    @property
    def max_upload_bytes(self) -> int:
        return self.max_upload_mb * 1024 * 1024

    def ensure_dirs(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)


@lru_cache
def get_settings() -> Settings:
    return Settings()
