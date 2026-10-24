from bot.cogs.status import format_players
from bot.cogs.tickets import ticket_channel_name, ticket_owner_id
from bot.config import _flag, _int_list, _int_or_none


def test_ticket_channel_name_is_discord_safe():
    assert ticket_channel_name("Mario_Rossi.99") == "ticket-mario-rossi-99"
    assert ticket_channel_name("___") == "ticket-utente"


def test_ticket_owner_id_roundtrip():
    assert ticket_owner_id("ticket-owner:123456") == 123456
    assert ticket_owner_id("altro topic") is None
    assert ticket_owner_id(None) is None
    assert ticket_owner_id("ticket-owner:abc") is None


def test_format_players():
    assert format_players(0, 20, []) == "**0/20**"
    assert format_players(2, 20, ["zed", "anna"]) == "**2/20**\nanna, zed"
    names = [f"p{i:02d}" for i in range(15)]
    assert format_players(30, 50, names).endswith("e altri 15")


def test_int_or_none():
    assert _int_or_none("") is None
    assert _int_or_none(None) is None
    assert _int_or_none(" 42 ") == 42


def test_int_list():
    assert _int_list(None) == ()
    assert _int_list("1, 22,333,") == (1, 22, 333)


def test_flag():
    assert _flag("1") and _flag("true") and _flag(" Sì ")
    assert not _flag(None) and not _flag("") and not _flag("0") and not _flag("no")


def test_defaults_and_overrides(monkeypatch):
    from bot.config import load_config

    monkeypatch.setattr("bot.config.load_dotenv", lambda: None)
    monkeypatch.setenv("DISCORD_TOKEN", "x")
    for name in ("GUILD_ID", "MC_ADDRESS", "STAFF_ROLE_ID", "TICKET_CATEGORY_ID", "COMING_SOON"):
        monkeypatch.delenv(name, raising=False)
    config = load_config()
    assert config.guild_id == 1359467339816370270
    assert config.mc_address == "remixsmp.net"
    assert len(config.staff_role_ids) == 4
    assert config.coming_soon is True

    monkeypatch.setenv("MC_ADDRESS", "remixsmp.net:25570")
    monkeypatch.setenv("COMING_SOON", "0")
    config = load_config()
    assert config.mc_address == "remixsmp.net:25570"
    assert config.coming_soon is False


def test_find_ticket_category_by_name():
    from types import SimpleNamespace

    import discord

    from bot.cogs.tickets import find_ticket_category

    def category(name):
        item = object.__new__(discord.CategoryChannel)
        item.name = name
        return item

    general, tickets = category("💬 GENERAL"), category("ticket💳")
    guild = SimpleNamespace(categories=[general, tickets], get_channel=lambda _id: None)
    assert find_ticket_category(guild, None, "ticket") is tickets
    assert find_ticket_category(guild, None, "TICKET") is tickets
    assert find_ticket_category(guild, None, "assente") is None
    assert find_ticket_category(guild, None, "") is None
    assert find_ticket_category(guild, None, "", general) is general
    assert find_ticket_category(guild, None, "assente", general) is general
    assert find_ticket_category(guild, None, "ticket", general) is tickets
