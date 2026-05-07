# Todo Roadmap

Short notes on how to implement the bot's next features.

## Low impact, low effort

### Export CSV/Excel

Add a `/export <month?> <year?>` command that queries transactions for the selected period, generates a CSV or XLSX file, and sends it as an attachment or via DM.

- Reuse the history query or create a dedicated helper in `db/database.py`.
- Generate the file in memory with `csv` or `openpyxl`.
- If the file is small enough, send it as an ephemeral attachment.
- If Discord response limits become a problem, send it by DM instead.

### Budget alerts

Create a per-category budget system with `/budget set <category> <amount>` and alerts when the user reaches a certain percentage of the limit.

- Add a new `budgets` table with `user_id`, `category`, `limit_amount`, and `alert_threshold`.
- When recording an expense, calculate the category total for the current month.
- If the total crosses the limit or a defined threshold, send a warning in the channel or by DM.
- Start with a single budget per category to keep the logic simple.

### Edit transaction

Add `/edit <id> <amount?> <category?> <description?>` so users can fix a transaction without deleting and recreating it.

- Reuse the ownership check from `delete_transaction`.
- Perform a partial `UPDATE`, changing only the fields that were provided.
- Validate `amount > 0` and block edits on another user's transactions.
- Keep the response ephemeral for consistency.

## Done

### Top categories in /summary

Show a breakdown of expenses by category in the existing embed.

- Run an aggregated query by category for the same period.
- Reuse the current embed and add an extra section with the main values.
- Sort by highest spending to surface the biggest costs quickly.

### Monthly charts

Generate a PNG with `matplotlib` and send the chart as an attachment.

- Reuse data from `summary` and/or `history`.
- Create a simple bar chart by category or by month.
- Store the image in memory with `BytesIO` and send it through Discord.
- This feature improves presentation a lot without changing the database too much.

### Filters in /history

Allow filters by type or category, for example `/history category:food`.

- Add optional parameters to the slash command.
- Extend the SQL query with safe dynamic filters.
- Keep the current pagination or limit so the embed stays manageable.

## High impact, more effort

### Recurring transactions

Support rent, salary, and subscriptions with a `recurring_transactions` table and a periodic job that creates transactions automatically.

- Create a new table for the recurring rule and the next execution date.
- Store frequency, start date, and default category.
- Add a worker/job that runs daily and inserts due transactions.
- Record executions to avoid duplicates.
