"""Tests for financial reports and CSV export."""

import csv

import pytest

from export import export_transactions
from reports import (
    get_category_expenses,
    get_financial_summary,
    get_highest_expense_category,
    get_monthly_summary,
)
from transactions import add_transaction


@pytest.fixture
def database_path(tmp_path):
    path = tmp_path / "report_test.db"
    add_transaction("income", "1000.00", "Salary", "2026-10-01", database_path=path)
    add_transaction("expense", "125.50", "Food", "2026-10-02", database_path=path)
    add_transaction("expense", "75.00", "Transport", "2026-10-03", database_path=path)
    add_transaction("expense", "10.00", "Food", "2026-09-10", database_path=path)
    return path


def test_financial_totals_and_balance(database_path):
    summary = get_financial_summary(database_path)

    assert summary == {
        "total_income": 1000.00,
        "total_expenses": 210.50,
        "balance": 789.50,
    }


def test_monthly_summary_filters_by_month(database_path):
    summary = get_monthly_summary(2026, 10, database_path)

    assert summary == {
        "total_income": 1000.00,
        "total_expenses": 200.50,
        "balance": 799.50,
    }


def test_category_report_and_highest_category(database_path):
    categories = get_category_expenses(database_path)

    assert categories == [
        {"category": "Food", "total": 135.50},
        {"category": "Transport", "total": 75.00},
    ]
    assert get_highest_expense_category(database_path) == categories[0]


def test_empty_report_has_no_highest_category(tmp_path):
    assert get_highest_expense_category(tmp_path / "empty.db") is None


def test_rejects_invalid_month(database_path):
    with pytest.raises(ValueError, match="Month"):
        get_monthly_summary(2026, 13, database_path)


def test_csv_export(database_path, tmp_path):
    csv_path = tmp_path / "exports" / "transactions.csv"

    count = export_transactions(csv_path, database_path)

    assert count == 4
    with csv_path.open(newline="", encoding="utf-8-sig") as csv_file:
        rows = list(csv.DictReader(csv_file))
    assert len(rows) == 4
    assert rows[0]["amount"] == "75.00"
    assert rows[0]["transaction_type"] == "expense"
