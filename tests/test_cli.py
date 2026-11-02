"""Tests for argparse commands using temporary, isolated data files."""

import csv

import pytest

import main
from transactions import add_transaction, get_transactions


@pytest.fixture
def database_path(tmp_path, monkeypatch):
    path = tmp_path / "cli_test.db"
    monkeypatch.setattr(main, "DEFAULT_DATABASE_PATH", path)
    return path


def test_add_command(database_path, capsys):
    result = main.main(
        [
            "add",
            "--type",
            "expense",
            "--amount",
            "12.50",
            "--category",
            "Food",
            "--date",
            "2026-10-12",
            "--description",
            "Lunch",
        ]
    )

    assert result == 0
    assert "Success: Expense transaction #1 added." in capsys.readouterr().out
    transaction = get_transactions(database_path)[0]
    assert transaction["amount"] == 12.50
    assert transaction["description"] == "Lunch"


def test_add_command_prompts_for_missing_options(database_path, monkeypatch, capsys):
    answers = iter(["income", "500", "Salary"])
    monkeypatch.setattr("builtins.input", lambda _prompt: next(answers))

    assert main.main(["add"]) == 0

    assert "Success: Income transaction #1 added." in capsys.readouterr().out
    assert get_transactions(database_path)[0]["category"] == "Salary"


def test_list_command(database_path, capsys):
    add_transaction(
        "income", 500, "Salary", "2026-10-01", "Pay", database_path=database_path
    )

    assert main.main(["list"]) == 0

    output = capsys.readouterr().out
    assert "Salary" in output
    assert "$   500.00" in output


def test_report_command_displays_month_and_category_reports(database_path, capsys):
    add_transaction(
        "income", 1000, "Salary", "2026-10-01", database_path=database_path
    )
    add_transaction(
        "expense", 50, "Food", "2026-10-02", database_path=database_path
    )

    assert main.main(["report", "--month", "2026-10"]) == 0

    output = capsys.readouterr().out
    assert "Financial Summary" in output
    assert "Monthly Summary: 2026-10" in output
    assert "Expense Categories for 2026-10" in output
    assert "Food" in output
    assert "$50.00" in output


def test_report_command_rejects_invalid_month(capsys):
    with pytest.raises(SystemExit) as error:
        main.main(["report", "--month", "2026-13"])

    assert error.value.code == 2
    assert "month must use YYYY-MM format" in capsys.readouterr().err


def test_export_command_writes_csv(database_path, tmp_path, capsys):
    add_transaction(
        "expense", 7.25, "Food", "2026-10-02", database_path=database_path
    )
    csv_path = tmp_path / "out" / "transactions.csv"

    assert main.main(["export", "--output", str(csv_path)]) == 0

    assert "exported 1 transaction(s)" in capsys.readouterr().out
    with csv_path.open(newline="", encoding="utf-8-sig") as csv_file:
        rows = list(csv.DictReader(csv_file))
    assert rows[0]["amount"] == "7.25"
    assert rows[0]["category"] == "Food"


def test_add_command_rejects_invalid_amount(database_path, capsys):
    with pytest.raises(SystemExit) as error:
        main.main(
            [
                "add",
                "--type",
                "expense",
                "--amount",
                "-5",
                "--category",
                "Food",
            ]
        )

    assert error.value.code == 2
    assert "Amount must be greater than zero." in capsys.readouterr().err


def test_no_arguments_still_runs_existing_menu(monkeypatch, capsys):
    monkeypatch.setattr(main, "initialize_database", lambda: None)
    monkeypatch.setattr("builtins.input", lambda _prompt: "10")

    assert main.main([]) == 0

    assert "Goodbye! Your transactions are saved." in capsys.readouterr().out
