# Slash Commands

All commands are shown to Discord users in English and all responses are ephemeral.

## `/expense <amount> <category> <description?>`

Records an expense for the current user.

- `amount` must be greater than zero.
- `category` is required.
- `description` is optional.
- The transaction is stored with type `expense`.

## `/income <amount> <description?>`

Records income for the current user.

- `amount` must be greater than zero.
- `description` is optional.
- The transaction is stored with type `income`.
- The stored category is `Income`.

## `/summary`

Shows a financial summary embed with:

- total income
- total expenses
- balance

## `/history <limit?>`

Shows the latest transactions for the current user in an embed.

- `limit` defaults to `10`
- `limit` is constrained to the range `1..25`
- Each entry includes the transaction ID, type, amount, category, description, and creation date

## `/delete <transaction_id>`

Deletes a transaction owned by the current user.

- The bot only deletes rows that match both the transaction ID and the user ID.
- If the ID does not belong to the user, the bot reports that nothing was found.
