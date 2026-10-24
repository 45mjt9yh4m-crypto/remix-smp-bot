import asyncio

import discord

from bot.cogs.dashboard import AnnouncementForm, AnnouncementPreview, DashboardPanel, Draft, build_announcement, mention_text
from bot.cogs.tickets import KINDS, TicketForm


def run(factory):
    async def build():
        return factory()
    return asyncio.run(build())


def test_ticket_form_always_asks_nick_and_edition():
    for kind in KINDS:
        form = run(lambda: TicketForm(bot=None, kind=kind))
        labels = [item.text for item in form.children]
        assert labels[:2] == ["Your in-game nickname", "What do you play on?"]
        assert len(labels) == 2 + len(kind.questions) <= 5
        assert form.nick.required and form.edition.required
        assert [option.value for option in form.edition.options] == ["Java", "Bedrock"]
        assert len(form.title) <= 45


def test_announcement_form_prefills_when_editing():
    draft = Draft(title="Evento", text="Sabato alle 21", color="red", image="banner", image_url="")
    form = run(lambda: AnnouncementForm(bot=None, draft=draft))
    assert len(form.children) == 5
    assert form.title_input.default == "Evento"
    assert [option.value for option in form.color_select.options if option.default] == ["red"]
    assert [option.value for option in form.image_select.options if option.default] == ["banner"]


def test_build_announcement_images():
    assert build_announcement(Draft("T", "x", image="logo")).thumbnail.url == "attachment://logo.png"
    banner = build_announcement(Draft("T", "x", image="banner"))
    assert banner.image.url == "attachment://banner.png" and banner.thumbnail.url is None
    custom = build_announcement(Draft("T", "x", image="logo", image_url="https://example.com/a.png"))
    assert custom.image.url == "https://example.com/a.png" and custom.thumbnail.url is None
    assert build_announcement(Draft("T", "x", image="none")).image.url is None


def test_mentions():
    assert mention_text("none") is None
    assert mention_text("everyone") == "@everyone"


def test_dashboard_views():
    panel = run(lambda: DashboardPanel(bot=None))
    assert panel.is_persistent()
    preview = run(lambda: AnnouncementPreview(bot=None, draft=Draft("T", "x")))
    assert any(isinstance(item, discord.ui.ChannelSelect) for item in preview.children)
