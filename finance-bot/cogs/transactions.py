"""Slash commands for recording and reviewing personal transactions.

This cog exposes the finance-related slash commands used by the bot:
expenses, income entries, summaries, history, and deletion.
"""

from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands

from db.database import (
    DatabaseError,
    add_transaction,
    delete_transaction,
    get_history,
    get_summary,
)


def format_currency(amount: float) -> str:
    """Format a numeric amount as euros for display in Discord embeds."""
    return f"€{amount:.2f}"


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

    @app_commands.command(name="expense", description="Record an expense")
    @app_commands.describe(
        amount="Expense amount",
        category="Expense category",
        description="Optional expense description",
    )
    async def expense(
        self,
        interaction: discord.Interaction,
        amount: float,
        category: str,
        description: str | None = None,
    ) -> None:
        """Register a new expense for the user who ran the command."""
        if amount <= 0:
            await interaction.response.send_message(
                "The amount must be greater than zero.", ephemeral=True
            )
            return

        try:
            transaction_id = await add_transaction(
                user_id=interaction.user.id,
                transaction_type="expense",
                amount=amount,
                category=category,
                description=description,
            )
        except DatabaseError:
            await send_database_error(interaction)
            return

        await interaction.response.send_message(
            f"Expense recorded successfully. ID: {transaction_id}", ephemeral=True
        )

    @app_commands.command(name="income", description="Record income")
    @app_commands.describe(
        amount="Income amount",
        description="Optional income description",
    )
    async def income(
        self,
        interaction: discord.Interaction,
        amount: float,
        description: str | None = None,
    ) -> None:
        """Register a new income entry for the user who ran the command."""
        if amount <= 0:
            await interaction.response.send_message(
                "The amount must be greater than zero.", ephemeral=True
            )
            return

        try:
            transaction_id = await add_transaction(
                user_id=interaction.user.id,
                transaction_type="income",
                amount=amount,
                category="Income",
                description=description,
            )
        except DatabaseError:
            await send_database_error(interaction)
            return

        await interaction.response.send_message(
            f"Income recorded successfully. ID: {transaction_id}", ephemeral=True
        )

    @app_commands.command(name="summary", description="Show your financial summary")
    async def summary(self, interaction: discord.Interaction) -> None:
        """Display the user's financial summary in an embed."""
        try:
            summary = await get_summary(interaction.user.id)
        except DatabaseError:
            await send_database_error(interaction)
            return

        embed = discord.Embed(
            title="Financial summary",
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
        embed.set_footer(text="Only you can see this data.")

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="history", description="Show recent transactions")
    @app_commands.describe(limit="Maximum number of transactions to show")
    async def history(
        self,
        interaction: discord.Interaction,
        limit: app_commands.Range[int, 1, 25] = 10,
    ) -> None:
        """Show the latest transactions for the current user."""
        try:
            history = await get_history(interaction.user.id, limit)
        except DatabaseError:
            await send_database_error(interaction)
            return

        embed = discord.Embed(
            title=f"Latest {len(history)} transactions",
            color=discord.Color.green(),
        )

        if not history:
            embed.description = "No transactions have been recorded yet."
        else:
            for transaction in history:
                entry_type = "Income" if transaction["type"] == "income" else "Expense"
                category = transaction["category"] or "Uncategorized"
                description = transaction["description"] or "No description"
                created_at = transaction["created_at"]
                embed.add_field(
                    name=f"#{transaction['id']} - {entry_type} - {format_currency(transaction['amount'])}",
                    value=(
                        f"Category: {category}\n"
                        f"Description: {description}\n"
                        f"Date: {created_at}"
                    ),
                    inline=False,
                )

        embed.set_footer(text="Only you can see this data.")
        await interaction.response.send_message(embed=embed, ephemeral=True)

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
