"""Main entry point for the personal finance tracking Discord bot.

This module loads environment variables, initialises the Postgres database,
registers the bot cogs, and synchronises the slash commands with Discord.
"""

from __future__ import annotations

import asyncio
from contextlib import suppress
import os

from aiohttp import web
import discord
from discord.ext import commands
from dotenv import load_dotenv

from db.database import close_db, init_db, ping_db


async def health_check(request: web.Request) -> web.Response:
    """Return a simple response for Render health checks."""
    return web.Response(text="ok\n")


async def start_health_server() -> web.AppRunner:
    """Start the tiny HTTP server required by Render Web Services."""
    app = web.Application()
    app.router.add_get("/", health_check)
    app.router.add_get("/health", health_check)

    runner = web.AppRunner(app)
    await runner.setup()

    port = int(os.getenv("PORT", "10000"))
    site = web.TCPSite(runner, host="0.0.0.0", port=port)
    await site.start()
    print(f"Health server listening on 0.0.0.0:{port}", flush=True)

    return runner


class FinanceBot(commands.Bot):
    """Discord bot that loads the finance tracking cogs on startup."""

    def __init__(self) -> None:
        intents = discord.Intents.default()
        super().__init__(command_prefix="!", intents=intents)
        self._db_health_task: asyncio.Task[None] | None = None

    async def setup_hook(self) -> None:
        """Prepare the bot before it connects to Discord."""
        await init_db()
        await self.load_extension("cogs.transactions")
        await self.tree.sync()
        self._db_health_task = asyncio.create_task(self._keep_database_alive())

    async def on_ready(self) -> None:
        """Called when the bot is connected and ready."""
        print(f"Bot online: {self.user} ({self.user.id})", flush=True)
        print("Slash commands sincronizados!", flush=True)

    async def close(self) -> None:
        """Close Discord and database resources cleanly."""
        if self._db_health_task is not None:
            self._db_health_task.cancel()
            with suppress(asyncio.CancelledError):
                await self._db_health_task
        await close_db()
        await super().close()

    async def _keep_database_alive(self) -> None:
        """Periodically check the database connection."""
        while not self.is_closed():
            await asyncio.sleep(30 * 60)
            try:
                await ping_db()
            except Exception as exc:
                print(f"Database health check failed: {exc!r}", flush=True)


async def main() -> None:
    """Start the bot using secrets loaded from the environment."""
    load_dotenv()

    print("Starting FinanceTrackerBot...", flush=True)

    token = os.getenv("DISCORD_TOKEN")
    if not token:
        raise RuntimeError("DISCORD_TOKEN is missing from the environment.")
    print("DISCORD_TOKEN is configured.", flush=True)

    if not os.getenv("DATABASE_URL"):
        raise RuntimeError("DATABASE_URL is missing from the environment.")
    print("DATABASE_URL is configured.", flush=True)

    health_runner = await start_health_server()
    bot = FinanceBot()

    try:
        print("Starting Discord bot...", flush=True)
        await bot.start(token)
    except Exception as exc:
        print(f"Fatal startup error: {type(exc).__name__}: {exc!r}", flush=True)
        raise
    finally:
        await health_runner.cleanup()
        if not bot.is_closed():
            await bot.close()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
