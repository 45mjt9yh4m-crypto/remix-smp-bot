import asyncio

from bot.config import Config
from main import COGS, RemixBot


def test_all_cogs_load_and_register_commands():
    config = Config(token="x", guild_id=None, mc_address="", staff_role_ids=(), ticket_category_id=None)

    async def run():
        bot = RemixBot(config)
        for cog in COGS:
            await bot.load_extension(cog)
        names = {command.name for command in bot.tree.get_commands()}
        await bot.close()
        return names

    names = asyncio.run(run())
    assert names == {"status", "kick", "ban", "timeout", "untimeout", "clear", "ticket-panel", "dashboard-setup", "parole"}
