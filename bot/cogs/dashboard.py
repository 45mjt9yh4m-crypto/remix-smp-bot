"""Dashboard dei messaggi: un canale privato per il proprietario e i manager.

Il pannello apre un modulo (titolo, testo, colore, immagine); il bot mostra l'anteprima,
si sceglie il canale e l'eventuale menzione, e il messaggio parte con la grafica del Remix SMP.
"""
from dataclasses import dataclass, replace

import discord
from discord import app_commands
from discord.ext import commands

from bot import brand

COLORS = {
    "teal": ("Teal (Remix)", brand.TEAL),
    "blue": ("Blue", brand.BLUE),
    "purple": ("Purple", brand.PURPLE),
    "green": ("Green", brand.GREEN),
    "orange": ("Orange", brand.ORANGE),
    "red": ("Red", brand.RED),
}
IMAGES = {
    "logo": "Small logo in the top right",
    "banner": "Big Remix SMP banner",
    "none": "No image",
}
MENTIONS = {"none": "No mention", "everyone": "@everyone", "here": "@here"}


@dataclass(frozen=True)
class Draft:
    title: str
    text: str
    color: str = "teal"
    image: str = "logo"
    image_url: str = ""


def build_announcement(draft: Draft) -> discord.Embed:
    """L'embed del messaggio; un link immagine personalizzato vince sulla scelta del menu."""
    url = draft.image_url.strip()
    thumbnail = "logo.png" if draft.image == "logo" and not url else None
    image = url or ("banner.png" if draft.image == "banner" else None)
    return brand.embed(draft.title, draft.text, COLORS[draft.color][1], thumbnail=thumbnail, image=image)


def mention_text(mention: str) -> str | None:
    return {"everyone": "@everyone", "here": "@here"}.get(mention)


def is_manager(member: discord.Member, manager_role_ids: tuple[int, ...]) -> bool:
    return member == member.guild.owner or member.guild_permissions.administrator or any(role.id in manager_role_ids for role in member.roles)


def _select(options: dict, chosen: str, label_of=lambda value: value) -> discord.ui.Select:
    return discord.ui.Select(
        options=[discord.SelectOption(label=label_of(value), value=key, default=key == chosen) for key, value in options.items()],
    )


class AnnouncementForm(discord.ui.Modal):
    def __init__(self, bot: commands.Bot, draft: Draft | None = None):
        super().__init__(title="New message · Remix SMP")
        self.bot = bot
        draft = draft or Draft(title="", text="")
        self.title_input = discord.ui.TextInput(placeholder="E.g. 🎉 Saturday event!", default=draft.title or None, max_length=256)
        self.text_input = discord.ui.TextInput(
            style=discord.TextStyle.paragraph,
            placeholder="The message text. You can use **bold**, lists and links.",
            default=draft.text or None,
            max_length=4000,
        )
        self.color_select = _select(COLORS, draft.color, lambda value: value[0])
        self.image_select = _select(IMAGES, draft.image)
        self.url_input = discord.ui.TextInput(
            placeholder="https://... (optional, replaces the image chosen above)", default=draft.image_url or None, required=False, max_length=500
        )
        self.add_item(discord.ui.Label(text="Title", component=self.title_input))
        self.add_item(discord.ui.Label(text="Text", component=self.text_input))
        self.add_item(discord.ui.Label(text="Color", component=self.color_select))
        self.add_item(discord.ui.Label(text="Image", component=self.image_select))
        self.add_item(discord.ui.Label(text="Custom image link", component=self.url_input))

    async def on_submit(self, interaction: discord.Interaction) -> None:
        url = self.url_input.value.strip()
        if url and not url.startswith(("http://", "https://")):
            await interaction.response.send_message("The image link must start with https://", ephemeral=True)
            return
        draft = Draft(
            title=self.title_input.value.strip(),
            text=self.text_input.value.strip(),
            color=self.color_select.values[0],
            image=self.image_select.values[0],
            image_url=url,
        )
        await AnnouncementPreview(self.bot, draft).show(interaction)


