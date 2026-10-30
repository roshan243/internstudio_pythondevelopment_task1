"""Create, read, update, and delete personal finance transactions."""

from datetime import date
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import sqlite3
from typing import Dict, List, Optional, Union

from database import DEFAULT_DATABASE_PATH, DatabasePath, get_connection, initialize_database


CATEGORIES = (
    "Food",
    "Education",
    "Transport",
    "Shopping",
    "Entertainment",
    "Salary",
    "Other",
)
TRANSACTION_TYPES = ("income", "expense")


def validate_amount(amount: Union[str, int, float, Decimal]) -> int:
    """Validate an amount and return its value in integer cents."""
    try:
        value = Decimal(str(amount))
    except (InvalidOperation, ValueError):
        raise ValueError("Amount must be a valid number.") from None

    if not value.is_finite() or value <= 0:
        raise ValueError("Amount must be greater than zero.")

    cents = (value * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    if cents <= 0:
        raise ValueError("Amount must be at least 0.01.")
    if cents > 9_000_000_000_000_000:
        raise ValueError("Amount is too large.")
    return int(cents)


def validate_transaction_type(transaction_type: str) -> str:
    """Return a normalized transaction type or raise a helpful error."""
    normalized = str(transaction_type).strip().lower()
    if normalized not in TRANSACTION_TYPES:
        raise ValueError("Transaction type must be 'income' or 'expense'.")
    return normalized


def validate_category(category: str) -> str:
    """Return a normalized supported category or raise a helpful error."""
    normalized = str(category).strip().title()
    if normalized not in CATEGORIES:
        choices = ", ".join(CATEGORIES)
        raise ValueError(f"Category must be one of: {choices}.")
    return normalized


def validate_date(transaction_date: Union[str, date]) -> str:
    """Validate a date and return it in YYYY-MM-DD format."""
    if isinstance(transaction_date, date):
        return transaction_date.isoformat()
    raw_date = str(transaction_date).strip()
    try:
        normalized_date = date.fromisoformat(raw_date).isoformat()
    except (TypeError, ValueError):
        raise ValueError("Date must be a valid date in YYYY-MM-DD format.") from None
    if normalized_date != raw_date:
        raise ValueError("Date must be a valid date in YYYY-MM-DD format.")
    return normalized_date


def _row_to_transaction(row: sqlite3.Row) -> Dict[str, object]:
    transaction = dict(row)
    transaction["amount"] = transaction.pop("amount_cents") / 100
    return transaction


def add_transaction(
    transaction_type: str,
    amount: Union[str, int, float, Decimal],
    category: str,
    transaction_date: Union[str, date],
    description: str = "",
    database_path: DatabasePath = DEFAULT_DATABASE_PATH,
) -> int:
    """Validate and save a transaction; return its new database ID."""
    kind = validate_transaction_type(transaction_type)
    amount_cents = validate_amount(amount)
    normalized_category = validate_category(category)
    normalized_date = validate_date(transaction_date)
    clean_description = str(description).strip()
    initialize_database(database_path)

    with get_connection(database_path) as connection:
        cursor = connection.execute(
            """
            INSERT INTO transactions
                (transaction_type, amount_cents, category, transaction_date, description)
            VALUES (?, ?, ?, ?, ?)
            """,
            (kind, amount_cents, normalized_category, normalized_date, clean_description),
        )
        return int(cursor.lastrowid)


def get_transactions(database_path: DatabasePath = DEFAULT_DATABASE_PATH) -> List[Dict[str, object]]:
    """Return all transactions, newest date and ID first."""
    initialize_database(database_path)
    with get_connection(database_path) as connection:
        rows = connection.execute(
            """
            SELECT id, transaction_type, amount_cents, category, transaction_date, description
            FROM transactions
            ORDER BY transaction_date DESC, id DESC
            """
        ).fetchall()
    return [_row_to_transaction(row) for row in rows]


def edit_transaction(
    transaction_id: int,
    *,
    transaction_type: Optional[str] = None,
    amount: Optional[Union[str, int, float, Decimal]] = None,
    category: Optional[str] = None,
    transaction_date: Optional[Union[str, date]] = None,
    description: Optional[str] = None,
    database_path: DatabasePath = DEFAULT_DATABASE_PATH,
) -> None:
    """Update supplied transaction fields; leave all other fields unchanged."""
    try:
        normalized_id = int(transaction_id)
    except (TypeError, ValueError):
        raise ValueError("Transaction ID must be a positive whole number.") from None
    if normalized_id <= 0:
        raise ValueError("Transaction ID must be a positive whole number.")

    updates = {}
    if transaction_type is not None:
        updates["transaction_type"] = validate_transaction_type(transaction_type)
    if amount is not None:
        updates["amount_cents"] = validate_amount(amount)
    if category is not None:
        updates["category"] = validate_category(category)
    if transaction_date is not None:
        updates["transaction_date"] = validate_date(transaction_date)
    if description is not None:
        updates["description"] = str(description).strip()
    if not updates:
        raise ValueError("Provide at least one field to update.")

    initialize_database(database_path)
    assignments = ", ".join(f"{column} = ?" for column in updates)
    values = list(updates.values()) + [normalized_id]
    with get_connection(database_path) as connection:
        cursor = connection.execute(
            f"UPDATE transactions SET {assignments} WHERE id = ?", values
        )
        if cursor.rowcount == 0:
            raise ValueError(f"No transaction found with ID {normalized_id}.")


def delete_transaction(
    transaction_id: int,
    database_path: DatabasePath = DEFAULT_DATABASE_PATH,
) -> None:
    """Delete a transaction by ID or raise if it does not exist."""
    try:
        normalized_id = int(transaction_id)
    except (TypeError, ValueError):
        raise ValueError("Transaction ID must be a positive whole number.") from None
    if normalized_id <= 0:
        raise ValueError("Transaction ID must be a positive whole number.")

    initialize_database(database_path)
    with get_connection(database_path) as connection:
        cursor = connection.execute("DELETE FROM transactions WHERE id = ?", (normalized_id,))
        if cursor.rowcount == 0:
            raise ValueError(f"No transaction found with ID {normalized_id}.")
