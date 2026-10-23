"""Ticket di supporto: un pannello con un bottone che apre un canale privato con lo staff."""
import asyncio
import re

import discord
from discord import app_commands
from discord.ext import commands

TOPIC_PREFIX = "ticket-owner:"


def ticket_channel_name(username: str) -> str:
    slug = re.sub(r"[^a-z0-9-]+", "-", username.lower()).strip("-")
    return f"ticket-{slug or 'utente'}"[:100]


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


class TicketPanel(discord.ui.View):
    """Pannello pubblico. È persistente: il bottone funziona anche dopo un riavvio del bot."""

    def __init__(self, bot: commands.Bot):
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(label="Apri un ticket", emoji="🎫", style=discord.ButtonStyle.primary, custom_id="remix:ticket:open")
    async def open_ticket(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        guild, user, config = interaction.guild, interaction.user, self.bot.config
        existing = find_open_ticket(guild, user.id)
        if existing:
            await interaction.response.send_message(f"Hai già un ticket aperto: {existing.mention}", ephemeral=True)
            return

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            user: discord.PermissionOverwrite(view_channel=True, send_messages=True, attach_files=True, read_message_history=True),
            guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_channels=True),
        }
        staff_roles = [role for role in map(guild.get_role, config.staff_role_ids) if role]
        for role in staff_roles:
            overwrites[role] = discord.PermissionOverwrite(view_channel=True, send_messages=True, read_message_history=True)
        category = guild.get_channel(config.ticket_category_id) if config.ticket_category_id else None

        channel = await guild.create_text_channel(
            ticket_channel_name(user.name),
            category=category if isinstance(category, discord.CategoryChannel) else None,
            overwrites=overwrites,
            topic=f"{TOPIC_PREFIX}{user.id}",
            reason=f"Ticket aperto da {user}",
        )
        embed = discord.Embed(
            title="🎫 Ticket di supporto",
            description=f"Ciao {user.mention}! Scrivi qui il tuo problema, lo staff ti risponderà il prima possibile.\n"
            "Quando hai finito premi **Chiudi ticket**.",
            color=discord.Color.blurple(),
        )
        await channel.send(content=" ".join(role.mention for role in staff_roles) or None, embed=embed, view=TicketControls())
        await interaction.response.send_message(f"Ticket creato: {channel.mention}", ephemeral=True)


class TicketControls(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Chiudi ticket", emoji="🔒", style=discord.ButtonStyle.danger, custom_id="remix:ticket:close")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        channel = interaction.channel
        is_owner = ticket_owner_id(channel.topic) == interaction.user.id
        if not (is_owner or channel.permissions_for(interaction.user).manage_channels):
            await interaction.response.send_message("Solo chi ha aperto il ticket o lo staff può chiuderlo.", ephemeral=True)
            return
        await interaction.response.send_message("🔒 Ticket chiuso, il canale verrà eliminato tra 5 secondi.")
        await asyncio.sleep(5)
        await channel.delete(reason=f"Ticket chiuso da {interaction.user}")


class Tickets(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def cog_load(self) -> None:
        self.bot.add_view(TicketPanel(self.bot))
        self.bot.add_view(TicketControls())

    @app_commands.command(name="ticket-panel", description="Pubblica in questo canale il pannello per aprire i ticket")
    @app_commands.default_permissions(manage_guild=True)
    @app_commands.guild_only()
    async def ticket_panel(self, interaction: discord.Interaction) -> None:
        embed = discord.Embed(
            title="Supporto Remix SMP",
            description="Hai un problema, vuoi segnalare un giocatore o fare una domanda allo staff?\n"
            "Premi il bottone qui sotto: si aprirà un canale privato solo per te e lo staff.",
            color=discord.Color.blurple(),
        )
        await interaction.channel.send(embed=embed, view=TicketPanel(self.bot))
        await interaction.response.send_message("Pannello pubblicato ✅", ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Tickets(bot))
