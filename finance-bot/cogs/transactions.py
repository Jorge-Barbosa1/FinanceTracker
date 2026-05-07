"""Slash commands for recording and reviewing personal transactions.

This cog exposes the finance-related slash commands used by the bot:
expenses, income entries, summaries, history, and deletion.
"""

from __future__ import annotations

from datetime import datetime
from io import BytesIO
import os
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import discord
from discord import app_commands
from discord.ext import commands
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from db.database import (
    DatabaseError,
    add_transaction,
    get_category_totals,
    delete_transaction,
    get_history,
    get_summary,
)


def current_period() -> tuple[int, int]:
    """Return the default accounting month and year."""
    timezone_name = os.getenv("APP_TIMEZONE", "Europe/Lisbon")
    try:
        timezone = ZoneInfo(timezone_name)
    except ZoneInfoNotFoundError:
        timezone = None

    now = datetime.now(timezone)
    return now.month, now.year


def resolve_period(month: int | None, year: int | None) -> tuple[int, int]:
    """Return the requested accounting period, filling missing values."""
    current_month, current_year = current_period()
    return month or current_month, year or current_year


def format_period(month: int, year: int) -> str:
    """Format an accounting period for Discord messages."""
    return datetime(year, month, 1).strftime("%B %Y")


def format_currency(amount: float) -> str:
    """Format a numeric amount as euros for display in Discord embeds."""
    return f"€{amount:.2f}"


def format_history_filters(
    transaction_type: str | None,
    category: str | None,
) -> str | None:
    """Format active history filters for display in Discord embeds."""
    filters = []
    if transaction_type:
        filters.append(
            f"Type: {'Income' if transaction_type == 'income' else 'Expense'}"
        )
    if category:
        filters.append(f"Category: {category}")
    return "Filters: " + ", ".join(filters) if filters else None


def build_spending_chart(
    category_totals: list[dict[str, object]],
    period: str,
    accounting_month: int,
    accounting_year: int,
) -> discord.File:
    """Render a PNG chart showing expenses by category."""
    categories = [str(item["category"]) for item in category_totals]
    totals = [float(item["total"]) for item in category_totals]

    figure_height = max(4.0, 0.6 * len(categories) + 1.5)
    figure, axis = plt.subplots(figsize=(10, figure_height))

    bars = axis.barh(categories, totals, color="#4F6BED")
    axis.set_title(f"Spending by category - {period}")
    axis.set_xlabel("Amount (€)")
    axis.invert_yaxis()
    axis.grid(axis="x", alpha=0.25)

    for bar, amount in zip(bars, totals, strict=False):
        axis.text(
            bar.get_width(),
            bar.get_y() + bar.get_height() / 2,
            f" €{amount:.2f}",
            va="center",
            ha="left",
            fontsize=9,
        )

    figure.tight_layout()

    buffer = BytesIO()
    figure.savefig(buffer, format="png", dpi=200, bbox_inches="tight")
    plt.close(figure)
    buffer.seek(0)

    filename = f"spending-chart-{accounting_year}-{accounting_month:02d}.png"
    return discord.File(buffer, filename=filename)


async def send_database_error(interaction: discord.Interaction) -> None:
    """Tell the user that the database is temporarily unavailable."""
    message = "The database is temporarily unavailable. Please try again in a moment."
    if interaction.response.is_done():
        await interaction.followup.send(message, ephemeral=True)
    else:
        await interaction.response.send_message(message, ephemeral=True)


