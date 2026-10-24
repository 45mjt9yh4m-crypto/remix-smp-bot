"""Comandi di moderazione per lo staff: /kick, /ban, /timeout, /untimeout, /clear.

Ogni azione pubblica un messaggio con la grafica del Remix SMP e, quando possibile,
avvisa l'user in privato prima di applicarla.
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
        return "You can't do that to yourself."
    if target == target.guild.owner:
        return "You can't do that to the server owner."
    if moderator != moderator.guild.owner and target.top_role >= moderator.top_role:
        return "This user has a role equal to or higher than yours."
    if target.top_role >= target.guild.me.top_role:
        return "My role is below this user's: move it higher in the server settings."
    return None


def format_duration(minutes: int) -> str:
    days, rest = divmod(minutes, 24 * 60)
    hours, mins = divmod(rest, 60)
    parts = [f"{days} d" if days else "", f"{hours} h" if hours else "", f"{mins} min" if mins else ""]
    return " ".join(part for part in parts if part)


def action_embed(
    title: str, color: discord.Color, target: discord.abc.User, moderator: discord.abc.User, reason: str | None, duration: str | None = None
) -> discord.Embed:
    embed = brand.embed(title, color=color, thumbnail=target.display_avatar.url)
    embed.add_field(name="👤 User", value=f"{target.mention}\n`{target.name}`")
    embed.add_field(name="🛡️ Staff", value=moderator.mention)
    if duration:
        embed.add_field(name="⏱️ Duration", value=duration)
    embed.add_field(name="📝 Reason", value=reason or "No reason given", inline=False)
    return embed


async def notify(member: discord.Member, title: str, color: discord.Color, reason: str | None, duration: str | None = None) -> None:
    """Avvisa l'utente in privato; se ha i messaggi privati chiusi, pazienza."""
    embed = brand.embed(title, f"This message comes from the **{member.guild.name}** staff.", color)
    if duration:
        embed.add_field(name="⏱️ Duration", value=duration)
    embed.add_field(name="📝 Reason", value=reason or "No reason given", inline=False)
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

    @app_commands.command(name="kick", description="Kick a user from the server")
    @app_commands.default_permissions(kick_members=True)
    @app_commands.guild_only()
    async def kick(self, interaction: discord.Interaction, user: discord.Member, reason: str | None = None) -> None:
        if not await self.check(interaction, user):
            return
        await notify(user, "👢 You have been kicked from Remix SMP", brand.ORANGE, reason)
        await user.kick(reason=f"{interaction.user}: {reason or 'no reason'}")
        await self.announce(interaction, action_embed("👢 User kicked", brand.ORANGE, user, interaction.user, reason))

    @app_commands.command(name="ban", description="Ban a user from the server")
    @app_commands.default_permissions(ban_members=True)
    @app_commands.guild_only()
    async def ban(self, interaction: discord.Interaction, user: discord.Member, reason: str | None = None) -> None:
        if not await self.check(interaction, user):
            return
        await notify(user, "🔨 You have been banned from Remix SMP", brand.RED, reason)
        await user.ban(reason=f"{interaction.user}: {reason or 'no reason'}", delete_message_days=0)
        await self.announce(interaction, action_embed("🔨 User banned", brand.RED, user, interaction.user, reason))

    @app_commands.command(name="timeout", description="Mute a user for a number of minutes")
    @app_commands.default_permissions(moderate_members=True)
    @app_commands.guild_only()
    async def timeout(
        self,
        interaction: discord.Interaction,
        user: discord.Member,
        minutes: app_commands.Range[int, 1, MAX_TIMEOUT_MINUTES],
        reason: str | None = None,
    ) -> None:
        if not await self.check(interaction, user):
            return
        duration = format_duration(minutes)
        await user.timeout(timedelta(minutes=minutes), reason=f"{interaction.user}: {reason or 'no reason'}")
        await notify(user, "🔇 You have been timed out on Remix SMP", brand.PURPLE, reason, duration)
        await self.announce(interaction, action_embed("🔇 User timed out", brand.PURPLE, user, interaction.user, reason, duration))

    @app_commands.command(name="untimeout", description="Remove a user's timeout")
    @app_commands.default_permissions(moderate_members=True)
    @app_commands.guild_only()
    async def untimeout(self, interaction: discord.Interaction, user: discord.Member) -> None:
        await user.timeout(None, reason=f"{interaction.user}: timeout removed")
        embed = brand.embed("🔊 Timeout removed", f"{user.mention} can chat again.", brand.GREEN, thumbnail=user.display_avatar.url)
        embed.add_field(name="🛡️ Staff", value=interaction.user.mention)
        await self.announce(interaction, embed)

    @app_commands.command(name="clear", description="Delete the latest messages in this channel")
    @app_commands.default_permissions(manage_messages=True)
    @app_commands.guild_only()
    async def clear(self, interaction: discord.Interaction, amount: app_commands.Range[int, 1, 100]) -> None:
        await interaction.response.defer(ephemeral=True)
        deleted = await interaction.channel.purge(limit=amount)
        embed = brand.embed("🧹 Cleanup done", f"Deleted **{len(deleted)}** messages.", brand.TEAL, thumbnail=None)
        await interaction.followup.send(embed=embed, files=brand.files(embed), ephemeral=True)

    async def cog_app_command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError) -> None:
        message = "I don't have permission to do that." if isinstance(getattr(error, "original", None), discord.Forbidden) else f"Error: {error}"
        if interaction.response.is_done():
            await interaction.followup.send(message, ephemeral=True)
        else:
            await interaction.response.send_message(message, ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Moderation(bot))
