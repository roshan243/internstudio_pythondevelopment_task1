"""Command-line interface for the personal finance tracker."""

from datetime import date
import sqlite3
from pathlib import Path

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


def _print_transactions() -> None:
    transactions = get_transactions()
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


def main() -> None:
    """Run the interactive menu until the user chooses to exit."""
    try:
        initialize_database()
    except sqlite3.Error as error:
        print(f"Database error: {error}")
        return
    except OSError as error:
        print(f"File or directory error: {error}")
        return

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


if __name__ == "__main__":
    main()
