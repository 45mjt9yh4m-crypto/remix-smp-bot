"""Configurazione letta dalle variabili d'ambiente (o dal file .env)."""
import os
from dataclasses import dataclass

from dotenv import load_dotenv

# Valori predefiniti del Remix SMP (non segreti). Una variabile d'ambiente con lo stesso nome li sostituisce.
DEFAULTS = {
    "GUILD_ID": "1359467339816370270",
    "MC_ADDRESS": "remixsmp.net",  # il giorno dell'apertura: aggiungere ":porta" se non è 25565
    "STAFF_ROLE_ID": "1457200870046302489,1490482020969873479,1440015751028281475,1473345415737905235",
    "MANAGER_ROLE_ID": "1457200870046302489",  # chi può usare la dashboard dei messaggi (oltre al proprietario)
    "TICKET_CATEGORY_ID": "",
    "TICKET_CATEGORY_NAME": "ticket",  # senza ID: la prima categoria che contiene questa parola ("tickets💳")
    "COMING_SOON": "1",  # il giorno dell'apertura: mettere "0"
}


def _env(name: str) -> str:
    value = os.getenv(name)
    return DEFAULTS[name] if value is None else value


def _int_or_none(value: str | None) -> int | None:
    value = (value or "").strip()
    return int(value) if value else None


def _flag(value: str | None) -> bool:
    return (value or "").strip().lower() in {"1", "true", "yes", "si", "sì", "on"}


def _int_list(value: str | None) -> tuple[int, ...]:
    return tuple(int(part) for part in (value or "").replace(" ", "").split(",") if part)


@dataclass(frozen=True)
class Config:
    token: str
    guild_id: int | None
    mc_address: str
    staff_role_ids: tuple[int, ...]
    ticket_category_id: int | None
    ticket_category_name: str = ""
    manager_role_ids: tuple[int, ...] = ()
    coming_soon: bool = False


def load_config() -> Config:
    load_dotenv()
    token = os.getenv("DISCORD_TOKEN", "").strip()
    if not token:
        raise SystemExit("Manca DISCORD_TOKEN: copia .env.example in .env e inserisci il token.")
    return Config(
        token=token,
        guild_id=_int_or_none(_env("GUILD_ID")),
        mc_address=_env("MC_ADDRESS").strip(),
        staff_role_ids=_int_list(_env("STAFF_ROLE_ID")),
        ticket_category_id=_int_or_none(_env("TICKET_CATEGORY_ID")),
        ticket_category_name=_env("TICKET_CATEGORY_NAME").strip(),
        coming_soon=_flag(_env("COMING_SOON")),
        manager_role_ids=_int_list(_env("MANAGER_ROLE_ID")),
    )
