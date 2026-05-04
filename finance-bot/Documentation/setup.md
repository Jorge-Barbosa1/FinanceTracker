# Bot Setup

This bot is designed to run on Python 3.12.

## Requirements

Install the pinned dependencies from `requirements.txt`:

- `discord.py==2.3.2`
- `python-dotenv==1.0.1`

SQLite is included with Python, so no extra database package is required.

## Environment variables

Create a `.env` file in the project root with the following variable:

- `DISCORD_TOKEN` - your Discord bot token

You can copy `.env.example` and fill in the real value.

## Startup flow

When the bot starts:

1. `bot.py` loads environment variables.
2. The SQLite database is initialised.
3. The transactions cog is loaded.
4. Slash commands are synced with Discord.
5. The bot connects using the token from `.env`.

## Notes

- `.env`, `__pycache__`, and `*.db` files are ignored by Git.
- The bot uses Discord slash commands only for the finance features.
