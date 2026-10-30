"""SQLite setup and shared database helpers for the finance tracker."""

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator, Union


PROJECT_DIR = Path(__file__).resolve().parent
DEFAULT_DATABASE_PATH = PROJECT_DIR / "data" / "finance.db"
DatabasePath = Union[str, Path]


@contextmanager
def get_connection(
    database_path: DatabasePath = DEFAULT_DATABASE_PATH,
) -> Iterator[sqlite3.Connection]:
    """Open and reliably close a connection, creating its parent directory if needed."""
    path = Path(database_path)
    if str(database_path) != ":memory:":
        path.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(str(database_path))
    try:
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()


def initialize_database(database_path: DatabasePath = DEFAULT_DATABASE_PATH) -> None:
    """Create the transactions table if it does not already exist."""
    with get_connection(database_path) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                transaction_type TEXT NOT NULL
                    CHECK (transaction_type IN ('income', 'expense')),
                amount_cents INTEGER NOT NULL CHECK (amount_cents > 0),
                category TEXT NOT NULL,
                transaction_date TEXT NOT NULL,
                description TEXT NOT NULL DEFAULT ''
            )
            """
        )
        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_transactions_date
            ON transactions (transaction_date)
            """
        )
