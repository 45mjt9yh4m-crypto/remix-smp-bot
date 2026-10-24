"""Avvio del bot Discord di Remix SMP: `python main.py`."""
import logging
import subprocess

import discord
from discord.ext import commands

from bot.brand import ASSETS
from bot.config import Config, load_config

COGS = ("bot.cogs.status", "bot.cogs.moderation", "bot.cogs.tickets", "bot.cogs.dashboard")


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
        if self.user.avatar is None:
            # Al primo avvio il bot si mette da solo il logo del Remix SMP come foto profilo.
            try:
                await self.user.edit(avatar=(ASSETS / "avatar.png").read_bytes())
                logging.info("Foto profilo impostata")
            except discord.HTTPException as error:
                logging.warning("Impossibile impostare la foto profilo: %s", error)


def version() -> str:
    """Il commit di GitHub da cui gira il bot, per controllare che un aggiornamento sia arrivato."""
    try:
        result = subprocess.run(["git", "log", "-1", "--format=%h %s"], capture_output=True, text=True, timeout=5)
        return result.stdout.strip() or "sconosciuta"
    except (OSError, subprocess.SubprocessError):
        return "sconosciuta"


def main() -> None:
    config = load_config()
    discord.utils.setup_logging(level=logging.INFO)
    logging.info("Versione del bot: %s", version())
    RemixBot(config).run(config.token, log_handler=None)


if __name__ == "__main__":
    main()
