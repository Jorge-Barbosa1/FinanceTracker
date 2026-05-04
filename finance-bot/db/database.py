"""SQLite helpers for storing and querying user transactions.

The functions in this module create the database schema and provide async
helpers for inserting, summarising, listing, and deleting transactions.
"""

from __future__ import annotations

import asyncio
import sqlite3
from pathlib import Path
from typing import Any

DATABASE_PATH = Path(__file__).resolve().parent.parent / "finance.db"


def _connect() -> sqlite3.Connection:
    """Create a SQLite connection with row access by column name."""
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def _to_dict(row: sqlite3.Row) -> dict[str, Any]:
    """Convert a SQLite row into a plain dictionary."""
    return dict(row)


def _init_db_sync() -> None:
    """Create the transactions table if it does not already exist."""
    with _connect() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                type TEXT NOT NULL CHECK (type IN ('income', 'expense')),
                amount REAL NOT NULL CHECK (amount > 0),
                category TEXT NOT NULL,
                description TEXT,
                created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
            )
            """
        )
        connection.commit()


async def init_db() -> None:
    """Initialise the SQLite database in a background thread."""
    await asyncio.to_thread(_init_db_sync)


def _add_transaction_sync(
    user_id: int,
    transaction_type: str,
    amount: float,
    category: str,
    description: str | None,
) -> int:
    """Insert a new transaction and return its database ID."""
    with _connect() as connection:
        cursor = connection.execute(
            """
            INSERT INTO transactions (user_id, type, amount, category, description)
            VALUES (?, ?, ?, ?, ?)
            """,
            (user_id, transaction_type, amount, category, description),
        )
        connection.commit()
        return int(cursor.lastrowid)


async def add_transaction(
    user_id: int,
    transaction_type: str,
    amount: float,
    category: str,
    description: str | None = None,
) -> int:
    """Store a transaction for the given user and return the created ID."""
    if transaction_type not in {"income", "expense"}:
        raise ValueError("transaction_type must be 'income' or 'expense'.")

    return await asyncio.to_thread(
        _add_transaction_sync,
        user_id,
        transaction_type,
        amount,
        category,
        description,
    )


def _get_summary_sync(user_id: int) -> dict[str, float]:
    """Calculate the user's total income, expenses, and balance."""
    with _connect() as connection:
        row = connection.execute(
            """
            SELECT
                COALESCE(SUM(CASE WHEN type = 'income' THEN amount ELSE 0 END), 0) AS income,
                COALESCE(SUM(CASE WHEN type = 'expense' THEN amount ELSE 0 END), 0) AS expenses
            FROM transactions
            WHERE user_id = ?
            """,
            (user_id,),
        ).fetchone()

    income = float(row["income"] or 0)
    expenses = float(row["expenses"] or 0)
    return {
        "income": income,
        "expenses": expenses,
        "balance": income - expenses,
    }


async def get_summary(user_id: int) -> dict[str, float]:
    """Return a financial summary for the given user."""
    return await asyncio.to_thread(_get_summary_sync, user_id)


def _get_history_sync(user_id: int, limit: int) -> list[dict[str, Any]]:
    """Fetch the most recent transactions for the given user."""
    with _connect() as connection:
        rows = connection.execute(
            """
            SELECT id, user_id, type, amount, category, description, created_at
            FROM transactions
            WHERE user_id = ?
            ORDER BY datetime(created_at) DESC, id DESC
            LIMIT ?
            """,
            (user_id, limit),
        ).fetchall()

    return [_to_dict(row) for row in rows]


async def get_history(user_id: int, limit: int = 10) -> list[dict[str, Any]]:
    """Return the most recent transactions for the given user."""
    limit = max(1, min(limit, 25))
    return await asyncio.to_thread(_get_history_sync, user_id, limit)


def _delete_transaction_sync(user_id: int, transaction_id: int) -> bool:
    """Delete a transaction owned by the given user."""
    with _connect() as connection:
        cursor = connection.execute(
            """
            DELETE FROM transactions
            WHERE id = ? AND user_id = ?
            """,
            (transaction_id, user_id),
        )
        connection.commit()
        return cursor.rowcount > 0


async def delete_transaction(user_id: int, transaction_id: int) -> bool:
    """Delete a transaction by ID if it belongs to the user."""
    return await asyncio.to_thread(_delete_transaction_sync, user_id, transaction_id)
