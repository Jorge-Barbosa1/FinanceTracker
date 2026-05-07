# Project Overview

This project is a personal finance tracking Discord bot built with Python 3.12, discord.py, and Postgres.

## Purpose

The bot lets a user record income and expenses, review a financial summary with top expense categories, inspect recent transactions, generate spending charts, and delete entries by ID.

## Main parts

- `bot.py` starts the bot, loads environment variables, initialises the Postgres pool, loads the cog, and syncs slash commands.
- `cogs/transactions.py` defines the slash commands and formats user-facing Discord responses.
- `db/database.py` manages the Postgres database and provides async helpers for inserts, summaries, history, and deletion.

## Behaviour

- All command responses are sent with `ephemeral=True`.
- Summary and history are presented using Discord embeds.
- Spending charts are generated as PNG attachments.
- Transaction data is stored in Postgres.
- The bot token is read from a `.env` file through `python-dotenv`.
