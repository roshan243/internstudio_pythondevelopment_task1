"""CSV export functionality."""

import csv
from pathlib import Path
from typing import Union

from database import DEFAULT_DATABASE_PATH, DatabasePath
from transactions import get_transactions


CSV_COLUMNS = (
    "id",
    "transaction_type",
    "amount",
    "category",
    "transaction_date",
    "description",
)


def export_transactions(
    csv_path: Union[str, Path],
    database_path: DatabasePath = DEFAULT_DATABASE_PATH,
) -> int:
    """Export all transactions to a UTF-8 CSV and return the number written."""
    destination = Path(csv_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    transactions = get_transactions(database_path)

    with destination.open("w", newline="", encoding="utf-8-sig") as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        for transaction in transactions:
            writer.writerow(
                {
                    **transaction,
                    "amount": f"{transaction['amount']:.2f}",
                }
            )
    return len(transactions)
