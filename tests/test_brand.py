import asyncio

import discord

from bot import brand
from bot.cogs.moderation import action_embed, format_duration
from bot.cogs.tickets import KINDS, TicketControls, TicketPanel


class FakeUser:
    mention = "<@1>"
    name = "steve"

    class display_avatar:
        url = "https://cdn.discordapp.com/avatars/1/a.png"


def test_assets_exist():
    for name in ("logo.png", "icon.png", "banner.png", "avatar.png"):
        assert (brand.ASSETS / name).is_file()


def test_embed_attaches_only_used_assets():
    embed = brand.embed("Titolo", image="banner.png")
    assert sorted(file.filename for file in brand.files(embed)) == ["banner.png", "icon.png", "logo.png"]
    embed = brand.embed("Titolo", thumbnail=FakeUser.display_avatar.url)
    assert [file.filename for file in brand.files(embed)] == ["icon.png"]
    assert embed.footer.text == brand.FOOTER


def test_action_embed_has_user_avatar_and_fields():
    embed = action_embed("🔨 Utente bannato", brand.RED, FakeUser, FakeUser, None, "1 h")
    assert embed.thumbnail.url == FakeUser.display_avatar.url
    assert [field.name for field in embed.fields] == ["👤 Utente", "🛡️ Staff", "⏱️ Durata", "📝 Motivo"]
    assert embed.fields[-1].value == "Nessun motivo indicato"


def test_format_duration():
    assert format_duration(5) == "5 min"
    assert format_duration(90) == "1 h 30 min"
    assert format_duration(2 * 24 * 60 + 60) == "2 g 1 h"


def test_ticket_views_have_persistent_buttons():
    async def build():
        return TicketPanel(bot=None), TicketControls(bot=None)

    panel, controls = asyncio.run(build())
    assert panel.is_persistent() and controls.is_persistent()
    assert [item.custom_id for item in panel.children] == [f"remix:ticket:open:{kind.key}" for kind in KINDS]
    assert all(isinstance(item, discord.ui.Button) for item in controls.children)
