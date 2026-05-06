# FinanceTrackerBot

FinanceTrackerBot is a personal finance Discord bot that lets a user record income and expenses, review monthly summaries, inspect recent activity, and delete transactions by ID. It stores data in Postgres, exposes slash commands only, and is ready for deployment on Render.

## What it does

- Records income and expenses for the current Discord user.
- Groups entries by accounting month and year.
- Shows monthly summaries with income, expenses, and balance.
- Lists recent transactions in a Discord embed.
- Generates a PNG spending chart by category.
- Deletes transactions owned by the same user.
- Sends all command responses as ephemeral messages.

## Tech stack

- Python 3.12
- discord.py 2.3.2
- asyncpg 0.29.0
- aiohttp 3.9.5 for the Render health check server
- python-dotenv 1.0.1 for local environment loading
- Postgres, typically through Supabase poolers

## Project layout

- [render.yaml](render.yaml) - Render service configuration
- [finance-bot/bot.py](finance-bot/bot.py) - application entry point and startup flow
- [finance-bot/cogs/transactions.py](finance-bot/cogs/transactions.py) - slash commands for finance actions
- [finance-bot/db/database.py](finance-bot/db/database.py) - Postgres pool, schema, and query helpers
- [finance-bot/Documentation/](finance-bot/Documentation/) - detailed project docs

## Features

The bot currently supports the following slash commands:

- `/expense` - record an expense with amount, category, optional description, and optional month/year
- `/income` - record income with amount, optional description, and optional month/year
- `/summary` - show a monthly financial summary
- `/history` - show recent transactions for a month
- `/chart` - show a monthly spending chart as a PNG attachment
- `/delete` - remove a transaction by ID if it belongs to the current user

The bot also starts a small HTTP health server so Render can keep the service alive and check whether it is healthy.

## Setup

### 1. Prerequisites

- Python 3.12
- A Discord application and bot token
- A Postgres database URL, such as a Supabase connection string

### 2. Install dependencies

From the repository root, go into the application folder:

```bash
cd finance-bot
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Configure environment variables

Create a `.env` file in `finance-bot/` using `.env.example` as the template:

```env
DISCORD_TOKEN=your-discord-bot-token-here
DATABASE_URL=postgres://postgres.project-ref:your-password@aws-0-region.pooler.supabase.com:5432/postgres
DATABASE_SSL=require
APP_TIMEZONE=Europe/Lisbon
```

Environment variables:

- `DISCORD_TOKEN` - required Discord bot token
- `DATABASE_URL` - required Postgres connection string
- `DATABASE_SSL` - optional; defaults to `require`
- `APP_TIMEZONE` - optional; defaults to `Europe/Lisbon`

### 4. Run the bot

```bash
python bot.py
```

On startup, the bot loads the environment, initialises the database, syncs slash commands, and connects to Discord.

## Deployment

The repo includes a [Render service definition](render.yaml) that starts the bot from `finance-bot/`.

Important runtime values for Render:

- `PYTHON_VERSION=3.12.7`
- `DISCORD_TOKEN`
- `DATABASE_URL`

The service also exposes `/health` for Render health checks.

## Database

The bot stores transactions in a single `transactions` table with:

- `id`
- `user_id`
- `type`
- `amount`
- `category`
- `description`
- `accounting_month`
- `accounting_year`
- `created_at`

The schema is created automatically on startup if it does not already exist.

## Documentation

More detailed notes live in [finance-bot/Documentation/](finance-bot/Documentation/):

- [Overview](finance-bot/Documentation/overview.md)
- [Setup](finance-bot/Documentation/setup.md)
- [Commands](finance-bot/Documentation/commands.md)
- [Database](finance-bot/Documentation/database.md)
- [Structure](finance-bot/Documentation/structure.md)

## Next feature ideas

If you want to evolve this bot, the most natural next steps are:

- category-based analytics and monthly charts
- recurring transactions
- budget limits and alerts
- export to CSV or Excel
- transaction editing and partial updates
- richer filtering for history by category or type

## Security note

Never commit `.env` or database credentials to Git. Use the sample file as a template and keep real secrets in environment variables or a secrets manager.
