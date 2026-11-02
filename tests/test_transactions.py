"""Tests for transaction management using an isolated temporary database."""

import pytest

from transactions import (
    add_transaction,
    delete_transaction,
    edit_transaction,
    get_transactions,
)


@pytest.fixture
def database_path(tmp_path):
    return tmp_path / "test_finance.db"


def test_add_income(database_path):
    transaction_id = add_transaction(
        "income", "2500.00", "Salary", "2026-10-01", "Monthly pay", database_path
    )
    transaction = get_transactions(database_path)[0]

    assert transaction_id == 1
    assert transaction["transaction_type"] == "income"
    assert transaction["amount"] == 2500.00
    assert transaction["category"] == "Salary"


def test_add_expense(database_path):
    add_transaction("expense", 12.50, "Food", "2026-10-02", "Lunch", database_path)

    transaction = get_transactions(database_path)[0]
    assert transaction["transaction_type"] == "expense"
    assert transaction["amount"] == 12.50


def test_view_transactions_returns_newest_first(database_path):
    add_transaction("income", 100, "Salary", "2026-10-01", database_path=database_path)
    add_transaction("expense", 20, "Food", "2026-10-03", database_path=database_path)

    transactions = get_transactions(database_path)
    assert len(transactions) == 2
    assert transactions[0]["transaction_date"] == "2026-10-03"


def test_edit_transaction(database_path):
    transaction_id = add_transaction(
        "expense", 10, "Food", "2026-10-01", "Snack", database_path
    )

    edit_transaction(
        transaction_id,
        amount=15.25,
        category="Shopping",
        description="Supplies",
        database_path=database_path,
    )

    transaction = get_transactions(database_path)[0]
    assert transaction["amount"] == 15.25
    assert transaction["category"] == "Shopping"
    assert transaction["description"] == "Supplies"
    assert transaction["transaction_date"] == "2026-10-01"


def test_delete_transaction(database_path):
    transaction_id = add_transaction(
        "expense", 10, "Food", "2026-10-01", database_path=database_path
    )

    delete_transaction(transaction_id, database_path)

    assert get_transactions(database_path) == []


@pytest.mark.parametrize(
    ("amount", "message"),
    [
        ("not-money", "valid number"),
        (0, "greater than zero"),
        (-3, "greater than zero"),
        ("1e100000", "too large"),
    ],
)
def test_rejects_invalid_amount(database_path, amount, message):
    with pytest.raises(ValueError, match=message):
        add_transaction("expense", amount, "Food", "2026-10-01", database_path=database_path)


def test_rejects_invalid_date(database_path):
    with pytest.raises(ValueError, match="YYYY-MM-DD"):
        add_transaction("expense", 1, "Food", "not-a-date", database_path=database_path)


def test_rejects_nonstandard_date_format(database_path):
    with pytest.raises(ValueError, match="YYYY-MM-DD"):
        add_transaction("expense", 1, "Food", "20261001", database_path=database_path)


def test_rejects_invalid_category(database_path):
    with pytest.raises(ValueError, match="Category"):
        add_transaction("expense", 1, "Unlisted", "2026-10-01", database_path=database_path)


def test_edit_missing_transaction(database_path):
    with pytest.raises(ValueError, match="No transaction found"):
        edit_transaction(999, amount=1, database_path=database_path)


def test_delete_missing_transaction(database_path):
    with pytest.raises(ValueError, match="No transaction found"):
        delete_transaction(999, database_path)
