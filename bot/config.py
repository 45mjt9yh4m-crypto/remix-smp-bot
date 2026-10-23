"""Configurazione letta dalle variabili d'ambiente (o dal file .env)."""
import os
from dataclasses import dataclass

from dotenv import load_dotenv


def _int_or_none(value: str | None) -> int | None:
    value = (value or "").strip()
    return int(value) if value else None


@dataclass(frozen=True)
class Config:
    token: str
    guild_id: int | None
    mc_address: str
    staff_role_id: int | None
    ticket_category_id: int | None


def load_config() -> Config:
    load_dotenv()
    token = os.getenv("DISCORD_TOKEN", "").strip()
    if not token:
        raise SystemExit("Manca DISCORD_TOKEN: copia .env.example in .env e inserisci il token.")
    return Config(
        token=token,
        guild_id=_int_or_none(os.getenv("GUILD_ID")),
        mc_address=os.getenv("MC_ADDRESS", "").strip(),
        staff_role_id=_int_or_none(os.getenv("STAFF_ROLE_ID")),
        ticket_category_id=_int_or_none(os.getenv("TICKET_CATEGORY_ID")),
    )
