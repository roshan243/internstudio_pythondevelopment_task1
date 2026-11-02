"""Command-line interface for the personal finance tracker."""

import argparse
from datetime import date
import re
import sqlite3
import sys
from pathlib import Path
from typing import Optional, Sequence

from database import DEFAULT_DATABASE_PATH, initialize_database
from export import export_transactions
from reports import (
    get_category_expenses,
    get_financial_summary,
    get_highest_expense_category,
    get_monthly_summary,
)
from transactions import (
    CATEGORIES,
    TRANSACTION_TYPES,
    add_transaction,
    delete_transaction,
    edit_transaction,
    get_transactions,
)


def _read_amount() -> float:
    raw_amount = input("Amount: ").strip()
    try:
        return float(raw_amount)
    except ValueError:
        raise ValueError("Amount must be a valid number.") from None


def _read_date() -> str:
    raw_date = input(f"Date (YYYY-MM-DD, default {date.today().isoformat()}): ").strip()
    return raw_date or date.today().isoformat()


def _read_category() -> str:
    print("Categories: " + ", ".join(CATEGORIES))
    return input("Category: ").strip()


def _print_transactions(database_path=DEFAULT_DATABASE_PATH) -> None:
    transactions = get_transactions(database_path)
    if not transactions:
        print("No transactions have been recorded yet.")
        return

    print("\nID  Type     Amount       Category          Date        Description")
    print("-" * 78)
    for item in transactions:
        print(
            f"{item['id']:<3} {item['transaction_type']:<8} "
            f"${item['amount']:>9.2f}  {item['category']:<17} "
            f"{item['transaction_date']:<11} {item['description']}"
        )


def _add_transaction(transaction_type: str) -> None:
    transaction_id = add_transaction(
        transaction_type=transaction_type,
        amount=_read_amount(),
        category=_read_category(),
        transaction_date=_read_date(),
        description=input("Description (optional): "),
    )
    print(f"Success: {transaction_type.title()} transaction #{transaction_id} added.")


def _edit_transaction() -> None:
    transaction_id = int(input("Transaction ID to edit: ").strip())
    print("Leave a field blank to keep its current value.")
    transaction_type = input("Type (income/expense): ").strip() or None
    raw_amount = input("Amount: ").strip()
    amount = float(raw_amount) if raw_amount else None
    category = input(f"Category ({', '.join(CATEGORIES)}): ").strip() or None
    transaction_date = input("Date (YYYY-MM-DD): ").strip() or None
    description = input("Description (blank keeps it, '-' clears it): ")
    if description == "-":
        description = ""
    elif description == "":
        description = None

    edit_transaction(
        transaction_id,
        transaction_type=transaction_type,
        amount=amount,
        category=category,
        transaction_date=transaction_date,
        description=description,
    )
    print(f"Success: transaction #{transaction_id} updated.")


def _delete_transaction() -> None:
    transaction_id = input("Transaction ID to delete: ").strip()
    delete_transaction(transaction_id)
    print(f"Success: transaction #{transaction_id} deleted.")


def _show_financial_summary() -> None:
    summary = get_financial_summary()
    print("\nFinancial Summary")
    print(f"Total income:   ${summary['total_income']:.2f}")
    print(f"Total expenses: ${summary['total_expenses']:.2f}")
    print(f"Current balance: ${summary['balance']:.2f}")
    highest = get_highest_expense_category()
    if highest:
        print(
            f"Highest expense category: {highest['category']} "
            f"(${highest['total']:.2f})"
        )
    else:
        print("Highest expense category: No expenses recorded")


def _show_monthly_report() -> None:
    year = int(input("Year (YYYY): ").strip())
    month = int(input("Month (1-12): ").strip())
    summary = get_monthly_summary(year, month)
    print(f"\nMonthly Summary: {year:04d}-{month:02d}")
    print(f"Income:   ${summary['total_income']:.2f}")
    print(f"Expenses: ${summary['total_expenses']:.2f}")
    print(f"Balance:  ${summary['balance']:.2f}")
    categories = get_category_expenses(year=year, month=month)
    if categories:
        print("Expense categories:")
        for item in categories:
            print(f"  {item['category']}: ${item['total']:.2f}")
    else:
        print("No expenses recorded for this month.")


def _show_category_report() -> None:
    categories = get_category_expenses()
    if not categories:
        print("No expenses have been recorded yet.")
        return
    print("\nExpenses by Category")
    for item in categories:
        print(f"{item['category']:<18} ${item['total']:.2f}")
    highest = categories[0]
    print(
        f"Highest expense category: {highest['category']} "
        f"(${highest['total']:.2f})"
    )


def _export_to_csv() -> None:
    default_path = Path(__file__).resolve().parent / "data" / "transactions.csv"
    requested_path = input(
        f"CSV file path (default {default_path}): "
    ).strip()
    output_path = Path(requested_path) if requested_path else default_path
    count = export_transactions(output_path)
    print(f"Success: exported {count} transaction(s) to {output_path}.")


def _show_menu() -> None:
    print(
        "\n=== Personal Finance Tracker ===\n"
        "1. Add Income\n"
        "2. Add Expense\n"
        "3. View Transactions\n"
        "4. Edit Transaction\n"
        "5. Delete Transaction\n"
        "6. View Financial Summary\n"
        "7. Monthly Report\n"
        "8. Category-wise Report\n"
        "9. Export to CSV\n"
        "10. Exit"
    )


def _parse_month(value: str) -> tuple[int, int]:
    """Parse a YYYY-MM month argument for argparse."""
    if not re.fullmatch(r"\d{4}-(0[1-9]|1[0-2])", value):
        raise argparse.ArgumentTypeError("month must use YYYY-MM format")
    year, month = (int(part) for part in value.split("-"))
    if year < 1:
        raise argparse.ArgumentTypeError("year must be greater than zero")
    return year, month


