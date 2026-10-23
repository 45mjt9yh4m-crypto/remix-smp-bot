"""Comandi di moderazione per lo staff: /kick, /ban, /timeout, /untimeout, /clear.

Ogni azione pubblica un messaggio con la grafica del Remix SMP e, quando possibile,
avvisa l'utente in privato prima di applicarla.
"""
from datetime import timedelta

import discord
from discord import app_commands
from discord.ext import commands

from bot import brand

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


def format_duration(minutes: int) -> str:
    days, rest = divmod(minutes, 24 * 60)
    hours, mins = divmod(rest, 60)
    parts = [f"{days} g" if days else "", f"{hours} h" if hours else "", f"{mins} min" if mins else ""]
    return " ".join(part for part in parts if part)


def action_embed(
    title: str, color: discord.Color, target: discord.abc.User, moderator: discord.abc.User, reason: str | None, duration: str | None = None
) -> discord.Embed:
    embed = brand.embed(title, color=color, thumbnail=target.display_avatar.url)
    embed.add_field(name="👤 Utente", value=f"{target.mention}\n`{target.name}`")
    embed.add_field(name="🛡️ Staff", value=moderator.mention)
    if duration:
        embed.add_field(name="⏱️ Durata", value=duration)
    embed.add_field(name="📝 Motivo", value=reason or "Nessun motivo indicato", inline=False)
    return embed


async def notify(member: discord.Member, title: str, color: discord.Color, reason: str | None, duration: str | None = None) -> None:
    """Avvisa l'utente in privato; se ha i messaggi privati chiusi, pazienza."""
    embed = brand.embed(title, f"Questo messaggio arriva dallo staff del **{member.guild.name}**.", color)
    if duration:
        embed.add_field(name="⏱️ Durata", value=duration)
    embed.add_field(name="📝 Motivo", value=reason or "Nessun motivo indicato", inline=False)
    try:
        await member.send(embed=embed, files=brand.files(embed))
    except discord.HTTPException:
        pass


class Moderation(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def check(self, interaction: discord.Interaction, member: discord.Member) -> bool:
        error = can_moderate(interaction.user, member)
        if error:
            await interaction.response.send_message(error, ephemeral=True)
        return error is None

    async def announce(self, interaction: discord.Interaction, embed: discord.Embed) -> None:
        await interaction.response.send_message(embed=embed, files=brand.files(embed))

    @app_commands.command(name="kick", description="Espelle un utente dal server")
    @app_commands.default_permissions(kick_members=True)
    @app_commands.guild_only()
    async def kick(self, interaction: discord.Interaction, utente: discord.Member, motivo: str | None = None) -> None:
        if not await self.check(interaction, utente):
            return
        await notify(utente, "👢 Sei stato espulso dal Remix SMP", brand.ORANGE, motivo)
        await utente.kick(reason=f"{interaction.user}: {motivo or 'nessun motivo'}")
        await self.announce(interaction, action_embed("👢 Utente espulso", brand.ORANGE, utente, interaction.user, motivo))

    @app_commands.command(name="ban", description="Banna un utente dal server")
    @app_commands.default_permissions(ban_members=True)
    @app_commands.guild_only()
    async def ban(self, interaction: discord.Interaction, utente: discord.Member, motivo: str | None = None) -> None:
        if not await self.check(interaction, utente):
            return
        await notify(utente, "🔨 Sei stato bannato dal Remix SMP", brand.RED, motivo)
        await utente.ban(reason=f"{interaction.user}: {motivo or 'nessun motivo'}", delete_message_days=0)
        await self.announce(interaction, action_embed("🔨 Utente bannato", brand.RED, utente, interaction.user, motivo))

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
        duration = format_duration(minuti)
        await utente.timeout(timedelta(minutes=minuti), reason=f"{interaction.user}: {motivo or 'nessun motivo'}")
        await notify(utente, "🔇 Sei in timeout sul Remix SMP", brand.PURPLE, motivo, duration)
        await self.announce(interaction, action_embed("🔇 Utente in timeout", brand.PURPLE, utente, interaction.user, motivo, duration))

    @app_commands.command(name="untimeout", description="Toglie il timeout a un utente")
    @app_commands.default_permissions(moderate_members=True)
    @app_commands.guild_only()
    async def untimeout(self, interaction: discord.Interaction, utente: discord.Member) -> None:
        await utente.timeout(None, reason=f"{interaction.user}: timeout rimosso")
        embed = brand.embed("🔊 Timeout rimosso", f"{utente.mention} può di nuovo scrivere.", brand.GREEN, thumbnail=utente.display_avatar.url)
        embed.add_field(name="🛡️ Staff", value=interaction.user.mention)
        await self.announce(interaction, embed)

    @app_commands.command(name="clear", description="Cancella gli ultimi messaggi del canale")
    @app_commands.default_permissions(manage_messages=True)
    @app_commands.guild_only()
    async def clear(self, interaction: discord.Interaction, quanti: app_commands.Range[int, 1, 100]) -> None:
        await interaction.response.defer(ephemeral=True)
        deleted = await interaction.channel.purge(limit=quanti)
        embed = brand.embed("🧹 Pulizia completata", f"Cancellati **{len(deleted)}** messaggi.", brand.TEAL, thumbnail=None)
        await interaction.followup.send(embed=embed, files=brand.files(embed), ephemeral=True)

    async def cog_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError) -> None:
        message = "Non ho i permessi per farlo." if isinstance(getattr(error, "original", None), discord.Forbidden) else f"Errore: {error}"
        if interaction.response.is_done():
            await interaction.followup.send(message, ephemeral=True)
        else:
            await interaction.response.send_message(message, ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Moderation(bot))
