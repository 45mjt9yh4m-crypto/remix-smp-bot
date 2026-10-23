"""Ticket di supporto del Remix SMP.

Il pannello ha un bottone per ogni tipo di ticket; ognuno apre un canale privato tra il giocatore
e lo staff, con domande guidate. Lo staff può prendere in carico il ticket e chiuderlo.
"""
import asyncio
import re
from dataclasses import dataclass

import discord
from discord import app_commands
from discord.ext import commands

from bot import brand

TOPIC_PREFIX = "ticket-owner:"


@dataclass(frozen=True)
class TicketKind:
    key: str
    label: str
    emoji: str
    style: discord.ButtonStyle
    prefix: str
    color: discord.Color
    questions: tuple[str, ...]


KINDS = (
    TicketKind("support", "Supporto", "🛠️", discord.ButtonStyle.primary, "supporto", brand.TEAL,
               ("Qual è il tuo nick in gioco?", "Di cosa hai bisogno? Spiegalo con più dettagli possibile.")),
    TicketKind("report", "Segnala un giocatore", "🚨", discord.ButtonStyle.danger, "segnalazione", brand.RED,
               ("Qual è il nick del giocatore che segnali?", "Cosa ha fatto, e quando?", "Hai prove? Allega screenshot o video.")),
    TicketKind("bug", "Bug", "🐛", discord.ButtonStyle.secondary, "bug", brand.ORANGE,
               ("Cosa succede, e cosa dovrebbe succedere invece?", "Dove e quando è capitato? (coordinate, mondo, orario)", "Se puoi, allega uno screenshot.")),
)


def ticket_channel_name(username: str, prefix: str = "ticket") -> str:
    slug = re.sub(r"[^a-z0-9-]+", "-", username.lower()).strip("-")
    return f"{prefix}-{slug or 'utente'}"[:100]


def ticket_owner_id(topic: str | None) -> int | None:
    if topic and topic.startswith(TOPIC_PREFIX):
        value = topic[len(TOPIC_PREFIX):].split()[0]
        return int(value) if value.isdigit() else None
    return None


def find_open_ticket(guild: discord.Guild, user_id: int) -> discord.TextChannel | None:
    for channel in guild.text_channels:
        if ticket_owner_id(channel.topic) == user_id:
            return channel
    return None


def is_staff(member: discord.Member, channel: discord.abc.GuildChannel, staff_role_ids: tuple[int, ...]) -> bool:
    return channel.permissions_for(member).manage_channels or any(role.id in staff_role_ids for role in member.roles)


class TicketPanel(discord.ui.View):
    """Pannello pubblico. È persistente: i bottoni funzionano anche dopo un riavvio del bot."""

    def __init__(self, bot: commands.Bot):
        super().__init__(timeout=None)
        self.bot = bot
        for kind in KINDS:
            button = discord.ui.Button(label=kind.label, emoji=kind.emoji, style=kind.style, custom_id=f"remix:ticket:open:{kind.key}")
            button.callback = self.opener(kind)
            self.add_item(button)

    def opener(self, kind: TicketKind):
        async def callback(interaction: discord.Interaction) -> None:
            await self.open_ticket(interaction, kind)
        return callback

    async def open_ticket(self, interaction: discord.Interaction, kind: TicketKind) -> None:
        guild, user, config = interaction.guild, interaction.user, self.bot.config
        existing = find_open_ticket(guild, user.id)
        if existing:
            await interaction.response.send_message(f"Hai già un ticket aperto: {existing.mention}", ephemeral=True)
            return

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            user: discord.PermissionOverwrite(view_channel=True, send_messages=True, attach_files=True, read_message_history=True),
            guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, attach_files=True, manage_channels=True),
        }
        staff_roles = [role for role in map(guild.get_role, config.staff_role_ids) if role]
        for role in staff_roles:
            overwrites[role] = discord.PermissionOverwrite(view_channel=True, send_messages=True, attach_files=True, read_message_history=True)
        category = guild.get_channel(config.ticket_category_id) if config.ticket_category_id else None

        channel = await guild.create_text_channel(
            ticket_channel_name(user.name, kind.prefix),
            category=category if isinstance(category, discord.CategoryChannel) else None,
            overwrites=overwrites,
            topic=f"{TOPIC_PREFIX}{user.id} · {kind.label}",
            reason=f"Ticket {kind.label} aperto da {user}",
        )
        questions = "\n".join(f"**{number}.** {question}" for number, question in enumerate(kind.questions, 1))
        embed = brand.embed(
            f"{kind.emoji} {kind.label}",
            f"Ciao {user.mention}, benvenuto nel supporto del **Remix SMP**!\n"
            f"Per aiutarti più in fretta, rispondi a queste domande:\n\n{questions}\n\n"
            "Lo staff ti risponderà il prima possibile.",
            kind.color,
            thumbnail=user.display_avatar.url,
        )
        await channel.send(
            content=" ".join([user.mention, *(role.mention for role in staff_roles)]),
            embed=embed,
            files=brand.files(embed),
            view=TicketControls(self.bot),
        )
        await interaction.response.send_message(f"✅ Ticket creato: {channel.mention}", ephemeral=True)