class TransactionsCog(commands.Cog):
    """Cog containing all finance-related slash commands."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="help", description="Show FinanceTrackerBot help")
    async def help(self, interaction: discord.Interaction) -> None:
        """Show a compact guide for the bot's slash commands."""
        embed = discord.Embed(
            title="FinanceTrackerBot help",
            description=(
                "Track income and expenses, review monthly totals, and inspect "
                "recent transactions directly from Discord."
            ),
            color=discord.Color.blurple(),
        )
        embed.add_field(
            name="Record transactions",
            value=(
                "`/expense amount:12.50 category:Food description:Lunch` - record an expense\n"
                "`/income amount:1200 description:Salary` - record income"
            ),
            inline=False,
        )
        embed.add_field(
            name="Review your finances",
            value=(
                "`/summary` - show monthly income, expenses, balance, and top categories\n"
                "`/history type:expense category:Food` - show recent transactions with optional filters\n"
                "`/chart` - generate a spending chart by category"
            ),
            inline=False,
        )
        embed.add_field(
            name="Manage entries",
            value="`/delete transaction_id:123` - delete one of your transactions by ID",
            inline=False,
        )
        embed.set_footer(
            text="Only you can see bot responses. Month and year are optional unless you need a specific period."
        )

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="expense", description="Record an expense")
    @app_commands.describe(
        amount="Expense amount",
        category="Expense category",
        description="Optional expense description",
        month="Accounting month for this expense",
        year="Accounting year for this expense",
    )
    async def expense(
        self,
        interaction: discord.Interaction,
        amount: float,
        category: str,
        description: str | None = None,
        month: app_commands.Range[int, 1, 12] = None,
        year: app_commands.Range[int, 2000, 2100] = None,
    ) -> None:
        """Register a new expense for the user who ran the command."""
        if amount <= 0:
            await interaction.response.send_message(
                "The amount must be greater than zero.", ephemeral=True
            )
            return

        accounting_month, accounting_year = resolve_period(month, year)
        try:
            transaction_id = await add_transaction(
                user_id=interaction.user.id,
                transaction_type="expense",
                amount=amount,
                category=category,
                description=description,
                accounting_month=accounting_month,
                accounting_year=accounting_year,
            )
        except DatabaseError:
            await send_database_error(interaction)
            return

        await interaction.response.send_message(
            (
                f"Expense recorded successfully for {format_period(accounting_month, accounting_year)}. "
                f"ID: {transaction_id}"
            ),
            ephemeral=True,
        )

    @app_commands.command(name="income", description="Record income")
    @app_commands.describe(
        amount="Income amount",
        description="Optional income description",
        month="Accounting month for this income",
        year="Accounting year for this income",
    )
    async def income(
        self,
        interaction: discord.Interaction,
        amount: float,
        description: str | None = None,
        month: app_commands.Range[int, 1, 12] = None,
        year: app_commands.Range[int, 2000, 2100] = None,
    ) -> None:
        """Register a new income entry for the user who ran the command."""
        if amount <= 0:
            await interaction.response.send_message(
                "The amount must be greater than zero.", ephemeral=True
            )
            return

        accounting_month, accounting_year = resolve_period(month, year)
        try:
            transaction_id = await add_transaction(
                user_id=interaction.user.id,
                transaction_type="income",
                amount=amount,
                category="Income",
                description=description,
                accounting_month=accounting_month,
                accounting_year=accounting_year,
            )
        except DatabaseError:
            await send_database_error(interaction)
            return

        await interaction.response.send_message(
            (
                f"Income recorded successfully for {format_period(accounting_month, accounting_year)}. "
                f"ID: {transaction_id}"
            ),
            ephemeral=True,
        )

    @app_commands.command(name="summary", description="Show your financial summary")
    @app_commands.describe(
        month="Accounting month to summarize",
        year="Accounting year to summarize",
    )
    async def summary(
        self,
        interaction: discord.Interaction,
        month: app_commands.Range[int, 1, 12] = None,
        year: app_commands.Range[int, 2000, 2100] = None,
    ) -> None:
        """Display the user's financial summary in an embed."""
        accounting_month, accounting_year = resolve_period(month, year)
        try:
            summary = await get_summary(
                interaction.user.id,
                accounting_month,
                accounting_year,
            )
        except DatabaseError:
            await send_database_error(interaction)
            return

        period = format_period(accounting_month, accounting_year)
        if summary["transaction_count"] == 0:
            await interaction.response.send_message(
                f"No transactions found for {period}.",
                ephemeral=True,
            )
            return

        try:
            category_totals = await get_category_totals(
                interaction.user.id,
                accounting_month,
                accounting_year,
            )
        except DatabaseError:
            await send_database_error(interaction)
            return

        embed = discord.Embed(
            title=f"Financial summary - {period}",
            color=discord.Color.blurple(),
        )
        embed.add_field(
            name="Income",
            value=format_currency(summary["income"]),
            inline=True,
        )
        embed.add_field(
            name="Expenses",
            value=format_currency(summary["expenses"]),
            inline=True,
        )
        embed.add_field(
            name="Balance",
            value=format_currency(summary["balance"]),
            inline=True,
        )

        if category_totals:
            top_categories = category_totals[:5]
            category_lines = []
            total_expenses = float(summary["expenses"])
            for item in top_categories:
                category_total = float(item["total"])
                share = (
                    (category_total / total_expenses) * 100
                    if total_expenses > 0
                    else 0
                )
                category_lines.append(
                    f"{item['category']}: {format_currency(category_total)} ({share:.1f}%)"
                )

            embed.add_field(
                name="Top expense categories",
                value="\n".join(category_lines),
                inline=False,
            )
        else:
            embed.add_field(
                name="Top expense categories",
                value="No expenses recorded for this period.",
                inline=False,
            )

        embed.set_footer(text="Only you can see this data.")

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="history", description="Show recent transactions")
    @app_commands.describe(
        limit="Maximum number of transactions to show",
        month="Accounting month to show",
        year="Accounting year to show",
        transaction_type="Only show income or expense transactions",
        category="Only show transactions from this category",
    )
    @app_commands.rename(transaction_type="type")
    @app_commands.choices(
        transaction_type=[
            app_commands.Choice(name="Income", value="income"),
            app_commands.Choice(name="Expense", value="expense"),
        ],
    )
    async def history(
        self,
        interaction: discord.Interaction,
        limit: app_commands.Range[int, 1, 25] = 10,
        month: app_commands.Range[int, 1, 12] = None,
        year: app_commands.Range[int, 2000, 2100] = None,
        transaction_type: app_commands.Choice[str] | None = None,
        category: str | None = None,
    ) -> None:
        """Show the latest transactions for the current user."""
        accounting_month, accounting_year = resolve_period(month, year)
        selected_type = transaction_type.value if transaction_type else None
        selected_category = category.strip() if category else None
        if selected_category == "":
            selected_category = None

        try:
            history = await get_history(
                interaction.user.id,
                limit,
                accounting_month,
                accounting_year,
                transaction_type=selected_type,
                category=selected_category,
            )
        except DatabaseError:
            await send_database_error(interaction)
            return

        period = format_period(accounting_month, accounting_year)
        embed = discord.Embed(
            title=f"Latest {len(history)} transactions - {period}",
            color=discord.Color.green(),
        )
        filter_description = format_history_filters(
            selected_type,
            selected_category,
        )
        if filter_description:
            embed.description = filter_description

        if not history:
            empty_message = f"No transactions found for {period}."
            embed.description = (
                f"{filter_description}\n{empty_message}"
                if filter_description
                else empty_message
            )
        else:
            for transaction in history:
                entry_type = "Income" if transaction["type"] == "income" else "Expense"
                category = transaction["category"] or "Uncategorized"
                description = transaction["description"] or "No description"
                created_at = transaction["created_at"]
                transaction_period = format_period(
                    transaction["accounting_month"],
                    transaction["accounting_year"],
                )
                embed.add_field(
                    name=f"#{transaction['id']} - {entry_type} - {format_currency(transaction['amount'])}",
                    value=(
                        f"Category: {category}\n"
                        f"Description: {description}\n"
                        f"Month: {transaction_period}\n"
                        f"Date: {created_at}"
                    ),
                    inline=False,
                )

        embed.set_footer(text="Only you can see this data.")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="chart", description="Show a spending chart")
    @app_commands.describe(
        month="Accounting month to chart",
        year="Accounting year to chart",
    )
    async def chart(
        self,
        interaction: discord.Interaction,
        month: app_commands.Range[int, 1, 12] = None,
        year: app_commands.Range[int, 2000, 2100] = None,
    ) -> None:
        """Show a bar chart of expenses by category for the requested period."""
        accounting_month, accounting_year = resolve_period(month, year)
        try:
            category_totals = await get_category_totals(
                interaction.user.id,
                accounting_month,
                accounting_year,
            )
        except DatabaseError:
            await send_database_error(interaction)
            return

        period = format_period(accounting_month, accounting_year)
        if not category_totals:
            await interaction.response.send_message(
                f"No expense transactions found for {period}.",
                ephemeral=True,
            )
            return

        file = build_spending_chart(
            category_totals,
            period,
            accounting_month,
            accounting_year,
        )
        embed = discord.Embed(
            title=f"Monthly spending chart - {period}",
            description="Spending by category for the selected period.",
            color=discord.Color.orange(),
        )
        embed.set_image(url=f"attachment://{file.filename}")
        embed.set_footer(text="Only you can see this data.")

        await interaction.response.send_message(embed=embed, file=file, ephemeral=True)

    @app_commands.command(name="delete", description="Delete a transaction by ID")
    @app_commands.describe(transaction_id="Transaction ID to delete")
    async def delete(
        self,
        interaction: discord.Interaction,
        transaction_id: int,
    ) -> None:
        """Delete one of the user's transactions by its database ID."""
        try:
            deleted = await delete_transaction(interaction.user.id, transaction_id)
        except DatabaseError:
            await send_database_error(interaction)
            return

        if not deleted:
            await interaction.response.send_message(
                "No transaction with that ID was found for your account.",
                ephemeral=True,
            )
            return

        await interaction.response.send_message(
            f"Transaction #{transaction_id} deleted successfully.", ephemeral=True
        )


async def setup(bot: commands.Bot) -> None:
    """Register the cog with the bot instance."""
    await bot.add_cog(TransactionsCog(bot))
