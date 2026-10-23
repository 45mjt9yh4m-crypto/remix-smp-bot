"""Grafica del Remix SMP per i messaggi del bot: colori, logo e immagini allegate."""
from datetime import datetime, timezone
from pathlib import Path

import discord

ASSETS = Path(__file__).resolve().parent.parent / "assets"

TEAL = discord.Color(0x029DA9)
BLUE = discord.Color(0x035085)
PURPLE = discord.Color(0x6884F5)
NAVY = discord.Color(0x01293E)
GREEN = discord.Color(0x3BD16F)
RED = discord.Color(0xE5484D)
ORANGE = discord.Color(0xF5A524)

NAME = "Remix SMP"
FOOTER = "Remix SMP • remixsmp.net"
_ATTACHMENT = "attachment://"


def _url(source: str) -> str:
    """Un nome di file in assets/ diventa un allegato; un URL resta com'è."""
    return source if "://" in source else _ATTACHMENT + source


def embed(
    title: str,
    description: str | None = None,
    color: discord.Color = TEAL,
    *,
    thumbnail: str | None = "logo.png",
    image: str | None = None,
) -> discord.Embed:
    result = discord.Embed(title=title, description=description, color=color, timestamp=datetime.now(timezone.utc))
    result.set_author(name=NAME, icon_url=_url("icon.png"))
    result.set_footer(text=FOOTER, icon_url=_url("icon.png"))
    if thumbnail:
        result.set_thumbnail(url=_url(thumbnail))
    if image:
        result.set_image(url=_url(image))
    return result


def files(*embeds: discord.Embed) -> list[discord.File]:
    """Le immagini di assets/ usate dagli embed, da allegare al messaggio (nuove a ogni invio)."""
    names: list[str] = []
    for item in embeds:
        for url in (item.author.icon_url, item.footer.icon_url, item.thumbnail.url, item.image.url):
            if url and url.startswith(_ATTACHMENT) and url[len(_ATTACHMENT):] not in names:
                names.append(url[len(_ATTACHMENT):])
    return [discord.File(ASSETS / name, filename=name) for name in names]
