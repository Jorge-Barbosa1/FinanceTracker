"""Main entry point for the personal finance tracking Discord bot.

This module loads environment variables, initialises the SQLite database,
registers the bot cogs, and synchronises the slash commands with Discord.
"""

from __future__ import annotations

import os

import discord
from discord.ext import commands
from dotenv import load_dotenv

from db.database import init_db


class FinanceBot(commands.Bot):
    """Discord bot that loads the finance tracking cogs on startup."""

    def __init__(self) -> None:
        intents = discord.Intents.default()
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self) -> None:
        """Prepare the bot before it connects to Discord."""
        await init_db()
        await self.load_extension("cogs.transactions")
        await self.tree.sync()

    async def on_ready(self) -> None:
        """Called when the bot is connected and ready."""
        print(f"Bot online: {self.user} ({self.user.id})")
        print("Slash commands sincronizados!")


async def main() -> None:
    """Start the bot using the token loaded from the .env file."""
    load_dotenv()

    token = os.getenv("DISCORD_TOKEN")
    if not token:
        raise RuntimeError("DISCORD_TOKEN is missing from the environment.")

    bot = FinanceBot()
    await bot.start(token)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