class AnnouncementPreview(discord.ui.View):
    """Anteprima visibile solo a chi la crea: scegli canale e menzione, poi Invia."""

    def __init__(self, bot: commands.Bot, draft: Draft):
        super().__init__(timeout=30 * 60)
        self.bot = bot
        self.draft = draft
        self.channel: discord.app_commands.AppCommandChannel | None = None
        self.mention = "none"

    async def show(self, interaction: discord.Interaction) -> None:
        embed = build_announcement(self.draft)
        await interaction.response.send_message(
            "👀 **Preview** (only you can see it). Pick the channel and press **Send**.",
            embed=embed,
            files=brand.files(embed),
            view=self,
            ephemeral=True,
        )

    @discord.ui.select(cls=discord.ui.ChannelSelect, placeholder="📍 Which channel should I send it to?", channel_types=[discord.ChannelType.text, discord.ChannelType.news])
    async def pick_channel(self, interaction: discord.Interaction, select: discord.ui.ChannelSelect) -> None:
        self.channel = select.values[0]
        await interaction.response.defer()

    @discord.ui.select(placeholder="🔔 Mention: none", options=[discord.SelectOption(label=label, value=key) for key, label in MENTIONS.items()])
    async def pick_mention(self, interaction: discord.Interaction, select: discord.ui.Select) -> None:
        self.mention = select.values[0]
        await interaction.response.defer()

    @discord.ui.button(label="Send", emoji="📤", style=discord.ButtonStyle.success)
    async def send(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        if self.channel is None:
            await interaction.response.send_message("Pick the channel from the 📍 menu first.", ephemeral=True)
            return
        channel = interaction.guild.get_channel(self.channel.id)
        if channel is None or not channel.permissions_for(interaction.guild.me).send_messages:
            await interaction.response.send_message(f"I can't post in {self.channel.mention}: check the bot's permissions.", ephemeral=True)
            return
        embed = build_announcement(self.draft)
        message = await channel.send(
            content=mention_text(self.mention),
            embed=embed,
            files=brand.files(embed),
            allowed_mentions=discord.AllowedMentions(everyone=self.mention != "none"),
        )
        self.stop()
        await interaction.response.edit_message(content=f"✅ Message sent in {channel.mention}: {message.jump_url}", embed=None, attachments=[], view=None)

    @discord.ui.button(label="Edit", emoji="✏️", style=discord.ButtonStyle.secondary)
    async def edit(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        self.stop()
        await interaction.response.send_modal(AnnouncementForm(self.bot, self.draft))

    @discord.ui.button(label="Cancel", emoji="✖️", style=discord.ButtonStyle.danger)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        self.stop()
        await interaction.response.edit_message(content="Message cancelled.", embed=None, attachments=[], view=None)


class DashboardPanel(discord.ui.View):
    """Pannello nel canale della dashboard. È persistente: funziona anche dopo un riavvio."""

    def __init__(self, bot: commands.Bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(label="New message", emoji="📢", style=discord.ButtonStyle.primary, custom_id="remix:dashboard:new")
    async def new_message(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        if not is_manager(interaction.user, self.bot.config.manager_role_ids):
            await interaction.response.send_message("Only the owner and managers can use the dashboard.", ephemeral=True)
            return
        await interaction.response.send_modal(AnnouncementForm(self.bot))


def panel_embed() -> discord.Embed:
    return brand.embed(
        "📢 Message dashboard",
        "From here you can have the bot send a Remix SMP styled message to any channel.\n\n"
        "**1.** Press **New message** and write the title and text\n"
        "**2.** Pick the color and image\n"
        "**3.** Check the preview, pick the channel and press **Send**",
        brand.PURPLE,
    )


class Dashboard(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def cog_load(self) -> None:
        self.bot.add_view(DashboardPanel(self.bot))

    @app_commands.command(name="dashboard-setup", description="Create the private message dashboard channel (owner and managers)")
    @app_commands.default_permissions(administrator=True)
    @app_commands.guild_only()
    async def dashboard_setup(self, interaction: discord.Interaction) -> None:
        guild = interaction.guild
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, attach_files=True, embed_links=True),
        }
        for role in map(guild.get_role, self.bot.config.manager_role_ids):
            if role:
                overwrites[role] = discord.PermissionOverwrite(view_channel=True, read_message_history=True, send_messages=True)
        channel = await guild.create_text_channel("📢・dashboard", overwrites=overwrites, reason=f"Dashboard created by {interaction.user}")
        embed = panel_embed()
        await channel.send(embed=embed, files=brand.files(embed), view=DashboardPanel(self.bot))
        await interaction.response.send_message(f"✅ Dashboard created: {channel.mention}", ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Dashboard(bot))