def _build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser and its supported subcommands."""
    parser = argparse.ArgumentParser(
        description="Record and review personal income and expenses."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    add_parser = subparsers.add_parser("add", help="add an income or expense transaction")
    add_parser.add_argument(
        "--type",
        dest="transaction_type",
        choices=TRANSACTION_TYPES,
        help="transaction type (prompts if omitted)",
    )
    add_parser.add_argument(
        "--amount",
        help="positive transaction amount (prompts if omitted)",
    )
    add_parser.add_argument(
        "--category",
        help="transaction category (prompts if omitted)",
    )
    add_parser.add_argument(
        "--date",
        dest="transaction_date",
        help="transaction date in YYYY-MM-DD format (defaults to today)",
    )
    add_parser.add_argument(
        "--description",
        help="optional transaction description (defaults to empty)",
    )

    subparsers.add_parser("list", help="list saved transactions")

    report_parser = subparsers.add_parser(
        "report", help="display the financial summary and monthly/category reports"
    )
    report_parser.add_argument(
        "--month",
        type=_parse_month,
        default=(date.today().year, date.today().month),
        metavar="YYYY-MM",
        help="month to report on (defaults to the current month)",
    )

    export_parser = subparsers.add_parser("export", help="export transactions to CSV")
    default_csv_path = Path(__file__).resolve().parent / "data" / "transactions.csv"
    export_parser.add_argument(
        "--output",
        type=Path,
        default=default_csv_path,
        metavar="PATH",
        help=f"CSV destination (default: {default_csv_path})",
    )
    return parser


def _run_add_command(args: argparse.Namespace) -> None:
    transaction_type = args.transaction_type
    if transaction_type is None:
        transaction_type = input("Type (income/expense): ").strip()

    amount = args.amount if args.amount is not None else _read_amount()
    category = args.category if args.category is not None else _read_category()
    transaction_date = (
        args.transaction_date if args.transaction_date is not None else date.today().isoformat()
    )
    description = args.description or ""

    transaction_id = add_transaction(
        transaction_type=transaction_type,
        amount=amount,
        category=category,
        transaction_date=transaction_date,
        description=description,
        database_path=DEFAULT_DATABASE_PATH,
    )
    print(f"Success: {transaction_type.title()} transaction #{transaction_id} added.")


def _run_report_command(month: tuple[int, int]) -> None:
    year, month_number = month
    summary = get_financial_summary(DEFAULT_DATABASE_PATH)
    monthly = get_monthly_summary(year, month_number, DEFAULT_DATABASE_PATH)
    categories = get_category_expenses(
        DEFAULT_DATABASE_PATH, year=year, month=month_number
    )

    print("\nFinancial Summary")
    print(f"Total income:   ${summary['total_income']:.2f}")
    print(f"Total expenses: ${summary['total_expenses']:.2f}")
    print(f"Current balance: ${summary['balance']:.2f}")

    print(f"\nMonthly Summary: {year:04d}-{month_number:02d}")
    print(f"Income:   ${monthly['total_income']:.2f}")
    print(f"Expenses: ${monthly['total_expenses']:.2f}")
    print(f"Balance:  ${monthly['balance']:.2f}")

    print(f"\nExpense Categories for {year:04d}-{month_number:02d}")
    if not categories:
        print("No expenses recorded for this month.")
        return
    for item in categories:
        print(f"{item['category']:<18} ${item['total']:.2f}")
    highest = categories[0]
    print(
        f"Highest expense category: {highest['category']} "
        f"(${highest['total']:.2f})"
    )


def _run_command(args: argparse.Namespace) -> int:
    if args.command == "add":
        _run_add_command(args)
    elif args.command == "list":
        _print_transactions(DEFAULT_DATABASE_PATH)
    elif args.command == "report":
        _run_report_command(args.month)
    elif args.command == "export":
        count = export_transactions(args.output, DEFAULT_DATABASE_PATH)
        print(f"Success: exported {count} transaction(s) to {args.output}.")
    return 0


def main(argv: Optional[Sequence[str]] = None) -> int:
    """Run a subcommand, or preserve the interactive menu when no args are given."""
    arguments = list(sys.argv[1:] if argv is None else argv)
    if arguments:
        parser = _build_parser()
        args = parser.parse_args(arguments)
        try:
            return _run_command(args)
        except ValueError as error:
            parser.error(str(error))
        except sqlite3.Error as error:
            print(f"Database error: {error}", file=sys.stderr)
            return 1
        except OSError as error:
            print(f"File or directory error: {error}", file=sys.stderr)
            return 1

    try:
        initialize_database()
    except sqlite3.Error as error:
        print(f"Database error: {error}")
        return 1
    except OSError as error:
        print(f"File or directory error: {error}")
        return 1

    actions = {
        "1": lambda: _add_transaction("income"),
        "2": lambda: _add_transaction("expense"),
        "3": _print_transactions,
        "4": _edit_transaction,
        "5": _delete_transaction,
        "6": _show_financial_summary,
        "7": _show_monthly_report,
        "8": _show_category_report,
        "9": _export_to_csv,
    }
    while True:
        _show_menu()
        choice = input("Enter your choice: ").strip()
        if choice == "10":
            print("Goodbye! Your transactions are saved.")
            break
        action = actions.get(choice)
        if action is None:
            print("Error: please enter a menu number from 1 to 10.")
            continue
        try:
            action()
        except ValueError as error:
            print(f"Error: {error}")
        except sqlite3.Error as error:
            print(f"Database error: {error}")
        except OSError as error:
            print(f"File or directory error: {error}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
