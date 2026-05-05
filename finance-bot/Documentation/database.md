# Database Design

The bot uses a cloud Postgres database configured through `DATABASE_URL`.

## Table: `transactions`

Fields:

- `id` - identity primary key
- `user_id` - Discord user ID
- `type` - either `income` or `expense`
- `amount` - positive numeric value
- `category` - transaction category
- `description` - optional text description
- `accounting_month` - month assigned to the transaction for summaries
- `accounting_year` - year assigned to the transaction for summaries
- `created_at` - timestamp created automatically by Postgres

## Functions

### `init_db()`

Creates the `transactions` table and indexes if they do not already exist.

### `add_transaction(user_id, transaction_type, amount, category, description=None, accounting_month, accounting_year)`

Inserts a new transaction and returns the created row ID.

### `get_summary(user_id, accounting_month, accounting_year)`

Returns a dictionary for the requested accounting month and year with:

- `transaction_count`
- `income`
- `expenses`
- `balance`

The values are calculated from the user's stored rows.

### `get_history(user_id, limit=10, accounting_month=None, accounting_year=None)`

Returns the most recent transactions for the user and requested accounting month,
ordered from newest to oldest.

### `delete_transaction(user_id, transaction_id)`

Deletes a transaction only if it belongs to the given user.

## Implementation notes

- Database calls use an async Postgres connection pool so the Discord bot does not block the event loop.
- The table enforces positive amounts and valid transaction types with SQL checks.
