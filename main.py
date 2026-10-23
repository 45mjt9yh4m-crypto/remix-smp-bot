"""Avvio del bot Discord di Remix SMP: `python main.py`."""
import logging

import discord
from discord.ext import commands

from bot.config import Config, load_config

COGS = ("bot.cogs.status", "bot.cogs.moderation", "bot.cogs.tickets")


class RemixBot(commands.Bot):
    def __init__(self, config: Config):
        intents = discord.Intents.default()
        super().__init__(command_prefix=commands.when_mentioned, intents=intents)
        self.config = config

    async def setup_hook(self) -> None:
        for cog in COGS:
            await self.load_extension(cog)
        # Con GUILD_ID gli slash command compaiono subito in quel server;
        # senza, vengono registrati globalmente (può volerci fino a un'ora).
        if self.config.guild_id:
            guild = discord.Object(id=self.config.guild_id)
            self.tree.copy_global_to(guild=guild)
            synced = await self.tree.sync(guild=guild)
        else:
            synced = await self.tree.sync()
        logging.info("Registrati %d slash command", len(synced))

    async def on_ready(self) -> None:
        logging.info("Online come %s (id %s)", self.user, self.user.id)


def main() -> None:
    config = load_config()
    discord.utils.setup_logging(level=logging.INFO)
    RemixBot(config).run(config.token, log_handler=None)


if __name__ == "__main__":
    main()
