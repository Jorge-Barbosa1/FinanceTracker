# Bot Setup

This bot is designed to run on Python 3.12.

## Requirements

Install the pinned dependencies from `requirements.txt`:

- `discord.py==2.3.2`
- `python-dotenv==1.0.1`
- `asyncpg==0.29.0`

The bot uses Postgres through `asyncpg`.

## Environment variables

Create a `.env` file in the project root with the following variable:

- `DISCORD_TOKEN` - your Discord bot token
- `DATABASE_URL` - your Supabase Postgres connection string
- `DATABASE_SSL` - optional; defaults to `require` for managed poolers

Use Supabase's Session Pooler connection string for production VM hosting unless
you know the VM has IPv6 access and want to use the direct connection.

## Startup flow

When the bot starts:

1. `bot.py` loads environment variables.
2. The Postgres connection pool is initialised.
3. The transactions cog is loaded.
4. Slash commands are synced with Discord.
5. The bot connects using the token from `.env`.

## Notes

- `.env`, `__pycache__`, and `*.db` files are ignored by Git.
- The bot uses Discord slash commands only for the finance features.

## Oracle VM deployment

On the VM, keep secrets outside Git in `/etc/finance-bot.env`:

```env
DISCORD_TOKEN=your-discord-bot-token-here
DATABASE_URL=postgres://postgres.project-ref:your-password@aws-0-region.pooler.supabase.com:5432/postgres
DATABASE_SSL=require
```

Example `systemd` unit:

```ini
[Unit]
Description=FinanceTrackerBot
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
WorkingDirectory=/opt/finance-bot
EnvironmentFile=/etc/finance-bot.env
ExecStart=/opt/finance-bot/.venv/bin/python /opt/finance-bot/bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```
