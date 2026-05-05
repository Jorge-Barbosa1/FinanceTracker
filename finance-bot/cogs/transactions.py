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
    message = "A base de dados está temporariamente indisponível. Tente novamente daqui a pouco."
    if interaction.response.is_done():
        await interaction.followup.send(message, ephemeral=True)
    else:
        await interaction.response.send_message(message, ephemeral=True)


class TransactionsCog(commands.Cog):
    """Cog containing all finance-related slash commands."""

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="gasto", description="Registar uma despesa")
    @app_commands.describe(
        valor="Valor da despesa",
        categoria="Categoria da despesa",
        descricao="Descrição opcional da despesa",
    )
    async def gasto(
        self,
        interaction: discord.Interaction,
        valor: float,
        categoria: str,
        descricao: str | None = None,
    ) -> None:
        """Register a new expense for the user who ran the command."""
        if valor <= 0:
            await interaction.response.send_message(
                "O valor tem de ser superior a zero.", ephemeral=True
            )
            return

        try:
            transaction_id = await add_transaction(
                user_id=interaction.user.id,
                transaction_type="expense",
                amount=valor,
                category=categoria,
                description=descricao,
            )
        except DatabaseError:
            await send_database_error(interaction)
            return

        await interaction.response.send_message(
            f"Despesa registada com sucesso. ID: {transaction_id}", ephemeral=True
        )

    @app_commands.command(name="entrada", description="Registar uma entrada")
    @app_commands.describe(
        valor="Valor da entrada",
        descricao="Descrição opcional da entrada",
    )
    async def entrada(
        self,
        interaction: discord.Interaction,
        valor: float,
        descricao: str | None = None,
    ) -> None:
        """Register a new income entry for the user who ran the command."""
        if valor <= 0:
            await interaction.response.send_message(
                "O valor tem de ser superior a zero.", ephemeral=True
            )
            return

        try:
            transaction_id = await add_transaction(
                user_id=interaction.user.id,
                transaction_type="income",
                amount=valor,
                category="Receita",
                description=descricao,
            )
        except DatabaseError:
            await send_database_error(interaction)
            return

        await interaction.response.send_message(
            f"Entrada registada com sucesso. ID: {transaction_id}", ephemeral=True
        )

    @app_commands.command(name="resumo", description="Mostrar um resumo financeiro")
    async def resumo(self, interaction: discord.Interaction) -> None:
        """Display the user's financial summary in an embed."""
        try:
            summary = await get_summary(interaction.user.id)
        except DatabaseError:
            await send_database_error(interaction)
            return

        embed = discord.Embed(
            title="Resumo financeiro",
            color=discord.Color.blurple(),
        )
        embed.add_field(
            name="Entradas",
            value=format_currency(summary["income"]),
            inline=True,
        )
        embed.add_field(
            name="Despesas",
            value=format_currency(summary["expenses"]),
            inline=True,
        )
        embed.add_field(
            name="Saldo",
            value=format_currency(summary["balance"]),
            inline=True,
        )
        embed.set_footer(text="Dados visíveis apenas para si.")

        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="historico", description="Mostrar o histórico de transações")
    @app_commands.describe(limit="Número máximo de transações a mostrar")
    async def historico(
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
            title=f"Últimas {len(history)} transações",
            color=discord.Color.green(),
        )

        if not history:
            embed.description = "Ainda não existem transações registadas."
        else:
            for transaction in history:
                entry_type = "Entrada" if transaction["type"] == "income" else "Despesa"
                category = transaction["category"] or "Sem categoria"
                description = transaction["description"] or "Sem descrição"
                created_at = transaction["created_at"]
                embed.add_field(
                    name=f"#{transaction['id']} - {entry_type} - {format_currency(transaction['amount'])}",
                    value=(
                        f"Categoria: {category}\n"
                        f"Descrição: {description}\n"
                        f"Data: {created_at}"
                    ),
                    inline=False,
                )

        embed.set_footer(text="Dados visíveis apenas para si.")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="apagar", description="Apagar uma transação pelo ID")
    @app_commands.describe(transaction_id="ID da transação a apagar")
    async def apagar(
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
                "Não foi encontrada nenhuma transação sua com esse ID.",
                ephemeral=True,
            )
            return

        await interaction.response.send_message(
            f"Transação #{transaction_id} apagada com sucesso.", ephemeral=True
        )


async def setup(bot: commands.Bot) -> None:
    """Register the cog with the bot instance."""
    await bot.add_cog(TransactionsCog(bot))
