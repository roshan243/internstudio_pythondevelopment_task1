"""Financial totals and transaction reports."""

from typing import Dict, List, Optional

from database import DEFAULT_DATABASE_PATH, DatabasePath, get_connection, initialize_database


def _amount_from_cents(cents: int) -> float:
    return cents / 100


def get_financial_summary(
    database_path: DatabasePath = DEFAULT_DATABASE_PATH,
) -> Dict[str, float]:
    """Calculate total income, expenses, and balance across all transactions."""
    initialize_database(database_path)
    with get_connection(database_path) as connection:
        totals = connection.execute(
            """
            SELECT
                COALESCE(SUM(CASE WHEN transaction_type = 'income'
                    THEN amount_cents ELSE 0 END), 0) AS income_cents,
                COALESCE(SUM(CASE WHEN transaction_type = 'expense'
                    THEN amount_cents ELSE 0 END), 0) AS expense_cents
            FROM transactions
            """
        ).fetchone()

    income = _amount_from_cents(totals["income_cents"])
    expenses = _amount_from_cents(totals["expense_cents"])
    return {
        "total_income": income,
        "total_expenses": expenses,
        "balance": income - expenses,
    }


def get_monthly_summary(
    year: int,
    month: int,
    database_path: DatabasePath = DEFAULT_DATABASE_PATH,
) -> Dict[str, float]:
    """Calculate income, expenses, and balance for a specific calendar month."""
    if not 1 <= month <= 12:
        raise ValueError("Month must be between 1 and 12.")
    if year < 1:
        raise ValueError("Year must be a positive whole number.")

    initialize_database(database_path)
    month_prefix = f"{year:04d}-{month:02d}"
    with get_connection(database_path) as connection:
        totals = connection.execute(
            """
            SELECT
                COALESCE(SUM(CASE WHEN transaction_type = 'income'
                    THEN amount_cents ELSE 0 END), 0) AS income_cents,
                COALESCE(SUM(CASE WHEN transaction_type = 'expense'
                    THEN amount_cents ELSE 0 END), 0) AS expense_cents
            FROM transactions
            WHERE transaction_date LIKE ?
            """,
            (month_prefix + "-%",),
        ).fetchone()

    income = _amount_from_cents(totals["income_cents"])
    expenses = _amount_from_cents(totals["expense_cents"])
    return {
        "total_income": income,
        "total_expenses": expenses,
        "balance": income - expenses,
    }


def get_category_expenses(
    database_path: DatabasePath = DEFAULT_DATABASE_PATH,
    year: Optional[int] = None,
    month: Optional[int] = None,
) -> List[Dict[str, object]]:
    """Return expense totals grouped by category, optionally for one month."""
    if (year is None) != (month is None):
        raise ValueError("Provide both year and month, or neither.")
    parameters = []
    date_filter = ""
    if year is not None and month is not None:
        if year < 1:
            raise ValueError("Year must be a positive whole number.")
        if not 1 <= month <= 12:
            raise ValueError("Month must be between 1 and 12.")
        date_filter = "AND transaction_date LIKE ?"
        parameters.append(f"{year:04d}-{month:02d}-%")

    initialize_database(database_path)
    with get_connection(database_path) as connection:
        rows = connection.execute(
            f"""
            SELECT category, SUM(amount_cents) AS total_cents
            FROM transactions
            WHERE transaction_type = 'expense' {date_filter}
            GROUP BY category
            ORDER BY total_cents DESC, category ASC
            """,
            parameters,
        ).fetchall()
    return [
        {"category": row["category"], "total": _amount_from_cents(row["total_cents"])}
        for row in rows
    ]


def get_highest_expense_category(
    database_path: DatabasePath = DEFAULT_DATABASE_PATH,
    year: Optional[int] = None,
    month: Optional[int] = None,
) -> Optional[Dict[str, object]]:
    """Return the category with the greatest expense, or None if there are none."""
    categories = get_category_expenses(database_path, year, month)
    return categories[0] if categories else None
