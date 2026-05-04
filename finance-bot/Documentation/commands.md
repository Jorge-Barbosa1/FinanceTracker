# Slash Commands

All commands are shown to Discord users in Portuguese and all responses are ephemeral.

## `/gasto <valor> <categoria> <descricao?>`

Registers an expense for the current user.

- `valor` must be greater than zero.
- `categoria` is required.
- `descricao` is optional.
- The transaction is stored with type `expense`.

## `/entrada <valor> <descricao?>`

Registers an income entry for the current user.

- `valor` must be greater than zero.
- `descricao` is optional.
- The transaction is stored with type `income`.
- The stored category is `Receita`.

## `/resumo`

Shows a financial summary embed with:

- total income
- total expenses
- balance

## `/historico <limit?>`

Shows the latest transactions for the current user in an embed.

- `limit` defaults to `10`
- `limit` is constrained to the range `1..25`
- Each entry includes the transaction ID, type, amount, category, description, and creation date

## `/apagar <id>`

Deletes a transaction owned by the current user.

- The bot only deletes rows that match both the transaction ID and the user ID
- If the ID does not belong to the user, the bot reports that nothing was found
