"""Stato del server Minecraft: comando /status e attività del bot aggiornata da sola.

Con COMING_SOON attivo il server non viene interrogato e il bot annuncia l'apertura imminente.
"""
import logging

import discord
from discord import app_commands
from discord.ext import commands, tasks
from mcstatus import JavaServer

from bot import brand

log = logging.getLogger(__name__)


def format_players(online: int, maximum: int, names: list[str]) -> str:
    text = f"**{online}/{maximum}**"
    if names:
        shown = ", ".join(sorted(names)[:15])
        extra = online - min(len(names), 15)
        text += f"\n{shown}" + (f" and {extra} more" if extra > 0 else "")
    return text


class Status(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.address = bot.config.mc_address
        self.coming_soon = bot.config.coming_soon

    async def cog_load(self) -> None:
        if self.address or self.coming_soon:
            self.update_presence.start()

    async def cog_unload(self) -> None:
        self.update_presence.cancel()

    async def fetch(self):
        server = await JavaServer.async_lookup(self.address)
        return await server.async_status()

    @tasks.loop(minutes=2)
    async def update_presence(self) -> None:
        if self.coming_soon:
            await self.bot.change_presence(status=discord.Status.online, activity=discord.Game("🚀 Opening soon!"))
            return
        try:
            status = await self.fetch()
            activity = discord.Game(f"{status.players.online}/{status.players.max} online on Remix SMP")
            await self.bot.change_presence(status=discord.Status.online, activity=activity)
        except Exception as error:
            log.warning("Server Minecraft non raggiungibile: %s", error)
            await self.bot.change_presence(status=discord.Status.dnd, activity=discord.Game("Server offline"))

    @update_presence.before_loop
    async def before_update(self) -> None:
        await self.bot.wait_until_ready()

    def coming_soon_embed(self) -> discord.Embed:
        embed = brand.embed(
            "🚀 Opening soon!",
            "**Remix SMP** isn't open yet, but it's coming soon.\n"
            "Keep an eye on the announcements so you don't miss the launch date!",
            brand.PURPLE,
            thumbnail=None,
            image="banner.png",
        )
        if self.address:
            embed.add_field(name="🌐 IP", value=f"`{self.address}`")
        return embed

    @app_commands.command(name="status", description="Show the status of the Remix SMP Minecraft server")
    async def status(self, interaction: discord.Interaction) -> None:
        if self.coming_soon:
            embed = self.coming_soon_embed()
            await interaction.response.send_message(embed=embed, files=brand.files(embed))
            return
        if not self.address:
            await interaction.response.send_message("MC_ADDRESS is not configured.", ephemeral=True)
            return
        await interaction.response.defer()
        try:
            status = await self.fetch()
        except Exception:
            embed = brand.embed("🔴 Server offline", "**Remix SMP** can't be reached right now. Try again in a bit!", brand.RED)
            embed.add_field(name="🌐 IP", value=f"`{self.address}`")
            await interaction.followup.send(embed=embed, files=brand.files(embed))
            return
        names = [p.name for p in (status.players.sample or [])]
        embed = brand.embed("🟢 Server online", "**Remix SMP** is open: jump in and play!", brand.GREEN)
        embed.add_field(name="👥 Players", value=format_players(status.players.online, status.players.max, names), inline=False)
        embed.add_field(name="🌐 IP", value=f"`{self.address}`")
        embed.add_field(name="🧩 Version", value=status.version.name)
        embed.add_field(name="📶 Ping", value=f"{round(status.latency)} ms")
        await interaction.followup.send(embed=embed, files=brand.files(embed))


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Status(bot))