class TicketControls(discord.ui.View):
    def __init__(self, bot: commands.Bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(label="Prendi in carico", emoji="🙋", style=discord.ButtonStyle.success, custom_id="remix:ticket:claim")
    async def claim_ticket(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        if not is_staff(interaction.user, interaction.channel, self.bot.config.staff_role_ids):
            await interaction.response.send_message("Solo lo staff può prendere in carico un ticket.", ephemeral=True)
            return
        embed = brand.embed("🙋 Ticket preso in carico", f"{interaction.user.mention} si occupa di questo ticket.", brand.GREEN, thumbnail=None)
        await interaction.response.send_message(embed=embed, files=brand.files(embed))

    @discord.ui.button(label="Chiudi ticket", emoji="🔒", style=discord.ButtonStyle.danger, custom_id="remix:ticket:close")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        channel = interaction.channel
        is_owner = ticket_owner_id(channel.topic) == interaction.user.id
        if not (is_owner or is_staff(interaction.user, channel, self.bot.config.staff_role_ids)):
            await interaction.response.send_message("Solo chi ha aperto il ticket o lo staff può chiuderlo.", ephemeral=True)
            return
        embed = brand.embed(
            "🔒 Ticket chiuso",
            f"Chiuso da {interaction.user.mention}. Il canale verrà eliminato tra 5 secondi.\nGrazie per aver contattato lo staff del Remix SMP!",
            brand.NAVY,
            thumbnail=None,
        )
        await interaction.response.send_message(embed=embed, files=brand.files(embed))
        await asyncio.sleep(5)
        await channel.delete(reason=f"Ticket chiuso da {interaction.user}")


class Tickets(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def cog_load(self) -> None:
        self.bot.add_view(TicketPanel(self.bot))
        self.bot.add_view(TicketControls(self.bot))

    @app_commands.command(name="ticket-panel", description="Pubblica in questo canale il pannello per aprire i ticket")
    @app_commands.default_permissions(manage_guild=True)
    @app_commands.guild_only()
    async def ticket_panel(self, interaction: discord.Interaction) -> None:
        kinds = "\n".join(f"{kind.emoji} **{kind.label}**" for kind in KINDS)
        embed = brand.embed(
            "🎫 Supporto Remix SMP",
            "Hai bisogno dello staff? Scegli il tipo di richiesta qui sotto:\n\n"
            f"{kinds}\n\n"
            "Si aprirà un canale privato visibile solo a te e allo staff.",
            brand.TEAL,
            thumbnail=None,
            image="banner.png",
        )
        await interaction.channel.send(embed=embed, files=brand.files(embed), view=TicketPanel(self.bot))
        await interaction.response.send_message("Pannello pubblicato ✅", ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Tickets(bot))
