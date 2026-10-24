"""Filtro parole: cancella i messaggi con parole vietate e mette in timeout chi le scrive.

Le parole si gestiscono da Discord con /words e sono salvate in data/parole.json sul server
(fuori da git, quindi gli aggiornamenti del bot non le toccano). Lo staff che può gestire
i messaggi non viene filtrato. Serve l'intent "Message Content" attivo nel Developer Portal.
"""
import json
import logging
import re
import unicodedata
from datetime import timedelta
from pathlib import Path

import discord
from discord import app_commands
from discord.ext import commands

from bot import brand
from bot.cogs.moderation import format_duration, notify

log = logging.getLogger(__name__)

WORDS_FILE = Path(__file__).resolve().parent.parent.parent / "data" / "parole.json"
# Lista di partenza, usata finché sul server non esiste data/parole.json (cioè prima del primo /parole).
DEFAULT_WORDS_FILE = Path(__file__).resolve().parent.parent / "parole_iniziali.json"
LEET = str.maketrans({"0": "o", "1": "i", "3": "e", "4": "a", "5": "s", "7": "t", "@": "a", "$": "s"})


def normalize(text: str) -> str:
    """Minuscole, senza accenti, con i trucchi più comuni (c4zz0 → cazzo, p.a.r.o.l.a → parola)."""
    text = unicodedata.normalize("NFKD", text.lower())
    text = "".join(char for char in text if not unicodedata.combining(char)).translate(LEET)
    text = re.sub(r"(?<=\w)[.\-_*](?=\w)", "", text)  # p.a.r.o.l.a
    return re.sub(r"(\w)\1{2,}", r"\1", text)  # ciaooooo → ciao


def _pattern(word: str) -> str:
    """Una parola intera; con * in fondo vale anche come inizio di parola (es. stupid* → stupido, stupida)."""
    prefix = word.endswith("*")
    core = re.escape(normalize(word.rstrip("*")))
    return rf"\b{core}\w*" if prefix else rf"\b{core}\b"


def find_banned(text: str, words: list[str]) -> str | None:
    """La prima parola vietata presente nel testo, oppure None."""
    clean = normalize(text)
    squashed = re.sub(r"\s+", "", clean)  # p a r o l a
    for word in words:
        pattern = _pattern(word)
        if re.search(pattern, clean) or (len(word.rstrip("*")) >= 4 and re.search(pattern.replace(r"\b", "", 1), squashed)):
            return word
    return None


def load_words(path: Path = WORDS_FILE, default: Path = DEFAULT_WORDS_FILE) -> list[str]:
    for source in (path, default):
        try:
            return json.loads(source.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
    return []


def save_words(words: list[str], path: Path = WORDS_FILE) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(sorted(set(words)), ensure_ascii=False, indent=2), encoding="utf-8")


class WordFilter(commands.Cog):
    words_group = app_commands.Group(
        name="words",
        description="Manage the banned words",
        default_permissions=discord.Permissions(manage_guild=True),
        guild_only=True,
    )

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.words = load_words()
        self.timeout_minutes = bot.config.filter_timeout_minutes

    def exempt(self, message: discord.Message) -> bool:
        author = message.author
        return (
            message.guild is None
            or author.bot
            or not isinstance(author, discord.Member)
            or message.channel.permissions_for(author).manage_messages
        )

    async def check(self, message: discord.Message) -> None:
        if not self.words or self.exempt(message):
            return
        word = find_banned(message.content, self.words)
        if word is None:
            return
        author = message.author
        try:
            await message.delete()
        except discord.HTTPException as error:
            log.warning("Non riesco a cancellare un messaggio con parola vietata: %s", error)
            return
        duration = format_duration(self.timeout_minutes) if self.timeout_minutes else None
        if self.timeout_minutes:
            try:
                await author.timeout(timedelta(minutes=self.timeout_minutes), reason=f"Word filter: {word}")
            except discord.HTTPException as error:
                log.warning("Non riesco a mettere in timeout %s: %s", author, error)
                duration = None
        embed = brand.embed(
            "🚫 Message removed",
            f"{author.mention}, that kind of language isn't allowed on **Remix SMP**."
            + (f"\nYou are timed out for **{duration}**." if duration else ""),
            brand.RED,
            thumbnail=author.display_avatar.url,
        )
        await message.channel.send(embed=embed, files=brand.files(embed), delete_after=10)
        await notify(author, "🚫 You used a banned word", brand.RED, f"Banned word in #{message.channel.name}", duration)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        await self.check(message)

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message) -> None:
        if before.content != after.content:
            await self.check(after)

    @words_group.command(name="add", description="Ban a word (put * at the end to ban its variants too)")
    async def add(self, interaction: discord.Interaction, word: app_commands.Range[str, 2, 50]) -> None:
        word = word.strip().lower()
        if word in self.words:
            await interaction.response.send_message(f"`{word}` is already banned.", ephemeral=True)
            return
        self.words = sorted({*self.words, word})
        save_words(self.words)
        await interaction.response.send_message(f"✅ `{word}` added to the banned words ({len(self.words)} in total).", ephemeral=True)

    @words_group.command(name="remove", description="Remove a word from the banned words")
    async def remove(self, interaction: discord.Interaction, word: str) -> None:
        word = word.strip().lower()
        if word not in self.words:
            await interaction.response.send_message(f"`{word}` isn't in the list.", ephemeral=True)
            return
        self.words = [item for item in self.words if item != word]
        save_words(self.words)
        await interaction.response.send_message(f"🗑️ `{word}` removed from the banned words.", ephemeral=True)

    @remove.autocomplete("word")
    async def remove_autocomplete(self, interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
        return [app_commands.Choice(name=word, value=word) for word in self.words if current.lower() in word][:25]

    @words_group.command(name="list", description="Show the banned words (only you can see it)")
    async def list_words(self, interaction: discord.Interaction) -> None:
        text = ", ".join(f"`{word}`" for word in self.words) or "No banned words yet."
        embed = brand.embed("🚫 Banned words", text[:4000], brand.RED, thumbnail=None)
        await interaction.response.send_message(embed=embed, files=brand.files(embed), ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(WordFilter(bot))
