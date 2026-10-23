"""Comandi di moderazione per lo staff: /kick, /ban, /timeout, /clear."""
from datetime import timedelta

import discord
from discord import app_commands
from discord.ext import commands

MAX_TIMEOUT_MINUTES = 28 * 24 * 60  # limite di Discord: 28 giorni


def can_moderate(moderator: discord.Member, target: discord.Member) -> str | None:
    """Restituisce un messaggio d'errore se `moderator` non può agire su `target`."""
    if target == moderator:
        return "Non puoi farlo su te stesso."
    if target == target.guild.owner:
        return "Non puoi farlo sul proprietario del server."
    if moderator != moderator.guild.owner and target.top_role >= moderator.top_role:
        return "Questo utente ha un ruolo uguale o superiore al tuo."
    if target.top_role >= target.guild.me.top_role:
        return "Il mio ruolo è sotto quello dell'utente: spostalo più in alto nelle impostazioni."
    return None


class Moderation(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def check(self, interaction: discord.Interaction, member: discord.Member) -> bool:
        error = can_moderate(interaction.user, member)
        if error:
            await interaction.response.send_message(error, ephemeral=True)
        return error is None

    @app_commands.command(name="kick", description="Espelle un utente dal server")
    @app_commands.default_permissions(kick_members=True)
    @app_commands.guild_only()
    async def kick(self, interaction: discord.Interaction, utente: discord.Member, motivo: str | None = None) -> None:
        if not await self.check(interaction, utente):
            return
        await utente.kick(reason=f"{interaction.user}: {motivo or 'nessun motivo'}")
        await interaction.response.send_message(f"👢 {utente.mention} è stato espulso. Motivo: {motivo or 'nessuno'}")

    @app_commands.command(name="ban", description="Banna un utente dal server")
    @app_commands.default_permissions(ban_members=True)
    @app_commands.guild_only()
    async def ban(self, interaction: discord.Interaction, utente: discord.Member, motivo: str | None = None) -> None:
        if not await self.check(interaction, utente):
            return
        await utente.ban(reason=f"{interaction.user}: {motivo or 'nessun motivo'}", delete_message_days=0)
        await interaction.response.send_message(f"🔨 {utente.mention} è stato bannato. Motivo: {motivo or 'nessuno'}")

    @app_commands.command(name="timeout", description="Silenzia un utente per un certo numero di minuti")
    @app_commands.default_permissions(moderate_members=True)
    @app_commands.guild_only()
    async def timeout(
        self,
        interaction: discord.Interaction,
        utente: discord.Member,
        minuti: app_commands.Range[int, 1, MAX_TIMEOUT_MINUTES],
        motivo: str | None = None,
    ) -> None:
        if not await self.check(interaction, utente):
            return
        await utente.timeout(timedelta(minutes=minuti), reason=f"{interaction.user}: {motivo or 'nessun motivo'}")
        await interaction.response.send_message(f"🔇 {utente.mention} è in timeout per {minuti} minuti. Motivo: {motivo or 'nessuno'}")

    @app_commands.command(name="untimeout", description="Toglie il timeout a un utente")
    @app_commands.default_permissions(moderate_members=True)
    @app_commands.guild_only()
    async def untimeout(self, interaction: discord.Interaction, utente: discord.Member) -> None:
        await utente.timeout(None, reason=f"{interaction.user}: timeout rimosso")
        await interaction.response.send_message(f"🔊 {utente.mention} può di nuovo scrivere.")

    @app_commands.command(name="clear", description="Cancella gli ultimi messaggi del canale")
    @app_commands.default_permissions(manage_messages=True)
    @app_commands.guild_only()
    async def clear(self, interaction: discord.Interaction, quanti: app_commands.Range[int, 1, 100]) -> None:
        await interaction.response.defer(ephemeral=True)
        deleted = await interaction.channel.purge(limit=quanti)
        await interaction.followup.send(f"🧹 Cancellati {len(deleted)} messaggi.", ephemeral=True)

    async def cog_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError) -> None:
        message = "Non ho i permessi per farlo." if isinstance(getattr(error, "original", None), discord.Forbidden) else f"Errore: {error}"
        if interaction.response.is_done():
            await interaction.followup.send(message, ephemeral=True)
        else:
            await interaction.response.send_message(message, ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Moderation(bot))
