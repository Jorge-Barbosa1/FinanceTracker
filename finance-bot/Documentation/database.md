# Database Design

The bot uses a local SQLite database stored at `finance.db` in the project root.

## Table: `transactions`

Fields:

- `id` - autoincrement primary key
- `user_id` - Discord user ID
- `type` - either `income` or `expense`
- `amount` - positive numeric value
- `category` - transaction category
- `description` - optional text description
- `created_at` - timestamp created automatically in local time

## Functions

### `init_db()`

Creates the `transactions` table if it does not already exist.

### `add_transaction(user_id, transaction_type, amount, category, description=None)`

Inserts a new transaction and returns the created row ID.

### `get_summary(user_id)`

Returns a dictionary with:

- `income`
- `expenses`
- `balance`

The values are calculated from the user's stored rows.

### `get_history(user_id, limit=10)`

Returns the most recent transactions for the user, ordered from newest to oldest.

### `delete_transaction(user_id, transaction_id)`

Deletes a transaction only if it belongs to the given user.

## Implementation notes

- Database calls are wrapped in `asyncio.to_thread` so the Discord bot does not block the event loop.
- The table enforces positive amounts and valid transaction types with SQL checks.
