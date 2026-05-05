# Slash Commands

All commands are shown to Discord users in English and all responses are ephemeral.

## `/expense <amount> <category> <description?> <month?> <year?>`

Records an expense for the current user.

- `amount` must be greater than zero.
- `category` is required.
- `description` is optional.
- `month` and `year` are optional; if omitted, the current month and year are used.
- The transaction is stored with type `expense`.

## `/income <amount> <description?> <month?> <year?>`

Records income for the current user.

- `amount` must be greater than zero.
- `description` is optional.
- `month` and `year` are optional; if omitted, the current month and year are used.
- The transaction is stored with type `income`.
- The stored category is `Income`.

## `/summary <month?> <year?>`

Shows a financial summary embed for the requested accounting month. If no month
or year is provided, the current month and year are used.

- total income
- total expenses
- balance
- If the user has no transactions in that month, the bot reports that nothing was found.

## `/history <limit?> <month?> <year?>`

Shows the latest transactions for the requested accounting month in an embed.

- `limit` defaults to `10`
- `limit` is constrained to the range `1..25`
- `month` and `year` default to the current month and year
- Each entry includes the transaction ID, type, amount, category, description, and creation date

## `/delete <transaction_id>`

Deletes a transaction owned by the current user.

- The bot only deletes rows that match both the transaction ID and the user ID.
- If the ID does not belong to the user, the bot reports that nothing was found.
