"""Stato del server Minecraft: comando /status e attività del bot aggiornata da sola."""
import logging

import discord
from discord import app_commands
from discord.ext import commands, tasks
from mcstatus import JavaServer

log = logging.getLogger(__name__)


def format_players(online: int, maximum: int, names: list[str]) -> str:
    text = f"**{online}/{maximum}**"
    if names:
        shown = ", ".join(sorted(names)[:15])
        extra = online - min(len(names), 15)
        text += f"\n{shown}" + (f" e altri {extra}" if extra > 0 else "")
    return text


class Status(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.address = bot.config.mc_address

    async def cog_load(self) -> None:
        if self.address:
            self.update_presence.start()

    async def cog_unload(self) -> None:
        self.update_presence.cancel()

    async def fetch(self):
        server = await JavaServer.async_lookup(self.address)
        return await server.async_status()

    @tasks.loop(minutes=2)
    async def update_presence(self) -> None:
        try:
            status = await self.fetch()
            activity = discord.Game(f"{status.players.online}/{status.players.max} online su Remix SMP")
            await self.bot.change_presence(status=discord.Status.online, activity=activity)
        except Exception as error:
            log.warning("Server Minecraft non raggiungibile: %s", error)
            await self.bot.change_presence(status=discord.Status.dnd, activity=discord.Game("Server offline"))

    @update_presence.before_loop
    async def before_update(self) -> None:
        await self.bot.wait_until_ready()

    @app_commands.command(name="status", description="Mostra lo stato del server Minecraft Remix SMP")
    async def status(self, interaction: discord.Interaction) -> None:
        if not self.address:
            await interaction.response.send_message("MC_ADDRESS non è configurato.", ephemeral=True)
            return
        await interaction.response.defer()
        try:
            status = await self.fetch()
        except Exception:
            embed = discord.Embed(title="Remix SMP", description="🔴 Il server è **offline**.", color=discord.Color.red())
            await interaction.followup.send(embed=embed)
            return
        names = [p.name for p in (status.players.sample or [])]
        embed = discord.Embed(title="Remix SMP", description="🟢 Il server è **online**!", color=discord.Color.green())
        embed.add_field(name="Giocatori", value=format_players(status.players.online, status.players.max, names), inline=False)
        embed.add_field(name="IP", value=f"`{self.address}`")
        embed.add_field(name="Versione", value=status.version.name)
        embed.add_field(name="Ping", value=f"{round(status.latency)} ms")
        await interaction.followup.send(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Status(bot))
