from bot.cogs.status import format_players
from bot.cogs.tickets import ticket_channel_name, ticket_owner_id
from bot.config import _int_or_none


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
