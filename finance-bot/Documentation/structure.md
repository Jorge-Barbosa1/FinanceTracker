# Project Structure

This page documents the files and folders that make up the bot.

## Root files

- `bot.py` - application entry point and startup orchestration
- `.env.example` - sample environment variables file
- `.gitignore` - ignores local secrets, cache files, and local database files
- `requirements.txt` - pinned Python dependencies

## `cogs/`

- `cogs/__init__.py` - marks the directory as a Python package
- `cogs/transactions.py` - slash commands for finance operations

## `db/`

- `db/__init__.py` - marks the directory as a Python package
- `db/database.py` - Postgres schema creation and transaction helpers

## `Documentation/`

- `README.md` - documentation index
- `overview.md` - project purpose and behaviour
- `setup.md` - installation and startup notes
- `commands.md` - command reference
- `database.md` - Postgres schema and data access details
